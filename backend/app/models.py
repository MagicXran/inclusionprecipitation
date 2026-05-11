# -*- coding: utf-8 -*-
"""Pydantic 数据模型 —— API 请求/响应定义"""
from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


# ── 枚举 ──────────────────────────────────────────────


class JobStatus(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


# ── 请求模型 ──────────────────────────────────────────


class ElementMass(BaseModel):
    symbol: str
    mass_g: float = Field(..., ge=0)


class TempRange(BaseModel):
    start_c: float = Field(800, ge=0)
    end_c: float = Field(1600, ge=0)
    step_c: float = Field(10, gt=0)
    pressure_atm: float = Field(1.0, gt=0)

    @field_validator("end_c")
    @classmethod
    def end_gt_start(cls, v, info):
        if "start_c" in info.data and v <= info.data["start_c"]:
            raise ValueError("end_c must be greater than start_c")
        return v


class JobRequest(BaseModel):
    template_id: str
    elements: list[ElementMass]
    temp_range: TempRange = Field(default_factory=TempRange)

    @field_validator("elements")
    @classmethod
    def validate_elements(cls, v):
        symbols = [e.symbol for e in v]
        if len(symbols) != len(set(symbols)):
            raise ValueError("Duplicate element symbols")
        # 只统计有效质量元素（排除 1E-10 级别的痕量占位）
        total = sum(e.mass_g for e in v if e.mass_g > 0.001)
        if abs(total - 100.0) > 5.0:
            raise ValueError(f"Total mass must be ~100g, got {total:.2f}g")
        return v


class ChartDataRequest(BaseModel):
    species_names: list[str]
    value_type: str = Field(
        "gram", pattern="^(gram|mole|wt_pct|activity|mole_fraction)$"
    )


# ── 响应模型 ──────────────────────────────────────────


class SpeciesListItem(BaseModel):
    name: str
    display_name: str
    category: str
    phase: str
    max_gram: float


class ChartSeries(BaseModel):
    name: str
    display_name: str
    data: list[float]


class ChartDataResponse(BaseModel):
    temperatures: list[float]
    series: list[ChartSeries]


class JobResponse(BaseModel):
    job_id: str
    status: JobStatus
    template_id: Optional[str] = None
    created_at: Optional[str] = None
    error: Optional[str] = None


class JobListItem(BaseModel):
    job_id: str
    status: JobStatus
    template_id: str
    created_at: str
