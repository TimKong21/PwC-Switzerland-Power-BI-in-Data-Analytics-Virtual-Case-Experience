const metricFile = "./data/case-metrics.json";

const number = new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 });
const decimal = new Intl.NumberFormat("en-US", { minimumFractionDigits: 1, maximumFractionDigits: 2 });

const get = (object, path) => path.split(".").reduce((value, key) => value?.[key], object);
const escapeHtml = (value) => String(value).replace(/[&<>"]/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[character]);

function format(value, type = "number") {
  if (value === undefined || value === null || Number.isNaN(value)) return "—";
  if (type === "percent") return `${decimal.format(value)}%`;
  if (type === "decimal") return decimal.format(value);
  if (type === "seconds") return `${decimal.format(value)}s`;
  if (type === "currency") return `$${decimal.format(value)}`;
  if (type === "currency-compact") {
    return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", notation: "compact", maximumFractionDigits: 2 }).format(value);
  }
  return number.format(value);
}

function accessibleTable(rows, fields, valueType = "number") {
  const head = fields.map((field) => `<th scope="col">${escapeHtml(field.label)}</th>`).join("");
  const body = rows.map((row) => `<tr>${fields.map((field) => `<td>${escapeHtml(field.format ? field.format(row[field.key]) : field.key === "label" ? row[field.key] : format(row[field.key], valueType))}</td>`).join("")}</tr>`).join("");
  return `<table class="sr-only"><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table>`;
}

function renderBar(host, rows) {
  const valueKey = host.dataset.value || "value";
  const valueType = host.dataset.format || "number";
  const maximum = Number(host.dataset.max) || Math.max(...rows.map((row) => Number(row[valueKey]) || 0), 1);
  const color = host.dataset.color || "teal";
  const description = rows.map((row) => `${row.label}: ${format(row[valueKey], valueType)}`).join(", ");
  host.setAttribute("role", "img");
  host.setAttribute("aria-label", description);
  host.innerHTML = `<div class="data-bar-chart">${rows.map((row) => {
    const width = Math.max(0, Math.min(100, (Number(row[valueKey]) || 0) / maximum * 100));
    return `<div class="data-bar-row"><span class="data-bar-label">${escapeHtml(row.label)}</span><span class="data-bar-track"><span class="data-bar-fill ${color}" style="width:${width.toFixed(3)}%"></span></span><strong class="data-bar-value">${format(row[valueKey], valueType)}</strong></div>`;
  }).join("")}</div>${accessibleTable(rows, [{ key: "label", label: "Category" }, { key: valueKey, label: "Value" }], valueType)}`;
}

function renderGroupedBar(host, rows) {
  const fields = host.dataset.series.split(",").map((entry) => {
    const [key, label, color = "teal"] = entry.split(":");
    return { key, label, color };
  });
  const valueType = host.dataset.format || "number";
  const maximum = Number(host.dataset.max) || Math.max(...rows.flatMap((row) => fields.map((field) => Number(row[field.key]) || 0)), 1);
  const description = rows.map((row) => `${row.label}: ${fields.map((field) => `${field.label} ${format(row[field.key], valueType)}`).join(", ")}`).join("; ");
  host.setAttribute("role", "img");
  host.setAttribute("aria-label", description);
  host.innerHTML = `<div class="chart-key">${fields.map((field) => `<span class="key ${field.color}">${escapeHtml(field.label)}</span>`).join("")}</div><div class="grouped-chart">${rows.map((row) => `<div class="grouped-row"><span class="data-bar-label">${escapeHtml(row.label)}</span><span class="grouped-bars">${fields.map((field) => {
    const width = Math.max(0, Math.min(100, (Number(row[field.key]) || 0) / maximum * 100));
    return `<span class="grouped-item"><span class="grouped-track"><span class="data-bar-fill ${field.color}" style="width:${width.toFixed(3)}%"></span></span><strong>${format(row[field.key], valueType)}</strong></span>`;
  }).join("")}</span></div>`).join("")}</div>${accessibleTable(rows, [{ key: "label", label: "Category" }, ...fields], valueType)}`;
}

function renderStackedBar(host, rows) {
  const fields = host.dataset.series.split(",").map((entry) => {
    const [key, label, color = "teal"] = entry.split(":");
    return { key, label, color };
  });
  const maximum = Number(host.dataset.max) || Math.max(...rows.map((row) => fields.reduce((sum, field) => sum + (Number(row[field.key]) || 0), 0)), 1);
  const description = rows.map((row) => `${row.label}: ${fields.map((field) => `${field.label} ${number.format(row[field.key])}`).join(", ")}`).join("; ");
  host.setAttribute("role", "img");
  host.setAttribute("aria-label", description);
  host.innerHTML = `<div class="chart-key">${fields.map((field) => `<span class="key ${field.color}">${escapeHtml(field.label)}</span>`).join("")}</div><div class="data-bar-chart">${rows.map((row) => {
    const total = fields.reduce((sum, field) => sum + (Number(row[field.key]) || 0), 0);
    return `<div class="data-bar-row"><span class="data-bar-label">${escapeHtml(row.label)}</span><span class="stacked-track">${fields.map((field) => `<span class="data-bar-fill ${field.color}" style="width:${((Number(row[field.key]) || 0) / maximum * 100).toFixed(3)}%"></span>`).join("")}</span><strong class="data-bar-value">${number.format(total)}</strong></div>`;
  }).join("")}</div>${accessibleTable(rows, [{ key: "label", label: "Category" }, ...fields])}`;
}

function renderDonut(host, rows) {
  const valueKey = host.dataset.value || "count";
  const valueType = host.dataset.format || "percent";
  const palette = ["#007c7c", "#b7791f", "#b84343", "#486581", "#5e5ce6", "#c05621"];
  const total = rows.reduce((sum, row) => sum + (Number(row[valueKey]) || 0), 0) || 1;
  let cursor = 0;
  const segments = rows.map((row, index) => {
    const share = (Number(row[valueKey]) || 0) / total * 100;
    const segment = `${palette[index % palette.length]} ${cursor.toFixed(3)}% ${(cursor + share).toFixed(3)}%`;
    cursor += share;
    return segment;
  });
  const description = rows.map((row) => `${row.label}: ${format(row[valueKey], valueType === "percent" ? "percent" : valueType)}`).join(", ");
  host.setAttribute("role", "img");
  host.setAttribute("aria-label", description);
  host.innerHTML = `<div class="donut-layout"><div class="donut-ring" style="background:conic-gradient(${segments.join(",")})"><span>${host.dataset.center || number.format(total)}</span></div><ul class="donut-key">${rows.map((row, index) => `<li><span style="background:${palette[index % palette.length]}"></span>${escapeHtml(row.label)} <strong>${format(row[valueKey], valueType === "percent" ? "percent" : valueType)}</strong></li>`).join("")}</ul></div>${accessibleTable(rows, [{ key: "label", label: "Category" }, { key: valueKey, label: "Value" }], valueType === "percent" ? "percent" : valueType)}`;
}

function renderLine(host, rows) {
  const valueKey = host.dataset.value || "count";
  const canvas = document.createElement("canvas");
  const description = rows.map((row) => `${row.label}: ${format(row[valueKey], host.dataset.format || "number")}`).join(", ");
  host.setAttribute("role", "img");
  host.setAttribute("aria-label", description);
  host.replaceChildren(canvas);
  const draw = () => {
    const bounds = host.getBoundingClientRect();
    const width = Math.max(300, Math.floor(bounds.width));
    const height = 255;
    const scale = window.devicePixelRatio || 1;
    canvas.width = width * scale;
    canvas.height = height * scale;
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;
    const context = canvas.getContext("2d");
    context.scale(scale, scale);
    const padding = { top: 24, right: 18, bottom: 38, left: 46 };
    const values = rows.map((row) => Number(row[valueKey]) || 0);
    const max = Math.max(...values, 1);
    const chartWidth = width - padding.left - padding.right;
    const chartHeight = height - padding.top - padding.bottom;
    context.font = "12px system-ui";
    context.strokeStyle = "#d9e2ec";
    context.fillStyle = "#486581";
    context.lineWidth = 1;
    for (let tick = 0; tick <= 4; tick += 1) {
      const y = padding.top + chartHeight - chartHeight * tick / 4;
      context.beginPath(); context.moveTo(padding.left, y); context.lineTo(width - padding.right, y); context.stroke();
      context.fillText(number.format(max * tick / 4), 2, y + 4);
    }
    context.strokeStyle = "#007c7c";
    context.lineWidth = 3;
    context.beginPath();
    values.forEach((value, index) => {
      const x = padding.left + chartWidth * index / Math.max(values.length - 1, 1);
      const y = padding.top + chartHeight - value / max * chartHeight;
      index ? context.lineTo(x, y) : context.moveTo(x, y);
    });
    context.stroke();
    context.fillStyle = "#007c7c";
    values.forEach((value, index) => {
      const x = padding.left + chartWidth * index / Math.max(values.length - 1, 1);
      const y = padding.top + chartHeight - value / max * chartHeight;
      context.beginPath(); context.arc(x, y, 4, 0, Math.PI * 2); context.fill();
      context.fillStyle = "#486581"; context.fillText(String(rows[index].label), x - 8, height - 14); context.fillStyle = "#007c7c";
    });
  };
  draw();
  new ResizeObserver(draw).observe(host);
  host.insertAdjacentHTML("beforeend", accessibleTable(rows, [{ key: "label", label: "Category" }, { key: valueKey, label: "Value" }], host.dataset.format || "number"));
}

function renderTable(host, rows) {
  const fields = host.dataset.columns.split(",").map((entry) => {
    const [key, label, formatType = "number"] = entry.split(":");
    return { key, label, format: (value) => key === "label" ? value : format(value, formatType) };
  });
  host.innerHTML = `<div class="table-wrap"><table class="data-table"><thead><tr>${fields.map((field) => `<th scope="col">${escapeHtml(field.label)}</th>`).join("")}</tr></thead><tbody>${rows.map((row) => `<tr>${fields.map((field) => `<td>${escapeHtml(field.format(row[field.key]))}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`;
}

function setReportTabs() {
  document.querySelectorAll("[data-report-tabs]").forEach((tabs) => {
    const buttons = [...tabs.querySelectorAll("button[data-tab-target]")];
    const activate = (button) => {
      buttons.forEach((candidate) => {
        const selected = candidate === button;
        candidate.setAttribute("aria-selected", String(selected));
        document.getElementById(candidate.dataset.tabTarget).hidden = !selected;
      });
    };
    buttons.forEach((button) => button.addEventListener("click", () => activate(button)));
  });
}

async function initialise() {
  const response = await fetch(metricFile);
  if (!response.ok) throw new Error("Case metrics could not be loaded.");
  const data = await response.json();
  document.querySelectorAll("[data-metric]").forEach((element) => {
    element.textContent = format(get(data, element.dataset.metric), element.dataset.format || "number");
  });
  document.querySelectorAll("[data-chart]").forEach((host) => {
    const rows = get(data, host.dataset.source);
    if (!Array.isArray(rows)) return;
    const renderer = { bar: renderBar, grouped: renderGroupedBar, stacked: renderStackedBar, donut: renderDonut, line: renderLine, table: renderTable }[host.dataset.chart];
    if (renderer) renderer(host, rows);
  });
  setReportTabs();
  document.documentElement.classList.add("charts-ready");
}

initialise().catch((error) => {
  console.error(error);
  document.querySelectorAll("[data-chart]").forEach((host) => { host.textContent = "Chart data could not be loaded."; });
});
