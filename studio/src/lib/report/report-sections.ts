/**
 * Report Sections — HTML generators for each report section.
 */

import type { KpiSnapshot, TrendPoint, WaterfallDriver, EvidenceRow } from '@/lib/dashboard/sample-data';

function escapeHtml(text: string): string {
  return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

export function renderPulseSection(kpis: KpiSnapshot[]): string {
  const cards = kpis.map((kpi) => {
    const delta = kpi.value - kpi.previousValue;
    const deltaStr = `${delta >= 0 ? '+' : ''}${delta.toFixed(1)}${kpi.unit}`;
    const statusClass = `status-${kpi.status}`;
    return `
      <div class="pulse-card">
        <div class="label">${escapeHtml(kpi.label)}</div>
        <div class="value ${statusClass}">${kpi.value}${kpi.unit}</div>
        <div class="delta ${statusClass}">${deltaStr} vs prior</div>
        <div class="target">Target: ${kpi.target}${kpi.unit}</div>
      </div>
    `;
  }).join('');

  return `<h2>KPI Pulse</h2><div class="pulse-grid">${cards}</div>`;
}

export function renderTrendSection(label: string, data: TrendPoint[]): string {
  const maxVal = Math.max(...data.map((d) => d.value));
  const bars = data.map((d) => {
    const heightPct = maxVal > 0 ? (d.value / maxVal) * 100 : 0;
    return `<div class="trend-bar" style="height:${heightPct}%"><span class="val">${d.value}</span></div>`;
  }).join('');
  const labels = data.map((d) => `<span>${d.period}</span>`).join('');

  return `
    <h2>${escapeHtml(label)} — 12-Month Trend</h2>
    <div class="trend-container">
      <div class="trend-bars">${bars}</div>
      <div class="trend-labels">${labels}</div>
    </div>
  `;
}

export function renderWaterfallSection(drivers: WaterfallDriver[]): string {
  const maxDelta = Math.max(...drivers.map((d) => Math.abs(d.delta)), 0.1);
  const items = drivers.map((d) => {
    const heightPct = (Math.abs(d.delta) / maxDelta) * 80;
    const barClass = d.delta >= 0 ? 'bar-positive' : 'bar-negative';
    const sign = d.delta >= 0 ? '+' : '';
    return `
      <div class="waterfall-item">
        <div class="bar ${barClass}" style="height:${heightPct}px"></div>
        <div class="driver">${escapeHtml(d.driver)}</div>
        <div class="delta-val">${sign}${d.delta.toFixed(1)}pp</div>
      </div>
    `;
  }).join('');

  return `
    <h2>Margin Bridge</h2>
    <div class="waterfall-container">
      <div class="waterfall-bars">${items}</div>
    </div>
  `;
}

export function renderEvidenceSection(rows: EvidenceRow[]): string {
  const tableRows = rows.map((r) => `
    <tr>
      <td>${escapeHtml(r.entity)}</td>
      <td>${r.kpiValue.toFixed(1)}%</td>
      <td class="${r.delta >= 0 ? 'status-on-track' : 'status-off-track'}">${r.delta >= 0 ? '+' : ''}${r.delta.toFixed(1)}pp</td>
      <td>${escapeHtml(r.actionCode)}</td>
      <td class="priority-${r.priority}">${r.priority}</td>
    </tr>
  `).join('');

  return `
    <h2>Evidence Matrix</h2>
    <table>
      <thead><tr><th>Entity</th><th>KPI Value</th><th>Delta</th><th>Action Code</th><th>Priority</th></tr></thead>
      <tbody>${tableRows}</tbody>
    </table>
  `;
}
