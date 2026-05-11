# -*- coding: utf-8 -*-
"""PyInstaller 打包脚本：生成可迁移的 onedir 运行目录。"""
from __future__ import annotations

import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DIST_NAME = "FactSage_InclPrecip"
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"
DIST_ROOT = ROOT / "dist"
DIST_DIR = DIST_ROOT / DIST_NAME
BUILD_ROOT = DIST_ROOT / "_build"
PYINSTALLER_WORK = DIST_ROOT / "_pyinstaller_work"
PYINSTALLER_SPEC = DIST_ROOT / "_pyinstaller_spec"
ENTRY = BUILD_ROOT / "start.py"
STAGED_FRONTEND = BUILD_ROOT / "frontend"

ECHARTS_URL = "https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"
ECHARTS_REL = Path("vendor") / "echarts.min.js"
ECHARTS_CDN_SNIPPET = (
    '<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>'
)
ECHARTS_LOCAL_SNIPPET = '<script src="vendor/echarts.min.js"></script>'


def _remove_tree(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)


def _write_entry() -> None:
    """生成 PyInstaller 入口，放在 dist 临时目录，避免污染源码树。"""
    ENTRY.parent.mkdir(parents=True, exist_ok=True)
    ENTRY.write_text(
        '# -*- coding: utf-8 -*-\n'
        '"""Frozen service entrypoint."""\n'
        'import uvicorn\n'
        'from app.config import settings\n'
        'from app.main import app\n\n'
        'if __name__ == "__main__":\n'
        '    uvicorn.run(app, host=settings.server_host, port=settings.server_port)\n',
        encoding="utf-8",
    )


def _stage_frontend() -> None:
    """复制前端并替换 CDN 依赖，确保打包产物离线可用。"""
    _remove_tree(STAGED_FRONTEND)
    shutil.copytree(FRONTEND, STAGED_FRONTEND)

    vendor_dir = STAGED_FRONTEND / ECHARTS_REL.parent
    vendor_dir.mkdir(parents=True, exist_ok=True)

    source_echarts = FRONTEND / ECHARTS_REL
    staged_echarts = STAGED_FRONTEND / ECHARTS_REL
    if source_echarts.exists():
        shutil.copy2(source_echarts, staged_echarts)
    else:
        print(f"下载前端离线依赖: {ECHARTS_URL}")
        urllib.request.urlretrieve(ECHARTS_URL, staged_echarts)

    index_path = STAGED_FRONTEND / "index.html"
    index_html = index_path.read_text(encoding="utf-8-sig")
    if ECHARTS_CDN_SNIPPET in index_html:
        index_html = index_html.replace(ECHARTS_CDN_SNIPPET, ECHARTS_LOCAL_SNIPPET)
    elif ECHARTS_LOCAL_SNIPPET not in index_html:
        raise RuntimeError("index.html 中未找到 ECharts 脚本引用，无法保证离线前端。")
    index_path.write_text(index_html, encoding="utf-8", newline="\n")


def _copy_runtime_assets() -> None:
    """复制运行时可变/可配置资产到 exe 同级目录。"""
    shutil.copy2(BACKEND / "config.json", DIST_DIR / "config.json")

    for source, target_name in (
        (BACKEND / "templates", "templates"),
        (STAGED_FRONTEND, "frontend"),
    ):
        target = DIST_DIR / target_name
        _remove_tree(target)
        shutil.copytree(source, target)

    demo_dir = ROOT / "demo"
    packaged_demo = DIST_DIR / "demo"
    _remove_tree(packaged_demo)
    packaged_demo.mkdir(parents=True, exist_ok=True)
    for name in ("Equi2.res", "Equ2222i.res"):
        source = demo_dir / name
        if source.exists():
            shutil.copy2(source, packaged_demo / name)

    for dirname in ("data", "work", "results"):
        (DIST_DIR / dirname).mkdir(parents=True, exist_ok=True)


def _run_pyinstaller() -> None:
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onedir",
        "--name",
        DIST_NAME,
        "--distpath",
        str(DIST_ROOT),
        "--workpath",
        str(PYINSTALLER_WORK),
        "--specpath",
        str(PYINSTALLER_SPEC),
        "--paths",
        str(BACKEND),
        "--hidden-import",
        "uvicorn.logging",
        "--hidden-import",
        "uvicorn.protocols.http.auto",
        "--hidden-import",
        "uvicorn.protocols.websockets.auto",
        "--hidden-import",
        "uvicorn.lifespan.on",
        str(ENTRY),
    ]

    print(f"执行: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)


def main() -> None:
    _remove_tree(DIST_DIR)
    _remove_tree(PYINSTALLER_WORK)
    _remove_tree(PYINSTALLER_SPEC)
    _remove_tree(BUILD_ROOT)

    _write_entry()
    _stage_frontend()
    _run_pyinstaller()
    _copy_runtime_assets()

    print(f"\n打包完成: {DIST_DIR}")
    print(f"运行: {DIST_DIR / (DIST_NAME + '.exe')}")
    print("迁移时复制整个目录，不要只复制 exe。")


if __name__ == "__main__":
    main()
