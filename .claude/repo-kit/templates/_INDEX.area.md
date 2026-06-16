---
last-reviewed: {{YYYY-MM-DD}}
shelf-life-days: 90
---
# {{Bereich}} — Zentraler Anlaufpunkt (_INDEX)

> **Einstieg in die {{Bereich}}-Ebene.** Ein neuer Chat/Agent liest **zuerst diese
> Datei** und navigiert von hier gezielt weiter — **nicht** den ganzen Ordner.
> Jede Zeile trägt Zweck + „lies-wenn". SoT-Disziplin: offene/erledigte Punkte und
> Ableitungsketten leben **hier**, nicht verstreut im Fließtext.

| Feld | Wert |
|---|---|
| Stand | {{YYYY-MM-DD}} |
| Rolle | L0-Navigation des {{Bereich}}-Betriebssystems (Schichten L0–L4) |
| Verlinkt von | `CLAUDE.md` (Pflicht-Erstkontakt für {{Bereich}}-Aufgaben) |

---

## 1. Schichtenmodell (optional — wenn der Bereich geschichtet ist)

```
L0  _INDEX.md ......... Navigation (diese Datei) — einziger Pflicht-Erstkontakt
L1  {{ZIELBILD}} ...... Übergeordnetes Modell / Operating-Model
L2  {{Detail}} ........ Einzeldokumente (Markt / Methodik / Technik …)
L3  {{Delivery}} ...... Workflow / Umsetzung (abgeleitet aus L1)
L4  {{Roadmap}} ....... Meilensteine → Tasks → Definition of Done (aus L1–L3)
```

Ableitungsrichtung ist **immer abwärts**: L4 leitet aus L1–L3 ab, nie umgekehrt.

---

## 2. „Lies-wenn"-Routing (Token-Disziplin — nur das Nötige lesen)

| Deine Aufgabe ist … | Lies (in dieser Reihenfolge) | NICHT nötig |
|---|---|---|
| {{Aufgabe A}} | `{{doc1}}` → `{{doc2}}` | {{Rest}} |
| {{Aufgabe B}} | `{{doc3}}` | {{Rest}} |
| {{Aufgabe C}} | `{{doc4}}` → `{{doc5}}` | — |

Faustregel: **Ein L0 → (ein Detail)-Pfad genügt** für die meisten Aufgaben.

---

## 3. Dokument-Register (jede `*.md` im Bereich MUSS hier stehen — Drift-Gate)

| Doc | Zweck | Lies-wenn |
|---|---|---|
| `{{doc1}}` | {{Zweck}} | {{wann}} |
| `{{doc2}}` | {{Zweck}} | {{wann}} |
<!-- check_index.py erzwingt: jede Datei im Ordner ist hier gelistet. -->

---

## 4. Offene Punkte (Ledger — hier abhaken, NICHT im Fließtext)

| ID | Punkt | Status | Datum |
|---|---|---|---|
| {{S-1}} | {{…}} | offen / **erledigt** | {{YYYY-MM-DD}} |
