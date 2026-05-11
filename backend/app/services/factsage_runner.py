# -*- coding: utf-8 -*-
"""FactSage 执行服务：调用 EquiSage.exe 或生成 mock 数据"""
from __future__ import annotations

import asyncio
import json
import logging
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict

from ..config import settings
from .res_parser import ResParser, parsed_result_to_dict

logger = logging.getLogger(__name__)


async def run_calculation(
    job_id: str, paths: Dict[str, Any]
) -> Path:
    """执行 FactSage 计算，返回 .res 文件路径。

    Args:
        job_id: 任务ID
        paths: 由 template_renderer.render_job_files 返回的路径字典

    Returns:
        result.res 文件的 Path
    """
    if settings.mock_mode:
        return await _mock_calculation(paths)
    return await _real_calculation(paths)


async def _real_calculation(paths: Dict[str, Any]) -> Path:
    """调用 EquiSage.exe 执行真实计算"""
    loop = asyncio.get_event_loop()
    rc = await loop.run_in_executor(
        None, _run_factsage_blocking, paths
    )
    if rc != 0:
        raise RuntimeError(f"FactSage 退出码: {rc}")

    res_path: Path = paths["out_dir"] / "result.res"
    if not res_path.exists():
        raise FileNotFoundError(f"FactSage 输出未找到: {res_path}")

    return res_path


def _run_factsage_blocking(paths: Dict[str, Any]) -> int:
    """同步调用 EquiSage.exe（在线程池中执行）"""
    exe = settings.factsage_exe
    if not exe.exists():
        raise FileNotFoundError(f"找不到 EquiSage.exe: {exe}")

    mac_path: Path = paths["mac_path"]
    run_log = Path(paths["out_dir"]) / "factsage_run.log"
    cmd = [str(exe), "/EQUILIB", "/MACRO", str(mac_path)]

    startupinfo = None
    if sys.platform == "win32":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 0  # SW_HIDE

    run_log.parent.mkdir(parents=True, exist_ok=True)
    with open(run_log, "w", encoding="utf-8") as f:
        f.write(f"cmd={cmd!r}\n")
        f.write(f"cwd={settings.factsage_dir}\n")
        f.write(f"mac_path={mac_path}\n")
        f.write(f"equi_path={paths.get('equi_path')}\n")
        f.write(f"out_dir={paths.get('out_dir')}\n")
        f.write(f"started_at={time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.flush()
        p = subprocess.Popen(
            cmd,
            cwd=str(settings.factsage_dir),
            startupinfo=startupinfo,
            stdout=f,
            stderr=subprocess.STDOUT,
        )
        try:
            rc = p.wait(timeout=settings.factsage_timeout)
        except subprocess.TimeoutExpired:
            p.kill()
            f.write(f"timeout_after_seconds={settings.factsage_timeout}\n")
            raise
        f.write(f"returncode={rc}\n")
        f.write(f"finished_at={time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        return rc


async def _mock_calculation(paths: Dict[str, Any]) -> Path:
    """Mock 模式：优先使用 demo/Equi2.res 的真实解析结果。"""
    await asyncio.sleep(settings.mock_delay)

    result_path = paths["out_dir"] / "parsed_result.json"
    result_path.parent.mkdir(parents=True, exist_ok=True)

    demo_res = _find_demo_res()
    if not demo_res.exists():
        raise FileNotFoundError(f"Mock 结果文件不存在: {demo_res}")

    parsed = ResParser().parse(demo_res)
    result = parsed_result_to_dict(parsed)
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False)
    return result_path


def _find_demo_res() -> Path:
    """定位开发环境中的 demo/Equi2.res。"""
    candidates = [
        settings.templates_dir.parent.parent / "demo" / "Equi2.res",
        settings.templates_dir.parent / "demo" / "Equi2.res",
    ]
    for path in candidates:
        if path.exists():
            return path
    return candidates[0]
