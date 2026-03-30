"use client";
import { useEffect, useState, useMemo } from "react";
import type { Registry, KpiRecord, UseCaseRecord, ActionCodeRecord } from "@/types/registry";
import { Badge, ImpactBadge, StatusBadge } from "@/components/ui/Badge";

type Tab = "use_cases" | "kpis" | "action_codes";

function StatCard({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="bg-white rounded-lg border border-slate-200 px-5 py-4">
      <div className={`text-2xl font-bold ${color}`}>{value}</div>
      <div className="text-xs text-slate-500 mt-0.5">{label}</div>
    </div>
  );
}

function UseCaseCard({ id, uc }: { id: string; uc: UseCaseRecord }) {
  const kpiCount =
    (uc.orchestration?.influencing_kpi_ids?.length ?? 0) +
    (uc.orchestration?.supporting_kpi_ids?.length ?? 0);
  const acCount = uc.orchestration?.action_code_ids?.length ?? 0;
  return (
    <div className="bg-white rounded-lg border border-slate-200 p-4 hover:border-brand-primary transition-colors">
      <div className="flex items-start justify-between gap-2 mb-2">
        <div>
          <span className="font-mono text-xs text-slate-500">{id}</span>
          <h3 className="font-semibold text-slate-900 text-sm mt-0.5 leading-snug">
            {uc.title ?? id}
          </h3>
        </div>
        <ImpactBadge direction={uc.value_driver_model?.impact_direction} />
      </div>
      {uc.domain && <p className="text-xs text-slate-500 mb-2">{uc.domain}</p>}
      {uc.orchestration?.strategic_kpi_id && (
        <div className="text-xs mb-2">
          <span className="text-slate-400">North Star: </span>
          <code className="bg-slate-50 px-1 py-0.5 rounded text-brand-primary">
            {uc.orchestration.strategic_kpi_id}
          </code>
        </div>
      )}
      <div className="flex gap-2 mt-3 flex-wrap">
        <Badge label={`${kpiCount} KPIs`} variant="blue" />
        <Badge label={`${acCount} actions`} variant="purple" />
      </div>
    </div>
  );
}

function KpiCard({ id, kpi }: { id: string; kpi: KpiRecord }) {
  return (
    <div className="bg-white rounded-lg border border-slate-200 p-4 hover:border-brand-primary transition-colors">
      <div className="flex items-start justify-between gap-2 mb-1.5">
        <code className="text-xs font-mono text-brand-primary break-all">{id}</code>
        <StatusBadge status={kpi.status} />
      </div>
      {kpi.business?.purpose && (
        <p className="text-xs text-slate-600 line-clamp-2 mb-2">{kpi.business.purpose}</p>
      )}
      <div className="flex gap-1.5 flex-wrap mt-2">
        {kpi.kpi_type && <Badge label={kpi.kpi_type} variant="blue" />}
        {kpi.impact_dimension && <Badge label={kpi.impact_dimension} />}
        {(kpi.domain_tag ?? []).map((t) => (
          <Badge key={t} label={t} variant="gray" />
        ))}
      </div>
    </div>
  );
}

function ActionCodeCard({ id, ac }: { id: string; ac: ActionCodeRecord }) {
  const name = (ac.raw as Record<string, unknown>)?.name as string | undefined;
  const trigger = ac.raw as Record<string, unknown> | undefined;
  const triggerWhen = (trigger?.trigger as Record<string, unknown>)?.when as string | undefined;
  return (
    <div className="bg-white rounded-lg border border-slate-200 p-4 hover:border-brand-primary transition-colors">
      <div className="flex items-start justify-between gap-2 mb-1.5">
        <code className="text-xs font-mono text-purple-700">{id}</code>
        <StatusBadge status={ac.status} />
      </div>
      {name && <h3 className="text-sm font-medium text-slate-800 mb-1 leading-snug">{name}</h3>}
      {triggerWhen && (
        <p className="text-xs text-slate-500 line-clamp-2 italic">"{triggerWhen}"</p>
      )}
      <div className="flex gap-1.5 flex-wrap mt-2">
        {ac.owner_domain && <Badge label={ac.owner_domain} variant="blue" />}
        {ac.impact_dimension && <Badge label={ac.impact_dimension} />}
      </div>
    </div>
  );
}

export default function ExplorerPage() {
  const [registry, setRegistry] = useState<Registry | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<Tab>("use_cases");
  const [search, setSearch] = useState("");

  useEffect(() => {
    fetch("/api/registry")
      .then((r) => r.json())
      .then((d) => {
        if (d.error) setError(d.error);
        else setRegistry(d);
      })
      .catch((e) => setError(e.message));
  }, []);

  const filtered = useMemo(() => {
    if (!registry) return {};
    const q = search.toLowerCase();
    if (tab === "use_cases") {
      return Object.fromEntries(
        Object.entries(registry.objects.use_cases).filter(
          ([id, uc]) =>
            !q ||
            id.toLowerCase().includes(q) ||
            (uc.title ?? "").toLowerCase().includes(q) ||
            (uc.domain ?? "").toLowerCase().includes(q)
        )
      );
    }
    if (tab === "kpis") {
      return Object.fromEntries(
        Object.entries(registry.objects.kpis).filter(
          ([id, kpi]) =>
            !q ||
            id.toLowerCase().includes(q) ||
            (kpi.business?.purpose ?? "").toLowerCase().includes(q) ||
            (kpi.impact_dimension ?? "").toLowerCase().includes(q)
        )
      );
    }
    if (tab === "action_codes") {
      return Object.fromEntries(
        Object.entries(registry.objects.action_codes).filter(
          ([id, ac]) =>
            !q ||
            id.toLowerCase().includes(q) ||
            (ac.owner_domain ?? "").toLowerCase().includes(q) ||
            (ac.impact_dimension ?? "").toLowerCase().includes(q)
        )
      );
    }
    return {};
  }, [registry, tab, search]);

  const tabs: { id: Tab; label: string; count: number; color: string }[] = registry
    ? [
        { id: "use_cases", label: "Use Cases", count: Object.keys(registry.objects.use_cases).length, color: "text-blue-600" },
        { id: "kpis", label: "KPIs", count: Object.keys(registry.objects.kpis).length, color: "text-green-600" },
        { id: "action_codes", label: "Action Codes", count: Object.keys(registry.objects.action_codes).length, color: "text-purple-600" },
      ]
    : [];

  if (error) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="max-w-md text-center">
          <div className="text-4xl mb-4">⚠️</div>
          <h2 className="font-semibold text-slate-800 mb-2">Registry not available</h2>
          <p className="text-sm text-slate-500 mb-4">{error}</p>
          <code className="block text-xs bg-slate-100 p-3 rounded text-left">
            python tooling/ontology/registry_builder.py
          </code>
        </div>
      </div>
    );
  }

  if (!registry) {
    return (
      <div className="h-full flex items-center justify-center text-slate-400">
        <div className="flex items-center gap-2">
          <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          Loading registry…
        </div>
      </div>
    );
  }

  const entries = Object.entries(filtered);

  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* Stat bar */}
      <div className="bg-white border-b border-slate-200 px-6 py-3 flex gap-4 shrink-0">
        {tabs.map((t) => (
          <StatCard key={t.id} label={t.label} value={t.count} color={t.color} />
        ))}
        <div className="ml-auto flex items-center text-xs text-slate-400">
          Generated {new Date(registry.meta.generated_at_utc).toLocaleString()}
        </div>
      </div>

      {/* Tabs + Search */}
      <div className="bg-white border-b border-slate-200 px-6 flex items-center gap-6 shrink-0">
        <div className="flex gap-0">
          {tabs.map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors cursor-pointer
                ${tab === t.id
                  ? "border-brand-primary text-brand-primary"
                  : "border-transparent text-slate-500 hover:text-slate-700"
                }`}
            >
              {t.label}
              <span className="ml-1.5 text-xs text-slate-400">({t.count})</span>
            </button>
          ))}
        </div>
        <input
          type="search"
          placeholder="Search…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="ml-auto w-56 text-sm border border-slate-200 rounded-md px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-brand-primary"
        />
      </div>

      {/* Cards grid */}
      <div className="flex-1 overflow-y-auto p-6">
        {entries.length === 0 ? (
          <p className="text-sm text-slate-400 text-center mt-16">No results for "{search}"</p>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
            {entries.map(([id, obj]) =>
              tab === "use_cases" ? (
                <UseCaseCard key={id} id={id} uc={obj as UseCaseRecord} />
              ) : tab === "kpis" ? (
                <KpiCard key={id} id={id} kpi={obj as KpiRecord} />
              ) : (
                <ActionCodeCard key={id} id={id} ac={obj as ActionCodeRecord} />
              )
            )}
          </div>
        )}
      </div>
    </div>
  );
}
