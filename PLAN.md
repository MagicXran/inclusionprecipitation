# 超级模板集成 + 系统完善计划

## 前置条件（用户手动完成）

用户在 FactSage GUI 中创建超级模板 .equi 文件：
- 包含自定义的全元素列表（用户提供）
- 不需要的元素质量设为 1e-10
- FactSage 自动生成覆盖所有元素组合的候选相列表
- 保存为 .equi 文件后交给系统

---

## 第一阶段：代码改造 — 支持超级模板

### 1.1 template_renderer.py — 未提交元素自动填充默认值

**当前问题**：`_render_tpl()` 对未提供的占位符会报错（`模板中存在未替换的占位符`）。超级模板有 ~22 个元素占位符，但用户可能只提交 5-8 个元素，剩余的必须自动填充 1e-10。

**改动**：在 `render_job_files()` 中，渲染前加载 meta.json，对模板中所有 supported_elements，如果用户未提交该元素，用 meta.json 的 `default_g`（通常为 1e-10）填充占位符。

```python
# render_job_files() 中，构建 variables 之后：
meta = load_template_meta(template_id)
user_symbols = {elem["symbol"] for elem in elements}
for el_def in meta["supported_elements"]:
    key = f"MASS_{el_def['symbol']}"
    if key not in variables:
        variables[key] = str(el_def["default_g"])
```

### 1.2 models.py — 放宽总质量校验

**当前问题**：`JobRequest.validate_elements` 校验 `abs(total - 100) > 1.0` 会报错。超级模板场景下，用户只提交"激活"的元素（比如 5 个加起来 ~100g），其余元素（1e-10 × 17 个 ≈ 0）由后端自动补全，但用户提交的 total 就是 ~100g，不包含那些 1e-10。

**改动**：放宽校验阈值到 5.0g，或改为软警告。实际上 1e-10 × 17 ≈ 0，不影响 ~100g 约束。但如果用户真的只提交 3 个元素加起来 50g，应该提醒。保持 `abs(total - 100) > 5.0` 的硬校验即可。

### 1.3 meta.json — 超级模板元数据

**改动**：创建新的 `templates/super_steel/meta.json`，结构同现有格式，但：
- `supported_elements` 包含全部 ~22 个元素
- 非必需元素的 `default_g` 设为 `1e-10`
- 新增 `"group"` 字段用于前端分组显示：
  - `"major"`: 主合金元素（Cr, Ni, Mo, Mn 等）
  - `"micro"`: 微合金元素（Ti, Al, V, Nb, B 等）
  - `"trace"`: 痕量/杂质（P, S, Ca, Mg 等）
  - `"base"`: 基体（Fe, C, O, N）

```json
{
    "symbol": "Nb", "default_g": 1e-10, "required": false,
    "group": "micro", "description": "铌"
}
```

### 1.4 registry.json — 注册超级模板

新增一条 `super_steel` 条目，与 `high_alloy_incl` 共存。

### 1.5 case.equi.tpl — 从用户提供的 .equi 生成

用户提供超级模板 .equi 后，将反应物质量和温度行替换为 `{{MASS_*}}` / `{{T_START}}` 等占位符。这一步等用户交付 .equi 后手动完成（反应物定义行的格式和行数取决于元素数量）。

---

## 第二阶段：前端改造 — 元素分组与激活控制

### 2.1 元素输入区 — 分组 + 启用开关

**当前**：所有 10 个元素平铺显示，每个元素一行输入框。
**改造**：
- 按 `group` 字段分组显示（基体 / 主合金 / 微合金 / 痕量）
- 每个非 required 元素前加 checkbox 开关
- 未勾选的元素 = 使用默认值（1e-10），输入框禁用变灰
- 勾选后激活输入框，可修改质量
- required 元素（如 Fe, O）始终显示，不可禁用

### 2.2 自动平衡 Fe 质量

**新增功能**：Fe 输入框旁加"自动计算"按钮或实时联动：
- 监听所有其他元素质量变化
- `Fe = 100 - sum(其他激活元素的质量)`
- 用户也可手动覆盖

### 2.3 物种分组标签修正

**当前问题**：`renderSpeciesList()` 中的 `categoryLabels` 用的是 `solution/precipitate/pure`，但解析器实际输出的 category 是 `solution_total/solution_component/pure/element`。

**改动**：修正映射：
```javascript
const categoryLabels = {
    solution_total:     '溶液相 (Solution Totals)',
    solution_component: '溶液相组分 (Solution Components)',
    pure:               '纯物质/析出相 (Pure Compounds)',
    element:            '元素 (Elements)',
};
```

---

## 第三阶段：Bug 修复与健壮性

### 3.1 template_renderer.py — .mac 路径转义

**当前**：第 114 行 `f"%OutDir = \"{out_dir}\\\\\"\r\n"` 生成的路径可能不正确。Windows 路径在 FactSage .mac 中需要单反斜杠 + 末尾双反斜杠。

**验证**：用真实 FactSage 运行一次确认路径格式是否正确。如有问题，改为：
```python
out_dir_str = str(out_dir).replace("/", "\\")
f'%OutDir = "{out_dir_str}\\"\r\n'
```

### 3.2 run.py — reload 模式缓存问题

**当前问题**：Windows 下 uvicorn reload 缓存旧代码（已验证复现）。

**改动**：run.py 默认不使用 reload，改为命令行参数可选：
```python
if __name__ == "__main__":
    import sys
    reload = "--reload" in sys.argv
    uvicorn.run("app.main:app", host=..., port=..., reload=reload)
```

### 3.3 res_parser.py — _build_result linter 反复覆盖

**当前问题**：linter hook 已三次把 `species=all_species` 改回 `species=significant`。

**改动**：删除 `significant` 变量和过滤注释，只保留 `all_species`，让 linter 无从覆盖。

---

## 第四阶段：真实 FactSage 集成测试

### 4.1 用现有 10 元素模板跑真实计算

- 确认 .mac 路径格式正确
- 确认 EquiSage.exe 调用成功
- 确认 .res 输出能被 res_parser 解析
- 对比 mock 结果与真实结果的结构一致性

### 4.2 用超级模板跑真实计算

- 用户创建超级模板 .equi 后
- 生成 .equi.tpl
- 提交只激活 5 个元素的任务
- 验证未激活元素（1e-10）不影响结果

---

## 第五阶段：打包部署

### 5.1 PyInstaller 打包

- build.py 已存在，验证打包结果能否运行
- 确认 templates/ 和 frontend/ 打包进 bundle
- 确认 config.json 外置可修改

### 5.2 config.json 文档

- FactSage 安装路径配置
- mock_mode 开关说明
- 端口配置

---

## 文件改动汇总

| 文件 | 改动类型 | 阶段 |
|------|---------|------|
| `backend/app/services/template_renderer.py` | 修改：自动填充默认元素 + 路径转义 | 1.1, 3.1 |
| `backend/app/models.py` | 修改：放宽质量校验 | 1.2 |
| `backend/templates/super_steel/meta.json` | **新建** | 1.3 |
| `backend/templates/super_steel/case.equi.tpl` | **新建**（等用户 .equi） | 1.5 |
| `backend/templates/registry.json` | 修改：新增 super_steel | 1.4 |
| `frontend/js/app.js` | 修改：分组显示 + 激活开关 + Fe 自动计算 + category 修正 | 2.1-2.3 |
| `frontend/css/style.css` | 修改：分组样式 + 开关样式 | 2.1 |
| `frontend/index.html` | 可能微调：元素区域结构 | 2.1 |
| `backend/app/services/res_parser.py` | 修改：清理 linter 冲突 | 3.3 |
| `run.py` | 修改：reload 可选 | 3.2 |

---

## 执行顺序

```
第一阶段（代码改造）→ 第三阶段（Bug 修复）→ 第二阶段（前端）
    ↓                                           ↓
  可用现有 10 元素模板立即测试              前端可用 mock 测试
    ↓                                           ↓
第四阶段（等用户超级模板 .equi）→ 第五阶段（打包）
```

先做 1 + 3（后端改造），再做 2（前端），最后 4 + 5（集成测试 + 打包）。
第一阶段改造对现有 10 元素模板完全向后兼容。
