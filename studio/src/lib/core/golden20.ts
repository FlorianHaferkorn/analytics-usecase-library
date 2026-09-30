/** The canonical Golden-spine KPI IDs used across the Blueprint page and Excel export.
 *  18 after the KPI dedup (removed svc.nps.index → KPI-CUS-003 and
 *  ops.otif.pct → KPI-SCM-007; both canonicals were already in the spine). */
export const GOLDEN_20_IDS = [
  'KPI-COM-005',
  'KPI-FIN-011',
  'KPI-CUS-001',
  'KPI-CUS-002',
  'KPI-CUS-003',
  'KPI-OPS-001',
  'KPI-OPS-002',
  'KPI-QUA-001',
  'KPI-QUA-003',
  'KPI-SCM-007',
  'KPI-SCM-001',
  'KPI-SCM-002',
  'KPI-SCM-005',
  'KPI-SCM-006',
  'KPI-COM-019',
  'KPI-COM-013',
  'KPI-SVC-005',
  'KPI-SVC-008',
] as const;

export const GOLDEN_20_IDS_SET: Set<string> = new Set(GOLDEN_20_IDS);
