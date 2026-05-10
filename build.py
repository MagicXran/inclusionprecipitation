# -*- coding: utf-8 -*-
"""PyInstaller 打包脚本"""
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DIST_NAME = "FactSage_InclPrecip"
BACKEND = ROOT / "backend"
ENTRY = BACKEND / "start.py"


def main():
    # 创建启动入口
    start_py = BACKEND / "start.py"
    start_py.write_text(
        '# -*- coding: utf-8 -*-\n'
        'import uvicorn\n'
        'from app.config import settings\n'
        'from app.main import app\n\n'
        'if __name__ == "__main__":\n'
        '    uvicorn.run(app, host=settings.server_host, port=settings.server_port)\n',
        encoding="utf-8",
    )

    dist_dir = ROOT / "dist" / DIST_NAME
    if dist_dir.exists():
        shutil.rmtree(dist_dir)

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--name", DIST_NAME,
        "--distpath", str(ROOT / "dist"),
        "--add-data", f"{BACKEND / 'templates'};templates",
        "--add-data", f"{ROOT / 'frontend'};frontend",
        "--hidden-import", "uvicorn.logging",
        "--hidden-import", "uvicorn.protocols.http.auto",
        "--hidden-import", "uvicorn.protocols.websockets.auto",
        "--hidden-import", "uvicorn.lifespan.on",
        str(start_py),
    ]

    print(f"执行: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)

    # 复制 config.json
    shutil.copy2(BACKEND / "config.json", dist_dir / "config.json")

    print(f"\n打包完成: {dist_dir}")
    print(f"运行: {dist_dir / (DIST_NAME + '.exe')}")


if __name__ == "__main__":
    main()
