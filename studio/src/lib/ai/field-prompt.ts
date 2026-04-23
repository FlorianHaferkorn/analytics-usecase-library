export interface FieldContext {
  entityType: 'kpi' | 'bracket' | 'action_code' | 'use_case';
  entityId: string;
  entityName: string;
  fieldName: string;
  fieldLabel: string;
  currentValue: string;
  relatedKpiIds?: string[];
  domainContext?: string;
}

/**
 * Builds a system prompt for AI-assisted field suggestions.
 * This is a pure utility — no React, no 'use client'.
 */
export function buildFieldPrompt(ctx: FieldContext): string {
  const relatedSection =
    ctx.relatedKpiIds && ctx.relatedKpiIds.length > 0
      ? `\nRelated KPI IDs: ${ctx.relatedKpiIds.join(', ')}`
      : '';

  const domainSection = ctx.domainContext
    ? `\nDomain context: ${ctx.domainContext}`
    : '';

  return `You are helping fill out an analytics governance field.
Entity: ${ctx.entityType} "${ctx.entityName}" (${ctx.entityId})
Field: ${ctx.fieldLabel} (${ctx.fieldName})
Current value: "${ctx.currentValue}"${domainSection}${relatedSection}

Suggest 3 concise alternatives for this field. Format as a numbered list:
1. ...
2. ...
3. ...

Keep each suggestion under 2 sentences. Match the analytical, business-oriented tone of the existing documentation.`;
}
