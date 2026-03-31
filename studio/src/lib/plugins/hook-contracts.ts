/**
 * Hook Contracts — Typed payloads for every plugin hook.
 *
 * Each hook has a well-defined payload type. Plugins receive typed data
 * instead of `unknown`, enabling autocomplete and compile-time safety.
 */

export interface OnBracketLoadPayload {
  bracketId: string;
  kpiIds: string[];
  status: string;
}

export interface OnKpiEvaluatePayload {
  kpiId: string;
  value: number;
  previousValue?: number;
  delta?: number;
}

export interface OnThemeChangePayload {
  primary: string;
  secondary: string;
  background: string;
  fontFamily?: string;
}

export interface OnExportPayload {
  format: string;
  bracketId: string;
  timestamp: string;
}

export interface OnApprovalPayload {
  bracketId: string;
  action: string;
  actor: string;
  status: string;
}

/** Map from hook name to its typed payload. */
export interface HookPayloadMap {
  onBracketLoad: OnBracketLoadPayload;
  onKpiEvaluate: OnKpiEvaluatePayload;
  onThemeChange: OnThemeChangePayload;
  onExport: OnExportPayload;
  onApproval: OnApprovalPayload;
}

export type TypedPluginHook = keyof HookPayloadMap;

/** All hook names as an array for validation. */
export const ALL_HOOKS: TypedPluginHook[] = [
  'onBracketLoad',
  'onKpiEvaluate',
  'onThemeChange',
  'onExport',
  'onApproval',
];
