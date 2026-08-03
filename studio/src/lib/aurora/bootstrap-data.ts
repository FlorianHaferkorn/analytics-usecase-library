/**
 * Server-side bootstrap payload for the Aurora showcase snapshot.
 *
 * The shell loads this once per request and hands it to a client component, which
 * publishes it into the project store. That keeps `node:fs` on the server (the snapshot
 * is read from disk) while client surfaces — the simulator, framework overview — can read
 * real Aurora values instead of falling back to their id-derived stubs.
 *
 * Reads the existing snapshot loader rather than a second data path: `kpi-snapshot.ts`
 * stays the single reader of `data/aurora_kpi_snapshot.json`.
 */
import { loadAuroraSnapshot, type AuroraKpiValue } from './kpi-snapshot';

export interface AuroraBootstrapData {
  /** Computed values per `kpi_id`; empty when no snapshot has been generated yet. */
  kpis: Record<string, AuroraKpiValue>;
  /** True when a snapshot was found — surfaces "showcase data is live" in the UI. */
  linked: boolean;
  /** When the snapshot was generated, ISO-8601; null when unknown or unlinked. */
  generatedAt: string | null;
  /** Which pipeline produced it, for provenance display; null when unlinked. */
  source: string | null;
}

const UNLINKED: AuroraBootstrapData = {
  kpis: {},
  linked: false,
  generatedAt: null,
  source: null,
};

/**
 * Build the client payload from the Aurora snapshot.
 *
 * Never throws and never returns undefined: a missing snapshot is a normal state (the
 * aggregator may not have run), and callers must be able to render without it.
 */
export function getAuroraBootstrapData(): AuroraBootstrapData {
  const snapshot = loadAuroraSnapshot();
  if (!snapshot) return UNLINKED;

  return {
    kpis: snapshot.kpis ?? {},
    linked: true,
    generatedAt: snapshot._meta?.generatedAt ?? null,
    source: snapshot._meta?.source ?? null,
  };
}
