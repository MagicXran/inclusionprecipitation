# -*- coding: utf-8 -*-
"""template_renderer 单元测试"""
from __future__ import annotations

import json
import re
import sys
import asyncio
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.template_renderer import (
    load_registry,
    load_template_meta,
    _macro_path,
    render_job_files,
)
from app.models import JobRequest
from app.services.factsage_runner import _mock_calculation


def _reactant_masses(equi_text):
    """提取反应物质量行里的元素质量，忽略候选相列表。"""
    pairs = re.findall(
        r"([0-9]+(?:\.[0-9]+)?(?:[eE][+-]?\d+)?)\s+([A-Z][a-z]?)\s*(?=[+=])",
        equi_text,
    )
    return {symbol: mass for mass, symbol in pairs}


def _template_mass_placeholders():
    tpl_path = (
        Path(__file__).resolve().parent.parent
        / "templates" / "high_alloy_incl" / "case.equi.tpl"
    )
    text = tpl_path.read_text(encoding="utf-8-sig")
    return re.findall(r"\{\{MASS_([A-Z][a-z]?)\}\}", text)


class TestRegistry:
    def test_load_registry(self):
        """registry.json 应可正常加载"""
        reg = load_registry()
        assert "templates" in reg
        assert len(reg["templates"]) >= 1

    def test_registry_has_high_alloy(self):
        """应包含 high_alloy_incl 模板"""
        reg = load_registry()
        ids = [t["id"] for t in reg["templates"]]
        assert "high_alloy_incl" in ids


class TestTemplateMeta:
    def test_load_meta(self):
        """meta.json 应包含必要字段"""
        meta = load_template_meta("high_alloy_incl")
        assert meta["id"] == "high_alloy_incl"
        assert "supported_elements" in meta
        assert "default_temp" in meta

    def test_meta_elements(self):
        """元素列表应包含 Fe 和 O"""
        meta = load_template_meta("high_alloy_incl")
        symbols = [e["symbol"] for e in meta["supported_elements"]]
        assert "Fe" in symbols
        assert "O" in symbols

    def test_meta_has_22_unique_grouped_elements(self):
        """meta.json 是 22 元素全集，且每个元素都有 UI 分组。"""
        meta = load_template_meta("high_alloy_incl")
        elements = meta["supported_elements"]
        symbols = [e["symbol"] for e in elements]

        assert len(symbols) == 22
        assert len(set(symbols)) == 22
        assert all(e.get("group") in {"base", "major", "micro", "trace"} for e in elements)

    def test_template_placeholders_match_meta_once(self):
        """模板 MASS_* 占位符必须与 meta 元素一一对应，无重复。"""
        meta = load_template_meta("high_alloy_incl")
        meta_symbols = {e["symbol"] for e in meta["supported_elements"]}
        placeholders = _template_mass_placeholders()

        assert len(placeholders) == 22
        assert len(set(placeholders)) == 22
        assert set(placeholders) == meta_symbols

    def test_meta_not_found(self):
        """不存在的模板应抛出 FileNotFoundError"""
        with pytest.raises(FileNotFoundError):
            load_template_meta("nonexistent_template")


class TestJobRequestValidation:
    def test_duplicate_element_rejected(self):
        """API 请求层应拒绝重复元素。"""
        with pytest.raises(ValueError, match="Duplicate element symbols"):
            JobRequest.model_validate({
                "template_id": "high_alloy_incl",
                "elements": [
                    {"symbol": "Fe", "mass_g": 99.0},
                    {"symbol": "Fe", "mass_g": 1.0},
                ],
            })

    def test_total_mass_tolerance_is_5g(self):
        """有效质量允许 95-105g，超过才拒绝。"""
        JobRequest.model_validate({
            "template_id": "high_alloy_incl",
            "elements": [{"symbol": "Fe", "mass_g": 95.0}],
        })

        with pytest.raises(ValueError, match="Total mass must be ~100g"):
            JobRequest.model_validate({
                "template_id": "high_alloy_incl",
                "elements": [{"symbol": "Fe", "mass_g": 94.9}],
            })


def _full_elements(overrides=None):
    """构建完整 22 元素列表，缺省元素用 1e-10 填充"""
    defaults = {
        "C": 0.35, "W": 1e-10, "Mo": 0.8, "Cr": 32.0,
        "Ti": 5.4, "Al": 2.4, "B": 1e-10, "Zr": 1e-10,
        "Fe": 58.785, "O": 0.01, "Si": 1e-10, "Mn": 1e-10,
        "P": 1e-10, "S": 1e-10, "Ni": 1e-10, "V": 1e-10,
        "Ca": 1e-10, "Cu": 1e-10, "Co": 1e-10,
        "Nb": 1e-10, "Mg": 1e-10, "N": 1e-10,
    }
    if overrides:
        defaults.update(overrides)
    return [{"symbol": s, "mass_g": m} for s, m in defaults.items()]


class TestRenderJobFiles:
    def test_render_creates_files(self, tmp_path, monkeypatch):
        """渲染应生成 .equi 和 .mac 文件"""
        from app.config import settings
        monkeypatch.setattr(settings, "_cfg", {
            **settings._cfg,
            "paths": {**settings._cfg["paths"], "work_root": str(tmp_path)},
        })
        # 强制 work_root 返回 tmp_path
        monkeypatch.setattr(type(settings), "work_root", property(lambda self: tmp_path))

        elements = _full_elements()
        temp_range = {"start_c": 800, "end_c": 1600, "step_c": 10, "pressure_atm": 1.0}

        paths = render_job_files("test001", "high_alloy_incl", elements, temp_range)

        assert paths["equi_path"].exists()
        assert paths["mac_path"].exists()

    def test_rendered_equi_has_correct_values(self, tmp_path, monkeypatch):
        """渲染后的 .equi 应包含正确的元素质量和温度"""
        from app.config import settings
        monkeypatch.setattr(type(settings), "work_root", property(lambda self: tmp_path))

        elements = _full_elements({
            "C": 0.5, "W": 0.1, "Mo": 1.0, "Cr": 25.0,
            "Ti": 3.0, "Al": 1.5, "B": 0.01, "Zr": 0.1,
            "Fe": 68.77, "O": 0.02,
        })
        temp_range = {"start_c": 900, "end_c": 1500, "step_c": 5, "pressure_atm": 1.0}

        paths = render_job_files("test002", "high_alloy_incl", elements, temp_range)
        content = paths["equi_path"].read_text(encoding="utf-8")

        # 检查元素质量已替换
        assert "0.5 C" in content
        assert "25.0 Cr" in content
        assert "68.77 Fe" in content
        # 检查温度已替换
        assert "'900 1500 5'" in content
        # 确保没有残留占位符
        assert "{{" not in content

    def test_rendered_equi_crlf(self, tmp_path, monkeypatch):
        """渲染后的 .equi 应使用 CRLF 行尾"""
        from app.config import settings
        monkeypatch.setattr(type(settings), "work_root", property(lambda self: tmp_path))

        elements = _full_elements()
        temp_range = {"start_c": 800, "end_c": 1600, "step_c": 10, "pressure_atm": 1.0}

        paths = render_job_files("test003", "high_alloy_incl", elements, temp_range)
        raw = paths["equi_path"].read_bytes()

        assert b"\r\n" in raw, "输出文件应包含 CRLF"
        # 确保没有孤立的 LF（去掉 CRLF 后不应有 LF）
        cleaned = raw.replace(b"\r\n", b"")
        assert b"\n" not in cleaned, "不应有孤立的 LF（应全部是 CRLF）"

    def test_rendered_mac_has_paths(self, tmp_path, monkeypatch):
        """渲染后的 .mac 应包含正确的文件路径"""
        from app.config import settings
        monkeypatch.setattr(type(settings), "work_root", property(lambda self: tmp_path))

        elements = _full_elements()
        temp_range = {"start_c": 800, "end_c": 1600, "step_c": 10, "pressure_atm": 1.0}

        paths = render_job_files("test004", "high_alloy_incl", elements, temp_range)
        mac_text = paths["mac_path"].read_text(encoding="utf-8")

        assert "OPEN" in mac_text
        assert "CALC" in mac_text
        assert "SAVE" in mac_text
        assert "result.res" in mac_text
        assert "%OutDir" not in mac_text
        assert "%OutFile" in mac_text
        assert f'%EquiFile = "{_macro_path(paths["equi_path"])}"' in mac_text
        assert f'%OutFile = "{_macro_path(paths["out_dir"] / "result.res")}"' in mac_text
        assert 'SAVE %OutFile' in mac_text

    def test_missing_elements_use_meta_defaults(self, tmp_path, monkeypatch):
        """用户只提交部分元素时，后端应按 meta 默认值补齐全集。"""
        from app.config import settings
        monkeypatch.setattr(type(settings), "work_root", property(lambda self: tmp_path))

        elements = [
            {"symbol": "C", "mass_g": 0.35},
            {"symbol": "Cr", "mass_g": 32.0},
            {"symbol": "Fe", "mass_g": 67.64},
            {"symbol": "O", "mass_g": 0.01},
        ]
        temp_range = {"start_c": 800, "end_c": 1600, "step_c": 10, "pressure_atm": 1.0}

        paths = render_job_files("test005", "high_alloy_incl", elements, temp_range)
        content = paths["equi_path"].read_text(encoding="utf-8")
        reactants = _reactant_masses(content)

        assert len(reactants) == 22
        assert reactants["Fe"] == "67.64"
        assert reactants["W"] == "1e-10"
        assert reactants["Nb"] == "1e-10"
        assert "{{" not in content

    def test_duplicate_input_element_raises(self, tmp_path, monkeypatch):
        """重复提交同一元素应报错，不能静默覆盖。"""
        from app.config import settings
        monkeypatch.setattr(type(settings), "work_root", property(lambda self: tmp_path))

        elements = [
            {"symbol": "Fe", "mass_g": 99.0},
            {"symbol": "Fe", "mass_g": 98.0},
            {"symbol": "O", "mass_g": 0.01},
        ]
        temp_range = {"start_c": 800, "end_c": 1600, "step_c": 10, "pressure_atm": 1.0}

        with pytest.raises(ValueError, match="重复元素"):
            render_job_files("test006", "high_alloy_incl", elements, temp_range)

    def test_unknown_input_element_raises(self, tmp_path, monkeypatch):
        """提交模板不支持的元素应报错，不能悄悄丢弃。"""
        from app.config import settings
        monkeypatch.setattr(type(settings), "work_root", property(lambda self: tmp_path))

        elements = [
            {"symbol": "Fe", "mass_g": 99.0},
            {"symbol": "O", "mass_g": 0.01},
            {"symbol": "H", "mass_g": 0.01},
        ]
        temp_range = {"start_c": 800, "end_c": 1600, "step_c": 10, "pressure_atm": 1.0}

        with pytest.raises(ValueError, match="不支持元素"):
            render_job_files("test007", "high_alloy_incl", elements, temp_range)


class TestMockCalculation:
    def test_mock_uses_demo_res_species(self, tmp_path):
        """Mock 模式应使用 demo/Equi2.res，而不是 5 条假曲线。"""
        paths = {"out_dir": tmp_path / "out"}

        result_path = asyncio.run(_mock_calculation(paths))
        result = json.loads(result_path.read_text(encoding="utf-8"))
        significant = [s for s in result["species"] if s["max_gram"] >= 1e-8]

        assert result["n_steps"] == 94
        assert len(result["species"]) == 1686
        assert len(significant) > 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
