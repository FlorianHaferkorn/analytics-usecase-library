# ADR 0009 — Wirkungs-Loop (Decision Intelligence): Action → KPI-Snapshot-Delta → Attribution

- **Status:** Accepted (I-8.2 implementiert das `before_after`-Tracking deterministisch — `tooling/superversion/eval/wirkung.py`; `diff_in_diff`/`holdout` brauchen ein Kontroll-Segment = geplant; I-8.3 Refinement-Trigger implementiert). **Maintainer-Ratifikation (E-5, I-10.5):** 2026-07-08 durch den Repo-Maintainer (haferkorn.florian@gmail.com) — korrigiert einen früheren Agenten-Commit, der den Status eigenmächtig als „ratifiziert-by-implementation" auf Accepted gesetzt hatte, ohne dass eine echte Maintainer-Freigabe stattgefunden hatte. Diese Zeile ist der Beleg für die tatsächliche Freigabe.
- **Date:** 2026-06-25
- **Scope:** Das **Modell + die Verträge** für den Wirkungs-Loop (I-8): wie eine ausgelöste Action gegen die spätere KPI-Bewegung gemessen und ehrlich attribuiert wird, und wie die Wirkung als *reviewbarer* Refinement-Vorschlag in die Ontologie zurückfließt. **Kein Code** — Discovery. Implementierung folgt in I-8.2 (Effekt-Tracking) / I-8.3 (Ontologie-Feedback).
- **Supersedes:** —
- **Related:** [`0005…`](0005-superversion-home-and-meridian-vendoring.md), [`0007…`](0007-studio-generate-docks-onto-superversion-core.md) (Freigabe-Schleuse als Gate), [`0008-ai-orchestration-routing-tokens-tracking-roi-config.md`](0008-ai-orchestration-routing-tokens-tracking-roi-config.md) (Attributions-Methoden-Enum, Ehrlichkeits-Regeln), [`../../../UMSETZUNGSPLAN_SUPERVERSION.md`](../../plans/UMSETZUNGSPLAN_SUPERVERSION.md) (I-8), `core/action_codes/`, `tooling/superversion/eval/`

---

## Context

**Wette (I-8):** Eine ausgelöste Action wird gegen die spätere KPI-Bewegung gemessen; die
Ontologie lernt, welche Entscheidung wirkte. Das baut **heute niemand** im Wettbewerb
(Meridian-DI = alert-only, AIS = advisory Level-1) — es ist der Schritt von „Insight" zu
„Decision Intelligence" (Z3).

Das ist Neuland, aber die **Eingänge existieren im Repo bereits** (deshalb ein Modell-ADR
und keine grüne-Wiese-Erfindung):

- **Action-Codes deklarieren ihren Wirkungsanspruch:** `core/action_codes/*.yaml` tragen
  `kpis.{trigger_kpis, guardrail_kpis, outcome_kpis}`, `impact_valuation.metric_kpi_id` und
  `impact.metric_kpi_id` — also *welche* KPI sich durch die Action bewegen soll.
- **KPI-Snapshots sind reproduzierbar berechenbar:** die Eval-Suite (`eval/refcalc.py`,
  I-4.1/4.2) leitet KPI-Werte deterministisch aus Daten + governter Formel ab; genau die
  Mechanik, die ein „KPI-Stand zu t0/t1" braucht.
- **Attributions-Methoden sind schon benannt:** ADR-0008 `roi.attributionMethod` ∈
  `{before_after, diff_in_diff, holdout}` — derselbe Vokabular-Anker.

Was fehlt, ist das **Loop-Modell**, das diese Teile ehrlich verbindet — ohne Korrelation als
Kausalität zu verkaufen und ohne den governten Core automatisch zu mutieren.

## Decision

**Adoptiere den Wirkungs-Loop als deterministische, ehrliche Pipeline
`ActionEvent → KPI-Snapshot(t0,t1) → Effekt-Delta → AttributionRecord → (geschwellt) Refinement-Vorschlag`,
gebaut nur auf governten Action-Codes + KPI-Definitionen, mit der Ontologie-Rückkopplung als
**reviewbarer Vorschlag** durch die Freigabe-Schleuse — nie als stille Core-Mutation.**

Sechs Festlegungen:

1. **ActionEvent als Anker.** Eine ausgelöste Action ist eine Instanz `{action_code_id, t_triggered,
   scope/segment, ausgelöst-durch (trigger_kpi)}`. Sie **referenziert** einen governten Action-Code
   (Golden Thread) — der Loop definiert keine Action neu.

2. **KPI-Snapshot über governte Definitionen.** Die `outcome_kpis` des Action-Codes werden zu
   **t0 (vor)** und **t1 (nach Wirkungsfenster)** als reproduzierbare Snapshots erfasst — über
   dieselbe governte KPI-Bedeutung/Formel wie die Eval-Suite (`refcalc`-Mechanik). **Fehlt ein
   Snapshot → UNCOMPUTED, nie 0** (wie Value-Gate/ROI). Das Wirkungsfenster ist Action-Code-Daten,
   abgeleitet aus `impact_valuation.success_window`/`impact.expected_range.time_to_effect`
   (O-3, s. u.) — kein neues Feld, kein Code-Sonderfall.

3. **Effekt = Delta auf outcome_kpis, methodisch attribuiert.** `effect = snapshot(t1) − snapshot(t0)`
   je outcome-KPI, attribuiert mit einer **deklarierten Methode** (ADR-0008-Enum):
   `before_after` (schwächster Kausalanspruch, ehrlicher Default), `diff_in_diff` / `holdout`
   (brauchen ein **Kontroll-Segment**). Methode + Annahmen werden **mitgeschrieben**.

4. **AttributionRecord ist eine Assoziation, keine Kausalität.** Je `(ActionEvent, outcome_kpi)`:
   `{delta, method, fenster, confidence/caveats, status: computed|uncomputed}`. Der Record sagt
   **nie** „die Action verursachte X" ohne die Methoden-Annahmen; `before_after` ohne Kontrolle ist
   explizit als nur-zeitliche Koinzidenz markiert (Ehrlichkeit v3, anti-Scheinkausalität).

5. **Feedback = reviewbarer Vorschlag, nie Auto-Mutation.** Ein Attribution-Record, der eine Schwelle
   überschreitet (anhaltende Wirkung / Null-Wirkung / Guardrail-Verletzung), erzeugt einen
   **Refinement-Trigger**: einen *Vorschlag* an die Ontologie (z. B. Action-Code-Schärfung,
   KPI-Target-Revision), der die **Freigabe-Schleuse** (ADR-0007/Approval, Zwei-Personen-Regel)
   durchläuft. Der governte Core mutiert nie automatisch aus einer Korrelation (I-8.3).

6. **Determinismus + Golden Thread.** Gleiche Inputs → gleicher AttributionRecord (testbar, wie die
   Eval-Suite). Der Loop **referenziert** governte Action-Codes + KPIs, definiert nie Bedeutung/Target
   neu, und schreibt nichts in den Core ohne Freigabe.

## Ratifiziert vs. aufgeschoben

- **Ratifiziert (Modell + Verträge):** ActionEvent/Snapshot/Effekt/AttributionRecord/Refinement-Trigger
  als Form; die Honesty-Invarianten (UNCOMPUTED, Assoziation≠Kausalität, kein Auto-Mutate);
  Wiederverwendung des ADR-0008-Methoden-Enums + der Freigabe-Schleuse.
- **Aufgeschoben (Implementierung):** I-8.2 = deterministisches Effekt-Tracking + Speicher (eine
  Tabelle/Artefakt für ActionEvents + AttributionRecords), Snapshot-Quelle konkret verdrahtet;
  I-8.3 = Refinement-Trigger → Approval-Vorschlag. Messgröße: **für 1 Action ist der KPI-Effekt
  nachvollziehbar attribuiert.**
- **Studio-Approval-Verdrahtung — implementiert (2026-07-10).** Festlegung 5 verlangt, dass ein
  Refinement-Vorschlag durch die Freigabe-Schleuse läuft — bis hierhin gab es dafür keine
  Studio-Oberfläche (`AttributionRecord`/`RefinementProposal` hatten null Referenzen unter
  `studio/src`). Geschlossen: `bridge.py attribute <use_case> <action_code_id> --t1 <json>`
  (governte `outcome_kpis`-Auflösung aus der Action-Code-YAML, t0 immer über
  `snapshot_via_refcalc`, t1 als expliziter Caller-Input — ehrlich, solange O-1s
  kundeneigener KPI-Feed nicht existiert) + eine neue `refinement_lifecycle`-Tabelle
  (`pending_review→approved/rejected`, admin-gated Approve wie bei Brackets, audit-logged) +
  ein neuer „Wirkungs-Loop Refinements"-Tab auf `/approvals`
  (`RefinementProposalsPanel`). Bewusst **kein** Umbau des bestehenden
  Bracket-Lifecycle-Systems zu einer polymorphen Approval-Engine — das hätte alle 11
  bestehenden Governance-Dateien angefasst für einen einzigen neuen Item-Typ; stattdessen das
  gleiche Muster (Workflow-Modul, RBAC-Admin-Gate, Audit-Log) parallel repliziert.

## Consequences

**Positiv**
- Schließt die Insight→Decision-Lücke (Z3) auf den schon vorhandenen Primitiven — minimaler Neubau,
  maximale Kohärenz (Action-Codes tragen ihren Wirkungsanspruch bereits selbst).
- Ehrlichkeit ist strukturell: UNCOMPUTED statt 0, Methode + Annahmen mitgeführt, keine Scheinkausalität.
- Kein Governance-Risiko: Wirkung mutiert den Core nie automatisch — sie schlägt vor, Menschen entscheiden.

**Negativ / Kosten**
- `diff_in_diff`/`holdout` brauchen **Kontroll-Segmente**, die heute nicht modelliert sind → ohne sie
  bleibt nur `before_after` (schwacher Kausalanspruch). Ehrlich zu labeln, nicht zu überverkaufen.
- KPI-Snapshots zu t0/t1 brauchen eine reale Datenquelle pro Kunde; ohne sie ist der Loop UNCOMPUTED
  (kein erfundener Effekt) — der Wert entsteht erst mit echten Snapshots.

**Neutral**
- Der Loop ist bewusst **attribution-, nicht kausal-inferenz-vollständig**: keine uplift-/causal-ML-Engine
  in I-8; das bleibt späteres Neuland, falls je nötig.

## Alternatives considered

- **Alert-only (Status quo Wettbewerb).** Verworfen als Endzustand: misst Wirkung nie, lernt nie —
  genau die Lücke, die I-8 schließt.
- **Ontologie automatisch aus Korrelation nachziehen.** Verworfen: verletzt Governance + Golden Thread;
  Korrelation ist nicht Kausalität. Feedback bleibt menschlich-gegated (Festlegung 5).
- **Volle Causal-Inference/Uplift-Engine jetzt.** Aufgeschoben: über das I-8-Ziel hinaus; das ehrliche
  Delta-mit-Methode liefert den Z3-Wert ohne diese Komplexität.
- **Eigene Snapshot-/KPI-Berechnung im Loop.** Verworfen: dupliziert die governte KPI-Bedeutung; der Loop
  nutzt die Eval-/`refcalc`-Mechanik (eine Wahrheit).

## Open decisions (I-10.5 — je entschieden, zwei davon bewusst weiter offen)

Geprüft gegen den heutigen Code-Stand (`tooling/superversion/eval/wirkung.py`,
`eval/refinement.py`) und die governten Action-Code-Felder. Ergebnis: O-3 und O-4 sind
reine interne Engineering-Entscheidungen und lassen sich aus dem Repo heraus treffen; O-1
und O-2 zerfallen je in eine bereits implementierte Fallback-Hälfte und eine Hälfte, die
echten Kundenkontext braucht — dieser Teil bleibt bewusst offen (DoD-Fehlerfall-Klausel:
„Kundenkontext nötig → als bewusst-offen markieren, nicht raten"), statt geraten zu werden.

- **O-1 Snapshot-Quelle — teilentschieden.** Der Referenzdaten-Pfad ist entschieden und
  bereits Default-Implementierung: `snapshot_via_refcalc()` (`eval/wirkung.py`) berechnet
  KPI-Snapshots deterministisch über dieselbe governte `refcalc`-Formel wie die Eval-Suite —
  „eine Wahrheit", keine Duplikation (Festlegung 6 oben). **Bewusst offen:** ein
  kundeneigener KPI-Feed als zweite Snapshot-Quelle — welches System, welche Frische,
  welcher Auth-Mechanismus, ist pro Kunde verschieden und ohne reale Deployment nicht
  generisch entscheidbar (s. Consequences: „KPI-Snapshots... brauchen eine reale
  Datenquelle pro Kunde").
- **O-2 Kontroll-Segment-Modell — teilentschieden.** Das Fallback-Verhalten ist entschieden
  und bereits implementiert: fehlt ein Kontroll-Snapshot, führt `attribute()` `diff_in_diff`/
  `holdout` als `status: uncomputed` („geplant"), `before_after` bleibt der ehrliche Default
  (`eval/wirkung.py`, getestet in `test_wirkung.py`). **Bewusst offen:** *woher* ein
  Kontroll-Segment für eine konkrete Kundenorganisation kommt (Kontroll-Filialen/-Regionen,
  ein gematchtes Kohorten-Modell, eine randomisierte Holdout-Gruppe) — eine
  Geschäftsmodellierungs-Frage, die von der Betriebsstruktur des jeweiligen Kunden abhängt,
  nicht generisch vorwegnehmbar.
- **O-3 Wirkungsfenster — entschieden: aus bestehenden Action-Code-Feldern ableiten, kein
  neues Feld.** Action-Codes tragen bereits governte, ISO-8601-artige Felder genau für diesen
  Zweck — z. B. `impact_valuation.success_window.duration` und
  `impact.expected_range.time_to_effect` (siehe `core/action_codes/Service/X-S1.1.yaml`).
  Ein neues Feld würde das duplizieren; der Loop liest das Wirkungsfenster aus diesen
  vorhandenen Feldern ab.
- **O-4 Speicher — entschieden: Artefakt/JSON, keine neue SQLite-Struktur, solange die
  Bracket-/Action-Code-Persistenz selbst artefaktbasiert bleibt.** `ActionEvent`/
  `AttributionRecord` sind heute reine `@dataclass(frozen=True)` mit `to_dict()`, ohne
  Persistenz (`eval/wirkung.py`: „store/UI surfacing is I-8.2-followup"); es gibt im gesamten
  `tooling/superversion/`-Baum keine `sqlite3`-Nutzung und damit kein Präzedenzmuster dafür.
  Der Rest des Superversion-Core (Bracket-/KPI-/Action-Code-Katalog) ist durchgängig
  Datei-/Artefakt-basiert (YAML/JSON, versioniert in Git) — eine neue SQLite-DB wäre der
  einzige DB-Layer im gesamten Core und ein Bruch mit diesem Muster ohne belegten Bedarf
  (Abfragevolumen/-muster, die eine relationale DB rechtfertigen, sind nicht ersichtlich).
  Entscheidung: `ActionEvent`/`AttributionRecord`-Historie als append-only JSON-Artefakte
  (ein Datensatz pro Zeile, analog zu bestehenden Snapshot-/Golden-Artefakten), nicht SQLite.
  Tatsächliche Implementierung bleibt außerhalb dieses ADR-Updates (I-10.5 liefert die
  Entscheidung, nicht den Code).

## References

- Intern: `core/action_codes/*.yaml` (`outcome_kpis`, `impact_valuation`, `impact`),
  `tooling/superversion/eval/refcalc.py` + `eval/value_gate.py` (reproduzierbare KPI-Snapshots, UNCOMPUTED-Doktrin),
  [`0008-ai-orchestration-routing-tokens-tracking-roi-config.md`](0008-ai-orchestration-routing-tokens-tracking-roi-config.md) (Attributions-Enum, Ehrlichkeit),
  [`0007-studio-generate-docks-onto-superversion-core.md`](0007-studio-generate-docks-onto-superversion-core.md) (Freigabe-Schleuse als Mutations-Gate),
  `docs/plans/UMSETZUNGSPLAN_SUPERVERSION.md` (I-8).
- Extern (Methoden-Familien, by reference): before/after, difference-in-differences, holdout/control —
  Standard-Attributions-/Quasi-Experiment-Ansätze; live zu vertiefen, falls I-8.2 über `before_after` hinausgeht.
