/**
 * GET /api/export/excel?view=steering&projectId=...
 *
 * Builds a CEO-grade .xlsx workbook for the steering view with:
 *   - One tab per KPI card (Golden-20 KPIs from the KPI catalog)
 *   - One tab per Detail matrix (bracket-level KPI breakdown)
 *   - One _Actions tab with current action-code recommendations
 *
 * Does NOT embed Power BI live connections.  Instead, each sheet
 * includes a documented HYPERLINK cell pointing to the Fabric dataset.
 *
 * Query params:
 *   view       - currently only 'steering' is supported
 *   projectId  - optional project slug (used to resolve Fabric dataset URL)
 */

import ExcelJS from 'exceljs';
import { loadKpiCatalog } from '@/lib/core/catalog-loader';
import { loadAllActionCodes } from '@/lib/core/action-loader';
import { loadAllBrackets } from '@/lib/core/bracket-loader';
import { GOLDEN_20_IDS_SET as GOLDEN_20_IDS } from '@/lib/core/golden20';

const FABRIC_BASE_URL = 'https://app.fabric.microsoft.com/groups/';
const MINT = 'FF00D4AA';
const GOLD = 'FFFFB800';
const DARK = 'FF1E293B';
const WHITE = 'FFFFFFFF';
const LIGHT_BG = 'FFF0FDF4';

function applyHeaderStyle(cell: ExcelJS.Cell, bg: string = DARK) {
  cell.font = { bold: true, color: { argb: WHITE }, size: 11 };
  cell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: bg } };
  cell.alignment = { vertical: 'middle', horizontal: 'left', wrapText: true };
  cell.border = {
    bottom: { style: 'thin', color: { argb: MINT } },
  };
}

function applyDataStyle(cell: ExcelJS.Cell, even: boolean) {
  cell.fill = {
    type: 'pattern',
    pattern: 'solid',
    fgColor: { argb: even ? 'FFF8FAFC' : WHITE },
  };
  cell.alignment = { vertical: 'middle', wrapText: true };
}

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const view = searchParams.get('view') ?? 'steering';
  const projectId = searchParams.get('projectId') ?? 'default';

  if (view !== 'steering') {
    return new Response(JSON.stringify({ error: 'Only view=steering is supported.' }), {
      status: 400,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  // Load data
  const [allKpis, actions, brackets] = await Promise.all([
    loadKpiCatalog(),
    loadAllActionCodes(),
    loadAllBrackets(),
  ]);

  const golden20Kpis = allKpis.filter((k) => GOLDEN_20_IDS.has(k.kpi_id));
  const fabricDatasetUrl = `${FABRIC_BASE_URL}${projectId}/datasets`;

  const wb = new ExcelJS.Workbook();
  wb.creator = 'ActionReady Studio';
  wb.created = new Date();
  wb.properties.date1904 = false;

  // ─────────────────────────────────────────────────────────────
  // Sheet 1: KPI Cards (Golden-20)
  // ─────────────────────────────────────────────────────────────
  const kpiSheet = wb.addWorksheet('KPI Cards — Golden 20');
  kpiSheet.columns = [
    { key: 'kpi_id', width: 32 },
    { key: 'kpi_key', width: 30 },
    { key: 'domain', width: 18 },
    { key: 'purpose', width: 60 },
    { key: 'unit_format', width: 20 },
    { key: 'owner', width: 30 },
    { key: 'pbi_link', width: 40 },
  ];

  const kpiHeaders = ['KPI ID', 'KPI Name', 'Domain', 'Business Purpose', 'Unit / Format', 'Business Owner', 'Open in Power BI'];
  const kpiHeaderRow = kpiSheet.addRow(kpiHeaders);
  kpiHeaderRow.eachCell((cell) => applyHeaderStyle(cell));
  kpiHeaderRow.height = 28;

  golden20Kpis.forEach((kpi, idx) => {
    const row = kpiSheet.addRow([
      kpi.kpi_id,
      kpi.kpi_key,
      (kpi.domain_tag ?? []).join(', '),
      kpi.business?.purpose ?? '',
      kpi.business?.unit_format ?? '',
      kpi.governance?.business_owner ?? '',
      { text: 'Open in Power BI', hyperlink: fabricDatasetUrl },
    ]);
    const even = idx % 2 === 0;
    row.eachCell((cell) => applyDataStyle(cell, even));
    const linkCell = row.getCell('pbi_link');
    linkCell.font = { color: { argb: 'FF0070C0' }, underline: true };
    row.height = 22;
  });

  kpiSheet.views = [{ state: 'frozen', xSplit: 0, ySplit: 1 }];

  // ─────────────────────────────────────────────────────────────
  // Sheet 2: Detail Matrix (brackets × KPIs)
  // ─────────────────────────────────────────────────────────────
  const detailSheet = wb.addWorksheet('Detail Matrix');
  detailSheet.columns = [
    { key: 'use_case_id', width: 16 },
    { key: 'use_case_title', width: 38 },
    { key: 'domain', width: 18 },
    { key: 'strategic_kpi', width: 30 },
    { key: 'impact_direction', width: 18 },
    { key: 'influencing_kpis', width: 50 },
    { key: 'action_codes', width: 40 },
    { key: 'pbi_link', width: 40 },
  ];

  const detailHeaders = [
    'Use Case ID', 'Title', 'Domain', 'Strategic KPI',
    'Impact Direction', 'Influencing KPIs', 'Action Codes', 'Open in Power BI',
  ];
  const detailHeaderRow = detailSheet.addRow(detailHeaders);
  detailHeaderRow.eachCell((cell) => applyHeaderStyle(cell, MINT.replace('FF', '')));
  detailHeaderRow.height = 28;

  brackets.forEach((b, idx) => {
    const row = detailSheet.addRow([
      b.id,
      b.title,
      b.domain,
      b.orchestration?.strategic_kpi_id ?? '',
      b.value_driver_model?.impact_direction ?? '',
      (b.orchestration?.influencing_kpi_ids ?? []).join(', '),
      (b.orchestration?.action_code_ids ?? []).join(', '),
      { text: 'Open in Power BI', hyperlink: fabricDatasetUrl },
    ]);
    const even = idx % 2 === 0;
    row.eachCell((cell) => applyDataStyle(cell, even));
    const linkCell = row.getCell('pbi_link');
    linkCell.font = { color: { argb: 'FF0070C0' }, underline: true };
    row.height = 22;
  });

  detailSheet.views = [{ state: 'frozen', xSplit: 0, ySplit: 1 }];

  // ─────────────────────────────────────────────────────────────
  // Sheet 3: _Actions
  // ─────────────────────────────────────────────────────────────
  const actionsSheet = wb.addWorksheet('_Actions');
  actionsSheet.columns = [
    { key: 'action_id', width: 16 },
    { key: 'action_name', width: 38 },
    { key: 'domain', width: 18 },
    { key: 'status', width: 14 },
    { key: 'trigger_kpis', width: 42 },
    { key: 'confidence', width: 14 },
    { key: 'impact_category', width: 16 },
    { key: 'pbi_link', width: 40 },
  ];

  const actionsHeaders = [
    'Action Code ID', 'Name', 'Domain', 'Status',
    'Trigger KPIs', 'Confidence', 'Impact Category', 'Open in Power BI',
  ];
  const actionsHeaderRow = actionsSheet.addRow(actionsHeaders);
  actionsHeaderRow.eachCell((cell) => applyHeaderStyle(cell, GOLD.replace('FF', '')));
  actionsHeaderRow.eachCell((cell) => {
    cell.font = { bold: true, color: { argb: DARK }, size: 11 };
  });
  actionsHeaderRow.height = 28;

  actions.forEach((a, idx) => {
    const row = actionsSheet.addRow([
      a.id,
      a.name,
      a.owner_domain,
      a.status,
      (a.kpis?.trigger_kpis ?? []).join(', '),
      (a.impact as Record<string, Record<string, string> | undefined> | undefined)?.confidence?.level ?? '',
      (a.impact as Record<string, string> | undefined)?.category ?? '',
      { text: 'Open in Power BI', hyperlink: fabricDatasetUrl },
    ]);
    const even = idx % 2 === 0;
    row.eachCell((cell) => applyDataStyle(cell, even));
    const linkCell = row.getCell('pbi_link');
    linkCell.font = { color: { argb: 'FF0070C0' }, underline: true };
    row.height = 22;
  });

  actionsSheet.views = [{ state: 'frozen', xSplit: 0, ySplit: 1 }];

  // ─────────────────────────────────────────────────────────────
  // Notes sheet
  // ─────────────────────────────────────────────────────────────
  const notesSheet = wb.addWorksheet('_Notes');
  notesSheet.getCell('A1').value = 'ActionReady Studio — Steering Export';
  notesSheet.getCell('A1').font = { bold: true, size: 14, color: { argb: DARK } };
  notesSheet.getCell('A2').value = `Generated: ${new Date().toISOString()}`;
  notesSheet.getCell('A3').value = `Project: ${projectId}`;
  notesSheet.getCell('A4').value = 'Power BI links open the Fabric semantic model dataset page.';
  notesSheet.getCell('A4').font = { italic: true, color: { argb: '80555555' } };
  notesSheet.getCell('A5').value = 'KPI definitions are governed in core/kpi_catalog/. Do not redefine meaning in this workbook.';
  notesSheet.getCell('A5').font = { italic: true, color: { argb: '80555555' } };
  notesSheet.getColumn('A').width = 80;

  // Serialize to buffer
  const buffer = await wb.xlsx.writeBuffer();

  return new Response(buffer, {
    headers: {
      'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      'Content-Disposition': `attachment; filename="steering-export-${projectId}.xlsx"`,
      'Cache-Control': 'no-store',
    },
  });
}
