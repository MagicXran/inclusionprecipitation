# -*- coding: utf-8 -*-
"""
FactSage .res 文件解析器

解析 EQUILIB 模块输出的 .res 文件，提取物种定义、热力学数据和系统元数据。
.res 文件采用固定宽度格式，每行可达 ~127k 字符，包含数百个物种的数据。
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

__all__ = [
    "SpeciesDef",
    "SpeciesData",
    "ParsedResult",
    "ResParser",
    "parse_res_file",
]

# ---------------------------------------------------------------------------
# 相名称映射：内部缩写 → 可读名称
# ---------------------------------------------------------------------------
PHASE_NICKNAMES: dict[str, str] = {
    "FCC":  "γ-FCC",
    "BCC":  "α-BCC",
    "HCP":  "ε-HCP",
    "LIQU": "Liquid",
    "Liqu": "Liquid",
    "CEME": "Cementite",
    "SIGM": "Sigma",
    "GAS":  "Gas",
}


# ===================================================================
# 数据类
# ===================================================================

@dataclass
class SpeciesDef:
    """物种定义——从 species identifier line 解析而来。"""
    raw_name: str         # 原始名称，如 FSstel-Al(Liqu#1)
    display_name: str     # 可读名称，如 Al in Liquid
    category: str         # solution_component / solution_total / pure / element
    phase: str            # 相标识，如 FSstel-Liqu#1 / PURE / ELEMENT
    db: str               # 数据库来源：FSstel / FactPS / FToxid / ""
    index: int            # 在物种列表中的位置索引（0-based）


@dataclass
class SpeciesData:
    """单个物种在所有温度步上的数值数据。"""
    definition: SpeciesDef
    temperatures: list[float] = field(default_factory=list)
    grams: list[float] = field(default_factory=list)
    moles: list[float] = field(default_factory=list)
    activities: list[float] = field(default_factory=list)
    mole_fractions: list[float] = field(default_factory=list)
    wt_pcts: list[float] = field(default_factory=list)
    max_gram: float = 0.0


@dataclass
class ParsedResult:
    """解析完成后的顶层结果。"""
    species: list[SpeciesData]
    temperatures: list[float]
    n_steps: int
    n_solutions: int
    version: str
    reactant_summary: str


# ===================================================================
# 解析器
# ===================================================================

class ResParser:
    """
    FactSage .res 固定宽度格式解析器。

    文件结构（由标记行驱动，不依赖硬编码行号）：
      - ``ENDF    0`` 标记 header 结束
      - 之后依次为: 反应物摘要、SOLUTIONS、相头、EQUILIB results、VERSION、
        RESULTS 摘要、species identifier line、column header、数据行。

    数据行布局：
      - 0..199:   系统列（TIME, CYCLE, Alpha, T(C), P, Vol, H, G, V, S, U, Cp + padding）
      - 200+:     每个物种 75 字符 = 5 值 × 15 字符
    """

    SPECIES_START = 200
    VALUE_WIDTH = 15
    VALUES_PER_SPECIES = 5
    SPECIES_BLOCK = VALUES_PER_SPECIES * VALUE_WIDTH  # 75

    # 系统列定义: (name, start, width)
    _SYSTEM_COLS: list[tuple[str, int, int]] = [
        ("time",   0,   8),
        ("cycle",  8,   7),
        ("alpha",  15,  15),
        ("T_C",    30,  15),
        ("P_atm",  45,  15),
        ("vol",    60,  15),
        ("H_J",    75,  15),
        ("G_J",    90,  15),
        ("V_L",    105, 15),
        ("S_JK",   120, 15),
        ("U_J",    135, 15),
        ("Cp_JK",  150, 15),
    ]

    # ------------------------------------------------------------------
    # 公开接口
    # ------------------------------------------------------------------

    def parse(self, filepath: Path) -> ParsedResult:
        """解析 .res 文件，返回 ``ParsedResult``。"""
        lines = self._read_lines(filepath)
        meta = self._parse_metadata(lines)
        species_defs = self._parse_species_line(lines[meta["species_line_idx"]])
        data = self._parse_data_rows(lines, meta, species_defs)
        return self._build_result(species_defs, data, meta)

    # ------------------------------------------------------------------
    # 内部方法
    # ------------------------------------------------------------------

    @staticmethod
    def _read_lines(filepath: Path) -> list[str]:
        """读取文件，处理 BOM 和 CRLF/LF。"""
        path = Path(filepath)
        raw = path.read_bytes()

        # 剥离 UTF-8 BOM
        if raw.startswith(b"\xef\xbb\xbf"):
            raw = raw[3:]

        text = raw.decode("utf-8")
        # 统一换行为 \n 后按行拆分
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        return text.split("\n")

    # ------------------------------------------------------------------

    @staticmethod
    def _parse_metadata(lines: list[str]) -> dict:
        """
        扫描标记行，返回元数据字典：
          endf_idx, reactant_summary, n_solutions, n_steps, version,
          species_line_idx, data_start_idx
        """
        meta: dict = {}

        # 1) 找 ENDF 行（header 终止标记）
        endf_idx = -1
        for i, line in enumerate(lines):
            if line.strip().startswith("ENDF") and "0" in line:
                endf_idx = i
                # 确认这是真正的 header 结尾而不是文件末尾的 ENDF
                # 真正的 header ENDF 后面会跟 // 开头的反应物摘要或 SOLUTIONS
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if next_line.startswith("//") or next_line.startswith("SOLUTIONS"):
                        break
        if endf_idx < 0:
            raise ValueError("未找到 'ENDF    0' 标记行，文件格式异常")
        meta["endf_idx"] = endf_idx

        # 从 ENDF 之后向下扫描，找到关键行
        scan_start = endf_idx + 1
        scan_end = min(scan_start + 30, len(lines))  # 元数据不会超过 30 行

        reactant_lines: list[str] = []
        for i in range(scan_start, scan_end):
            line = lines[i].strip()

            # 反应物摘要行 (以 // 开头)
            if line.startswith("//"):
                reactant_lines.append(line.lstrip("/ ").rstrip(" \\"))
                continue

            # SOLUTIONS 行
            m = re.match(r"SOLUTIONS\s+(\d+)", line)
            if m:
                meta["n_solutions"] = int(m.group(1))
                continue

            # N EQUILIB results
            m = re.match(r"(\d+)\s+EQUILIB\s+results", line)
            if m:
                meta["n_steps"] = int(m.group(1))
                continue

            # VERSION
            m = re.match(r"VERSION\s+([\d.]+)", line)
            if m:
                meta["version"] = m.group(1)
                continue

            # RESULTS 摘要行（日期开头，如 "08May26"）
            if re.match(r"\d{2}[A-Z][a-z]{2}\d{2}", line):
                # 后面紧跟 species line 和 column header
                meta["species_line_idx"] = i + 1
                meta["data_start_idx"] = i + 3  # species line + column header + 1
                break

        meta["reactant_summary"] = "  +  ".join(reactant_lines) if reactant_lines else ""

        # 安全校验
        for key in ("n_solutions", "n_steps", "version", "species_line_idx", "data_start_idx"):
            if key not in meta:
                raise ValueError(f"解析元数据失败：未找到 '{key}'")

        return meta

    # ------------------------------------------------------------------

    def _parse_species_line(self, line: str) -> list[SpeciesDef]:
        """
        从 species identifier line 解析物种定义。

        每个物种占 75 字符（最后一个可能更短），包含：
          - solution_component: ``FSstel-Al(Liqu#1)  FSstel-Liqu#1  1``
          - solution_total:     ``FSstel-Liqu#1  SOLUTION  961``
          - pure:               ``FactPS-TiO(s2)  PURE  777``
          - element:            ``W_GAS  ELEMENT``  (无索引)
        """
        species_part = line[self.SPECIES_START:]
        defs: list[SpeciesDef] = []

        pos = 0
        idx = 0
        while pos < len(species_part):
            block = species_part[pos : pos + self.SPECIES_BLOCK]
            pos += self.SPECIES_BLOCK

            tokens = block.split()
            if not tokens:
                # 空块——仍占一个数据槽位
                defs.append(SpeciesDef(
                    raw_name="", display_name="(empty)", category="empty",
                    phase="", db="", index=idx,
                ))
                idx += 1
                continue

            raw_name = tokens[0]
            phase_token = tokens[1] if len(tokens) >= 2 else ""

            if phase_token == "ELEMENT":
                category = "element"
                phase = "ELEMENT"
            elif phase_token == "PURE":
                category = "pure"
                phase = "PURE"
            elif phase_token == "SOLUTION":
                category = "solution_total"
                phase = "SOLUTION"
            else:
                category = "solution_component"
                phase = phase_token

            db = self._extract_db(raw_name)
            display_name = self._make_display_name(raw_name, phase_token, category)

            defs.append(SpeciesDef(
                raw_name=raw_name,
                display_name=display_name,
                category=category,
                phase=phase,
                db=db,
                index=idx,
            ))
            idx += 1

        return defs

    # ------------------------------------------------------------------

    def _parse_data_rows(
        self,
        lines: list[str],
        meta: dict,
        species_defs: list[SpeciesDef],
    ) -> dict:
        """
        解析所有数据行，返回：
          {
            "temperatures": [...],
            "system": {col_name: [...]},
            "species_values": [[mole, gram, activity, mole_frac, wt%], ...] per species per step
          }
        """
        start = meta["data_start_idx"]
        n_steps = meta["n_steps"]
        n_species = len(species_defs)

        temperatures: list[float] = []
        # 为每个物种预分配五列
        sp_moles:     list[list[float]] = [[] for _ in range(n_species)]
        sp_grams:     list[list[float]] = [[] for _ in range(n_species)]
        sp_acts:      list[list[float]] = [[] for _ in range(n_species)]
        sp_molfracs:  list[list[float]] = [[] for _ in range(n_species)]
        sp_wtpcts:    list[list[float]] = [[] for _ in range(n_species)]

        for row_idx in range(n_steps):
            line_idx = start + row_idx
            if line_idx >= len(lines):
                break
            row = lines[line_idx]

            # 系统列：温度
            t_str = row[30:45]
            temperatures.append(self._parse_float(t_str))

            # 物种数据
            offset = self.SPECIES_START
            w = self.VALUE_WIDTH
            for si in range(n_species):
                base = offset + si * self.SPECIES_BLOCK
                vals = []
                for vi in range(self.VALUES_PER_SPECIES):
                    s = base + vi * w
                    e = s + w
                    chunk = row[s:e] if e <= len(row) else row[s:]
                    vals.append(self._parse_float(chunk))

                sp_moles[si].append(vals[0])
                sp_grams[si].append(vals[1])
                sp_acts[si].append(vals[2])
                sp_molfracs[si].append(vals[3])
                sp_wtpcts[si].append(vals[4])

        return {
            "temperatures": temperatures,
            "moles": sp_moles,
            "grams": sp_grams,
            "activities": sp_acts,
            "mole_fractions": sp_molfracs,
            "wt_pcts": sp_wtpcts,
        }

    # ------------------------------------------------------------------

    @staticmethod
    def _build_result(
        species_defs: list[SpeciesDef],
        data: dict,
        meta: dict,
    ) -> ParsedResult:
        """组装 ParsedResult，返回所有物种（过滤由 API 层负责）。"""
        temperatures = data["temperatures"]
        all_species: list[SpeciesData] = []

        for i, sdef in enumerate(species_defs):
            grams = data["grams"][i]
            max_gram = max(abs(g) for g in grams) if grams else 0.0

            sd = SpeciesData(
                definition=sdef,
                temperatures=temperatures,
                grams=grams,
                moles=data["moles"][i],
                activities=data["activities"][i],
                mole_fractions=data["mole_fractions"][i],
                wt_pcts=data["wt_pcts"][i],
                max_gram=max_gram,
            )
            all_species.append(sd)

        return ParsedResult(
            species=all_species,
            temperatures=temperatures,
            n_steps=meta["n_steps"],
            n_solutions=meta["n_solutions"],
            version=meta["version"],
            reactant_summary=meta["reactant_summary"],
        )

    # ------------------------------------------------------------------
    # 工具方法
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_float(s: str) -> float:
        """安全解析浮点数，处理空白和无效值。"""
        s = s.strip()
        if not s:
            return 0.0
        try:
            return float(s)
        except ValueError:
            return 0.0

    @staticmethod
    def _extract_db(raw_name: str) -> str:
        """从原始名称提取数据库前缀。"""
        if "-" in raw_name:
            prefix = raw_name.split("-", 1)[0]
            if prefix in ("FSstel", "FactPS", "FToxid"):
                return prefix
        return ""

    @staticmethod
    def _make_display_name(raw_name: str, phase_token: str, category: str) -> str:
        """
        将原始物种名称转换为可读的显示名称。

        规则：
          - solution_component: ``FSstel-Al(Liqu#1)`` → ``Al in Liquid #1``
          - solution_total:     ``FSstel-FCC#1`` → ``γ-FCC #1 (total)``
          - pure:               ``FactPS-TiO(s2)`` → ``TiO``
          - element:            ``W_GAS`` → ``W (element)``
        """

        def _phase_friendly(phase_short: str) -> str:
            """将相缩写转化为可读名称，如 ``Liqu#1`` → ``Liquid #1``。"""
            # 拆分基本名和编号: "FCC#2" → ("FCC", "#2"), "CEME" → ("CEME", "")
            m = re.match(r"([A-Za-z]+)(#?\d*)$", phase_short)
            if not m:
                return phase_short
            base, suffix = m.group(1), m.group(2)
            nick = PHASE_NICKNAMES.get(base, base)
            if suffix:
                return f"{nick} {suffix}"
            return nick

        # --- element ---
        if category == "element":
            # FSstel-W_Liqu#1 → W, W_GAS → W, Fe_Liqu#1 → Fe
            name = raw_name
            # 先去掉数据库前缀
            if "-" in name:
                name = name.split("-", 1)[1]
            # 再按 _ 取元素符号
            element = name.split("_", 1)[0] if "_" in name else name
            return f"{element} (element)"

        # --- solution_component ---
        if category == "solution_component":
            # FSstel-Al(Liqu#1) → element=Al, phase_part=Liqu#1
            m = re.match(r"(?:\w+-)?(.*?)\((.+?)\)$", raw_name)
            if m:
                element = m.group(1)
                phase_part = m.group(2)
                return f"{element} in {_phase_friendly(phase_part)}"
            # 回退
            return raw_name

        # --- solution_total ---
        if category == "solution_total":
            # GAS → Gas (total)
            # FSstel-FCC#1 → γ-FCC #1 (total)
            name = raw_name
            if "-" in name:
                name = name.split("-", 1)[1]  # 去掉 db 前缀
            m = re.match(r"([A-Za-z]+)(#?\d*)$", name)
            if m:
                base, suffix = m.group(1), m.group(2)
                nick = PHASE_NICKNAMES.get(base, base)
                label = f"{nick} {suffix}".strip() if suffix else nick
                return f"{label} (total)"
            return f"{name} (total)"

        # --- pure ---
        if category == "pure":
            # FactPS-TiO(s2) → TiO
            # FToxid-Al2O3(s) → Al2O3 (FToxid)
            db = ""
            name = raw_name
            if "-" in name:
                prefix, name = name.split("-", 1)
                if prefix == "FToxid":
                    db = "FToxid"
            # 去掉相后缀: TiO(s2) → TiO
            formula = re.sub(r"\(s\d*\)$", "", name)
            if db:
                return f"{formula} ({db})"
            return formula

        return raw_name


# ===================================================================
# 便捷函数
# ===================================================================

def parse_res_file(filepath: Path) -> ParsedResult:
    """解析 .res 文件的便捷入口。"""
    return ResParser().parse(filepath)
