# -*- coding: utf-8 -*-
"""template_renderer 单元测试"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.template_renderer import (
    load_registry,
    load_template_meta,
    render_job_files,
)


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

    def test_meta_not_found(self):
        """不存在的模板应抛出 FileNotFoundError"""
        with pytest.raises(FileNotFoundError):
            load_template_meta("nonexistent_template")


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

    def test_missing_placeholder_raises(self, tmp_path, monkeypatch):
        """缺少占位符值应抛出 ValueError"""
        from app.config import settings
        monkeypatch.setattr(type(settings), "work_root", property(lambda self: tmp_path))

        # 故意缺少 Mo
        elements = [
            {"symbol": "C", "mass_g": 0.35},
            {"symbol": "Fe", "mass_g": 99.0},
        ]
        temp_range = {"start_c": 800, "end_c": 1600, "step_c": 10, "pressure_atm": 1.0}

        with pytest.raises(ValueError, match="未替换"):
            render_job_files("test005", "high_alloy_incl", elements, temp_range)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
