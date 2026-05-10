# -*- coding: utf-8 -*-
"""FactSage 执行服务：调用 EquiSage.exe 或生成 mock 数据"""
from __future__ import annotations

import asyncio
import logging
import math
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict

from ..config import settings

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
        None, _run_factsage_blocking, paths["mac_path"]
    )
    if rc != 0:
        raise RuntimeError(f"FactSage 退出码: {rc}")

    res_path: Path = paths["out_dir"] / "result.res"
    if not res_path.exists():
        raise FileNotFoundError(f"FactSage 输出未找到: {res_path}")

    return res_path


def _run_factsage_blocking(mac_path: Path) -> int:
    """同步调用 EquiSage.exe（在线程池中执行）"""
    exe = settings.factsage_exe
    if not exe.exists():
        raise FileNotFoundError(f"找不到 EquiSage.exe: {exe}")

    cmd = [str(exe), "/EQUILIB", "/MACRO", str(mac_path)]

    startupinfo = None
    if sys.platform == "win32":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 0  # SW_HIDE

    p = subprocess.Popen(
        cmd, cwd=str(settings.factsage_dir), startupinfo=startupinfo
    )
    return p.wait(timeout=settings.factsage_timeout)


async def _mock_calculation(paths: Dict[str, Any]) -> Path:
    """Mock 模式：直接生成 parsed_result.json（跳过 .res 解析）。

    .res 格式太复杂（127K 字符/行），不值得在 mock 中模拟。
    直接输出解析器的最终产物，由 job_manager 识别并跳过解析步骤。
    """
    await asyncio.sleep(settings.mock_delay)
    equi_path: Path = paths["equi_path"]
    t_start, t_end, t_step = _extract_temp_range(equi_path)
    elements = _extract_elements(equi_path)

    result_path = paths["out_dir"] / "parsed_result.json"
    _generate_mock_result(result_path, t_start, t_end, t_step, elements)
    return result_path


def _extract_temp_range(equi_path: Path) -> tuple[float, float, float]:
    """从渲染后的 .equi 文件中提取温度范围"""
    text = equi_path.read_text(encoding="utf-8")
    for line in text.splitlines():
        if "'T'" in line and "'P'" in line:
            # 格式: 'T' '800 1600 10' 'P' '1' 'DH' ''
            parts = line.split("'")
            for i, p in enumerate(parts):
                if p.strip() == "T" and i + 2 < len(parts):
                    t_str = parts[i + 2].strip()
                    vals = t_str.split()
                    if len(vals) >= 3:
                        return float(vals[0]), float(vals[1]), float(vals[2])
    return 800.0, 1600.0, 10.0


def _extract_elements(equi_path: Path) -> Dict[str, float]:
    """从渲染后的 .equi 文件中提取元素质量"""
    import re
    text = equi_path.read_text(encoding="utf-8")
    elements: Dict[str, float] = {}
    for line in text.splitlines():
        # 匹配: 0.35 C  +  0.2 W  + ...  或  58.785 Fe  +  0.01 O  =
        matches = re.findall(r"([\d.]+)\s+([A-Z][a-z]?)\s+[+=]", line)
        for mass_str, symbol in matches:
            elements[symbol] = float(mass_str)
    return elements


def _generate_mock_result(
    result_path: Path,
    t_start: float,
    t_end: float,
    t_step: float,
    elements: Dict[str, float],
) -> None:
    """直接生成 parsed_result.json — 与 res_parser 输出格式一致。"""
    import json

    result_path.parent.mkdir(parents=True, exist_ok=True)
    temps = []
    t = t_start
    while t <= t_end + 0.01:
        temps.append(round(t, 4))
        t += t_step

    total_mass = sum(elements.values())
    n_steps = len(temps)

    def _curve(temps_list, func):
        return [round(func(t), 8) for t in temps_list]

    species = []

    # Liquid: 随温度升高增多
    liq_grams = _curve(temps, lambda t: total_mass * min(1.0, ((t - t_start) / (t_end - t_start)) * 1.2))
    species.append({
        "name": "FSstel-Liqu#1", "display_name": "Liquid #1 (total)",
        "category": "solution_total", "phase": "SOLUTION", "db": "FSstel",
        "max_gram": max(liq_grams), "grams": liq_grams,
        "moles": [g / 56.0 for g in liq_grams],
        "activities": [1.0] * n_steps, "mole_fractions": [1.0] * n_steps,
        "wt_pcts": [g / total_mass * 100 for g in liq_grams],
    })

    # FCC: 中温峰值
    fcc_grams = _curve(temps, lambda t: (
        total_mass * 0.3 * math.exp(-(((t - t_start) / (t_end - t_start) - 0.4) ** 2) / 0.05)
        if (t - t_start) / (t_end - t_start) < 0.9 else 0
    ))
    species.append({
        "name": "FSstel-FCC#1", "display_name": "\u03b3-FCC #1 (total)",
        "category": "solution_total", "phase": "SOLUTION", "db": "FSstel",
        "max_gram": max(fcc_grams), "grams": fcc_grams,
        "moles": [g / 56.0 for g in fcc_grams],
        "activities": [1.0] * n_steps, "mole_fractions": [0.5] * n_steps,
        "wt_pcts": [g / total_mass * 100 for g in fcc_grams],
    })

    # BCC: 低温为主
    bcc_grams = _curve(temps, lambda t: total_mass * max(0, 0.8 * (1 - ((t - t_start) / (t_end - t_start)) * 1.1)))
    species.append({
        "name": "FSstel-BCC#1", "display_name": "\u03b1-BCC #1 (total)",
        "category": "solution_total", "phase": "SOLUTION", "db": "FSstel",
        "max_gram": max(bcc_grams), "grams": bcc_grams,
        "moles": [g / 56.0 for g in bcc_grams],
        "activities": [1.0] * n_steps, "mole_fractions": [0.5] * n_steps,
        "wt_pcts": [g / total_mass * 100 for g in bcc_grams],
    })

    # TiN: 中间温度区间析出
    ti_mass = elements.get("Ti", 0)
    if ti_mass > 0:
        tin_grams = _curve(temps, lambda t: ti_mass * 0.1 * max(0, 1 - abs((t - t_start) / (t_end - t_start) - 0.5) * 4))
        species.append({
            "name": "FactPS-TiN(s)", "display_name": "TiN",
            "category": "pure", "phase": "PURE", "db": "FactPS",
            "max_gram": max(tin_grams), "grams": tin_grams,
            "moles": [g / 62.0 for g in tin_grams],
            "activities": [1.0] * n_steps, "mole_fractions": [0.0] * n_steps,
            "wt_pcts": [g / total_mass * 100 for g in tin_grams],
        })

    # Al2O3: 痕量氧化物
    al_mass = elements.get("Al", 0)
    if al_mass > 0:
        al2o3_grams = _curve(temps, lambda t: al_mass * 0.01 * max(0, 1 - (t - t_start) / (t_end - t_start)))
        species.append({
            "name": "FactPS-Al2O3(s)", "display_name": "Al2O3",
            "category": "pure", "phase": "PURE", "db": "FactPS",
            "max_gram": max(al2o3_grams), "grams": al2o3_grams,
            "moles": [g / 102.0 for g in al2o3_grams],
            "activities": [1.0] * n_steps, "mole_fractions": [0.0] * n_steps,
            "wt_pcts": [g / total_mass * 100 for g in al2o3_grams],
        })

    result = {
        "temperatures": temps,
        "n_steps": n_steps,
        "n_solutions": 3,
        "version": "8.3-mock",
        "reactant_summary": " + ".join(f"{v}g {k}" for k, v in elements.items()),
        "species": species,
    }

    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False)
