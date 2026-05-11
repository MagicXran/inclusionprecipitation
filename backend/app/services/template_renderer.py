# -*- coding: utf-8 -*-
"""模板渲染：简单 {{KEY}} 占位符替换，生成 .equi 和 .mac 文件"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List


from ..config import settings


# ── 注册表 / 元数据加载 ────────────────────────────────

def load_registry() -> dict:
    """加载 templates/registry.json"""
    registry_path = settings.templates_dir / "registry.json"
    with open(registry_path, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def load_template_meta(template_id: str) -> dict:
    """加载 templates/{template_id}/meta.json"""
    meta_path = settings.templates_dir / template_id / "meta.json"
    if not meta_path.exists():
        raise FileNotFoundError(f"模板 '{template_id}' 的 meta.json 不存在: {meta_path}")
    with open(meta_path, "r", encoding="utf-8-sig") as f:
        return json.load(f)


# ── 文件 I/O ────────────────────────────────────────────

def _read_text(path: Path) -> str:
    """读取模板文件（兼容 BOM），统一行尾为 \\n"""
    raw = path.read_bytes().decode("utf-8-sig")
    raw = raw.replace("\r\r\n", "\n").replace("\r\n", "\n").replace("\r", "\n")
    return raw


def _write_text(path: Path, text: str) -> None:
    """写出文件，统一使用 Windows CRLF 行尾，UTF-8 无 BOM"""
    path.parent.mkdir(parents=True, exist_ok=True)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\n", "\r\n")
    path.write_text(text, encoding="utf-8", newline="")


def _macro_path(path: Path) -> str:
    """FactSage 宏里使用保守的绝对 Windows 路径。"""
    return str(path.resolve()).replace("/", "\\")


def _render_tpl(template_text: str, variables: Dict[str, str]) -> str:
    """简单 {{KEY}} → value 替换"""
    result = template_text
    for key, value in variables.items():
        result = result.replace("{{" + key + "}}", str(value))
    remaining = re.findall(r"\{\{(\w+)\}\}", result)
    if remaining:
        raise ValueError(f"模板中存在未替换的占位符: {remaining}")
    return result


def _mass_placeholders(template_text: str) -> list[str]:
    """提取模板中的 MASS_* 元素占位符。"""
    return re.findall(r"\{\{MASS_([A-Z][a-z]?)\}\}", template_text)


def _validate_template_contract(template_id: str, meta: dict, template_text: str) -> None:
    """确保 meta 元素全集与 .equi.tpl 占位符一一对应。"""
    meta_symbols = [e["symbol"] for e in meta.get("supported_elements", [])]
    if len(meta_symbols) != len(set(meta_symbols)):
        duplicated = sorted({s for s in meta_symbols if meta_symbols.count(s) > 1})
        raise ValueError(f"模板 '{template_id}' 的 meta.json 存在重复元素: {duplicated}")

    placeholders = _mass_placeholders(template_text)
    if len(placeholders) != len(set(placeholders)):
        duplicated = sorted({s for s in placeholders if placeholders.count(s) > 1})
        raise ValueError(f"模板 '{template_id}' 的 case.equi.tpl 存在重复占位符: {duplicated}")

    meta_set = set(meta_symbols)
    placeholder_set = set(placeholders)
    missing = sorted(meta_set - placeholder_set)
    extra = sorted(placeholder_set - meta_set)
    if missing or extra:
        raise ValueError(
            f"模板 '{template_id}' 的 meta 与占位符不一致: "
            f"meta未出现在模板={missing}, 模板未登记={extra}"
        )


def _build_mass_variables(
    template_id: str,
    meta: dict,
    elements: List[Dict[str, Any]],
) -> Dict[str, str]:
    """用户提交值覆盖 meta 默认值，缺失元素由后端兜底补齐。"""
    element_defs = meta.get("supported_elements", [])
    supported = {e["symbol"]: e for e in element_defs}
    variables: Dict[str, str] = {}
    seen: set[str] = set()

    for elem in elements:
        symbol = elem["symbol"]
        if symbol in seen:
            raise ValueError(f"模板 '{template_id}' 收到重复元素: {symbol}")
        if symbol not in supported:
            raise ValueError(f"模板 '{template_id}' 不支持元素: {symbol}")
        seen.add(symbol)
        variables[f"MASS_{symbol}"] = str(elem["mass_g"])

    for symbol, elem_def in supported.items():
        key = f"MASS_{symbol}"
        if key not in variables:
            variables[key] = str(elem_def.get("default_g", 1e-10))

    return variables


# ── 主渲染函数 ──────────────────────────────────────────

def render_job_files(
    job_id: str,
    template_id: str,
    elements: List[Dict[str, Any]],
    temp_range: Dict[str, Any],
) -> Dict[str, Any]:
    """渲染 .equi 和 .mac 文件。

    Args:
        job_id: 任务唯一标识
        template_id: 模板 ID（如 "high_alloy_incl"）
        elements: 元素列表，每项含 {"symbol": "C", "mass_g": 0.35}
        temp_range: 温度范围，含 start_c / end_c / step_c / pressure_atm

    Returns:
        dict: job_dir, in_dir, out_dir, equi_path, mac_path
    """
    # 1) 创建工作目录
    job_dir = settings.work_root / job_id
    in_dir = job_dir / "input"
    out_dir = job_dir / "out"
    in_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 2) 读取模板元数据和 .equi.tpl 模板
    meta = load_template_meta(template_id)
    tpl_path = settings.templates_dir / template_id / "case.equi.tpl"
    if not tpl_path.exists():
        raise FileNotFoundError(f"模板文件不存在: {tpl_path}")
    tpl_text = _read_text(tpl_path)
    _validate_template_contract(template_id, meta, tpl_text)

    # 3) 构建替换变量
    variables = _build_mass_variables(template_id, meta, elements)
    variables["T_START"] = str(temp_range.get("start_c", 800))
    variables["T_END"] = str(temp_range.get("end_c", 1600))
    variables["T_STEP"] = str(temp_range.get("step_c", 10))
    variables["P_ATM"] = str(temp_range.get("pressure_atm", 1.0))

    # 4) 渲染 .equi
    equi_text = _render_tpl(tpl_text, variables)
    equi_path = in_dir / "case.equi"
    _write_text(equi_path, equi_text)

    # 5) 生成 .mac 文件（通用格式，所有模板共享）
    equi_macro_path = _macro_path(equi_path)
    result_macro_path = _macro_path(out_dir / "result.res")
    mac_text = (
        "VARIABLE %EquiFile %OutFile\r\n"
        "HIDE\r\n"
        "HIDE_MACRO\r\n"
        f"%EquiFile = \"{equi_macro_path}\"\r\n"
        f"%OutFile = \"{result_macro_path}\"\r\n"
        "\r\n"
        "OPEN %EquiFile\r\n"
        "CALC\r\n"
        "SAVE %OutFile\r\n"
        "\r\n"
        "END\r\n"
    )
    mac_path = in_dir / "case.mac"
    # mac_text 已经包含 CRLF，直接写出
    mac_path.parent.mkdir(parents=True, exist_ok=True)
    mac_path.write_text(mac_text, encoding="utf-8", newline="")

    return {
        "template_id": template_id,
        "job_dir": job_dir,
        "in_dir": in_dir,
        "out_dir": out_dir,
        "equi_path": equi_path,
        "mac_path": mac_path,
    }
