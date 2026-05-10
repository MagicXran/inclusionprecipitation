/* ============================================
   FactSage 夹杂物/析出相计算系统 - 前端逻辑
   ============================================ */

// ---- 状态 ----
let currentJobId = null;
let speciesList = [];
let chartInstance = null;
let pollingTimer = null;

const STATUS_LABELS = {
    pending:   '等待中',
    running:   '计算中',
    completed: '已完成',
    failed:    '失败',
};

// ---- 初始化 ----
document.addEventListener('DOMContentLoaded', () => {
    chartInstance = echarts.init(document.getElementById('chart'));
    loadTemplates();
    loadHistory();
    checkMockMode();

    window.addEventListener('resize', () => {
        if (chartInstance) chartInstance.resize();
    });

    document.getElementById('templateSelect').addEventListener('change', (e) => {
        const id = e.target.value;
        if (id) {
            loadTemplateMeta(id);
        } else {
            document.getElementById('elementInputs').innerHTML =
                '<p class="hint-text">请先选择计算模板</p>';
            document.getElementById('submitBtn').disabled = true;
        }
    });
});

// ============================================
// API 调用
// ============================================

async function apiFetch(url, options) {
    try {
        const resp = await fetch(url, options);
        if (!resp.ok) {
            const text = await resp.text();
            let msg;
            try {
                const json = JSON.parse(text);
                msg = json.detail || json.message || text;
            } catch {
                msg = text;
            }
            throw new Error(`请求失败 (${resp.status}): ${msg}`);
        }
        return resp;
    } catch (err) {
        if (err.name === 'TypeError' && err.message.includes('fetch')) {
            throw new Error('无法连接到服务器，请确认后端服务是否已启动。');
        }
        throw err;
    }
}

// 检查是否为模拟模式
async function checkMockMode() {
    try {
        const resp = await apiFetch('/api/config/info');
        const data = await resp.json();
        if (data.mock_mode) {
            document.getElementById('mockBadge').style.display = '';
        }
    } catch {
        // 静默失败，不阻塞主流程
    }
}

// 加载模板列表
async function loadTemplates() {
    try {
        const resp = await apiFetch('/api/templates');
        const templates = await resp.json();
        const select = document.getElementById('templateSelect');

        templates.forEach(t => {
            const opt = document.createElement('option');
            opt.value = t.id;
            opt.textContent = t.name;
            select.appendChild(opt);
        });

        // 如果只有一个模板，自动选中
        if (templates.length === 1) {
            select.value = templates[0].id;
            loadTemplateMeta(templates[0].id);
        }
    } catch (err) {
        showError('加载模板列表失败：' + err.message);
    }
}

// 加载模板元信息，填充元素输入
async function loadTemplateMeta(templateId) {
    try {
        const resp = await apiFetch(`/api/templates/${templateId}`);
        const meta = await resp.json();

        // 填充元素输入
        renderElementInputs(meta.supported_elements);

        // 填充默认温度/压力
        if (meta.default_temp) {
            document.getElementById('tempStart').value = meta.default_temp.start_c ?? '';
            document.getElementById('tempEnd').value = meta.default_temp.end_c ?? '';
            document.getElementById('tempStep').value = meta.default_temp.step_c ?? '';
        }
        if (meta.default_pressure_atm != null) {
            document.getElementById('pressure').value = meta.default_pressure_atm;
        }

        // 描述
        document.getElementById('templateDesc').textContent = meta.description || '';

        // 启用提交按钮
        document.getElementById('submitBtn').disabled = false;
    } catch (err) {
        showError('加载模板详情失败：' + err.message);
    }
}

// 提交计算
async function submitCalculation() {
    const templateId = document.getElementById('templateSelect').value;
    if (!templateId) {
        showError('请先选择计算模板。');
        return;
    }

    // 收集全部元素数据（active 发用户值，inactive 发 1E-10）
    const elementRows = document.querySelectorAll('.element-row');
    const elements = [];
    for (const row of elementRows) {
        const toggle = row.querySelector('.element-toggle');
        const input = row.querySelector('.element-input');
        const symbol = input.dataset.symbol;

        if (toggle.checked) {
            const val = parseFloat(input.value);
            if (isNaN(val) || val <= 0) {
                showError(`元素 ${symbol} 已启用但未填写有效质量。`);
                return;
            }
            elements.push({ symbol, mass_g: val });
        } else {
            elements.push({ symbol, mass_g: 1e-10 });
        }
    }

    if (elements.length === 0) {
        showError('请至少输入一个元素的质量。');
        return;
    }

    // 收集温度/压力
    const startC = parseFloat(document.getElementById('tempStart').value);
    const endC = parseFloat(document.getElementById('tempEnd').value);
    const stepC = parseFloat(document.getElementById('tempStep').value);
    const pressure = parseFloat(document.getElementById('pressure').value);

    if (isNaN(startC) || isNaN(endC) || isNaN(stepC)) {
        showError('请完整填写温度范围（起始、终止、步长）。');
        return;
    }

    if (startC >= endC) {
        showError('起始温度必须小于终止温度。');
        return;
    }

    if (stepC <= 0) {
        showError('温度步长必须大于 0。');
        return;
    }

    const body = {
        template_id: templateId,
        elements: elements,
        temp_range: {
            start_c: startC,
            end_c: endC,
            step_c: stepC,
            pressure_atm: isNaN(pressure) ? 1 : pressure,
        },
    };

    // 禁用按钮，显示加载
    const btn = document.getElementById('submitBtn');
    btn.disabled = true;
    btn.classList.add('loading');
    btn.textContent = '计算中...';
    hideError();

    try {
        const resp = await apiFetch('/api/calculate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });
        const result = await resp.json();
        currentJobId = result.job_id;
        updateStatus(result.status);
        pollJobStatus(result.job_id);
    } catch (err) {
        showError('提交计算失败：' + err.message);
        resetSubmitBtn();
    }
}

// 轮询任务状态
function pollJobStatus(jobId) {
    if (pollingTimer) clearInterval(pollingTimer);

    pollingTimer = setInterval(async () => {
        try {
            const resp = await apiFetch(`/api/jobs/${jobId}`);
            const job = await resp.json();
            updateStatus(job.status, job.error);

            if (job.status === 'completed') {
                clearInterval(pollingTimer);
                pollingTimer = null;
                resetSubmitBtn();
                await loadSpeciesList(jobId);
                loadHistory();
            } else if (job.status === 'failed') {
                clearInterval(pollingTimer);
                pollingTimer = null;
                resetSubmitBtn();
                showError(job.error || '计算失败，未知错误。');
                loadHistory();
            }
        } catch (err) {
            clearInterval(pollingTimer);
            pollingTimer = null;
            resetSubmitBtn();
            showError('查询任务状态失败：' + err.message);
        }
    }, 2000);
}

// 加载物种列表
async function loadSpeciesList(jobId) {
    try {
        const resp = await apiFetch(`/api/jobs/${jobId}/species`);
        speciesList = await resp.json();
        renderSpeciesList(speciesList);

        // 自动选中 max_gram 最大的前 5 个
        const sorted = [...speciesList].sort((a, b) => b.max_gram - a.max_gram);
        const topNames = sorted.slice(0, 5).map(s => s.name);
        topNames.forEach(name => {
            const cb = document.querySelector(`input[data-species="${name}"]`);
            if (cb) cb.checked = true;
        });

        await reloadChart();
    } catch (err) {
        showError('加载物种列表失败：' + err.message);
    }
}

// 加载图表数据
async function loadChartData(jobId, speciesNames, valueType) {
    if (!speciesNames.length) {
        chartInstance.clear();
        chartInstance.setOption({
            title: {
                text: '请选择至少一个物种',
                left: 'center',
                top: 'center',
                textStyle: { color: '#aaa', fontSize: 16 },
            },
        });
        return;
    }

    try {
        const params = new URLSearchParams();
        params.set('species_names', speciesNames.join(','));
        params.set('value_type', valueType);

        const resp = await apiFetch(`/api/jobs/${jobId}/chart-data?${params.toString()}`);
        const data = await resp.json();
        updateChart(data, valueType);
    } catch (err) {
        showError('加载图表数据失败：' + err.message);
    }
}

// 加载历史记录
async function loadHistory() {
    try {
        const resp = await apiFetch('/api/jobs');
        const jobs = await resp.json();
        const container = document.getElementById('historyList');

        if (!jobs.length) {
            container.innerHTML = '<p class="hint-text">暂无历史记录</p>';
            return;
        }

        // 按创建时间倒序
        jobs.sort((a, b) => {
            if (!a.created_at || !b.created_at) return 0;
            return new Date(b.created_at) - new Date(a.created_at);
        });

        container.innerHTML = jobs.map(job => {
            const statusLabel = STATUS_LABELS[job.status] || job.status;
            const time = job.created_at ? formatTime(job.created_at) : '';
            const isActive = job.job_id === currentJobId ? ' active' : '';
            return `
                <div class="history-item${isActive}" onclick="loadJob('${job.job_id}')" title="${job.job_id}">
                    <div>
                        <span class="job-id">${shortenId(job.job_id)}</span>
                        <span class="job-time">${time}</span>
                    </div>
                    <span class="job-status ${job.status}">${statusLabel}</span>
                </div>
            `;
        }).join('');
    } catch {
        // 静默失败
    }
}

// 点击历史条目加载任务
async function loadJob(jobId) {
    currentJobId = jobId;
    hideError();

    try {
        const resp = await apiFetch(`/api/jobs/${jobId}`);
        const job = await resp.json();
        updateStatus(job.status, job.error);

        if (job.status === 'completed') {
            await loadSpeciesList(jobId);
        } else if (job.status === 'running' || job.status === 'pending') {
            pollJobStatus(jobId);
        }

        loadHistory(); // 刷新高亮
    } catch (err) {
        showError('加载任务失败：' + err.message);
    }
}

// ============================================
// UI 渲染
// ============================================

// 渲染元素输入（带 checkbox 开关）
function renderElementInputs(elements) {
    const container = document.getElementById('elementInputs');

    if (!elements || !elements.length) {
        container.innerHTML = '<p class="hint-text">该模板无需配置元素</p>';
        return;
    }

    container.innerHTML = elements.map(el => {
        const isActive = el.active !== false;
        const isRequired = !!el.required;
        const checkedAttr = isActive ? 'checked' : '';
        const disabledCb = isRequired ? 'disabled' : '';
        const disabledInput = isActive ? '' : 'disabled';
        const rowClass = isActive ? 'element-row' : 'element-row inactive';
        const displayVal = el.default_g ?? '';

        return `
            <div class="${rowClass}" data-symbol="${el.symbol}">
                <input type="checkbox"
                    class="element-toggle"
                    data-symbol="${el.symbol}"
                    data-required="${isRequired}"
                    data-default-g="${el.default_g ?? 1e-10}"
                    ${checkedAttr} ${disabledCb}
                    onchange="onElementToggle(this)"
                    title="${isRequired ? '必选元素，不可关闭' : '启用/禁用此元素'}"
                >
                <span class="element-label">${el.symbol}</span>
                <input type="number"
                    class="element-input"
                    data-symbol="${el.symbol}"
                    data-required="${isRequired}"
                    value="${displayVal}"
                    step="any"
                    placeholder="质量"
                    ${disabledInput}
                    oninput="updateTotalMass()"
                >
                <span class="element-unit">g</span>
            </div>
        `;
    }).join('');

    updateTotalMass();
}

// 元素开关切换
function onElementToggle(checkbox) {
    const symbol = checkbox.dataset.symbol;
    const row = checkbox.closest('.element-row');
    const input = row.querySelector('.element-input');

    if (checkbox.checked) {
        row.classList.remove('inactive');
        input.disabled = false;
        // 恢复到默认值（如果当前是 1e-10）
        const val = parseFloat(input.value);
        if (val <= 1e-9) {
            input.value = checkbox.dataset.defaultG;
        }
    } else {
        row.classList.add('inactive');
        input.disabled = true;
        input.value = 1e-10;
    }
    updateTotalMass();
}

// 更新总质量显示
function updateTotalMass() {
    const indicator = document.getElementById('totalMassIndicator');
    const valueSpan = document.getElementById('totalMassValue');
    if (!indicator || !valueSpan) return;

    const rows = document.querySelectorAll('.element-row');
    if (!rows.length) {
        indicator.style.display = 'none';
        return;
    }

    let total = 0;
    rows.forEach(row => {
        const toggle = row.querySelector('.element-toggle');
        if (toggle && toggle.checked) {
            const input = row.querySelector('.element-input');
            const val = parseFloat(input.value);
            if (!isNaN(val) && val > 0.001) total += val;
        }
    });

    valueSpan.textContent = formatNumber(total);
    indicator.style.display = '';

    // 颜色指示：接近 100g 为绿色，偏差大为红色
    const deviation = Math.abs(total - 100);
    if (deviation <= 1) {
        indicator.className = 'total-mass-indicator mass-ok';
    } else if (deviation <= 5) {
        indicator.className = 'total-mass-indicator mass-warn';
    } else {
        indicator.className = 'total-mass-indicator mass-bad';
    }
}

// 渲染物种列表（按 category 分组）
function renderSpeciesList(species) {
    const panel = document.getElementById('speciesPanel');

    if (!species || !species.length) {
        panel.innerHTML = '<p class="hint-text">无物种数据</p>';
        return;
    }

    const categoryLabels = {
        solution_total:     '溶液相 (Solution Phases)',
        pure:               '析出相/纯物质 (Precipitates)',
        solution_component: '溶液组分 (Solution Components)',
        element:            '元素 (Elements)',
    };

    // 按 category 分组
    const groups = {};
    species.forEach(s => {
        const cat = s.category || 'other';
        if (!groups[cat]) groups[cat] = [];
        groups[cat].push(s);
    });

    // 每组按 max_gram 降序排列
    Object.values(groups).forEach(arr =>
        arr.sort((a, b) => b.max_gram - a.max_gram)
    );

    // 渲染顺序：溶液相总量 → 析出相 → 溶液组分 → 元素
    const order = ['solution_total', 'pure', 'solution_component', 'element'];
    const allCats = [...order, ...Object.keys(groups).filter(c => !order.includes(c))];

    panel.innerHTML = allCats
        .filter(cat => groups[cat] && groups[cat].length)
        .map(cat => {
            const label = categoryLabels[cat] || cat;
            const items = groups[cat];
            return `
                <div class="species-group" data-category="${cat}">
                    <div class="species-group-header">
                        <span class="species-group-title">${label}</span>
                        <button class="toggle-all-btn" onclick="toggleGroup('${cat}')">全选/全不选</button>
                    </div>
                    ${items.map(s => `
                        <label class="species-item">
                            <input type="checkbox"
                                data-species="${s.name}"
                                onchange="onSpeciesChange()"
                            >
                            <span class="species-name">${s.display_name || s.name}</span>
                            <span class="species-max">max: ${formatNumber(s.max_gram)} g</span>
                        </label>
                    `).join('')}
                </div>
            `;
        }).join('');
}

// 更新图表
function updateChart(chartData, valueType) {
    if (!chartData || !chartData.series || !chartData.series.length) {
        chartInstance.clear();
        chartInstance.setOption({
            title: {
                text: '无数据',
                left: 'center',
                top: 'center',
                textStyle: { color: '#aaa', fontSize: 16 },
            },
        });
        return;
    }

    const option = buildChartOption(chartData, valueType);
    chartInstance.clear();
    chartInstance.setOption(option);
}

// 构建 ECharts 配置
function buildChartOption(data, valueType) {
    const yAxisNames = {
        gram:          '质量 (g)',
        mole:          '摩尔 (mol)',
        'wt%':         '质量分数 (wt%)',
        activity:      '活度',
        mole_fraction: '摩尔分数',
    };

    return {
        title: { text: '析出相/夹杂物 vs 温度', left: 'center', textStyle: { fontSize: 15 } },
        tooltip: {
            trigger: 'axis',
            confine: true,
            formatter: function (params) {
                if (!params.length) return '';
                let html = `<strong>${params[0].axisValueLabel} °C</strong><br>`;
                params.forEach(p => {
                    html += `${p.marker} ${p.seriesName}: <strong>${formatNumber(p.value)}</strong><br>`;
                });
                return html;
            },
        },
        legend: { type: 'scroll', bottom: 0 },
        grid: { left: 80, right: 30, top: 60, bottom: 80 },
        xAxis: {
            type: 'category',
            name: '温度 (°C)',
            data: data.temperatures,
            nameLocation: 'middle',
            nameGap: 30,
        },
        yAxis: {
            type: 'value',
            name: yAxisNames[valueType] || valueType,
            nameLocation: 'middle',
            nameGap: 55,
        },
        dataZoom: [
            { type: 'inside' },
            { type: 'slider', bottom: 30 },
        ],
        toolbox: {
            feature: {
                saveAsImage: { title: '保存图片' },
                dataView: { title: '数据视图', readOnly: true },
                restore: { title: '还原' },
            },
        },
        series: data.series.map(s => ({
            name: s.display_name || s.name,
            type: 'line',
            data: s.data,
            smooth: true,
            showSymbol: false,
            emphasis: { focus: 'series' },
        })),
    };
}

// 更新状态指示器
function updateStatus(status, error) {
    const container = document.getElementById('statusIndicator');
    const badge = document.getElementById('statusBadge');
    const text = document.getElementById('statusText');

    container.style.display = 'flex';
    badge.className = 'status-badge ' + status;
    text.textContent = STATUS_LABELS[status] || status;

    if (status === 'failed' && error) {
        showError(error);
    }
}

// ============================================
// 事件处理
// ============================================

// 物种勾选变化 → 重载图表
function onSpeciesChange() {
    reloadChart();
}

// 数值类型变化 → 重载图表
function onValueTypeChange() {
    reloadChart();
}

// 重载图表（收集选中物种 + 数值类型）
async function reloadChart() {
    if (!currentJobId) return;

    const checked = document.querySelectorAll('input[data-species]:checked');
    const names = Array.from(checked).map(cb => cb.dataset.species);
    const valueType = document.getElementById('valueType').value;

    await loadChartData(currentJobId, names, valueType);
}

// 全选/全不选某分组
function toggleGroup(category) {
    const group = document.querySelector(`.species-group[data-category="${category}"]`);
    if (!group) return;

    const checkboxes = group.querySelectorAll('input[type="checkbox"]');
    const allChecked = Array.from(checkboxes).every(cb => cb.checked);

    checkboxes.forEach(cb => { cb.checked = !allChecked; });
    reloadChart();
}

// ============================================
// 导出
// ============================================

function exportCSV() {
    if (!currentJobId) {
        showError('请先完成一次计算。');
        return;
    }
    window.open(`/api/jobs/${currentJobId}/export-csv`);
}

function downloadFiles() {
    if (!currentJobId) {
        showError('请先完成一次计算。');
        return;
    }
    window.open(`/api/jobs/${currentJobId}/download`);
}

function exportPNG() {
    if (!chartInstance) {
        showError('图表尚未初始化。');
        return;
    }
    const url = chartInstance.getDataURL({
        type: 'png',
        pixelRatio: 2,
        backgroundColor: '#fff',
    });
    const a = document.createElement('a');
    a.href = url;
    a.download = `factsage_chart_${currentJobId || 'unknown'}.png`;
    a.click();
}

// ============================================
// 工具函数
// ============================================

function resetSubmitBtn() {
    const btn = document.getElementById('submitBtn');
    btn.disabled = false;
    btn.classList.remove('loading');
    btn.textContent = '开始计算';
}

function showError(msg) {
    const el = document.getElementById('errorMsg');
    el.textContent = msg;
    el.style.display = '';
}

function hideError() {
    document.getElementById('errorMsg').style.display = 'none';
}

function shortenId(id) {
    if (!id) return '';
    return id.length > 12 ? id.slice(0, 8) + '...' : id;
}

function formatTime(isoStr) {
    try {
        const d = new Date(isoStr);
        const pad = n => String(n).padStart(2, '0');
        return `${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
    } catch {
        return '';
    }
}

function formatNumber(val) {
    if (val == null || isNaN(val)) return '-';
    if (Math.abs(val) < 0.001 && val !== 0) return val.toExponential(3);
    if (Math.abs(val) >= 10000) return val.toExponential(3);
    return parseFloat(val.toFixed(4)).toString();
}
