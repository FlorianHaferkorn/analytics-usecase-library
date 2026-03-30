"use client";
import { useStudio } from "@/store/studio";

function TreeNode({
  label,
  value,
  children,
}: {
  label: string;
  value?: string;
  children?: React.ReactNode;
}) {
  return (
    <div className="ml-4 border-l border-theme pl-3 py-0.5">
      <div className="flex items-baseline gap-1.5">
        <span className="text-xs text-theme-tertiary shrink-0">{label}</span>
        {value && <code className="text-xs font-mono font-medium text-theme-secondary">{value}</code>}
      </div>
      {children}
    </div>
  );
}

export function LivingTree() {
  const { draft } = useStudio();
  const orch = draft.orchestration;
  const vdm = draft.value_driver_model;

  return (
    <div className="p-4 overflow-y-auto h-full">
      <h3 className="text-xs font-semibold text-theme-tertiary uppercase tracking-wider mb-3">
        Golden Thread
      </h3>

      {/* Use Case root */}
      <div className="bg-theme rounded border border-theme px-3 py-2 mb-1">
        <div className="text-xs text-theme-tertiary">Use Case</div>
        <div className="font-semibold text-theme text-sm">{draft.title || "\u2014"}</div>
        <code className="text-xs text-theme-tertiary">{draft.id}</code>
        {draft.domain && (
          <span className="ml-2 text-xs bg-theme-tertiary text-theme-secondary px-1.5 py-0.5 rounded">
            {draft.domain}
          </span>
        )}
      </div>

      {/* Strategic KPI */}
      <div className="ml-2">
        <div className="text-xs text-theme-tertiary mb-0.5 flex items-center gap-1">
          <span className="w-2 h-px bg-theme-tertiary inline-block" />
          North Star KPI (3-second signal)
        </div>
        {orch.strategic_kpi_id ? (
          <div className="bg-brand-mint/10 dark:bg-brand-mint/5 border border-brand-mint/30 rounded px-3 py-2 mb-1">
            <code className="text-sm font-mono font-semibold text-brand-mint">
              {orch.strategic_kpi_id}
            </code>
            {vdm.impact_direction && (
              <span
                className={`ml-2 text-xs font-medium ${
                  vdm.impact_direction === "maximize" ? "text-signal-positive" : "text-signal-negative"
                }`}
              >
                {vdm.impact_direction === "maximize" ? "maximize" : "minimize"}
              </span>
            )}
            {vdm.formula && (
              <div className="text-xs text-brand-mint/70 font-mono mt-1 truncate" title={vdm.formula}>
                {vdm.formula}
              </div>
            )}
          </div>
        ) : (
          <div className="bg-theme-tertiary border border-dashed border-theme rounded px-3 py-2 mb-1 text-xs text-theme-tertiary italic">
            No strategic KPI set
          </div>
        )}

        {/* Influencing KPIs */}
        <div className="text-xs text-theme-tertiary mb-0.5 mt-2 flex items-center gap-1">
          <span className="w-2 h-px bg-theme-tertiary inline-block" />
          Influencing KPIs (30-second levers)
        </div>
        {orch.influencing_kpi_ids && orch.influencing_kpi_ids.length > 0 ? (
          <div className="space-y-1 ml-2">
            {orch.influencing_kpi_ids.map((kid) => (
              <div
                key={kid}
                className="bg-theme border border-theme rounded px-2.5 py-1.5 flex items-center gap-2"
              >
                <span className="text-theme-tertiary text-xs">&#9675;</span>
                <code className="text-xs font-mono text-theme-secondary">{kid}</code>
                {vdm.primary_driver === kid && (
                  <span className="ml-auto text-[10px] bg-nagarro-yellow-100 text-nagarro-yellow-700 dark:bg-nagarro-yellow-700/20 dark:text-nagarro-yellow-300 px-1.5 py-0.5 rounded">
                    primary driver
                  </span>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="ml-2 text-xs text-theme-tertiary italic">No influencing KPIs</div>
        )}

        {/* Action Codes */}
        <div className="text-xs text-theme-tertiary mb-0.5 mt-2 flex items-center gap-1">
          <span className="w-2 h-px bg-theme-tertiary inline-block" />
          Action Codes (300-second prescriptions)
        </div>
        {orch.action_code_ids && orch.action_code_ids.length > 0 ? (
          <div className="space-y-1 ml-2">
            {orch.action_code_ids.map((aid) => (
              <div
                key={aid}
                className="bg-nagarro-purple-300/10 dark:bg-nagarro-purple-900/20 border border-nagarro-purple-300/30 dark:border-nagarro-purple-700/30 rounded px-2.5 py-1.5 flex items-center gap-2"
              >
                <span className="text-nagarro-purple-500 dark:text-nagarro-purple-300 text-xs">&#9889;</span>
                <code className="text-xs font-mono text-nagarro-purple-700 dark:text-nagarro-purple-300 font-medium">{aid}</code>
              </div>
            ))}
          </div>
        ) : (
          <div className="ml-2 text-xs text-theme-tertiary italic">No action codes</div>
        )}

        {/* Governance */}
        {(draft.governance.owner_role || draft.governance.steward_role) && (
          <>
            <div className="text-xs text-theme-tertiary mb-0.5 mt-3 flex items-center gap-1">
              <span className="w-2 h-px bg-theme-tertiary inline-block" />
              Governance
            </div>
            <div className="ml-2 space-y-1">
              {draft.governance.owner_role && (
                <TreeNode label="Business Owner" value={draft.governance.owner_role} />
              )}
              {draft.governance.steward_role && (
                <TreeNode label="Data Steward" value={draft.governance.steward_role} />
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
