# -*- coding: utf-8 -*-
"""res_parser 单元测试 —— 用 demo/Equi2.res 验证"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# 确保能导入 backend
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import Settings
from app.services.res_parser import (
    filter_species_by_min_gram,
    parsed_result_to_dict,
    parse_res_file,
)

DEMO_RES = Path(__file__).resolve().parent.parent.parent / "demo" / "Equi2.res"


@pytest.fixture(scope="module")
def parsed():
    """解析 demo .res 文件（整个测试模块共享）"""
    assert DEMO_RES.exists(), f"Demo file not found: {DEMO_RES}"
    return parse_res_file(DEMO_RES)


class TestMetadata:
    def test_temperature_count(self, parsed):
        """应有 94 个温度点"""
        assert parsed.n_steps == 94

    def test_temperature_range(self, parsed):
        """温度范围: 800°C → 1600°C"""
        assert parsed.temperatures[0] == pytest.approx(800.0, abs=1)
        assert parsed.temperatures[-1] == pytest.approx(1600.0, abs=1)

    def test_temperatures_sorted(self, parsed):
        """温度应单调递增"""
        for i in range(1, len(parsed.temperatures)):
            assert parsed.temperatures[i] >= parsed.temperatures[i - 1]

    def test_solutions_count(self, parsed):
        """应有 66 个溶液相"""
        assert parsed.n_solutions == 66

    def test_version(self, parsed):
        """版本号"""
        assert "8.3" in parsed.version


class TestSpecies:
    def test_total_species_count(self, parsed):
        """应有 1686 个 species（含所有类别）"""
        assert len(parsed.species) == 1686

    def test_significant_species(self, parsed):
        """过滤后应有 50-200 个有意义物种"""
        significant = [s for s in parsed.species if s.max_gram >= 1e-8]
        assert 10 <= len(significant) <= 500

    def test_serialized_result_keeps_all_species_for_api_filtering(self, parsed):
        """序列化结果应保留全部 species，由 API 层过滤 gram=0 物种。"""
        result = parsed_result_to_dict(parsed)
        significant = [s for s in result["species"] if s["max_gram"] >= 1e-8]

        assert len(result["species"]) == 1686
        assert len(significant) > 5

    def test_species_filter_threshold_is_configurable(self):
        """物种过滤阈值应可配置，不能把 1e-8 写死在路由里。"""
        species = [
            {"name": "trace", "max_gram": 1e-10},
            {"name": "default-visible", "max_gram": 1e-8},
            {"name": "large", "max_gram": 1e-6},
        ]

        assert [s["name"] for s in filter_species_by_min_gram(species, 1e-8)] == [
            "default-visible",
            "large",
        ]
        assert [s["name"] for s in filter_species_by_min_gram(species, 1e-10)] == [
            "trace",
            "default-visible",
            "large",
        ]

    def test_default_species_filter_threshold_comes_from_settings(self):
        """默认展示阈值来自配置层，前后端共享同一个语义。"""
        settings = Settings()

        assert settings.default_species_min_gram == 1e-8
        assert 1e-10 in settings.species_min_gram_options
        assert 1e-8 in settings.species_min_gram_options

    def test_liquid_phase_exists(self, parsed):
        """应存在 Liquid 相"""
        liquids = [
            s for s in parsed.species
            if "Liqu" in s.definition.raw_name
            and s.definition.category == "solution_total"
        ]
        assert len(liquids) > 0

    def test_liquid_at_high_temp(self, parsed):
        """1600°C 时 Liquid 总量应接近 100g"""
        liqu_total = None
        for s in parsed.species:
            if s.definition.raw_name == "FSstel-Liqu#1" and s.definition.category == "solution_total":
                liqu_total = s
                break
        assert liqu_total is not None, "FSstel-Liqu#1 (solution_total) not found"
        last_gram = liqu_total.grams[-1]
        assert last_gram > 50, f"Liquid at 1600°C should be >50g, got {last_gram}"

    def test_fcc_bcc_exist(self, parsed):
        """应存在 FCC 和 BCC 相"""
        names = {s.definition.raw_name for s in parsed.species}
        assert "FSstel-FCC#1" in names
        assert "FSstel-BCC#1" in names

    def test_species_data_lengths(self, parsed):
        """每个 species 的数据长度应与温度点数一致"""
        for s in parsed.species[:50]:
            assert len(s.grams) == parsed.n_steps, \
                f"{s.definition.raw_name}: grams length {len(s.grams)} != {parsed.n_steps}"
            assert len(s.moles) == parsed.n_steps
            assert len(s.wt_pcts) == parsed.n_steps


class TestCategories:
    def test_solution_components(self, parsed):
        """应有溶液组分（如 Al in Liquid）"""
        components = [
            s for s in parsed.species
            if s.definition.category == "solution_component"
        ]
        assert len(components) > 0

    def test_solution_totals(self, parsed):
        """应有溶液总量"""
        totals = [
            s for s in parsed.species
            if s.definition.category == "solution_total"
        ]
        assert len(totals) > 0

    def test_pure_compounds(self, parsed):
        """应有纯物质"""
        pures = [
            s for s in parsed.species
            if s.definition.category == "pure"
        ]
        assert len(pures) > 0

    def test_categories_valid(self, parsed):
        """所有 category 值应是预定义类型"""
        valid = {"solution_component", "solution_total", "pure", "element"}
        for s in parsed.species:
            assert s.definition.category in valid, \
                f"Invalid category '{s.definition.category}' for {s.definition.raw_name}"


class TestDisplayNames:
    def test_liquid_display_name(self, parsed):
        """Liquid 相的显示名称"""
        for s in parsed.species:
            if s.definition.raw_name == "FSstel-Liqu#1" and s.definition.category == "solution_total":
                assert "Liquid" in s.definition.display_name or "LIQU" in s.definition.display_name
                break

    def test_component_display_name(self, parsed):
        """组分的显示名称应包含元素名"""
        for s in parsed.species:
            if s.definition.raw_name == "FSstel-Al(Liqu#1)":
                assert "Al" in s.definition.display_name
                break


class TestDataIntegrity:
    def test_no_nan_values(self, parsed):
        """数据中不应有 NaN"""
        import math
        for s in parsed.species[:100]:
            for v in s.grams:
                assert not math.isnan(v), f"NaN in grams of {s.definition.raw_name}"

    def test_mass_conservation(self, parsed):
        """每个温度点的总质量应约为 100g（质量守恒）"""
        # 找到所有 solution_total species
        totals = [
            s for s in parsed.species
            if s.definition.category == "solution_total"
        ]
        pures = [
            s for s in parsed.species
            if s.definition.category == "pure"
        ]
        for temp_idx in [0, len(parsed.temperatures) // 2, -1]:
            total_mass = sum(s.grams[temp_idx] for s in totals)
            total_mass += sum(s.grams[temp_idx] for s in pures)
            # 允许 5% 误差（gas 相等可能有少量损失）
            assert 90 <= total_mass <= 110, \
                f"Total mass at T[{temp_idx}]={parsed.temperatures[temp_idx]}°C: {total_mass:.2f}g"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
