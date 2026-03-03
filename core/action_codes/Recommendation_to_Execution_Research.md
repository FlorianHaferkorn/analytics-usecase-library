# Action Codes: Von Empfehlung zu Execution (Recherche)

Kurze Zusammenfassung der Recherche zu der Frage: **Soll man Action Codes zuerst nur als informative Empfehlung umsetzen und die API-Anbindung (Execution in anderen Systemen) erst in einem zweiten Schritt ergänzen – oder von Anfang an beides?**

---

## 1. Etablierte Muster: Human-in-the-Loop

Wenn Analytics- oder BI-Empfehlungen am Ende **Aktionen in anderen Systemen** auslösen (API, Webhook, Workflow), ist das etablierte Muster **nicht** „Empfehlung → sofort API-Call“, sondern:

1. **Exception Detection** – System erkennt, dass eine Entscheidung nötig ist  
2. **Handoff** – Empfehlung wird mit vollem Kontext an Menschen übergeben  
3. **Intervention** – Mensch prüft, genehmigt oder korrigiert  
4. **Resolution** – System führt die **genehmigte** Entscheidung aus (API/Execution)  
5. **Feedback** – Ergebnis und ggf. Overrides fließen zurück (Audit, Lernschleife)

Quellen: Moxo (Human-in-the-Loop Lifecycle), Balto, Microsoft Agent Framework (Human-in-the-Loop), SailPoint/Claw (Approval Gates vor Execution).

**Kern:** Für folgenreiche Entscheidungen bleibt der Mensch verantwortlich; die Automation führt aus, was freigegeben wurde. Direkter Sprung von „Empfehlung anzeigen“ zu „API ausführen“ ohne Freigabe wird in Enterprise- und Governance-Kontexten als riskant beschrieben.

---

## 2. Staged Autonomy / Phased Rollout

Für den Weg von „passivem BI“ zu „actionable“ Systemen mit Execution wird explizit ein **stufenweises Vorgehen** empfohlen:

- **Stufe 1 – Autonomously Alerting:** Proaktive Erkennung + Kontext + Empfehlung **ohne** Execution. Nutzer sehen, was empfohlen wird, und können manuell handeln.  
- **Stufe 2 – Autonomously Decisioning:** System trifft Vorschläge; **Human Review** wo nötig; danach Execution.  
- **Stufe 3 – Autonomously Actioning:** Vollautomatische Execution nur für klar definierte, low-risk Fälle unter Guardrails und Audit.

Quelle: OpsVeda (Agentic AI You Can Trust), AWS/Well-Architected (staggered deployment).

**Für Action Codes:**  
- **Phase 1:** Action Codes nur **informativ** (Panel, Zeilen-Spalte, Narrative) – keine API-Anbindung. Zweck: Logik validieren, Vertrauen aufbauen, Akzeptanz prüfen.  
- **Phase 2:** Execution Layer (z. B. `execution_bridge` im YAML) hinzufügen – aber nur mit **expliziter Freigabe** (z. B. „Empfehlung anzeigen“ + Button „Aktion ausführen“ → dann Webhook/API). Human-in-the-Loop bleibt zentral.  
- **Phase 3 (optional):** Für einzelne, gut abgegrenzte Action Codes und nur bei hoher Reife: automatische Execution mit Policy-as-Code und Audit (Approval Gates, Step-up Approvals).

---

## 3. Closed-Loop Analytics – mit und ohne Mensch

„Closed Loop“ bedeutet oft: **Erkennen → Entscheiden → Ausführen → Messen**. Die Frage ist, wo der Mensch steht:

- **Mit Mensch im Loop (empfohlen für Entscheidungen):**  
  Erkennen → Empfehlung anzeigen → Mensch genehmigt/ändert → Ausführen (API) → Ergebnis messen.  
  Quelle: Ensemble AI (Blog), Kelvin (Recommendation Objects mit Approval), Mastra (Human-in-the-Loop).

- **Ohne Mensch (nur für low-risk, hochautomatisierbare Fälle):**  
  Erkennen → automatische Entscheidung → API-Aufruf.  
  Typisch: sehr klare Regeln, geringe Konsequenz bei Fehlern, starke Guardrails.

**Fazit:** Für Action Codes, die echte Steuerungsentscheidungen abbilden (Preis, Rabatt, Bestellung, Eskalation), ist der **zweigeteilte Ansatz** konsistent mit der Literatur: erst informative Empfehlung, dann Execution mit Freigabe.

---

## 4. Governance und Audit bei API-Execution

Wenn BI/Analytics **externe Systeme per API** auslöst, wird empfohlen:

- **Keine direkte Verbindung** „Report → API“, sondern **dazwischen** eine Governance-Schicht: Approval Gate, Event Trigger mit Freigabe, oder zentrale Pipeline (z. B. Orchestrator), die Aufrufe protokolliert und optional genehmigungspflichtig macht.  
- **Audit:** Wer hat welche Empfehlung wann genehmigt/abgelehnt, welche Payload wurde an welchen Endpoint gesendet (z. B. Claw EA, SailPoint).  
- **Approval vor Execution:** Besonders bei hohem Risiko – explizite Approve/Deny-Entscheidung, festgehalten mit Identität und Zeitstempel.

Quellen: SailPoint (Dynamic Approval), Claw EA (Step-up approvals), Orchestra (API-triggered pipelines mit Parametern).

**Implikation für Action Codes:** Das `execution_bridge` im YAML (Webhook/API) sollte so designed werden, dass es **nicht** „von Power BI direkt ohne Freigabe“ aufgerufen wird, sondern über einen Dienst/Gate, der Freigabe und Audit unterstützt. Phase 1 (nur Anzeige) umgeht diese Anforderung zunächst vollständig.

---

## 5. Vertrauen und Adoption

Untersuchungen zu Trust in AI und Automation zeigen:

- Nutzer akzeptieren Automation eher, wenn sie **verstehen**, was empfohlen wird und **Kontrolle** behalten (z. B. Empfehlung anzeigen, dann „Execute“ bestätigen).  
- Ein „Show first, execute later“-Muster erhöht die Bereitschaft, das System später auch autonom handeln zu lassen („Paradox of control“ – wer stoppen kann, vertraut eher).  
- Empfehlungen zuerst nur anzuzeigen, reduziert Risiko und erlaubt Kalibrierung: Stimmen die Empfehlungen mit der Erwartung der Fachseite überein, bevor überhaupt Execution möglich ist?

Quellen: Point11 (UX patterns for trust), Medium (Calibrated Trust), OpsVeda (Guardrails, Human-in-the-Loop).

---

## 6. Empfehlung für das Framework

**Ja, zweigeteilt umsetzen:**

1. **Erste Stufe (informative Empfehlung)**  
   - Action Codes erscheinen **nur** als Information: im Action Panel, als Zeilen-Spalte in der Detail-Matrix, ggf. Smart Narrative für Kontext.  
   - Kein Aufruf von `execution_bridge`-Endpoints aus dem Report heraus.  
   - Ziel: Logik und Darstellung validieren, Ownership und Akzeptanz sichern, keine ungewollten Side-Effects in anderen Systemen.

2. **Zweite Stufe (Execution über API mit Freigabe)**  
   - `execution_bridge` (Webhook/API) wird genutzt – aber **nur** nach expliziter Nutzeraktion (z. B. „Aktion ausführen“ pro Zeile oder pro Empfehlung).  
   - Idealerweise über eine **zentrale Komponente** (z. B. Backend/Orchestrator), die:  
     - Payload aus Action Code + Kontext baut,  
     - optional Approval-Gates unterstützt,  
     - Aufruf und Ergebnis auditierbar protokolliert.  
   - Power BI/Report bleibt dann „Empfehlung anzeigen + Freigabe-Signal“, die eigentliche API-Execution liegt außerhalb.

3. **Optionale dritte Stufe**  
   - Für wenige, klar definierte und low-risk Action Codes: automatische Execution unter Guardrails (z. B. nur bei hoher Konfidenz, nur bestimmte Aktionstypen), weiterhin mit Audit und Rollback-Optionen.

Diese Reihenfolge entspricht dem in der Recherche gefundenen Muster: **erst Empfehlung sichtbar und vertrauenswürdig machen, dann Execution mit Human-in-the-Loop einführen, danach optional selektiv automatisieren.**

---

## Referenzen (Auswahl)

- Moxo: The complete human-in-the-loop automation lifecycle (6 stages)  
- Balto: What Is Human-in-the-Loop Automation?  
- Microsoft Learn: Human-in-the-Loop with AG-UI  
- OpsVeda: Agentic AI You Can Trust – Guardrails, Human-in-the-Loop, Staged Autonomy  
- Ensemble AI: Real Time Closed Loop Analytics  
- Kelvin: Recommendation messages, produce recommendations  
- Mastra: Human-in-the-Loop – Where to Put Approval  
- Claw EA: Step-up approvals (human-in-the-loop) for Agents  
- GoodData: Automation Intelligence, Building Automation Intelligence  
- Point11: The UX patterns that make people trust AI agents  
- SailPoint: Access Request Dynamic Approval (event triggers)  
- AWS Well-Architected: Staggered deployment and release strategies  
