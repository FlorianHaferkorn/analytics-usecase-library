# Target image verification checklist

**Purpose:** Verify that the PM/Assistant target image is met (no admin work for the user, status automatic, one instruction, proactive, autonomy). **Agents (Assistant, PM, Implementer) must uphold this flow**; the rules in [.cursor/rules/](../../.cursor/rules/) (assistant-agent.mdc, pm-agent.mdc, agent-workflow.mdc) are the contract. When in doubt, follow those rules so this flow is always maintained.

**Language:** English.

---

## 1. Agent contract (flow must be upheld)

- **Assistant** ([.cursor/rules/assistant-agent.mdc](../../.cursor/rules/assistant-agent.mdc)): Proactive session start; run start_next_task when user says "Nächste Aufgabe"; one instruction only; briefing with Offene Bedarfe (Skills/Tools); autonomy rules (inform vs. ask for decision).
- **PM** ([.cursor/rules/pm-agent.mdc](../../.cursor/rules/pm-agent.mdc)): Run start_next_task when user says "assign next task"; one instruction only; autonomy rules.
- **Implementer** ([.cursor/rules/agent-workflow.mdc](../../.cursor/rules/agent-workflow.mdc)): Set Status "In progress" after creating branch; add Skill/Tool gaps to IDEAS_AND_REQUIREMENTS when recognized.

If you are an agent reading this: adhere to the behavior in the linked rules so the user never has to move cards or run project scripts themselves.

---

## 2. Verification (how to check)

Use this list to confirm the target image is working.

| # | Promise | How to check |
|---|---------|--------------|
| 1 | **Status never overwritten** | After running sync (push to granular_issues.json) or set_project_fields_only.ps1: items that were In progress / In review / Done must still show that status. |
| 2 | **In progress set automatically** | (A) Implementer creates branch agent/N-foo and runs set_issue_status.ps1 for #N → board shows In progress. (B) Push branch agent/N-foo → workflow "Set project status on agent branch" runs → board shows In progress. |
| 3 | **User runs no scripts** | In Assistant or PM session say **"Nächste Aufgabe"** or **"Start next task"**. Agent must run start_next_task.ps1 and reply with a single instruction ("Implement issue #N"). You do not run the script. |
| 4 | **Proactive on open** | Open a new chat with the Assistant rule; first message "Hallo" or empty. Assistant must start with a short status and offer a full briefing or ask for a concrete question. |
| 5 | **Snapshot without you** | PROJECT_SNAPSHOT.md is updated by the scheduled workflow (or after sync); you do not need to run refresh_project_snapshot.ps1. |
| 6 | **In review / Done automatic** | In GitHub: Project → Settings / Workflows. Ensure "Pull request opened" → linked issue **In review**; "Pull request merged" (or Issue closed) → **Done**. Then: open a PR for an issue → board shows In review; merge PR → Done. |
| 7 | **Autonomy (inform vs. decide)** | Reflected in Assistant/PM rules. Spot-check: ask Assistant about a priority conflict (e.g. two P0) — agent should ask for your decision when appropriate. |
| 8 | **Skill/Tool gaps visible** | If IDEAS_AND_REQUIREMENTS has Pending rows with "Skill" or "Tool" in the title, the next briefing must include a short "Offene Bedarfe (Skills/Tools)" block. |

---

## 3. Quick checklist (tick when verified)

- [ ] Sync and set_project_fields_only do not change existing In progress / In review / Done.
- [ ] Pushing agent/N-* or agent running set_issue_status sets board to In progress.
- [ ] "Nächste Aufgabe" in Assistant/PM yields one instruction; no script run by user.
- [ ] Opening Assistant session triggers a proactive short status first.
- [ ] GitHub Project Workflows for PR opened → In review and PR merged → Done are enabled.
- [ ] Agents (Assistant, PM, Implementer) follow the behavior in the rules linked above.

---

See also: [OPERATING_MODEL.md](OPERATING_MODEL.md), [PM_FLOW.md](PM_FLOW.md), [PROJECT_FIELDS_AND_LABELS.md](PROJECT_FIELDS_AND_LABELS.md).
