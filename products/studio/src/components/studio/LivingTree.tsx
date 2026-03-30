"use client";
import { useStudio } from "@/store/studio";

function TreeNode({
  label,
  value,
  color = "text-slate-700",
  children,
}: {
  label: string;
  value?: string;
  color?: string;
  children?: React.ReactNode;
}) {
  return (
    <div className="ml-4 border-l border-slate-200 pl-3 py-0.5">
      <div className="flex items-baseline gap-1.5">
        <span className="text-xs text-slate-400 shrink-0">{label}</span>
        {value && <code className={`text-xs font-mono font-medium ${color}`}>{value}</code>}
      </div>
      {children}
    </div>
  );
}

function EmptySlot({ label }: { label: string }) {
  return (
    <div className="ml-4 border-l border-dashed border-slate-200 pl-3 py-0.5">
      <span className="text-xs text-slate-300 italic">{label}</span>
    </div>
  );
}

export function LivingTree() {
  const { draft } = useStudio();
  const orch = draft.orchestration;
  const vdm = draft.value_driver_model;

  return (
    <div className="p-4 overflow-y-auto h-full">
      <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">
        Golden Thread
      </h3>

      {/* Use Case root */}
      <div className="bg-white rounded border border-slate-200 px-3 py-2 mb-1">
        <div className="text-xs text-slate-400">Use Case</div>
        <div className="font-semibold text-slate-900 text-sm">{draft.title || "—"}</div>
        <code className="text-xs text-slate-400">{draft.id}</code>
        {draft.domain && (
          <span className="ml-2 text-xs bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded">
            {draft.domain}
          </span>
        )}
      </div>

      {/* Strategic KPI */}
      <div className="ml-2">
        <div className="text-xs text-slate-400 mb-0.5 flex items-center gap-1">
          <span className="w-2 h-px bg-slate-300 inline-block" />
          North Star KPI (3-second signal)
        </div>
        {orch.strategic_kpi_id ? (
          <div className="bg-blue-50 border border-blue-200 rounded px-3 py-2 mb-1">
            <code className="text-sm font-mono font-semibold text-brand-primary">
              {orch.strategic_kpi_id}
            </code>
            {vdm.impact_direction && (
              <span
                className={`ml-2 text-xs font-medium ${
                  vdm.impact_direction === "maximize" ? "text-green-600" : "text-red-600"
                }`}
              >
                {vdm.impact_direction === "maximize" ? "↑ maximize" : "↓ minimize"}
              </span>
            )}
            {vdm.formula && (
              <div className="text-xs text-blue-500 font-mono mt-1 truncate" title={vdm.formula}>
                {vdm.formula}
              </div>
            )}
          </div>
        ) : (
          <div className="bg-slate-50 border border-dashed border-slate-200 rounded px-3 py-2 mb-1 text-xs text-slate-400 italic">
            No strategic KPI set — edit YAML or ask Chat
          </div>
        )}

        {/* Influencing KPIs */}
        <div className="text-xs text-slate-400 mb-0.5 mt-2 flex items-center gap-1">
          <span className="w-2 h-px bg-slate-300 inline-block" />
          Influencing KPIs (30-second levers)
        </div>
        {orch.influencing_kpi_ids && orch.influencing_kpi_ids.length > 0 ? (
          <div className="space-y-1 ml-2">
            {orch.influencing_kpi_ids.map((kid) => (
              <div
                key={kid}
                className="bg-white border border-slate-200 rounded px-2.5 py-1.5 flex items-center gap-2"
              >
                <span className="text-slate-300">○</span>
                <code className="text-xs font-mono text-slate-700">{kid}</code>
                {vdm.primary_driver === kid && (
                  <span className="ml-auto text-xs bg-yellow-100 text-yellow-700 px-1.5 py-0.5 rounded">
                    primary driver
                  </span>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="ml-2 text-xs text-slate-300 italic">No influencing KPIs</div>
        )}

        {/* Action Codes */}
        <div className="text-xs text-slate-400 mb-0.5 mt-2 flex items-center gap-1">
          <span className="w-2 h-px bg-slate-300 inline-block" />
          Action Codes (300-second prescriptions)
        </div>
        {orch.action_code_ids && orch.action_code_ids.length > 0 ? (
          <div className="space-y-1 ml-2">
            {orch.action_code_ids.map((aid) => (
              <div
                key={aid}
                className="bg-purple-50 border border-purple-200 rounded px-2.5 py-1.5 flex items-center gap-2"
              >
                <span className="text-purple-300">⚡</span>
                <code className="text-xs font-mono text-purple-700 font-medium">{aid}</code>
              </div>
            ))}
          </div>
        ) : (
          <div className="ml-2 text-xs text-slate-300 italic">No action codes</div>
        )}

        {/* Governance */}
        {(draft.governance.owner_role || draft.governance.steward_role) && (
          <>
            <div className="text-xs text-slate-400 mb-0.5 mt-3 flex items-center gap-1">
              <span className="w-2 h-px bg-slate-300 inline-block" />
              Governance
            </div>
            <div className="ml-2 space-y-1">
              {draft.governance.owner_role && (
                <TreeNode label="Business Owner" value={draft.governance.owner_role} color="text-slate-700" />
              )}
              {draft.governance.steward_role && (
                <TreeNode label="Data Steward" value={draft.governance.steward_role} color="text-slate-700" />
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
