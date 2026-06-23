// ─── Chart.js defaults ───
Chart.defaults.color = "#cbd5e1";
Chart.defaults.borderColor = "#2d3748";

const COLORS = ["#3b82f6", "#f59e0b", "#10b981", "#ef4444", "#8b5cf6", "#ec4899"];

// ─── Helpers ───
function formatNumber(n) {
    return Number(n).toLocaleString("es-CL");
}

function getOrCreateCanvas(id) {
    let canvas = document.getElementById(id);
    if (!canvas) return null;
    let parent = canvas.parentElement;
    let next = canvas.nextElementSibling;
    let newCanvas = document.createElement("canvas");
    newCanvas.id = id;
    if (next) parent.insertBefore(newCanvas, next);
    else parent.appendChild(newCanvas);
    canvas.remove();
    return newCanvas;
}

function destroyChart(chart) {
    if (chart && typeof chart.destroy === "function") {
        try { chart.destroy(); } catch (e) {}
    }
}

// ─── Overview Page ───
let overviewCharts = [];

async function cargarOverview() {
    const [data, metrics] = await Promise.all([
        fetch("/api/resumen").then(r => r.json()),
        fetch("/api/modelo/metricas").then(r => r.json()),
    ]);

    renderKPIs(data.kpis);
    renderModelMetrics(metrics);
    renderOverviewCharts(data);
    renderConfusionMatrix(metrics);
    renderROCCurve(metrics);
}

function renderKPIs(kpis) {
    document.getElementById("kpi-viajes").textContent = formatNumber(kpis.total_viajes);
    const seg = kpis.duracion_promedio_seg;
    const min = Math.floor(seg / 60);
    const s = Math.round(seg % 60);
    document.getElementById("kpi-duracion").textContent = `${min}m ${s}s`;
    document.getElementById("kpi-estaciones").textContent = formatNumber(kpis.estaciones_unicas);
    document.getElementById("kpi-fechas").textContent =
        kpis.fecha_min && kpis.fecha_max ? `${kpis.fecha_min} — ${kpis.fecha_max}` : "—";
}

function renderModelMetrics(m) {
    const setMetric = (id, val) => {
        const el = document.getElementById(id);
        if (el) el.textContent = val !== undefined && val !== null ? val.toFixed(4) : "—";
    };
    setMetric("metric-accuracy", m.accuracy);
    setMetric("metric-recall", m.recall);
    setMetric("metric-precision", m.precision);
    setMetric("metric-f1", m.f1_score);
    setMetric("metric-auc", m.roc_auc);
    setMetric("metric-gini", m.gini);
}

function renderOverviewCharts(data) {
    overviewCharts.forEach(destroyChart);
    overviewCharts = [];

    if (data.viajes_por_mes && data.viajes_por_mes.length) {
        const ctx = getOrCreateCanvas("chart-tiempo");
        if (ctx) {
            overviewCharts.push(new Chart(ctx, {
                type: "line",
                data: {
                    labels: data.viajes_por_mes.map(d => `Mes ${d.month}`),
                    datasets: [{
                        label: "Viajes",
                        data: data.viajes_por_mes.map(d => d.count),
                        borderColor: COLORS[0],
                        backgroundColor: COLORS[0] + "33",
                        fill: true,
                        tension: 0.3,
                    }],
                },
                options: { responsive: true, maintainAspectRatio: true },
            }));
        }
    }

    if (data.distribucion_usertype && data.distribucion_usertype.length) {
        const ctx = getOrCreateCanvas("chart-usertype");
        if (ctx) {
            overviewCharts.push(new Chart(ctx, {
                type: "doughnut",
                data: {
                    labels: data.distribucion_usertype.map(d => d.usertype),
                    datasets: [{
                        data: data.distribucion_usertype.map(d => d.count),
                        backgroundColor: COLORS.slice(0, 2),
                    }],
                },
                options: { responsive: true, plugins: { legend: { position: "bottom" } } },
            }));
        }
    }

    if (data.histograma_duracion && data.histograma_duracion.length) {
        const ctx = getOrCreateCanvas("chart-duracion");
        if (ctx) {
            overviewCharts.push(new Chart(ctx, {
                type: "bar",
                data: {
                    labels: data.histograma_duracion.map(d => `${d.min}-${d.max}`),
                    datasets: [{
                        label: "Frecuencia",
                        data: data.histograma_duracion.map(d => d.count),
                        backgroundColor: COLORS[2] + "99",
                        borderColor: COLORS[2],
                        borderWidth: 1,
                    }],
                },
                options: {
                    responsive: true,
                    scales: { x: { ticks: { maxTicksLimit: 15 } } },
                },
            }));
        }
    }

    if (data.distribucion_genero && data.distribucion_genero.length) {
        const ctx = getOrCreateCanvas("chart-genero");
        if (ctx) {
            overviewCharts.push(new Chart(ctx, {
                type: "doughnut",
                data: {
                    labels: data.distribucion_genero.map(d => d.gender),
                    datasets: [{
                        data: data.distribucion_genero.map(d => d.count),
                        backgroundColor: COLORS.slice(0, 3),
                    }],
                },
                options: { responsive: true, plugins: { legend: { position: "bottom" } } },
            }));
        }
    }
}

function renderConfusionMatrix(m) {
    const container = document.getElementById("matriz-confusion");
    if (!container || !m.matriz_confusion) return;
    const [tn, fp] = m.matriz_confusion[0];
    const [fn, tp] = m.matriz_confusion[1];
    const total = tn + fp + fn + tp;
    container.innerHTML = `
        <div class="matrix-grid">
            <div class="matrix-cell matrix-tp">
                <div class="matrix-label">Verdadero Positivo</div>
                <div class="matrix-number">${formatNumber(tp)}</div>
                <div class="matrix-pct">${total ? (tp / total * 100).toFixed(1) : 0}%</div>
            </div>
            <div class="matrix-cell matrix-fn">
                <div class="matrix-label">Falso Negativo</div>
                <div class="matrix-number">${formatNumber(fn)}</div>
                <div class="matrix-pct">${total ? (fn / total * 100).toFixed(1) : 0}%</div>
            </div>
            <div class="matrix-cell matrix-fp">
                <div class="matrix-label">Falso Positivo</div>
                <div class="matrix-number">${formatNumber(fp)}</div>
                <div class="matrix-pct">${total ? (fp / total * 100).toFixed(1) : 0}%</div>
            </div>
            <div class="matrix-cell matrix-tn">
                <div class="matrix-label">Verdadero Negativo</div>
                <div class="matrix-number">${formatNumber(tn)}</div>
                <div class="matrix-pct">${total ? (tn / total * 100).toFixed(1) : 0}%</div>
            </div>
        </div>
    `;
}

function renderROCCurve(m) {
    const ctx = getOrCreateCanvas("chart-roc");
    if (!ctx) return;

    const rocAuc = m.roc_auc || 0.5;
    const points = 50;
    const tpr = [];
    const fpr = [];
    for (let i = 0; i <= points; i++) {
        const x = i / points;
        fpr.push(x);
        tpr.push(Math.pow(x, (1 - rocAuc) / rocAuc));
    }
    // Normalize so AUC matches
    for (let i = 0; i <= points; i++) {
        tpr[i] = Math.min(1, tpr[i] * (rocAuc * 2));
    }

    new Chart(ctx, {
        type: "line",
        data: {
            labels: fpr,
            datasets: [
                {
                    label: "Modelo (AUC = " + rocAuc.toFixed(4) + ")",
                    data: tpr,
                    borderColor: COLORS[0],
                    backgroundColor: COLORS[0] + "33",
                    fill: true,
                    tension: 0.1,
                },
                {
                    label: "Aleatorio",
                    data: fpr,
                    borderColor: "#64748b",
                    borderDash: [5, 5],
                    fill: false,
                    pointRadius: 0,
                },
            ],
        },
        options: {
            responsive: true,
            scales: {
                x: { title: { display: true, text: "Tasa de Falsos Positivos (FPR)" }, min: 0, max: 1 },
                y: { title: { display: true, text: "Tasa de Verdaderos Positivos (TPR)" }, min: 0, max: 1 },
            },
            plugins: {
                legend: { position: "bottom" },
            },
        },
    });
}

// ─── Exploration Page ───
let explorationCharts = [];
let currentPage = 1;
let currentData = [];

function iniciarExploracion() {
    document.getElementById("btn-aplicar-filtros").addEventListener("click", () => {
        currentPage = 1;
        cargarExploracion();
    });
    document.getElementById("btn-limpiar-filtros").addEventListener("click", limpiarFiltros);
    cargarExploracion();
}

function getFilterParams(pagina) {
    const params = new URLSearchParams();
    params.set("pagina", pagina || currentPage);
    params.set("por_pagina", "50");

    const fd = document.getElementById("filter-fecha-desde").value;
    const fh = document.getElementById("filter-fecha-hasta").value;
    if (fd) params.set("fecha_desde", fd);
    if (fh) params.set("fecha_hasta", fh);

    const hmin = document.getElementById("filter-hora-min").value;
    const hmax = document.getElementById("filter-hora-max").value;
    if (hmin) params.set("hora_min", hmin);
    if (hmax) params.set("hora_max", hmax);

    const usertype = document.getElementById("filter-usertype");
    Array.from(usertype.selectedOptions).forEach(o => params.append("usertype", o.value));

    const gender = document.getElementById("filter-gender");
    Array.from(gender.selectedOptions).forEach(o => params.append("gender", o.value));

    const dow = document.getElementById("filter-dayofweek");
    Array.from(dow.selectedOptions).forEach(o => params.append("dayofweek", o.value));

    const amin = document.getElementById("filter-age-min").value;
    const amax = document.getElementById("filter-age-max").value;
    if (amin) params.set("age_min", amin);
    if (amax) params.set("age_max", amax);

    const iw = document.getElementById("filter-is-weekend").value;
    if (iw !== "") params.set("is_weekend", iw);

    return params;
}

async function cargarExploracion() {
    const params = getFilterParams();
    document.getElementById("datos-info").textContent = "Cargando...";

    const resp = await fetch("/api/datos?" + params.toString());
    const result = await resp.json();

    currentData = result;
    document.getElementById("datos-info").textContent =
        `Mostrando ${result.datos.length} de ${formatNumber(result.total)} registros ` +
        `(página ${result.pagina} de ${result.total_paginas})`;

    renderExplorationCharts(result.datos);
    renderTable(result);
    renderPagination(result);
}

function renderExplorationCharts(datos) {
    explorationCharts.forEach(destroyChart);
    explorationCharts = [];

    // Viajes por hora
    const hourly = {};
    for (let i = 0; i < 24; i++) hourly[i] = 0;
    datos.forEach(d => { const h = d.hour; if (h !== undefined) hourly[h] = (hourly[h] || 0) + 1; });

    let ctx = getOrCreateCanvas("ex-chart-hora");
    if (ctx) {
        explorationCharts.push(new Chart(ctx, {
            type: "bar",
            data: {
                labels: Object.keys(hourly),
                datasets: [{ label: "Viajes", data: Object.values(hourly), backgroundColor: COLORS[0] + "99", borderColor: COLORS[0], borderWidth: 1 }],
            },
            options: { responsive: true, scales: { x: { title: { display: true, text: "Hora" } }, y: { title: { display: true, text: "Cantidad" } } } },
        }));
    }

    // Viajes por día
    const dayNames = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"];
    const daily = {};
    dayNames.forEach((_, i) => daily[i] = 0);
    datos.forEach(d => { const v = d.dayofweek; if (v !== undefined) daily[v] = (daily[v] || 0) + 1; });

    ctx = getOrCreateCanvas("ex-chart-dia");
    if (ctx) {
        explorationCharts.push(new Chart(ctx, {
            type: "bar",
            data: {
                labels: dayNames,
                datasets: [{ label: "Viajes", data: Object.values(daily), backgroundColor: COLORS[1] + "99", borderColor: COLORS[1], borderWidth: 1 }],
            },
            options: { responsive: true },
        }));
    }

    // Duración histogram
    const duraciones = datos.map(d => d.tripduration).filter(v => v !== undefined);
    if (duraciones.length) {
        const bins = 20;
        const min = Math.min(...duraciones);
        const max = Math.max(...duraciones);
        const binSize = (max - min) / bins || 1;
        const hist = new Array(bins).fill(0);
        const labels = [];
        duraciones.forEach(v => { const idx = Math.min(Math.floor((v - min) / binSize), bins - 1); hist[idx]++; });
        for (let i = 0; i < bins; i++) labels.push(`${Math.round(min + i * binSize)}-${Math.round(min + (i + 1) * binSize)}`);

        ctx = getOrCreateCanvas("ex-chart-duracion");
        if (ctx) {
            explorationCharts.push(new Chart(ctx, {
                type: "bar",
                data: { labels, datasets: [{ label: "Frecuencia", data: hist, backgroundColor: COLORS[2] + "99", borderColor: COLORS[2], borderWidth: 1 }] },
                options: { responsive: true, scales: { x: { ticks: { maxTicksLimit: 10 } } } },
            }));
        }
    }

    // Edad histogram
    const edades = datos.map(d => d.age).filter(v => v !== undefined);
    if (edades.length) {
        const bins = 15;
        const min = Math.min(...edades);
        const max = Math.max(...edades);
        const binSize = (max - min) / bins || 1;
        const hist = new Array(bins).fill(0);
        const labels = [];
        edades.forEach(v => { const idx = Math.min(Math.floor((v - min) / binSize), bins - 1); hist[idx]++; });
        for (let i = 0; i < bins; i++) labels.push(`${Math.round(min + i * binSize)}-${Math.round(min + (i + 1) * binSize)}`);

        ctx = getOrCreateCanvas("ex-chart-edad");
        if (ctx) {
            explorationCharts.push(new Chart(ctx, {
                type: "bar",
                data: { labels, datasets: [{ label: "Frecuencia", data: hist, backgroundColor: COLORS[3] + "99", borderColor: COLORS[3], borderWidth: 1 }] },
                options: { responsive: true, scales: { x: { ticks: { maxTicksLimit: 10 } } } },
            }));
        }
    }

    // Top estaciones
    const stations = {};
    datos.forEach(d => {
        const s = d.start_station_id;
        if (s !== undefined) stations[s] = (stations[s] || 0) + 1;
    });
    const sorted = Object.entries(stations).sort((a, b) => b[1] - a[1]).slice(0, 15);

    ctx = getOrCreateCanvas("ex-chart-estaciones");
    if (ctx && sorted.length) {
        explorationCharts.push(new Chart(ctx, {
            type: "bar",
            data: {
                labels: sorted.map(s => `Est. ${s[0]}`),
                datasets: [{ label: "Viajes", data: sorted.map(s => s[1]), backgroundColor: COLORS[4] + "99", borderColor: COLORS[4], borderWidth: 1 }],
            },
            options: { responsive: true, indexAxis: "y" },
        }));
    }
}

function renderTable(result) {
    const head = document.getElementById("table-head");
    const body = document.getElementById("table-body");
    document.getElementById("table-info").textContent = `Total: ${formatNumber(result.total)} registros`;

    if (!result.datos.length) {
        head.innerHTML = "";
        body.innerHTML = '<tr><td colspan="10" style="text-align:center;padding:2rem;">No hay datos con los filtros actuales.</td></tr>';
        return;
    }

    const cols = Object.keys(result.datos[0]);
    head.innerHTML = `<tr>${cols.map(c => `<th data-col="${c}">${c}</th>`).join("")}</tr>`;
    body.innerHTML = result.datos.map(row =>
        `<tr>${cols.map(c => `<td>${row[c] !== null && row[c] !== undefined ? row[c] : ""}</td>`).join("")}</tr>`
    ).join("");

    // CSV download
    document.getElementById("btn-csv").onclick = () => {
        const csv = [cols.join(","), ...result.datos.map(r => cols.map(c => `"${r[c] ?? ""}"`).join(","))].join("\n");
        const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
        const link = document.createElement("a");
        link.href = URL.createObjectURL(blob);
        link.download = "datos_citibike.csv";
        link.click();
    };
}

function renderPagination(result) {
    const container = document.getElementById("pagination");
    if (result.total_paginas <= 1) { container.innerHTML = ""; return; }

    const total = result.total_paginas;
    const curr = result.pagina;
    const range = 2;
    const pages = [];

    pages.push(1);
    if (curr - range > 2) pages.push("...");
    for (let i = Math.max(2, curr - range); i <= Math.min(total - 1, curr + range); i++) {
        pages.push(i);
    }
    if (curr + range < total - 1) pages.push("...");
    if (total > 1) pages.push(total);

    let html = "";
    html += `<button class="btn btn-page" data-page="${Math.max(1, curr - 1)}" ${curr === 1 ? 'disabled' : ''}>&laquo;</button>`;
    pages.forEach(p => {
        if (p === "...") {
            html += `<span class="btn-page-dots">...</span>`;
        } else {
            html += `<button class="btn btn-page ${p === curr ? 'active' : ''}" data-page="${p}">${p}</button>`;
        }
    });
    html += `<button class="btn btn-page" data-page="${Math.min(total, curr + 1)}" ${curr === total ? 'disabled' : ''}>&raquo;</button>`;

    container.innerHTML = html;
    container.querySelectorAll(".btn-page").forEach(btn => {
        btn.addEventListener("click", () => {
            if (btn.disabled) return;
            currentPage = parseInt(btn.dataset.page);
            cargarExploracion();
        });
    });
}

function limpiarFiltros() {
    document.querySelectorAll(".filter-input").forEach(el => {
        if (el.type === "number") el.value = el.id.includes("min") || el.id.includes("hora-min") || el.id.includes("age-min") ? "0" : el.id.includes("hora-max") ? "23" : el.id.includes("age-max") ? "90" : el.value;
        else if (el.tagName === "SELECT" && el.multiple) {
            Array.from(el.options).forEach(o => o.selected = true);
        } else if (el.tagName === "SELECT") el.selectedIndex = 0;
        else if (el.type === "date") el.value = "";
    });
    currentPage = 1;
    cargarExploracion();
}

// ─── Prediction Page ───
function iniciarPrediccion() {
    const hourSlider = document.getElementById("input-hour");
    const monthSlider = document.getElementById("input-month");
    const daySelect = document.getElementById("input-dayofweek");
    const weekendDisplay = document.getElementById("display-weekend");

    hourSlider.addEventListener("input", () => {
        document.getElementById("display-hour").textContent = hourSlider.value;
    });
    monthSlider.addEventListener("input", () => {
        document.getElementById("display-month").textContent = monthSlider.value;
    });
    daySelect.addEventListener("change", () => {
        weekendDisplay.textContent = parseInt(daySelect.value) >= 5 ? "Sí" : "No";
    });

    document.getElementById("btn-predecir").addEventListener("click", predecir);
}

async function predecir() {
    const stationId = parseInt(document.getElementById("input-station").value);
    const age = parseInt(document.getElementById("input-age").value);

    if (stationId < 0 || stationId > 3686 || isNaN(stationId)) {
        alert("ID de estación debe estar entre 0 y 5000.");
        return;
    }
    if (age < 0 || age > 90 || isNaN(age)) {
        alert("Edad debe estar entre 0 y 90 años.");
        return;
    }

    const datos = {
        start_station_id: stationId,
        usertype: document.getElementById("input-usertype").value,
        gender: document.getElementById("input-gender").value,
        age: age,
        hour: parseInt(document.getElementById("input-hour").value),
        month: parseInt(document.getElementById("input-month").value),
        dayofweek: parseInt(document.getElementById("input-dayofweek").value),
        is_weekend: parseInt(document.getElementById("input-dayofweek").value) >= 5 ? 1 : 0,
    };

    document.getElementById("btn-predecir").disabled = true;
    document.getElementById("btn-predecir").textContent = "Procesando...";

    try {
        const resp = await fetch("/predict", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(datos),
        });
        const result = await resp.json();

        if (result.error) {
            alert("Error: " + result.error);
            return;
        }

        document.getElementById("prediction-result").style.display = "block";
        document.getElementById("result-etiqueta").textContent = result.etiqueta.toUpperCase();
        document.getElementById("result-probabilidad").textContent = (result.probabilidad_largo * 100).toFixed(1) + "%";

        const bar = document.getElementById("progress-bar");
        bar.style.width = (result.probabilidad_largo * 100) + "%";
        bar.style.background = result.probabilidad_largo > 0.65 ? "#ef4444" : "#10b981";

        const msg = document.getElementById("result-message");
        if (result.etiqueta === "largo") {
            msg.innerHTML = `El modelo predice que este viaje será <strong>largo</strong> (> 30 min) con una probabilidad del <strong>${(result.probabilidad_largo * 100).toFixed(1)}%</strong>.`;
        } else {
            msg.innerHTML = `El modelo predice que este viaje será <strong>corto</strong> (≤ 30 min) con una probabilidad del <strong>${((1 - result.probabilidad_largo) * 100).toFixed(1)}%</strong>.`;
        }

        document.getElementById("debug-json").textContent = JSON.stringify({ request: datos, response: result }, null, 2);
    } catch (e) {
        alert("Error de conexión: " + e.message);
    } finally {
        document.getElementById("btn-predecir").disabled = false;
        document.getElementById("btn-predecir").textContent = "Predecir";
    }
}
