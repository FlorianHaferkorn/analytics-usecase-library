import type { Registry, CatalogSnapshot } from "@/types/registry";

let _cache: Registry | null = null;

export async function loadRegistry(): Promise<Registry> {
  if (_cache) return _cache;
  const res = await fetch("/api/registry", { next: { revalidate: 60 } });
  if (!res.ok) throw new Error("Failed to load registry");
  _cache = await res.json();
  return _cache!;
}

export function buildCatalogSnapshot(registry: Registry): CatalogSnapshot {
  return {
    kpi_ids: Object.keys(registry.objects.kpis),
    action_code_ids: Object.keys(registry.objects.action_codes),
    use_case_ids: Object.keys(registry.objects.use_cases),
    allowed_grains: [], // populated by API if needed
  };
}

export function getKpiDomains(registry: Registry): string[] {
  const domains = new Set<string>();
  for (const kpi of Object.values(registry.objects.kpis)) {
    (kpi.domain_tag ?? []).forEach((d) => domains.add(d));
  }
  return [...domains].sort();
}

export function getImpactDimensions(registry: Registry): string[] {
  const dims = new Set<string>();
  for (const kpi of Object.values(registry.objects.kpis)) {
    if (kpi.impact_dimension) dims.add(kpi.impact_dimension);
  }
  return [...dims].sort();
}
