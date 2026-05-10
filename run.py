# -*- coding: utf-8 -*-
"""开发模式入口：python run.py"""
import sys
from pathlib import Path

# 确保 backend 在 sys.path 中
backend_dir = Path(__file__).resolve().parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import uvicorn
from app.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.server_host,
        port=settings.server_port,
        reload=True,
        reload_dirs=[str(backend_dir / "app")],
    )
