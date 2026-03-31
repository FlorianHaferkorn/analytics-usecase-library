/**
 * Decision Spine type — hand-authored.
 *
 * No JSON Schema exists for decision spines yet, so this is not auto-generated.
 * Based on observed YAML structure in core/action_codes/decision_spines/.
 */

export interface DecisionSpine {
  schema_version: string;
  id: string;
  name: string;
  owner_domains: string[];
  impact_dimension: string;
  purpose: {
    intent: string;
  };
  decision_context: {
    decision_type: string;
    primary_question: string;
    decision_owner_roles: string[];
  };
  decision_tradeoffs: {
    improves: string[];
    risks: string[];
  };
  when_not_to_act: {
    conditions: Array<{
      description: string;
      signal: string;
    }>;
  };
  escalation_logic: {
    principle: string;
    escalation_path: Array<{
      level: 'EarlyWarning' | 'RequiredIntervention' | 'PrescriptiveExecution';
      action: string;
    }>;
  };
  decision_confidence: {
    level: string;
    rationale: string[];
  };
  governance: {
    ownership: {
      accountable_role: string;
      consulted_roles: string[];
    };
    change_policy: string[];
  };
  quality_rules: string[];
}
