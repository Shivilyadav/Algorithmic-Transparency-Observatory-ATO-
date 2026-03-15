let API_BASE = '';
const API_CANDIDATES = [
    'http://localhost:8001/api',
    'http://localhost:8080/api',
    'http://localhost:8000/api'
];

document.addEventListener('DOMContentLoaded', () => {
    // 1. Navigation Logic
    const navItems = document.querySelectorAll('.nav-item');
    const viewSections = document.querySelectorAll('.view-section');

    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            navItems.forEach(nav => nav.classList.remove('active'));
            item.classList.add('active');
            viewSections.forEach(view => view.classList.add('hidden'));
            const viewId = item.getAttribute('data-view');
            document.getElementById(`view-${viewId}`).classList.remove('hidden');
        });
    });

    // 2. Global Chart Instances
    Chart.defaults.color = '#94a3b8';
    Chart.defaults.borderColor = 'rgba(255, 255, 255, 0.1)';
    window.charts = {};

    // 3. Data Fetching & Initialization
    initXAIChart();
    initApplication();

    // Refresh Dashboard Data Every 5 Seconds (Real-time monitoring)
    setInterval(() => {
        fetchDashboardData();
        fetchRecentDecisions(); // Keep drop downs fresh
        fetchRawDatabaseLogs();
        fetchTransparencyReport();
        fetchResearchLens();
    }, 5000);

    // 4. XAI Analyze Logic
    document.getElementById('btn-analyze-xai').addEventListener('click', fetchXAIData);
    document.getElementById('btn-generate-report').addEventListener('click', generateComplianceReport);
});


async function initApplication() {
    await detectBackendBase();
    if (!API_BASE) {
        console.error('No backend server found on ports 8001/8080/8000.');
        return;
    }

    fetchDashboardData();
    fetchBiasData();
    fetchRecentDecisions();
    fetchComplianceLogs();
    fetchRawDatabaseLogs();
    fetchAgentArchitectures();
    fetchTransparencyReport();
    fetchResearchLens();
}

async function detectBackendBase() {
    for (const base of API_CANDIDATES) {
        try {
            const response = await fetch(`${base}/health`);
            if (response.ok) {
                API_BASE = base;
                return;
            }
        } catch (error) {
            // try next base
        }
    }
}
// --- API Fetch Functions ---

async function fetchDashboardData() {
    try {
        const response = await fetch(`${API_BASE}/dashboard/metrics`);
        if (!response.ok) throw new Error('Network response was not ok');
        const data = await response.json();
        
        // Update DOM elements
        document.getElementById('active-models-val').innerText = (data.active_models ?? 0).toLocaleString();
        document.getElementById('total-decisions-val').innerText = data.total_decisions_24h.toLocaleString();
        document.getElementById('alerts-triggered-val').innerText = (data.alerts_triggered ?? 0).toLocaleString();
        document.getElementById('fairness-score-val').innerText = data.fairness_score + '%';

        // Update Charts
        updateThroughputChart(data.throughput_history);
        populateFlaggedTable(data.recent_flags);
        
        // Update status indicator
        document.querySelector('.status-indicator').classList.add('online');
        document.querySelector('.status-indicator').style.backgroundColor = 'var(--accent-green)';
    } catch (error) {
        console.error("Error fetching dashboard data:", error);
        document.querySelector('.status-indicator').classList.remove('online');
        document.querySelector('.status-indicator').style.backgroundColor = 'var(--accent-red)';
    }
}

async function fetchBiasData() {
    try {
        const response = await fetch(`${API_BASE}/bias/analytics`);
        const data = await response.json();
        updateBiasCharts(data);
    } catch (error) {
        console.error("Error fetching bias data:", error);
    }
}

async function fetchRecentDecisions() {
    try {
        const response = await fetch(`${API_BASE}/decisions/recent`);
        const data = await response.json();
        const select = document.getElementById('decision-select');
        
        let html = '';
        if (data.hr) {
            html += `<optgroup label="HR Recruitment">`;
            data.hr.forEach(d => html += `<option value="${d.id}">${d.id} (${d.outcome})</option>`);
            html += `</optgroup>`;
        }
        if (data.finance) {
            html += `<optgroup label="Credit Risk">`;
            data.finance.forEach(d => html += `<option value="${d.id}">${d.id} (${d.outcome})</option>`);
            html += `</optgroup>`;
        }
        if (data.healthcare) {
            html += `<optgroup label="Healthcare Triage">`;
            data.healthcare.forEach(d => html += `<option value="${d.id}">${d.id} (${d.outcome})</option>`);
            html += `</optgroup>`;
        }
        select.innerHTML = html;
        
    } catch (e) { console.error("Error fetching decisions dropdown:", e); }
}

async function fetchXAIData() {
    const decId = document.getElementById('decision-select').value;
    if (!decId) return;
    
    const overlay = document.getElementById('loading-overlay');
    overlay.classList.remove('hidden');

    try {
        const response = await fetch(`${API_BASE}/xai/explain/${decId}`);
        const data = await response.json();
        
        overlay.classList.add('hidden');
        
        if (data.error) {
            alert(data.error);
            return;
        }
        
        const summaryBox = document.getElementById('xai-summary');
        
        // Build input details list
        let inputsHtml = '<ul>';
        for(let i=0; i<data.features.length; i++) {
             inputsHtml += `<li>${data.features[i]}: ${data.inputs[i].toFixed(2)}</li>`;
        }
        inputsHtml += '</ul>';
        
        summaryBox.innerHTML = `
            <p><strong>Decision ID:</strong> ${data.decision_id}</p><br>
            <p><strong>Outcome:</strong> ${data.outcome}</p><br>
            <p><strong>Input Parameters:</strong></p>
            ${inputsHtml}<br>
            <p><strong>Analysis:</strong> ${data.summary}</p>
        `;

        // Update Chart
        if(window.charts.shap) {
            window.charts.shap.data.labels = data.features;
            window.charts.shap.data.datasets[0].data = data.shap_values;
            window.charts.shap.update();
        }

        // Render explicit logic steps
        const logicContainer = document.getElementById('xai-logic-steps');
        if (logicContainer) {
            if (data.logic_steps && data.logic_steps.length > 0) {
                logicContainer.innerHTML = data.logic_steps
                    .map(step => `<li style="margin-bottom: 0.5rem;">${step}</li>`)
                    .join('');
            } else {
                logicContainer.innerHTML = `<li style="list-style: none; opacity: 0.5;">No detailed logic steps logged for this decision.</li>`;
            }
        }
    } catch (error) {
        overlay.classList.add('hidden');
        console.error("Error fetching XAI data:", error);
    }
}

async function fetchComplianceLogs() {
    try {
        const response = await fetch(`${API_BASE}/compliance/logs`);
        const data = await response.json();
        populateAuditLogs(data.logs);
    } catch (error) {
        console.error("Error fetching logs:", error);
    }
}

async function fetchRawDatabaseLogs() {
    try {
        const response = await fetch(`${API_BASE}/database/raw`);
        const data = await response.json();
        
        const tbody = document.getElementById('raw-db-tbody');
        let html = '';
        data.forEach(item => {
            const outcomeClass = item.outcome === 'Approved' ? 'badge-info' : 'badge-danger';
            html += `
                <tr>
                    <td><strong>${item.id}</strong></td>
                    <td>${item.model}</td>
                    <td>${item.timestamp}</td>
                    <td>${item.demographics}</td>
                    <td>${item.score.toFixed(2)}</td>
                    <td><span class="badge-tag ${outcomeClass}">${item.outcome}</span></td>
                    <td>${item.driver}</td>
                </tr>
            `;
        });
        tbody.innerHTML = html;
    } catch (error) {
        console.error("Error fetching raw database logs:", error);
    }
}

async function fetchAgentArchitectures() {
    try {
        const response = await fetch(`${API_BASE}/agents/architectures`);
        const data = await response.json();
        
        const container = document.getElementById('architectures-container');
        let html = '';
        
        data.architectures.forEach(arch => {
            let paramsHtml = '';
            arch.parameters.forEach(p => {
                let wColor = p.weight.includes('-') ? 'var(--accent-red)' : 'var(--accent-green)';
                paramsHtml += `<tr><td>${p.name}</td><td style="color:${wColor}; font-weight:bold;">${p.weight}</td></tr>`;
            });
            
            html += `
                <div class="architecture-card glass-panel">
                    <h2>${arch.name}</h2>
                    <div class="arch-type"><i class="fa-solid fa-code-branch"></i> ${arch.type}</div>
                    <p>${arch.description}</p>
                    <div>
                        <strong style="font-size:12px; color:var(--text-secondary);">Calculation Formula:</strong>
                        <div class="formula">${arch.algorithm_formula}</div>
                    </div>
                    <table class="arch-params">
                        <thead><tr><th>Parameter</th><th>Algorithm Weight</th></tr></thead>
                        <tbody>${paramsHtml}</tbody>
                    </table>
                    <div class="formula" style="color:#a3b8cc;">Decision Threshold: ${arch.threshold}</div>
                </div>
            `;
        });
        container.innerHTML = html;
        
    } catch (e) { console.error("Error fetching architectures", e); }
}

async function fetchTransparencyReport() {
    try {
        const response = await fetch(`${API_BASE}/reports/transparency`);
        if (!response.ok) throw new Error('Network response was not ok');
        const report = await response.json();
        renderTransparencyHighlights(report);
    } catch (error) {
        console.error("Error fetching transparency report:", error);
    }
}

function renderTransparencyHighlights(report) {
    document.getElementById('report-generated-at').innerText =
        `Last generated: ${new Date(report.generated_at_utc).toLocaleString()}`;
    document.getElementById('compliance-score-val').innerText =
        `${report.kpis.compliance_score_percent}%`;
    document.getElementById('xai-coverage-val').innerText =
        `${report.kpis.xai_coverage_percent}%`;
    document.getElementById('dir-val').innerText =
        report.kpis.disparate_impact_ratio;

    const insights = document.getElementById('research-insights-list');
    insights.innerHTML = report.recommendations
        .slice(0, 4)
        .map(item => `<li>${item}</li>`)
        .join('');
}

function renderGeneratedReport(report) {
    const stageLines = report.pipeline_status
        .map(stage => `[${stage.status.toUpperCase()}] ${stage.stage}: ${stage.detail}`)
        .join('<br>');
    const terminal = document.getElementById('generated-report-content');
    terminal.innerHTML = `
        <div class="log-line">Title: ${report.research_context.title}</div>
        <div class="log-line">Generated: ${new Date(report.generated_at_utc).toLocaleString()}</div>
        <div class="log-line">Compliance Score: ${report.kpis.compliance_score_percent}%</div>
        <div class="log-line">Fairness Score: ${report.kpis.fairness_score_percent}%</div>
        <div class="log-line">XAI Coverage: ${report.kpis.xai_coverage_percent}%</div>
        <div class="log-line">Disparate Impact Ratio: ${report.kpis.disparate_impact_ratio}</div>
        <div class="log-line">${stageLines}</div>
    `;
}


async function generateComplianceReport() {
    if (!API_BASE) return;

    try {
        const response = await fetch(`${API_BASE}/compliance/report`);
        if (!response.ok) throw new Error('Unable to generate report');

        const report = await response.json();
        renderTransparencyHighlights(report);
        renderGeneratedReport(report);
    } catch (error) {
        console.error('Error generating compliance report:', error);
        alert('Compliance report generation failed. Check backend server health.');
    }
}

async function fetchResearchLens() {
    try {
        const [flowRes, govRes, collectionRes, reportRes, fairnessRes] = await Promise.all([
            fetch(`${API_BASE}/flowchart/stages`),
            fetch(`${API_BASE}/governance/compliance`),
            fetch(`${API_BASE}/data-collection/status`),
            fetch(`${API_BASE}/evaluation/report`),
            fetch(`${API_BASE}/fairness/snapshot`)
        ]);

        if (![flowRes, govRes, collectionRes, reportRes, fairnessRes].every(r => r.ok)) return;

        const flow = await flowRes.json();
        const governance = await govRes.json();
        const collection = await collectionRes.json();
        const report = await reportRes.json();
        const fairness = await fairnessRes.json();

        const flowCount = document.getElementById('flow-stage-count');
        const governanceScore = document.getElementById('governance-score-val');
        const disparateImpact = document.getElementById('disparate-impact-val');
        const totalRecords = document.getElementById('sector-total-val');

        if (flowCount) flowCount.innerText = flow.total_stages || 0;
        if (governanceScore) governanceScore.innerText = `${(governance.score || 0).toFixed(1)}%`;
        if (disparateImpact) disparateImpact.innerText = fairness.disparate_impact_ratio ?? 0;
        if (totalRecords) totalRecords.innerText = collection.total_records || 0;

        renderFlowchartStages(flow.stages || []);
        renderGovernanceChecks(governance.checks || []);
        renderSectorCollection(collection.sectors || []);
        renderEvaluationSummary(report);
    } catch (error) {
        console.error('Error fetching research lens data:', error);
    }
}

function renderFlowchartStages(stages) {
    const box = document.getElementById('flowchart-stages-list');
    if (!box) return;
    box.innerHTML = stages
        .map((stage, i) => `<div class="log-line"><span class="timestamp">S${i + 1}</span> ${stage}</div>`)
        .join('');
}

function renderGovernanceChecks(checks) {
    const box = document.getElementById('governance-checks-list');
    if (!box) return;
    box.innerHTML = checks
        .map(c => `<div class="log-line"><span class="${c.status === 'pass' ? 'level-INFO' : 'level-WARN'}">${c.status.toUpperCase()}</span> ${c.name} (${c.value} / ${c.target})</div>`)
        .join('');
}

function renderSectorCollection(sectors) {
    const tbody = document.getElementById('sector-collection-tbody');
    if (!tbody) return;
    tbody.innerHTML = sectors
        .map(s => `
            <tr>
                <td>${s.sector}</td>
                <td>${s.decisions}</td>
                <td>${s.approved}</td>
                <td>${s.rejected}</td>
                <td>${s.approval_rate}%</td>
            </tr>`)
        .join('');
}

function renderEvaluationSummary(report) {
    const box = document.getElementById('evaluation-summary-box');
    if (!box) return;
    if (!report || !report.summary) {
        box.innerHTML = '<p>Evaluation report unavailable.</p>';
        return;
    }
    const recommendations = (report.recommendations || []).map(item => `<li>${item}</li>`).join('');
    box.innerHTML = `
        <p><strong>Total Decisions:</strong> ${report.summary.total_decisions}</p>
        <p><strong>Alerts:</strong> ${report.summary.alerts}</p>
        <p><strong>Fairness Score:</strong> ${report.summary.fairness_score}%</p>
        <p><strong>Governance Score:</strong> ${report.summary.governance_score}%</p>
        <p><strong>Active Models:</strong> ${report.summary.active_models}</p>
        <p><strong>Recommendations:</strong></p>
        <ul>${recommendations}</ul>
    `;
}
// --- Chart Update Functions ---

function updateThroughputChart(historyData) {
    const ctx = document.getElementById('throughputChart').getContext('2d');
    
    if (window.charts.throughput) {
        window.charts.throughput.data.datasets[0].data = historyData;
        window.charts.throughput.update();
    } else {
        const gradient = ctx.createLinearGradient(0, 0, 0, 400);
        gradient.addColorStop(0, 'rgba(59, 130, 246, 0.5)');
        gradient.addColorStop(1, 'rgba(59, 130, 246, 0.0)');

        window.charts.throughput = new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['-6m', '-5m', '-4m', '-3m', '-2m', '-1m', 'Now'],
                datasets: [{
                    label: 'Decisions / min',
                    data: historyData,
                    borderColor: '#3b82f6',
                    backgroundColor: gradient,
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });
    }
}

function updateBiasCharts(data) {
    // Bar Chart
    const ctxBar = document.getElementById('biasBarChart').getContext('2d');
    if (!window.charts.biasBar) {
        window.charts.biasBar = new Chart(ctxBar, {
            type: 'bar',
            data: {
                labels: data.demographic_groups,
                datasets: [{
                    label: 'Approval Rate (%)',
                    data: data.approval_rates,
                    backgroundColor: data.approval_rates.map(rate => rate < 50 ? 'rgba(239, 68, 68, 0.7)' : 'rgba(59, 130, 246, 0.7)'),
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } }
            }
        });
    }

    // Radar Chart
    const ctxRadar = document.getElementById('demographicParityChart').getContext('2d');
    if (!window.charts.biasRadar) {
        window.charts.biasRadar = new Chart(ctxRadar, {
            type: 'radar',
            data: {
                labels: data.parity_labels,
                datasets: [{
                    label: 'Model Fairness Score',
                    data: data.parity_scores,
                    backgroundColor: 'rgba(139, 92, 246, 0.2)',
                    borderColor: '#8b5cf6',
                    pointBackgroundColor: '#8b5cf6',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    r: {
                        angleLines: { color: 'rgba(255, 255, 255, 0.1)' },
                        grid: { color: 'rgba(255, 255, 255, 0.1)' },
                        pointLabels: { color: '#94a3b8' },
                        ticks: { display: false, min: 0, max: 1 }
                    }
                }
            }
        });
    }
}

function initXAIChart() {
    const ctx = document.getElementById('shapChart').getContext('2d');
    window.charts.shap = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Feature 1', 'Feature 2', 'Feature 3', 'Feature 4', 'Feature 5'],
            datasets: [{
                label: 'Impact on output',
                data: [0, 0, 0, 0, 0],
                backgroundColor: (context) => {
                    const value = context.dataset.data[context.dataIndex];
                    return value > 0 ? 'rgba(16, 185, 129, 0.7)' : 'rgba(239, 68, 68, 0.7)';
                },
                borderRadius: 4
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } }
        }
    });
}

// --- UI Population Functions ---

function populateFlaggedTable(flags) {
    const tbody = document.getElementById('flagged-decisions-tbody');
    let html = '';
    flags.forEach(item => {
        html += `
            <tr>
                <td><strong>#${item.id}</strong></td>
                <td>${item.model}</td>
                <td>${item.sector}</td>
                <td><span class="badge-tag badge-${item.type}">${item.reason}</span></td>
                <td>
                    <button class="btn" style="padding: 4px 8px; background: rgba(255,255,255,0.1); color: white; border:none; border-radius:4px; cursor:pointer;">View</button>
                    <button class="btn" style="padding: 4px 8px; background: rgba(239,68,68,0.2); color: #ef4444; border:none; border-radius:4px; cursor:pointer;">Audit</button>
                </td>
            </tr>
        `;
    });
    // Add placeholders if less than 3
    for(let i=flags.length; i<3; i++) {
        html += `<tr><td colspan="5" style="text-align:center; opacity:0.3">-</td></tr>`;
    }
    tbody.innerHTML = html;
}

function populateAuditLogs(logs) {
    const logContainer = document.getElementById('audit-log-content');
    let html = '';
    logs.forEach(log => {
        let levelClass = 'level-INFO';
        if (log.includes('[WARN]')) levelClass = 'level-WARN';
        if (log.includes('[ERR]')) levelClass = 'level-ERR';
        
        const safeLog = log.replace('[INFO]', `<span class="${levelClass}">INFO</span>`)
                           .replace('[WARN]', `<span class="${levelClass}">WARN</span>`);
                           
        html += `<div class="log-line"><span class="timestamp">${new Date().toISOString().split('T')[0]}</span> ${safeLog}</div>`;
    });
    logContainer.innerHTML = html;
}


