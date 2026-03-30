"use client";
import { useEffect, useState, useMemo, useCallback } from "react";
import type { Registry, KpiRecord, UseCaseRecord, ActionCodeRecord } from "@/types/registry";
import { Badge, ImpactBadge, StatusBadge, QualityBadge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";

type Tab = "use_cases" | "kpis" | "action_codes";

/* ---------- Detail Panel ---------- */

function DetailPanel({
  type,
  id,
  data,
  onClose,
}: {
  type: Tab;
  id: string;
  data: UseCaseRecord | KpiRecord | ActionCodeRecord;
  onClose: () => void;
}) {
  const [yaml, setYaml] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saveMsg, setSaveMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const [editing, setEditing] = useState(false);
  const sourcePath = (data as { source?: string }).source;

  const loadYaml = useCallback(async () => {
    if (!sourcePath) return;
    setLoading(true);
    try {
      const res = await fetch(`/api/artifact?path=${encodeURIComponent(sourcePath)}`);
      const d = await res.json();
      if (d.error) setYaml(`# Could not load: ${d.error}`);
      else setYaml(d.content);
    } catch {
      setYaml("# Failed to load source file");
    } finally {
      setLoading(false);
    }
  }, [sourcePath]);

  useEffect(() => { loadYaml(); }, [loadYaml]);

  async function handleSave() {
    if (!yaml || !sourcePath) return;
    setSaving(true);
    setSaveMsg(null);
    try {
      const res = await fetch("/api/artifact", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content: yaml, path: sourcePath }),
      });
      const d = await res.json();
      if (d.error) throw new Error(d.error);
      setSaveMsg({ ok: true, text: `Saved to ${sourcePath}` });
      setEditing(false);
    } catch (e) {
      setSaveMsg({ ok: false, text: e instanceof Error ? e.message : "Save failed" });
    } finally {
      setSaving(false);
    }
  }

  const uc = type === "use_cases" ? (data as UseCaseRecord) : null;
  const kpi = type === "kpis" ? (data as KpiRecord) : null;
  const ac = type === "action_codes" ? (data as ActionCodeRecord) : null;

  return (
    <div className="fixed inset-0 z-50 flex">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />
      {/* Panel */}
      <div className="relative ml-auto w-full max-w-2xl bg-theme h-full overflow-y-auto shadow-2xl border-l border-theme">
        {/* Header */}
        <div className="sticky top-0 bg-theme border-b border-theme px-6 py-4 flex items-start justify-between z-10">
          <div className="min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <code className="text-xs font-mono text-brand-mint">{id}</code>
              <StatusBadge status={(data as { status?: string }).status} />
              {kpi?.governance && <QualityBadge score={kpi.metadata_quality?.completeness_score} />}
            </div>
            <h2 className="text-lg font-semibold text-theme truncate">
              {uc?.title ?? kpi?.title ?? kpi?.business?.purpose?.slice(0, 60) ?? ac?.name ?? id}
            </h2>
            {uc?.domain && <span className="text-xs text-theme-tertiary">{uc.domain}</span>}
            {ac?.owner_domain && <span className="text-xs text-theme-tertiary">{ac.owner_domain}</span>}
          </div>
          <button onClick={onClose} className="text-theme-tertiary hover:text-theme text-xl cursor-pointer shrink-0 ml-4">&times;</button>
        </div>

        {/* Metadata */}
        <div className="px-6 py-4 space-y-4">
          {/* Use Case details */}
          {uc && (
            <>
              <Section title="Orchestration">
                {uc.orchestration?.strategic_kpi_id && (
                  <Field label="North Star KPI" value={uc.orchestration.strategic_kpi_id} />
                )}
                {uc.orchestration?.influencing_kpi_ids?.length ? (
                  <Field label="Influencing KPIs" value={uc.orchestration.influencing_kpi_ids.join(", ")} />
                ) : null}
                {uc.orchestration?.action_code_ids?.length ? (
                  <Field label="Action Codes" value={uc.orchestration.action_code_ids.join(", ")} />
                ) : null}
              </Section>
              {uc.value_driver_model && (
                <Section title="Value Driver Model">
                  <Field label="Direction" value={uc.value_driver_model.impact_direction} />
                  {uc.value_driver_model.formula && <Field label="Formula" value={uc.value_driver_model.formula} mono />}
                  {uc.value_driver_model.primary_driver && <Field label="Primary Driver" value={uc.value_driver_model.primary_driver} />}
                </Section>
              )}
              {uc.governance && (
                <Section title="Governance">
                  <Field label="Owner" value={uc.governance.owner_role} />
                  <Field label="Steward" value={uc.governance.steward_role} />
                </Section>
              )}
            </>
          )}

          {/* KPI details */}
          {kpi && (
            <>
              <Section title="Business">
                {kpi.business?.purpose && <Field label="Purpose" value={kpi.business.purpose} />}
                {kpi.business?.definition && <Field label="Definition" value={kpi.business.definition} />}
                {kpi.business?.grain_scope && <Field label="Grain" value={kpi.business.grain_scope} />}
                {kpi.business?.unit_format && <Field label="Unit" value={kpi.business.unit_format} />}
              </Section>
              <Section title="Classification">
                <div className="flex gap-1.5 flex-wrap">
                  {kpi.kpi_type && <Badge label={kpi.kpi_type} variant="blue" />}
                  {kpi.calc_type && <Badge label={kpi.calc_type} variant="gray" />}
                  {kpi.impact_dimension && <Badge label={kpi.impact_dimension} variant="mint" />}
                  {(kpi.domain_tag ?? []).map((t) => <Badge key={t} label={t} variant="default" />)}
                </div>
              </Section>
              {kpi.technical && (
                <Section title="Technical">
                  {kpi.technical.measure_name && <Field label="Measure" value={kpi.technical.measure_name} mono />}
                  {kpi.technical.description && <Field label="Description" value={kpi.technical.description} />}
                  {kpi.technical.depends_on_measures?.length ? (
                    <Field label="Dependencies" value={kpi.technical.depends_on_measures.join(", ")} mono />
                  ) : null}
                </Section>
              )}
              {kpi.governance && (
                <Section title="Governance">
                  {kpi.governance.business_owner && <Field label="Business Owner" value={kpi.governance.business_owner} />}
                  {kpi.governance.data_owner && <Field label="Data Owner" value={kpi.governance.data_owner} />}
                </Section>
              )}
            </>
          )}

          {/* Action Code details */}
          {ac && (
            <>
              {ac.raw && (() => {
                const trigger = ac.raw.trigger as Record<string, string> | undefined;
                const kpis = ac.raw.kpis as Record<string, string[]> | undefined;
                const opExec = ac.raw.operational_execution as Record<string, unknown> | undefined;
                const steps = opExec?.steps as Array<Record<string, string>> | undefined;
                return (
                  <>
                    <Section title="Scope & Trigger">
                      {trigger?.when && <Field label="Trigger" value={trigger.when} />}
                      {trigger?.type && <Field label="Type" value={trigger.type} />}
                    </Section>
                    {kpis && (
                      <Section title="Linked KPIs">
                        {kpis.trigger_kpis?.length ? (
                          <Field label="Trigger KPIs" value={kpis.trigger_kpis.join(", ")} mono />
                        ) : null}
                        {kpis.outcome_kpis?.length ? (
                          <Field label="Outcome KPIs" value={kpis.outcome_kpis.join(", ")} mono />
                        ) : null}
                      </Section>
                    )}
                    {steps && (
                      <Section title="Operational Execution">
                        {steps.map((step, i) => (
                          <div key={i} className="text-sm text-theme-secondary">
                            <span className="text-theme-tertiary mr-2">{step.step ?? i + 1}.</span>
                            {step.action ?? step.description ?? JSON.stringify(step)}
                          </div>
                        ))}
                      </Section>
                    )}
                  </>
                );
              })()}
              {(ac.owner_role || ac.steward_role) && (
                <Section title="Governance">
                  {ac.owner_role && <Field label="Owner" value={ac.owner_role} />}
                  {ac.steward_role && <Field label="Steward" value={ac.steward_role} />}
                </Section>
              )}
            </>
          )}

          {/* Source path */}
          {sourcePath && (
            <div className="text-xs text-theme-tertiary pt-2 border-t border-theme">
              <code>{sourcePath}</code>
            </div>
          )}

          {/* YAML Editor */}
          {sourcePath && (
            <div className="pt-2">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-xs font-semibold text-theme-secondary uppercase tracking-wider">Source YAML</h3>
                <div className="flex gap-2">
                  {!editing ? (
                    <Button size="sm" variant="secondary" onClick={() => setEditing(true)}>
                      Edit
                    </Button>
                  ) : (
                    <>
                      <Button size="sm" variant="ghost" onClick={() => { setEditing(false); loadYaml(); setSaveMsg(null); }}>
                        Cancel
                      </Button>
                      <Button size="sm" onClick={handleSave} loading={saving}>
                        Save to Core
                      </Button>
                    </>
                  )}
                </div>
              </div>
              {saveMsg && (
                <p className={`text-xs mb-2 ${saveMsg.ok ? "text-signal-positive" : "text-signal-negative"}`}>
                  {saveMsg.text}
                </p>
              )}
              {loading ? (
                <div className="text-xs text-theme-tertiary py-4 text-center">Loading...</div>
              ) : editing ? (
                <textarea
                  value={yaml ?? ""}
                  onChange={(e) => { setYaml(e.target.value); setSaveMsg(null); }}
                  className="w-full yaml-editor bg-nagarro-blue-900 dark:bg-surface-dark text-nagarro-green-300 p-3 rounded border border-theme resize-none min-h-[300px] focus:outline-none focus:ring-1 focus:ring-brand-mint"
                  spellCheck={false}
                />
              ) : (
                <pre className="text-xs font-mono bg-theme-tertiary rounded p-3 overflow-x-auto max-h-[400px] overflow-y-auto text-theme-secondary whitespace-pre-wrap">
                  {yaml}
                </pre>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <h3 className="text-xs font-semibold text-theme-tertiary uppercase tracking-wider mb-2">{title}</h3>
      <div className="space-y-1.5">{children}</div>
    </div>
  );
}

function Field({ label, value, mono }: { label: string; value?: string; mono?: boolean }) {
  if (!value) return null;
  return (
    <div className="flex gap-2 text-sm">
      <span className="text-theme-tertiary shrink-0 w-28">{label}</span>
      <span className={`text-theme ${mono ? "font-mono text-xs" : ""} break-words`}>{value}</span>
    </div>
  );
}

/* ---------- Cards ---------- */

function UseCaseCard({ id, uc, onClick }: { id: string; uc: UseCaseRecord; onClick: () => void }) {
  const kpiCount =
    (uc.orchestration?.influencing_kpi_ids?.length ?? 0) +
    (uc.orchestration?.supporting_kpi_ids?.length ?? 0);
  const acCount = uc.orchestration?.action_code_ids?.length ?? 0;
  return (
    <button
      onClick={onClick}
      className="text-left w-full bg-theme rounded-lg border border-theme p-4 hover:border-brand-mint transition-colors cursor-pointer group"
    >
      <div className="flex items-start justify-between gap-2 mb-1.5">
        <div className="min-w-0">
          <code className="text-[10px] font-mono text-theme-tertiary">{id}</code>
          <h3 className="font-medium text-theme text-sm mt-0.5 leading-snug group-hover:text-brand-mint transition-colors">
            {uc.title ?? id}
          </h3>
        </div>
        <ImpactBadge direction={uc.value_driver_model?.impact_direction} />
      </div>
      {uc.domain && <p className="text-xs text-theme-tertiary mb-2">{uc.domain}</p>}
      {uc.orchestration?.strategic_kpi_id && (
        <div className="text-xs mb-2">
          <span className="text-theme-tertiary">North Star: </span>
          <code className="text-brand-mint text-[10px]">{uc.orchestration.strategic_kpi_id}</code>
        </div>
      )}
      <div className="flex gap-1.5 mt-2 flex-wrap">
        <Badge label={`${kpiCount} KPIs`} variant="blue" />
        <Badge label={`${acCount} actions`} variant="purple" />
      </div>
    </button>
  );
}

function KpiCard({ id, kpi, onClick }: { id: string; kpi: KpiRecord; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="text-left w-full bg-theme rounded-lg border border-theme p-4 hover:border-brand-mint transition-colors cursor-pointer group"
    >
      <div className="flex items-start justify-between gap-2 mb-1">
        <div className="min-w-0">
          <code className="text-[10px] font-mono text-brand-mint break-all">{id}</code>
          {kpi.title && (
            <h3 className="font-medium text-theme text-sm mt-0.5 leading-snug group-hover:text-brand-mint transition-colors">
              {kpi.title}
            </h3>
          )}
        </div>
        <div className="flex gap-1 shrink-0">
          <StatusBadge status={kpi.status} />
          <QualityBadge score={kpi.metadata_quality?.completeness_score} />
        </div>
      </div>
      {kpi.business?.purpose && (
        <p className="text-xs text-theme-secondary line-clamp-2 mb-2">{kpi.business.purpose}</p>
      )}
      <div className="flex gap-1 flex-wrap mt-1.5">
        {kpi.kpi_type && <Badge label={kpi.kpi_type} variant="blue" />}
        {kpi.impact_dimension && <Badge label={kpi.impact_dimension} variant="mint" />}
        {(kpi.domain_tag ?? []).slice(0, 2).map((t) => (
          <Badge key={t} label={t} variant="gray" />
        ))}
      </div>
    </button>
  );
}

function ActionCodeCard({ id, ac, onClick }: { id: string; ac: ActionCodeRecord; onClick: () => void }) {
  const name = ac.name ?? (ac.raw as Record<string, unknown>)?.name as string | undefined;
  const trigger = ac.raw as Record<string, unknown> | undefined;
  const triggerWhen = (trigger?.trigger as Record<string, unknown>)?.when as string | undefined;
  return (
    <button
      onClick={onClick}
      className="text-left w-full bg-theme rounded-lg border border-theme p-4 hover:border-brand-mint transition-colors cursor-pointer group"
    >
      <div className="flex items-start justify-between gap-2 mb-1">
        <div className="min-w-0">
          <code className="text-[10px] font-mono text-nagarro-purple-500 dark:text-nagarro-purple-300">{id}</code>
          {name && (
            <h3 className="font-medium text-theme text-sm mt-0.5 leading-snug group-hover:text-brand-mint transition-colors">
              {name}
            </h3>
          )}
        </div>
        <StatusBadge status={ac.status} />
      </div>
      {triggerWhen && (
        <p className="text-xs text-theme-secondary line-clamp-2 italic mb-2">&ldquo;{triggerWhen}&rdquo;</p>
      )}
      <div className="flex gap-1 flex-wrap mt-1.5">
        {ac.owner_domain && <Badge label={ac.owner_domain} variant="blue" />}
        {ac.impact_dimension && <Badge label={ac.impact_dimension} variant="mint" />}
      </div>
    </button>
  );
}

/* ---------- Main Page ---------- */

export default function ExplorerPage() {
  const [registry, setRegistry] = useState<Registry | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<Tab>("use_cases");
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState<{ type: Tab; id: string } | null>(null);

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
            (kpi.title ?? "").toLowerCase().includes(q) ||
            (kpi.business?.purpose ?? "").toLowerCase().includes(q) ||
            (kpi.impact_dimension ?? "").toLowerCase().includes(q)
        )
      );
    }
    if (tab === "action_codes") {
      return Object.fromEntries(
        Object.entries(registry.objects.action_codes).filter(
          ([id, ac]) => {
            const name = ac.name ?? (ac.raw as Record<string, unknown>)?.name as string ?? "";
            return !q ||
              id.toLowerCase().includes(q) ||
              name.toLowerCase().includes(q) ||
              (ac.owner_domain ?? "").toLowerCase().includes(q);
          }
        )
      );
    }
    return {};
  }, [registry, tab, search]);

  const tabs: { id: Tab; label: string; count: number }[] = registry
    ? [
        { id: "use_cases", label: "Use Cases", count: Object.keys(registry.objects.use_cases).length },
        { id: "kpis", label: "KPIs", count: Object.keys(registry.objects.kpis).length },
        { id: "action_codes", label: "Action Codes", count: Object.keys(registry.objects.action_codes).length },
      ]
    : [];

  const selectedData =
    selected && registry
      ? selected.type === "use_cases"
        ? registry.objects.use_cases[selected.id]
        : selected.type === "kpis"
          ? registry.objects.kpis[selected.id]
          : registry.objects.action_codes[selected.id]
      : null;

  if (error) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="max-w-md text-center">
          <h2 className="font-semibold text-theme mb-2">Registry not available</h2>
          <p className="text-sm text-theme-tertiary mb-4">{error}</p>
          <code className="block text-xs bg-theme-tertiary rounded p-3 text-left text-theme-secondary">
            py tooling/ontology/registry_builder.py
          </code>
        </div>
      </div>
    );
  }

  if (!registry) {
    return (
      <div className="h-full flex items-center justify-center text-theme-tertiary">
        <div className="flex items-center gap-2">
          <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          Loading registry...
        </div>
      </div>
    );
  }

  const entries = Object.entries(filtered);

  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* Stat bar */}
      <div className="bg-theme border-b border-theme px-6 py-3 flex gap-4 shrink-0">
        {tabs.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`px-4 py-2 rounded-md transition-colors cursor-pointer text-left
              ${tab === t.id
                ? "bg-brand-mint/10 dark:bg-brand-mint/15"
                : "hover:bg-theme-tertiary"}`}
          >
            <div className={`text-xl font-bold ${tab === t.id ? "text-brand-mint" : "text-theme"}`}>
              {t.count}
            </div>
            <div className="text-xs text-theme-tertiary">{t.label}</div>
          </button>
        ))}
        <div className="ml-auto flex items-center text-xs text-theme-tertiary">
          {new Date(registry.meta.generated_at_utc).toLocaleDateString()}
        </div>
      </div>

      {/* Search */}
      <div className="bg-theme border-b border-theme px-6 py-2 shrink-0">
        <input
          type="search"
          placeholder={`Search ${tab.replace("_", " ")}...`}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full max-w-sm text-sm bg-theme-secondary border border-theme rounded-md px-3 py-1.5 text-theme focus:outline-none focus:ring-1 focus:ring-brand-mint placeholder:text-theme-tertiary"
        />
      </div>

      {/* Cards grid */}
      <div className="flex-1 overflow-y-auto p-6 bg-theme-secondary">
        {entries.length === 0 ? (
          <p className="text-sm text-theme-tertiary text-center mt-16">No results for &ldquo;{search}&rdquo;</p>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
            {entries.map(([id, obj]) =>
              tab === "use_cases" ? (
                <UseCaseCard key={id} id={id} uc={obj as UseCaseRecord} onClick={() => setSelected({ type: tab, id })} />
              ) : tab === "kpis" ? (
                <KpiCard key={id} id={id} kpi={obj as KpiRecord} onClick={() => setSelected({ type: tab, id })} />
              ) : (
                <ActionCodeCard key={id} id={id} ac={obj as ActionCodeRecord} onClick={() => setSelected({ type: tab, id })} />
              )
            )}
          </div>
        )}
      </div>

      {/* Detail Panel */}
      {selected && selectedData && (
        <DetailPanel
          type={selected.type}
          id={selected.id}
          data={selectedData}
          onClose={() => setSelected(null)}
        />
      )}
    </div>
  );
}
