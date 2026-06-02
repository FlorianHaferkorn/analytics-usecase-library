/** Entity kinds and detail routes — see studio/docs/rebuild/DETAIL_IA.md */

export const STUDIO_ENTITY_KINDS = ['kpi', 'action', 'usecase', 'contract'] as const;
export type StudioEntityKind = (typeof STUDIO_ENTITY_KINDS)[number];

export type PaletteEntityKind = StudioEntityKind;

export function detailPath(kind: StudioEntityKind, id: string): string {
  return `/detail/${kind}/${encodeURIComponent(id)}`;
}

/** Map bracket loader ids to detail kind `usecase`. */
export function bracketDetailPath(bracketId: string): string {
  return detailPath('usecase', bracketId);
}
