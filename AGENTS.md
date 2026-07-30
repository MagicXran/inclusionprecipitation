# AGENTS.md

## 0. Scope

本文件是 `D:\Nercar\Wuhu\Apps\factsage_app\inclusionprecipitation` 的项目级指令。

- 只记录本项目长期有效的技术事实、运行方式、编码边界和验证要求。
- 全局沟通风格、Git 通用规则、Windows 编码规则以用户全局 AGENTS 为准。
- 如果代码、测试、配置和本文件冲突，先相信当前代码，再更新本文件。
- `mem/` 是本地记忆与会话产物，不作为项目源码处理；不要因为 Git 状态里出现 `mem/` 改动就修改或提交它。

## 1. Project Overview

这是一个本地化的 FactSage 夹杂物/析出相温度扫描 Web 应用。

核心定位：

- 它不是热力学求解器本体，而是 FactSage Equilib 的本地包装层。
- 真实计算依赖外部 `EquiSage.exe`，默认路径来自 `C:\FactSage`。
- 用户输入钢种模板、元素质量、温度区间和压力；系统生成 FactSage `.equi` 与 `.mac`，调用 FactSage 后解析 `.res`，再给前端展示曲线和导出数据。
- 无 FactSage 环境时可用 mock 模式跑通 API、前端和解析链路；mock 结果来自 demo `.res` 文件，不是随便编曲线。

当前模板：

- `high_alloy_incl`：前端名称为“探索模式”，22 元素高合金钢体系。
- `bearing_steel_52100`：轴承钢 `52100 / 100Cr6`，13 元素体系，基于手工导出的 Equilib 案例。

面向客户介绍时必须讲清边界：

- 可以说“把 FactSage 专家操作流程标准化、自动化、可视化”。
- 不要说本项目替代 FactSage 或自研热力学数据库。
- 不要把 PLAN.md 里的路线图当成已实现功能。

## 2. Tech Stack

- Backend: Python, FastAPI, Uvicorn, Pydantic v2, SQLite。
- Frontend: 静态 `HTML + CSS + vanilla JS`，图表使用本地 `frontend/vendor/echarts.min.js`。
- Compute: 外部 FactSage `EquiSage.exe`，命令行参数为 `/EQUILIB /MACRO <case.mac>`。
- Packaging: PyInstaller `onedir`，入口由 `build.py` 临时生成。
- Tests: `pytest`，优先使用项目虚拟环境 `.venv\Scripts\python.exe`。

## 3. Repository Map

- `run.py`：开发模式入口，把 `backend/` 加入 `sys.path`，启动 `app.main:app`。
- `backend/config.json`：开发模式配置；打包后会复制到 exe 同级目录。
- `backend/app/main.py`：FastAPI 应用入口，启动/停止 `job_manager`，挂载静态前端资源。
- `backend/app/models.py`：API 请求/响应模型和输入校验。
- `backend/app/routers/jobs.py`：模板、计算、任务状态、species、chart-data、下载、CSV 导出、运行配置 API。
- `backend/app/services/job_manager.py`：SQLite 持久化、内存 FIFO 队列、单 worker 后台执行链。
- `backend/app/services/template_renderer.py`：加载模板元数据，校验 `meta.json` 与 `.equi.tpl`，渲染 `.equi/.mac`。
- `backend/app/services/factsage_runner.py`：真实调用 FactSage 或 mock 解析 demo `.res`。
- `backend/app/services/res_parser.py`：解析 FactSage 固定宽度 `.res`，输出前端可消费的 JSON。
- `backend/app/services/db.py`：SQLite `jobs` 表封装。
- `backend/templates/registry.json`：模板注册表。
- `backend/templates/<template_id>/meta.json`：模板元数据、元素默认值、UI 分组、默认温度。
- `backend/templates/<template_id>/case.equi.tpl`：FactSage Equilib 输入模板。
- `frontend/index.html`：静态页面结构。
- `frontend/js/app.js`：前端状态、API 调用、轮询、图表、导出逻辑。
- `frontend/css/style.css`：页面样式。
- `frontend/vendor/echarts.min.js`：离线 ECharts，打包时必须存在或由 `build.py` 下载。
- `demo/`：示例 `.equi/.mac/.res` 资产；mock 和测试依赖其中的 `.res`。
- `build.py`：生成 `dist/FactSage_InclPrecip` 可迁移目录。
- `PLAN.md`：历史计划，不是当前实现的可信来源；使用前必须回看代码。

## 4. Runtime Flow

主链路：

1. `run.py` 启动 `uvicorn`，默认监听 `127.0.0.1:10688`。
2. `backend/app/main.py` 在 FastAPI lifespan 中启动 `job_manager`。
3. 前端通过 `/api/templates` 和 `/api/templates/{template_id}` 加载模板。
4. 用户提交 `/api/calculate`，请求体包含 `template_id`、`elements`、`temp_range`。
5. `JobManager.submit()` 写入 SQLite，并把 `job_id` 放入内存队列。
6. 单 worker 取任务后调用 `render_job_files()` 生成 `case.equi` 和 `case.mac`。
7. `run_calculation()` 根据 `settings.mock_mode` 选择真实 FactSage 或 mock。
8. 真实模式调用 `EquiSage.exe /EQUILIB /MACRO case.mac`，输出 `result.res`。
9. mock 模式选择 `demo/Equi2.res` 或模板专用 `demo/Equ2222i.res`，解析后直接生成 `parsed_result.json`。
10. 真实模式再由 `ResParser` 解析 `.res`，写出 `parsed_result.json`。
11. 前端轮询 `/api/jobs/{job_id}`，完成后加载 species 和 chart-data。
12. 用户可导出 CSV、PNG，或下载 `.equi/.mac/.res` zip。

关键 API：

- `GET /api/templates`
- `GET /api/templates/{template_id}`
- `POST /api/calculate`
- `GET /api/jobs/{job_id}`
- `GET /api/jobs/{job_id}/species?min_gram=...`
- `GET /api/jobs/{job_id}/chart-data?species_names=...&value_type=...`
- `GET /api/jobs/{job_id}/export-csv`
- `GET /api/jobs/{job_id}/download`
- `GET /api/jobs`
- `GET /api/config/info`

## 5. Commands

先确认虚拟环境：

```powershell
Test-Path .venv\Scripts\python.exe
.venv\Scripts\python.exe -m pytest --version
```

安装依赖：

```powershell
.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
```

开发启动：

```powershell
.venv\Scripts\python.exe run.py
```

访问：

```text
http://127.0.0.1:10688/
```

强制 mock 模式启动：

```powershell
$env:MOCK_MODE='true'
.venv\Scripts\python.exe run.py
```

运行测试：

```powershell
.venv\Scripts\python.exe -m pytest backend\tests
```

打包：

```powershell
.venv\Scripts\python.exe build.py
```

打包产物：

```text
dist/FactSage_InclPrecip/
```

迁移时复制整个目录，不要只复制 exe。

## 6. Configuration

配置来源：

- 开发模式基准目录是 `backend/`。
- 打包模式基准目录是 exe 所在目录。
- 默认配置在 `backend/app/config.py` 的 `_DEFAULT_CONFIG`。
- 用户配置从 `config.json` 加载，支持 UTF-8 BOM。
- 环境变量覆盖 `config.json`。

重要环境变量：

- `FACTSAGE_DIR`：FactSage 安装目录，默认 `C:\FactSage`。
- `WORK_ROOT`：任务工作目录。
- `TEMPLATES_DIR`：模板目录。
- `FRONTEND_DIR`：静态前端目录。
- `DB_PATH`：SQLite 数据库路径。
- `RESULTS_DIR`：结果目录。
- `HOST`：服务监听地址。
- `PORT`：服务端口。
- `MOCK_MODE`：`true`、`false`、`auto`。默认 `auto`，找不到 `EquiSage.exe` 时进入 mock。

默认运行参数：

- host: `127.0.0.1`
- port: `10688`
- FactSage timeout: `600` 秒
- species 默认过滤阈值: `1e-8 g`
- species 可选阈值: `1e-10`、`1e-8`、`1e-6`、`1e-4`

## 7. Data And Generated Files

源码不要依赖未说明的全局路径，除 `C:\FactSage` 这类用户配置默认值外。

生成或运行态目录：

- 开发模式默认在 `backend/work/` 写任务输入输出。
- 开发模式默认在 `backend/data/inclprecip.db` 写 SQLite 数据库。
- 打包模式在 exe 同级创建 `data/`、`work/`、`results/`。
- `dist/`、`dist/_build/`、`dist/_pyinstaller_work/`、`dist/_pyinstaller_spec/` 是打包产物。
- `.pytest_cache/`、`__pycache__/` 是测试或 Python 缓存。
- `mem/` 是 Codex 本地记忆和会话产物，忽略。

注意：

- `.res` 文件通常是运行产物，但 `demo/Equi2.res` 和 `demo/Equ2222i.res` 是 mock 与测试依赖资产，不要误删。
- `frontend/vendor/echarts.min.js` 是离线运行资产，不要替换成只依赖 CDN。

## 8. Template Rules

修改模板必须同时考虑三件事：

- `backend/templates/registry.json`
- `backend/templates/<template_id>/meta.json`
- `backend/templates/<template_id>/case.equi.tpl`

硬约束：

- `meta.json` 的 `supported_elements[].symbol` 必须与 `.equi.tpl` 中所有 `{{MASS_*}}` 占位符一一对应。
- 不允许重复元素，不允许模板里有未登记元素，也不允许 meta 登记了模板没用的元素。
- 非必需或未激活元素默认值通常是 `1e-10`，用于占位而不是参与有效总质量。
- 元素分组使用 `base`、`major`、`micro`、`trace`，前端按这些分组渲染。
- `JobRequest` 会拒绝重复元素。
- 有效质量只统计 `mass_g > 0.001` 的元素，总量需约等于 `100g`，容差为 `5g`。
- 温度区间要求 `end_c > start_c`，`step_c > 0`，`pressure_atm > 0`。

文件格式：

- 模板 JSON 读取兼容 UTF-8 BOM。
- `.equi.tpl` 读取兼容 UTF-8 BOM 并统一换行。
- 输出给 FactSage 的 `.equi` 和 `.mac` 使用 CRLF。
- FactSage 宏路径使用 Windows 绝对路径，避免 `/` 和相对路径。

## 9. Frontend Rules

- 前端没有构建步骤，直接由 FastAPI 静态挂载 `css/`、`js/`、`vendor/`。
- API 使用同源 `/api/...`，不要引入前端环境变量体系，除非先明确部署模型。
- `frontend/js/app.js` 维护页面状态、模板切换、元素输入、提交、轮询、species 分组、ECharts 图表和导出。
- 支持的 `value_type` 必须与后端一致：`gram`、`mole`、`wt_pct`、`activity`、`mole_fraction`。
- 改前端交互后，至少用浏览器或 HTTP 跑一次完整 mock 任务，而不是只看代码。
- 不要把 `vendor/echarts.min.js` 改回 CDN 依赖；离线打包依赖本地文件。

## 10. Backend Rules

- 保持 API 兼容，尤其是客户或前端可能依赖的 `/api/*` 路径和返回字段。
- `JobManager` 当前是单 worker FIFO；不要假装它支持并发计算。
- 服务启动时会把旧的 `pending/running` 任务标记为 failed，这是现有恢复语义。
- `run_calculation()` 的真实模式必须保留超时控制和 `factsage_run.log`，否则现场排障会很痛苦。
- mock 模式必须继续基于 demo `.res` 解析，不能改成手写假数据。
- `ResParser` 绑定 FactSage `.res` 固定宽度格式；改解析器必须跑解析测试。
- 不要吞异常；失败原因要能进入任务 `error`，便于前端显示和排障。

## 11. Packaging Rules

- `build.py` 生成 PyInstaller onedir 包，不是单文件 exe。
- 打包前端时要把 ECharts 改成本地 `vendor/echarts.min.js`。
- 打包产物要复制：
  - `config.json`
  - `templates/`
  - `frontend/`
  - demo `.res`
  - `data/`
  - `work/`
  - `results/`
- 对外交付时复制 `dist/FactSage_InclPrecip/` 整个目录。
- 包装配置和源码配置的基准目录不同，改路径逻辑时必须同时考虑开发模式和 frozen 模式。

## 12. Validation

代码修改后必须按影响面验证。

后端、模板、解析器改动：

```powershell
.venv\Scripts\python.exe -m pytest backend\tests
```

入口、配置、API 或前端改动：

```powershell
$env:MOCK_MODE='true'
.venv\Scripts\python.exe run.py
```

然后访问 `http://127.0.0.1:10688/`，提交一次 mock 任务，确认：

- `/api/config/info` 返回预期 mock 状态。
- `/api/templates` 能加载模板。
- `/api/calculate` 能返回 job_id。
- `/api/jobs/{job_id}` 最终 completed。
- species 列表、图表、CSV 导出、原始文件下载可用。

打包改动：

```powershell
.venv\Scripts\python.exe build.py
```

然后从 `dist/FactSage_InclPrecip/FactSage_InclPrecip.exe` 启动验证页面和 mock 任务。

不能验证时要明确说明没验证什么，不能把“代码看起来对”说成“已验证”。

## 13. Git Boundaries

- 默认不提交、不 push。
- 修改前看 `git status`，但忽略 `mem/` 噪声。
- 不要使用 `git add .`。
- 只 stage 本次任务明确修改的文件。
- 不要格式化无关文件。
- 不要删除 demo、模板、vendor 资产，除非任务明确要求并且已确认替代链路。

## 14. Common Pitfalls

- 只看 `PLAN.md` 会被历史计划误导，必须回看当前源码。
- 有监听端口不等于真实 FactSage 可用；`MOCK_MODE=auto` 可能已经降级到 mock。
- mock 任务成功只证明 Web、队列、模板和解析链路可用，不证明真实热力学计算成功。
- 单 worker 下一个长任务会堵住后续任务。
- `.res` 解析格式脆弱，改字段切片或 species 分类时必须用 demo 文件回归。
- 打包后只复制 exe 会坏，因为模板、前端、配置和运行目录都在 exe 同级目录。
