## Context
Improve agent/PM workflow: clearer roles, handoffs, and recommended expert usage.

## Scope (pragmatic order)

1. **Reviewer-Rule** (new `.cursor/rules/reviewer-agent.mdc`)
   - Fixed role: review PRs against .cursor/rules and skills; Stage 1 compliance.
   - Checklist + structured output.
   - Document handoff in PM_FLOW and/or ASSISTANT_BRIEFING: "After opening PR: start session with Reviewer rule and say: Review PR #N."

2. **Briefing / Assistant**
   - Assistant output always includes the **concrete rule file** for the recommended expert (e.g. "Start session with `.cursor/rules/fabric-expert.mdc`"), not only "Fabric-Expert".

3. **Router-Rule** (optional)
   - New rule (e.g. `router-agent.mdc`): input = Issue # or description → output = recommended Expert, relevant Skills, short rationale. No code changes; enables clear "Route issue #N" sessions and future handoffs.

## Out of scope (for this issue)
- New tool experts (e.g. Tableau, Looker) — only mentioned in AGENT_SETUP so far.
- Changing start_next_task.ps1 Area→Expert mapping (keep as is).

## Acceptance
- [ ] reviewer-agent.mdc exists with role, checklist, output format
- [ ] PM_FLOW or ASSISTANT_BRIEFING mentions Reviewer handoff after PR
- [ ] Assistant rule or briefing output names the Expert rule file path
- [ ] (Optional) router-agent.mdc exists; doc updated if added
