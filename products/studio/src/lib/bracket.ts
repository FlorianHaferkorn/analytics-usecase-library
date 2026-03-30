import yaml from "js-yaml";
import type { UseCaseDraft, ValidationResult } from "@/types/bracket";

export const EMPTY_DRAFT: UseCaseDraft = {
  schema_version: "2.0",
  id: "NEW-001",
  title: "New Use Case",
  domain: "Commercial",
  governance: { owner_role: "", steward_role: "" },
  orchestration: {
    strategic_kpi_id: "",
    influencing_kpi_ids: [],
    action_code_ids: [],
    supporting_kpi_ids: [],
  },
  value_driver_model: {
    formula: "",
    impact_direction: "maximize",
    primary_driver: "",
    impact_logic: "",
  },
  ux_layout_rules: {
    report_structure: "2-Page-Lead",
    page_1_summary: {
      title: "Overview",
      page_type: "T1_Strategic_Overview",
      template_id: "pulse",
      component_3s: { kpi_id: "", visual_type: "kpi_card" },
      component_30s: [],
    },
    page_2_execution: {
      title: "Execution",
      page_type: "T2_Tactical_Variance",
      template_id: "action_matrix",
      component_300s: {
        evidence_grain: "entity_month",
        evidence_columns: [],
        action_panel: true,
        payload_mode: "full",
      },
    },
  },
  documentation: { business_factsheet: "./Business_Factsheet.md" },
};

export function draftToYaml(draft: UseCaseDraft): string {
  return yaml.dump(draft, { lineWidth: 120, noRefs: true, quotingType: '"' });
}

export function yamlToDraft(text: string): UseCaseDraft {
  const parsed = yaml.load(text);
  if (!parsed || typeof parsed !== "object") throw new Error("Invalid YAML — must be a mapping");
  return parsed as UseCaseDraft;
}

export function validateDraft(draft: UseCaseDraft): ValidationResult {
  const errors: string[] = [];
  const warnings: string[] = [];

  if (!draft.id || draft.id === "NEW-001") warnings.push("Set a proper use case ID (e.g. COM-001)");
  if (!draft.title) errors.push("title is required");
  if (!draft.domain) errors.push("domain is required");
  if (!draft.governance?.owner_role) errors.push("governance.owner_role is required");
  if (!draft.governance?.steward_role) errors.push("governance.steward_role is required");
  if (!draft.orchestration?.strategic_kpi_id) errors.push("orchestration.strategic_kpi_id is required");
  if (!draft.orchestration?.influencing_kpi_ids?.length)
    warnings.push("No influencing_kpi_ids — add at least one lever KPI");
  if (!draft.orchestration?.action_code_ids?.length)
    warnings.push("No action_code_ids — add at least one action code");
  if (!draft.value_driver_model?.formula) warnings.push("value_driver_model.formula is empty");
  if (!["maximize", "minimize"].includes(draft.value_driver_model?.impact_direction ?? ""))
    errors.push('impact_direction must be "maximize" or "minimize"');

  return { valid: errors.length === 0, errors, warnings };
}

export function exportPath(draft: UseCaseDraft): string {
  const slug = draft.title.replace(/[^a-zA-Z0-9]+/g, "_").replace(/^_|_$/g, "");
  return `core/usecases/core/${draft.id}_${slug}/UseCase_Bracket.yaml`;
}
