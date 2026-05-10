# -*- coding: utf-8 -*-
"""FastAPI 应用入口"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .config import settings
from .routers import jobs
from .services.job_manager import job_manager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "启动 FactSage 夹杂物/析出相计算服务  mock=%s  port=%d",
        settings.mock_mode, settings.server_port,
    )
    await job_manager.start()
    yield
    await job_manager.stop()


app = FastAPI(
    title="FactSage 夹杂物/析出相计算",
    description="基于 FactSage Equilib 模块的温度扫描计算 API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(
        "422 验证失败  url=%s  errors=%s", request.url, exc.errors()
    )
    return JSONResponse(status_code=422, content={"detail": exc.errors()})


app.include_router(jobs.router)

_FE = settings.frontend_dir
if _FE.exists():
    app.mount("/css", StaticFiles(directory=_FE / "css"), name="css")
    app.mount("/js", StaticFiles(directory=_FE / "js"), name="js")

    @app.get("/")
    async def index():
        return FileResponse(_FE / "index.html")
else:
    logger.warning("前端目录不存在: %s，仅提供 API 服务", _FE)
