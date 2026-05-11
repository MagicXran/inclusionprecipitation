# -*- coding: utf-8 -*-
"""API 路由：任务提交 / 查询 / 模板 / 结果数据"""
from __future__ import annotations

import csv
import io
import json
import logging
import zipfile
from typing import List

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from ..config import settings
from ..models import (
    ChartDataResponse,
    ChartSeries,
    JobListItem,
    JobRequest,
    JobResponse,
    JobStatus,
    SpeciesListItem,
)
from ..services.job_manager import job_manager
from ..services.res_parser import filter_species_by_min_gram
from ..services.template_renderer import load_registry, load_template_meta

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["jobs"])


# ── 模板接口 ──────────────────────────────────────────────


@router.get("/templates")
async def list_templates():
    """列出所有可用模板"""
    reg = load_registry()
    return [
        {"id": t["id"], "name": t["name"], "description": t.get("description", "")}
        for t in reg.get("templates", [])
    ]


@router.get("/templates/{template_id}")
async def get_template(template_id: str):
    """获取模板详情（含元素列表和默认参数）"""
    try:
        meta = load_template_meta(template_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"模板 '{template_id}' 不存在")
    return meta


# ── 计算接口 ──────────────────────────────────────────────


@router.post("/calculate")
async def calculate(request: JobRequest) -> JobResponse:
    """提交一次计算任务"""
    # 检查模板存在
    try:
        load_template_meta(request.template_id)
    except FileNotFoundError:
        raise HTTPException(
            status_code=400, detail=f"模板 '{request.template_id}' 不存在"
        )

    job_id = await job_manager.submit(request)
    job = job_manager.get(job_id)
    return JobResponse(
        job_id=job_id,
        status=job["status"],
        template_id=job["template_id"],
        created_at=job["created_at"],
    )


@router.get("/jobs/{job_id}")
async def get_job(job_id: str) -> JobResponse:
    """查询任务状态"""
    job = job_manager.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="任务不存在")
    return JobResponse(
        job_id=job["job_id"],
        status=job["status"],
        template_id=job["template_id"],
        created_at=job["created_at"],
        error=job["error"],
    )


@router.get("/jobs/{job_id}/species")
async def get_species(
    job_id: str,
    min_gram: float = Query(
        settings.default_species_min_gram,
        ge=0,
        description="按物种最大质量过滤，单位 g",
    ),
) -> List[SpeciesListItem]:
    """获取物种列表（轻量，不含数据序列）"""
    result = job_manager.get_parsed_result(job_id)
    if result is None:
        job = job_manager.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="任务不存在")
        if job["status"] != JobStatus.completed:
            raise HTTPException(status_code=400, detail=f"任务状态: {job['status'].value}")
        raise HTTPException(status_code=404, detail="结果文件不存在")

    items = []
    for s in filter_species_by_min_gram(result["species"], min_gram):
        items.append(SpeciesListItem(
            name=s["name"],
            display_name=s["display_name"],
            category=s["category"],
            phase=s["phase"],
            max_gram=s["max_gram"],
        ))
    items.sort(key=lambda x: x.max_gram, reverse=True)
    return items


@router.get("/jobs/{job_id}/chart-data")
async def get_chart_data(
    job_id: str,
    species_names: str = Query(..., description="逗号分隔的物种名称"),
    value_type: str = Query("gram", description="数据类型: gram/mole/wt_pct/activity/mole_fraction"),
) -> ChartDataResponse:
    """获取选中物种的图表数据"""
    result = job_manager.get_parsed_result(job_id)
    if result is None:
        raise HTTPException(status_code=404, detail="结果不存在")

    names = [n.strip() for n in species_names.split(",") if n.strip()]
    if not names:
        raise HTTPException(status_code=400, detail="至少选择一个物种")

    # 值类型映射
    type_map = {
        "gram": "grams",
        "mole": "moles",
        "wt_pct": "wt_pcts",
        "activity": "activities",
        "mole_fraction": "mole_fractions",
    }
    data_key = type_map.get(value_type)
    if not data_key:
        raise HTTPException(status_code=400, detail=f"无效的值类型: {value_type}")

    # 构建 species 索引
    species_map = {s["name"]: s for s in result["species"]}

    series = []
    for name in names:
        s = species_map.get(name)
        if s is None:
            continue
        series.append(ChartSeries(
            name=s["name"],
            display_name=s["display_name"],
            data=s[data_key],
        ))

    return ChartDataResponse(
        temperatures=result["temperatures"],
        series=series,
    )


@router.get("/jobs/{job_id}/download")
async def download_result(job_id: str):
    """下载原始计算文件（.equi + .mac + .res 的 zip 包）"""
    job_dir = settings.work_root / job_id
    if not job_dir.exists():
        raise HTTPException(status_code=404, detail="任务目录不存在")

    files_to_zip = []
    for subdir in ("input", "out"):
        d = job_dir / subdir
        if d.exists():
            for f in d.iterdir():
                if f.is_file() and f.suffix in (".equi", ".mac", ".res"):
                    files_to_zip.append(f)
    if not files_to_zip:
        raise HTTPException(status_code=404, detail="无可下载的文件")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in files_to_zip:
            arcname = f"{p.parent.name}/{p.name}"
            zf.write(p, arcname)
    buf.seek(0)

    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{job_id}_result.zip"'
        },
    )


@router.get("/jobs/{job_id}/export-csv")
async def export_csv(
    job_id: str,
    value_type: str = Query("gram", description="数据类型"),
    min_gram: float = Query(
        settings.default_species_min_gram,
        ge=0,
        description="按物种最大质量过滤，单位 g",
    ),
):
    """导出选中的数据为 CSV"""
    result = job_manager.get_parsed_result(job_id)
    if result is None:
        raise HTTPException(status_code=404, detail="结果不存在")

    type_map = {
        "gram": "grams",
        "mole": "moles",
        "wt_pct": "wt_pcts",
        "activity": "activities",
        "mole_fraction": "mole_fractions",
    }
    data_key = type_map.get(value_type, "grams")

    # 只导出达到当前阈值的物种
    significant = filter_species_by_min_gram(result["species"], min_gram)
    significant.sort(key=lambda x: x["max_gram"], reverse=True)

    buf = io.StringIO()
    writer = csv.writer(buf)

    # 表头
    header = ["Temperature (°C)"] + [s["display_name"] for s in significant]
    writer.writerow(header)

    # 数据行
    for i, t in enumerate(result["temperatures"]):
        row = [t]
        for s in significant:
            vals = s[data_key]
            row.append(vals[i] if i < len(vals) else 0)
        writer.writerow(row)

    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{job_id}_{value_type}.csv"'
        },
    )


@router.get("/jobs")
async def list_jobs() -> List[JobListItem]:
    """列出所有任务"""
    return [
        JobListItem(
            job_id=j["job_id"],
            status=j["status"],
            template_id=j["template_id"],
            created_at=j["created_at"],
        )
        for j in job_manager.list_all()
    ]


@router.get("/config/info")
async def config_info():
    """返回当前运行模式信息"""
    return {
        "mock_mode": settings.mock_mode,
        "factsage_dir": str(settings.factsage_dir),
        "templates_dir": str(settings.templates_dir),
        "species_filter": {
            "default_min_gram": settings.default_species_min_gram,
            "options": settings.species_min_gram_options,
        },
    }
