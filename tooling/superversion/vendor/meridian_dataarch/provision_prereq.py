"""provision_prereq — Tag-0 identity/secrets bootstrap + a fail-fast prereq gate.

I-19.6 (ADR-0050): the Tag-0 bounding assumption (capacity · SPN + consent · tenant settings ·
git repo · gateways · Key Vault) is IT/Org, not code — but two pieces *are* emittable and belong
in the kit:

  * **``bootstrap_spn.sh``** — an ``az`` CLI script that creates the Fabric-automation service
    principal, notes the security group the tenant settings authorize, and scaffolds the Key
    Vault + secret. Tenant-specific ids are **VERIFY** placeholders, never invented.
  * **``prereq_check.sh``** — a **fail-fast** gate run *before* Tag-1: it collects every missing
    prerequisite (CLI tools, env/identity, capacity, git remote, KV) and prints one clear list,
    exiting non-zero if anything required is absent — so ``platform.sh`` never starts half-ready.

The Tag-0 **tenant-settings checklist** is not duplicated here — it already lives in
``apply/TENANT_SETUP.md`` (``--emit-apply``); ``_PREREQ.md`` points at it. Honest by construction:
the scripts are runnable but tenant-specific values stay VERIFY/env-driven; full verification needs
a real tenant (the DoD's ``agent`` marker). Rollback = delete the SPN. Emits only; never executes.
"""
from __future__ import annotations

# Prereqs the gate checks. kind: "cmd" (a CLI must be installed) or "env" (a var must be set).
# required=True → its absence fails the gate; required=False → advisory note only.
_PREREQS = [
    {"kind": "cmd", "name": "az", "why": "Azure CLI — SPN + Key-Vault bootstrap", "required": True},
    {"kind": "cmd", "name": "fab", "why": "Fabric CLI — item/workspace ops", "required": True},
    {"kind": "cmd", "name": "terraform", "why": "Landing-Zone (nur bei --emit-terraform)", "required": False},
    # 27.08.2026: von Pflicht auf advisory. Die beiden Variablen gehören dem SPN-Pfad, und der
    # ist einer von zwei dokumentierten Wegen — `provision_fabric` nennt `fab auth login`
    # (Browser) ausdrücklich als den einfachsten für einen Trial. Als Pflichtfeld hätte dieses
    # Gate jeden Trial-Erstlauf gestoppt, bei dem es noch gar keinen SPN gibt. Das ist eine
    # **Abweichung** von der Tag-0-Annahme des Moduldocstrings („SPN + consent"), absichtlich
    # und benannt: die Annahme gilt für die Lieferung im Kundenbetrieb, nicht für den ersten Lauf.
    {"kind": "env", "name": "AZURE_TENANT_ID",
     "why": "Entra Tenant für SPN-Auth — leer heißt: interaktive Anmeldung (fab auth login)", "required": False},
    {"kind": "env", "name": "AZURE_CLIENT_ID",
     "why": "SPN App-Id (nach bootstrap_spn.sh) — leer heißt: interaktive Anmeldung", "required": False},
    # `CAP` zählt genauso: die emittierten Skripte lesen `CAP` (provision_fabric, provision_cicd),
    # `platform.env.example` nennt `CAP`, und `FABRIC_CAPACITY` setzte ausserhalb der eigenen
    # Tests nichts. Gemessen 27.08.2026 — wer die dokumentierte Variable füllte, fiel hier durch.
    {"kind": "env", "name": "FABRIC_CAPACITY", "auch": ("CAP",),
     "why": "zugewiesene Kapazität (oder Trial); CAP zählt genauso", "required": True},
    {"kind": "env", "name": "GIT_REMOTE", "why": "Git-Repo (GitHub/ADO) für das Deployment-Modell", "required": True},
    {"kind": "env", "name": "KEY_VAULT_NAME", "why": "Key Vault für Secrets", "required": False},
]


#: MS empfiehlt das Kontingent 25–50 % ueber dem ermittelten Bedarf zu beantragen. Der Puffer
#: deckt nicht nur das Hochskalieren: die Overage-Grenze zieht 1/24 ihres Werts aus demselben
#: Kontingent, und der Spark-Autoscale-Regler ist ebenfalls dadurch begrenzt.
QUOTA_PUFFER_MIN_PCT = 25
QUOTA_PUFFER_MAX_PCT = 50
#: Overage wird zum dreifachen Pay-as-you-go-Satz abgerechnet. Ab einem Drittel der
#: Tages-CU-Stunden kostet es dasselbe wie die naechstgroessere SKU — MS nennt genau diesen Punkt.
OVERAGE_EMPFEHLUNG_ANTEIL = "ein Drittel"
#: Die 24-Stunden-Grenze wird alle 5 Minuten geprueft. Zwischen zwei Pruefungen laeuft sie weiter.
OVERAGE_PRUEFTAKT_MIN = 5
BESCHAFFUNG_PATH = "prereq/BESCHAFFUNG.md"


def _beschaffung_md() -> str:
    """Return ``BESCHAFFUNG.md`` — die fuenf Entscheidungen vor der ersten Kapazitaet.

    BK-F02 (Region) · BK-F03 (Abrechnungsmodell) · BK-F04 (Kontingent) · BK-F07 (Overage) ·
    BK-K02 (Budgetwarnung). Keine davon ist Code, alle fuenf sind vor Tag 1 faellig, und drei
    von ihnen haengen voneinander ab. Die Antworten kommen aus den Intake-Fragen gleichen
    Namens; hier stehen die Folgen, die Fallen und die Reihenfolge.
    """
    lines = [
        "# Beschaffung — was vor der ersten Kapazität entschieden sein muss (generiert)", "",
        "Fünf Entscheidungen, die kein Emitter treffen kann und die trotzdem vor Tag 1 stehen "
        "müssen. Vier davon sind später nur mit Aufwand zu korrigieren, eine gar nicht ohne "
        "Datenumzug. Die Antworten kommen aus dem Intake-Fragebogen; dieses Blatt hält fest, "
        "was an der jeweiligen Antwort hängt.", "",
        "| # | Entscheidung | Kanon | Intake-Frage | Später änderbar? |",
        "|---|---|---|---|---|",
        "| 1 | Region der Kapazität | `BK-F02` | `capacity_region` | nur per Umzug der Workspaces, "
        "mit Verlusten |",
        "| 2 | Abrechnungsmodell (Reservierung / Pay-as-you-go) | `BK-F03` | `billing_commitment` "
        "| Laufzeit 1 oder 3 Jahre, Rückgabe nur als Tausch |",
        "| 3 | Azure-Kontingent mit Puffer | `BK-F04` | `azure_quota_owner` | ja, Antrag dauert "
        "Minuten — die Freigabe im Haus länger |",
        "| 4 | Capacity Overage / Autoscale-Abrechnung | `BK-F07` | `overage_policy` | ja, "
        "jederzeit umstellbar |",
        "| 5 | Budgetwarnung mit benanntem Empfänger | `BK-K02` | `cost_alert_recipient` | ja |", "",
        "> Alle fünf sind Handgriffe im Azure-Portal beziehungsweise im Fabric-Admin-Portal. "
        "Diese Lieferung führt keinen davon aus. Sie sagt, was zu entscheiden ist, was die "
        "Entscheidung kostet und woran man merkt, dass sie falsch war.", "",

        "## 1. Region der Kapazität (`BK-F02`)", "",
        "Antwort: `________________________________`  (Intake: `capacity_region`)", "",
        "**Abweichung vom Kanonstand, benannt statt geglättet (Belegpflicht Regel 5).** Der "
        "Betriebskanon sagte bis 16.08.2026, die Region sei „nachträglich nur durch Neuaufbau zu "
        "ändern\". Gemessen gegen die MS-Dokumentation am 16.08.2026 ist das zu absolut. Der "
        "dokumentierte Weg lautet: eine neue Kapazität in der Zielregion anlegen und die "
        "Workspaces dorthin verschieben. Kein Neuaufbau des Tenants. Der Preis steht aber fest "
        "und ist hoch genug, um die Entscheidung trotzdem vorher zu treffen:", "",
        "- Elemente, die keine Workspace-Neuzuweisung unterstützen, müssen vorher **entfernt** "
        "werden. Lakehouse- und KQL-Shortcuts gehören dazu; sie werden in der Zielregion neu "
        "angelegt, nicht mitgenommen.",
        "- Semantikmodelle im **Large-Storage-Format** dürfen die Region nicht wechseln. MS ist "
        "hier eindeutig: Berichte darauf laden dann nicht mehr und melden `Cannot load model`. "
        "Der Rückweg ist, das Modell in seine ursprüngliche Region zurückzuholen.",
        "- Quell- und Zielkapazität müssen während des Umzugs **beide aktiv** sein. Wird eine "
        "davon pausiert oder gelöscht, kann der Workspace unvollständig ankommen.", "",
        "Was die Region festlegt:", "",
        "- Die **Heimatregion** des Tenants stammt aus der Rechnungsadresse des Benutzers, der "
        "sich als erster angemeldet hat. Neue Kapazitäten landen standardmäßig dort. Eine andere "
        "Region verlangt **Multi-Geo**.",
        "- Eine Multi-Geo-Kapazität verlagert **nicht alles**. MS: „Choosing a different region "
        "for your capacity doesn't entirely relocate all of your data to that region.\" "
        "Tenant-Metadaten bleiben in der Heimatregion.",
        "- Für die **EU-Datengrenze** müssen Tenant **und** Kapazität in EU/EFTA liegen. Eine "
        "EU-Kapazität unter einem Tenant außerhalb der EU erfüllt sie nicht.", "",
        "**Die Falle, die jede richtige Regionswahl überlebt.** OneLake hat einen globalen "
        "Endpunkt und regionale Endpunkte. Beim globalen (`onelake.dfs.fabric.microsoft.com`) "
        "kann während der Auflösung Verkehr die Region verlassen — MS schreibt das ausdrücklich "
        "hin. Wer Datenresidenz zusagt, verwendet den regionalen Endpunkt:", "",
        "```", "https://<region>-onelake.dfs.fabric.microsoft.com", "```", "",
        "Diese Zeile gehört in jede Verbindungszeichenfolge, die ein externes Werkzeug auf "
        "OneLake ansetzt. Sie steht in keinem Standarddialog.", "",

        "## 2. Abrechnungsmodell (`BK-F03`)", "",
        "Antwort: `________________________________`  (Intake: `billing_commitment`)", "",
        "**Korrektur vom 16.08.2026.** Eine Fabric-Reservierung wird **nicht an eine Kapazität "
        "gebunden**. Gekauft wird eine **CU-Menge für eine Azure-Region**, in Schritten von 1 CU, "
        "über 1 oder 3 Jahre. Der Rabatt wird automatisch auf die passende Nutzung in dieser "
        "Region angewandt und deckt mehrere Kapazitäten zugleich — MS rechnet es an 64 "
        "reservierten CUs vor, die zwei F32 genauso decken wie eine F64. Wer pro Kapazität "
        "fragt, stellt die Frage in der falschen Einheit.", "",
        "| Eigenschaft | Gemessener Stand (MS-Doku, 16.08.2026) |", "|---|---|",
        "| Einheit | CU-Menge je Azure-Region, Schritte von 1 CU |",
        "| Laufzeit | 1 oder 3 Jahre, Zahlung im Voraus oder monatlich |",
        "| Geltungsbereich | Ressourcengruppe, Abonnement, geteilt oder Verwaltungsgruppe — nach "
        "dem Kauf änderbar |",
        "| Nicht gedeckt | **Speicher und Netzwerk**. Beide laufen weiter zum Pay-as-you-go-Satz |",
        "| Anrechnung | stündlich auf tatsächlich verbrauchte CUs. Nicht genutzte Stunden "
        "verfallen und werden nicht übertragen |",
        "| Verlängerung | **nicht automatisch**. Nach Ablauf laufen die Workloads weiter, zum "
        "Pay-as-you-go-Preis |",
        "| Name in der Kostenanalyse | `Dataflows Standard Compute Capacity Usage CU`, Typ "
        "`Purchase`. Ein Filter auf „Fabric\" findet ihn nicht |",
        "| Rechte zum Kauf | Owner oder Reservation Purchaser. Bei EA muss zusätzlich die "
        "Richtlinie **Reserved Instances** eingeschaltet sein |", "",
        "**Die Kopplung zum Pausierplan (`BK-F08`).** Der Abschaltplan spart nur, was über die "
        "reservierte Menge hinaus läuft. Bleiben nach dem Pausieren weniger CUs aktiv als die "
        "Region reserviert hat, verfällt die Differenz Stunde für Stunde. Deshalb wird die "
        "Reservierung auf die Menge gekauft, die **durchläuft**, nicht auf die Summe aller "
        "Stufen. Details in `platform/capacity_schedule.md`.", "",
        "**Der Kontrollpunkt, der das Auseinanderlaufen meldet.** Azure Cost Management kennt "
        "eine Warnung auf die **Auslastung von Commitment-Plänen**: sie meldet, wenn die "
        "Ausnutzung einer Reservierung unter einen Schwellwert fällt. Das ist die einzige "
        "Meldung, die „wir haben reserviert und schalten trotzdem ab\" sichtbar macht, bevor es "
        "auf der Jahresrechnung steht. Sie wird zusammen mit der Budgetwarnung aus Punkt 5 "
        "eingerichtet.", "",
        "Für den gemischten Fall nennt MS eine Faustregel: Reservierung für die Grundlast, "
        "Pay-as-you-go für Spitzen — und wenn die zusätzliche Kapazität an **mehr als vier Tagen "
        "je Woche** gebraucht wird, ist eine zweite Reservierung günstiger als der Aufschlag.", "",

        "## 3. Azure-Kontingent (`BK-F04`)", "",
        "Antwort: `________________________________`  (Intake: `azure_quota_owner`)", "",
        "Das Kontingent begrenzt die maximale CU-Zahl je Kapazität **pro Abonnement**. Es kostet "
        "nichts; abgerechnet werden nur die Kapazitäten selbst.", "",
        f"MS empfiehlt, es **{QUOTA_PUFFER_MIN_PCT}–{QUOTA_PUFFER_MAX_PCT} %** über dem "
        "ermittelten Bedarf zu beantragen. Der Puffer ist nicht nur für das Hochskalieren da, und "
        "das wird regelmäßig übersehen: die Overage-Grenze aus Punkt 4 zieht **1/24 ihres Werts** "
        "aus demselben Kontingent, und der Regler für Spark-Autoscale ist ebenfalls dadurch "
        "begrenzt. Ein knapp bemessenes Kontingent blockiert also nicht nur die größere SKU, "
        "sondern auch das Sicherheitsnetz.", "",
        "**Der Blocker vor dem ersten Handgriff.** Vor der ersten Kapazität — oder wenn das "
        "Kontingent auf 0 steht — muss der Resource Provider `Microsoft.Fabric` im Abonnement "
        "**registriert** sein. Ohne Registrierung ist das Kontingent 0, und keine Fehlermeldung "
        "sagt warum. `prereq_check.sh` prüft das mit.", "",
        "```bash", "az provider show -n Microsoft.Fabric --query registrationState -o tsv",
        "az provider register -n Microsoft.Fabric      # falls 'NotRegistered'", "```", "",
        "| Handlung | Benötigte Rolle |", "|---|---|",
        "| Kontingent ansehen | Contributor (oder eine Rolle, die Contributor einschließt) |",
        "| Kontingent erhöhen | **Quota Request Operator** |", "",
        "**Zur Vorlaufzeit, damit die Schätzung nicht in die falsche Richtung falsch ist.** Die "
        "Azure-Seite entscheidet über einen Kontingentantrag **innerhalb von Minuten** und meldet "
        "das Ergebnis zurück. Die Wochen, die in vielen Häusern für so einen Antrag angesetzt "
        "werden, sind die interne Freigabe, nicht Azure. Wer beides in einen Wert wirft, plant "
        "den falschen Puffer ein. Bei abgelehntem Antrag bleibt der Support-Fall — der dauert "
        "dann tatsächlich.", "",
        "MS rät außerdem zu **mehreren Abonnements**, weil das Kontingent je Abonnement gilt und "
        "für alle Ressourcen darin zusammen.", "",

        "## 4. Capacity Overage und Autoscale-Abrechnung (`BK-F07`)", "",
        "Antwort: `________________________________`  (Intake: `overage_policy`)", "",
        "**Abweichung, benannt statt geglättet (Belegpflicht Regel 5).** Der Kanonpunkt heißt "
        "„Autoscale-Abrechnung und Capacity Overage\", als wären das zwei Schalter derselben "
        "Sache. Gemessen am 16.08.2026 sind es **drei verschiedene Dinge**, und eines davon gibt "
        "es auf der SKU-Familie, die wir ausliefern, gar nicht:", "",
        "| Mechanismus | Verfügbar auf | Stand |", "|---|---|---|",
        "| **Power BI Autoscale** | **nur P-SKUs** | auf F-Kapazitäten nicht vorhanden. Für diese "
        "Lieferung damit gegenstandslos |",
        "| **Capacity Overage** | F-SKUs | **allgemein verfügbar** (Stand 29.09.2026), "
        "E-Mail-Benachrichtigungen dazu Preview. Kauft Drosselung ab, zum dreifachen Satz |",
        "| **Autoscale Billing for Spark** | F2 und größer, **nicht** auf Testkapazität | "
        "allgemein verfügbar seit Juli 2025. Verlagert Spark-Jobs aus der Kapazität heraus |", "",
        "### Capacity Overage", "",
        "Der Mechanismus zahlt Überverbrauch ab, statt zu drosseln — bis zu einer Grenze, die der "
        "Kapazitäts-Admin setzt.", "",
        "**Abweichung vom Stand 16.08.2026, benannt statt geglättet (Belegpflicht Regel 5).** Hier "
        "stand bis 29.09.2026: Preview, ab Werk **aus**, Grenze in Vielfachen von 48 CU. Gelesen "
        "am 29.09.2026 (`enterprise/capacity-overage-overview`, `enterprise/enable-capacity-"
        "overage`): Overage ist allgemein verfügbar und bei **neuen** F-Kapazitäten **ab Werk "
        "an**, mit einer Schwelle von 25 % (Schieberegler in 5-%-Schritten oder absolut in "
        "CU-Stunden). Wer „drosseln\" entscheidet, muss es **beim Anlegen** ausschalten — sonst "
        "hat er zugekauft, ohne es zu wissen.", "",
        "- Abgerechnet wird über einen eigenen Zähler zum **dreifachen** Pay-as-you-go-Satz, und "
        "nur für die CU-Stunden über der SKU. In der Kostenanalyse heißt er "
        "`Capacity Overage Capacity Usage CU`.",
        "- Die Grenze ist ein rollierendes 24-Stunden-Limit in **CU-Stunden**. Der Bauplan trägt "
        "sie je Kapazität als `overage` (`state`, `threshold_cu_hours`), benannt wie die "
        "ARM-Eigenschaft `properties.overage` (API `2026-08-01-preview`).",
        f"- Sie wird alle **{OVERAGE_PRUEFTAKT_MIN} Minuten** ausgewertet. MS schreibt die Folge "
        "selbst hin: „you might exceed your limit\". Die Grenze ist eine Bremse, kein Anschlag.",
        f"- MS empfiehlt, sie unter **{OVERAGE_EMPFEHLUNG_ANTEIL}** der Tages-CU-Stunden zu "
        "halten. Darüber kostet Overage dasselbe wie die nächstgrößere SKU, ohne deren Leistung "
        "zu liefern.",
        "- Die Grenze **verbraucht Kontingent** (1/24 ihres Werts). Ohne freies Kontingent lässt "
        "sie sich nicht setzen.",
        "- Overage erhöht die SKU **nicht**. Es verhindert Drosselung, es beschleunigt nichts. "
        "Für Dauerlast bleibt die SKU-Größe die Antwort.", "",
        "> **Die Falle beim Einschalten im Ernstfall.** Wird Overage *während* eines laufenden "
        "Drosselungsereignisses eingeschaltet, berechnet Fabric den **gesamten aufgelaufenen "
        "Carry-forward** zu diesem Zeitpunkt. Der Schalter ist damit als Notmaßnahme die teuerste "
        "seiner Varianten. Wer ihn will, schaltet ihn in der Ruhe ein.", "",
        "**Für den Regelbetrieb bewertet:** die SKU auf die Dauerlast auslegen und Overage "
        "höchstens als Sicherheitsnetz für seltene Spitzen nutzen, mit gesetzter Grenze unter "
        "einem Drittel der Tages-CU-Stunden. Wer das Budget über die Antwortzeit stellt, schaltet "
        "es beim Anlegen aus und nimmt Drosselung in Kauf. Tabelle je Kapazität, Kontingentbedarf "
        "und Kalkulationszeile: `platform/CAPACITY_RUNBOOK.md`.", "",
        "### Autoscale Billing for Spark", "",
        "Verlagert Spark-Jobs auf serverlose Ressourcen; sie verbrauchen dann **kein** CU der "
        "Kapazität mehr. Abgerechnet wird nur Laufzeit aktiver Jobs (0,5 CU-Stunde), kein "
        "Leerlauf.", "",
        "- **Ein-, Ausschalten oder Verkleinern der Maximalgrenze bricht laufende Spark-Jobs ab.** "
        "Das ist der Punkt, der im Betrieb wehtut, und er steht so in der MS-Doku.",
        "- Es gibt **kein Bursting und keine Glättung** und keinen Rückfall auf die Kapazität. Ist "
        "die Grenze erreicht, werden interaktive Jobs gedrosselt und Batch-Jobs eingereiht.",
        "- Der Regler ist durch das **genehmigte Kontingent** begrenzt — siehe Punkt 3.",
        "- Auf **Testkapazitäten** nicht verfügbar. Wer den Modus in der Testphase erproben will, "
        "braucht dafür bereits eine F-Kapazität.", "",

        "## 5. Budgetwarnung mit benanntem Empfänger (`BK-K02`)", "",
        "Antwort: `________________________________`  (Intake: `cost_alert_recipient`)", "",
        "Fabric rechnet **bereitgestellte** Kapazität ab, nicht Nutzung. Eine vergessene "
        "Testkapazität erzeugt keinen Alarm, keine Fehlermeldung und keinen Eintrag im "
        "Monitoring. Sie steht auf der Rechnung.", "",
        "**Was eine Budgetwarnung tut und was nicht.** Sie benachrichtigt, wenn die Kosten einen "
        "Schwellwert erreichen. Sie stoppt nichts. Wer mehr will, hängt an das Budget eine "
        "**Aktionsgruppe** — für Budgets auf Abonnement- und Ressourcengruppenebene ist das "
        "vorgesehen und kann bis zum Abschalten weiterer Kosten gehen. Ohne Aktionsgruppe ist die "
        "Warnung eine Mail, sonst nichts.", "",
        "| Warnungstyp | Wofür | Empfohlene Schwelle |", "|---|---|---|",
        "| Budgetwarnung (Ist) | tatsächlich aufgelaufene Kosten | 90 %, 100 %, 110 % des Ziels |",
        "| Prognosewarnung | Trend läuft auf Überschreitung zu | 110 % des Ziels |",
        "| Anomaliewarnung | unerwarteter Sprung im Tagesverbrauch | nur auf Abonnementebene "
        "verfügbar |",
        "| Auslastung Commitment-Plan | Reservierung wird nicht ausgenutzt | siehe Punkt 2 |", "",
        "| Rolle | Budgetwarnungen |", "|---|---|",
        "| Owner, Contributor, Cost Management Contributor | lesen und ändern |",
        "| Reader, Cost Management Reader | **nur lesen** |", "",
        "**Ein Unterschied, der beim Anlegen auffällt, nicht davor.** Unter einer Enterprise "
        "Agreement lassen sich Budgets im Portal anlegen. Unter einer Microsoft Customer "
        "Agreement führt der unterstützte Weg über die **Budgets-REST-API**. Wer den Termin für "
        "den Portal-Klick plant und eine MCA hat, plant den falschen Termin.", "",
        "Der Empfänger ist der eigentliche Inhalt dieser Entscheidung. Eine Warnung an ein "
        "unbesetztes Postfach ist teurer als keine, weil sie als erledigt gilt.", "",

        "## Reihenfolge", "",
        "Drei der fünf Punkte hängen voneinander ab. In dieser Folge abarbeiten:", "",
        "```",
        "Region (1)  →  Provider registrieren + Kontingent mit Puffer (3)",
        "                 ├→ SKU wählen  →  Abrechnungsmodell (2)  →  Reservierung kaufen",
        "                 └→ Overage-Grenze / Spark-Regler setzen (4)   [zieht Kontingent]",
        "                                                              ↓",
        "                              Budgetwarnung + Auslastungswarnung (5)",
        "```", "",
        "Die Region steht am Anfang, weil sie die einzige ist, deren Korrektur Daten bewegt. Das "
        "Kontingent steht vor der SKU-Wahl, weil es sie deckelt. Die Budgetwarnung steht am "
        "Ende, weil sie erst dann auf eine bezifferte Erwartung gesetzt werden kann.", "",
    ]
    return "\n".join(lines) + "\n"


def emit_prereq_check_sh() -> str:
    """Return ``prereq_check.sh`` — fail-fast Tag-0 gate that lists every missing prerequisite."""
    lines = [
        "#!/usr/bin/env bash",
        "# Tag-0 Prereq-Gate (ADR-0050 / I-19.6). Generated. Vor Tag 1 (platform.sh) laufen lassen.",
        "# Sammelt ALLE fehlenden Voraussetzungen und meldet eine klare Liste (fail-fast vor dem Setup).",
        "set -uo pipefail",
        "missing=()",
        "advis=()",
        "",
        "need_cmd() {  # need_cmd <tool> <why> <required>",
        '  command -v "$1" >/dev/null 2>&1 && return 0',
        '  if [ "$3" = "1" ]; then missing+=("cmd:$1 — $2"); else advis+=("cmd:$1 — $2"); fi',
        "}",
        "need_env() {  # need_env <VAR [VAR2 …]> <why> <required> — erfuellt, wenn EINE gesetzt ist",
        '  local v label="${1// /|}"',
        '  for v in $1; do [ -n "${!v:-}" ] && return 0; done',
        '  if [ "$3" = "1" ]; then missing+=("env:$label — $2"); else advis+=("env:$label — $2"); fi',
        "}",
        "",
        'echo "=== Tag-0 prereq check ==="',
    ]
    for p in _PREREQS:
        fn = "need_cmd" if p["kind"] == "cmd" else "need_env"
        req = "1" if p["required"] else "0"
        namen = " ".join((p["name"], *p.get("auch", ())))
        lines.append(f'{fn} "{namen}" "{p["why"]}" "{req}"')
    lines += [
        "",
        # BK-F04: ohne registrierten Resource Provider steht das Fabric-Kontingent auf 0 und
        # keine Kapazitaet laesst sich anlegen — ohne dass eine Meldung den Grund nennt.
        # Bewusst dreiwertig: nicht lesbar ist NICHT dasselbe wie nicht registriert. Ein Gate,
        # das beides gleich behandelt, meldet bei jedem nicht angemeldeten Lauf einen Blocker,
        # den es nicht gibt — und wird nach dem dritten Mal ignoriert.
        "check_fabric_provider() {  # BK-F04 — Microsoft.Fabric muss registriert sein",
        '  command -v az >/dev/null 2>&1 || return 0   # az fehlt: meldet bereits need_cmd',
        '  local state',
        '  state="$(az provider show -n Microsoft.Fabric --query registrationState -o tsv '
        '2>/dev/null || true)"',
        '  if [ -z "$state" ]; then',
        '    advis+=("az:Microsoft.Fabric — Registrierung nicht lesbar (nicht angemeldet?). '
        'Vor der ersten Kapazitaet pruefen: az provider show -n Microsoft.Fabric")',
        '  elif [ "$state" != "Registered" ]; then',
        '    missing+=("az:Microsoft.Fabric — Resource Provider steht auf \'$state\'. Ohne '
        'Registrierung ist das Kontingent 0. Fix: az provider register -n Microsoft.Fabric")',
        "  fi",
        "}",
        "check_fabric_provider",
        "",
        # I-21 W1.1 (29.09.2026): die Overage-Schwelle zieht Schwelle/24 CU aus dem Kontingent
        # (Learn enterprise/capacity-overage-overview). Dreiwertig wie oben: nicht lesbar ist
        # nicht dasselbe wie zu knapp. Ohne Schwelle in der Umgebung wird nicht geprueft — und
        # das sagt der Lauf, statt still „OK" zu melden.
        "check_overage_quota() {  # BK-F07 — freies Kontingent >= Schwelle/24",
        '  local schwelle="${OVERAGE_SCHWELLE_CUH:-}"',
        '  if [ -z "$schwelle" ] || [ "$schwelle" = "0" ]; then',
        '    advis+=("quota:Overage — nicht geprueft: OVERAGE_SCHWELLE_CUH leer (Overage aus oder '
        'nicht entschieden, siehe platform/CAPACITY_RUNBOOK.md)")',
        "    return 0",
        "  fi",
        '  command -v az >/dev/null 2>&1 || return 0',
        '  if [ -z "${AZURE_SUBSCRIPTION_ID:-}" ] || [ -z "${FABRIC_REGION:-}" ]; then',
        '    advis+=("quota:Overage — nicht geprueft: AZURE_SUBSCRIPTION_ID und FABRIC_REGION setzen")',
        "    return 0",
        "  fi",
        '  local bedarf=$(( (schwelle + 23) / 24 ))',
        '  local werte',
        '  werte="$(az rest --method get --url "https://management.azure.com/subscriptions/'
        '${AZURE_SUBSCRIPTION_ID}/providers/Microsoft.Fabric/locations/${FABRIC_REGION}/usages'
        '?api-version=2023-11-01" --query "value[?name.value==\'CapacityQuota\'] | [0].[limit, '
        'currentValue]" -o tsv 2>/dev/null || true)"',
        '  if [ -z "$werte" ]; then',
        '    advis+=("quota:Overage — Kontingent nicht lesbar (Rolle Contributor noetig?)")',
        "    return 0",
        "  fi",
        "  local limit aktuell frei",
        '  read -r limit aktuell <<<"$werte"',
        '  frei=$(( ${limit%.*} - ${aktuell%.*} ))',
        '  if [ "$frei" -lt "$bedarf" ]; then',
        '    missing+=("quota:Overage — Schwelle $schwelle CU-h braucht $bedarf CU freies '
        'Kontingent, frei sind $frei (Limit $limit, belegt $aktuell). Kontingent erhoehen oder '
        'Schwelle senken")',
        "  fi",
        "}",
        "check_overage_quota",
        "",]
    lines += [
        "",
        'if [ "${#advis[@]}" -gt 0 ]; then',
        '  echo "optional (advisory) fehlt:"; for a in "${advis[@]}"; do echo "  ⚠ $a"; done',
        "fi",
        'if [ "${#missing[@]}" -gt 0 ]; then',
        '  echo "PREREQ: FAIL — diese Pflicht-Voraussetzungen fehlen (vor Tag 1 erfüllen):"',
        '  for m in "${missing[@]}"; do echo "  ✗ $m"; done',
        "  exit 1",
        "fi",
        'echo "PREREQ: OK — Tag-0-Voraussetzungen erfüllt"',
    ]
    return "\n".join(lines) + "\n"


def emit_bootstrap_spn_sh() -> str:
    """Return ``bootstrap_spn.sh`` — az CLI SPN + Key-Vault scaffold (VERIFY tenant-specific ids)."""
    return "\n".join([
        "#!/usr/bin/env bash",
        "# Tag-0 SPN + Key-Vault Bootstrap (ADR-0050 / I-19.6). Generated; review before running.",
        "# Legt den Fabric-Automation-Service-Principal an + scaffoldet den Key Vault. az login vorausgesetzt.",
        "# Tenant-spezifische Werte sind VERIFY-Platzhalter — nie erfunden. Rollback: SPN + KV löschen.",
        "set -euo pipefail",
        'APP_NAME="${APP_NAME:-<customer>-fabric-sp}"',
        'KEY_VAULT_NAME="${KEY_VAULT_NAME:-<customer>-kv}"',
        'RESOURCE_GROUP="${RESOURCE_GROUP:-<resource-group>}"',
        "",
        "# 1. Service Principal für Fabric-Automation (Entra App + SP).",
        'echo "creating SPN $APP_NAME"',
        'az ad sp create-for-rbac --name "$APP_NAME" --skip-assignment   # VERIFY: notiere appId/tenant/secret',
        "#   → appId  = AZURE_CLIENT_ID   (in prereq_check.sh / CI-Secrets exportieren)",
        "#   → tenant = AZURE_TENANT_ID",
        "#   → password = client secret → in den Key Vault (unten), NICHT ins Repo",
        "",
        "# 2. SPN in die Sicherheitsgruppe, die die Tenant-Settings autorisieren.",
        "#    Welche Settings: apply/TENANT_SETUP.md (--emit-apply). SP braucht dort Setting #1/#2.",
        '#   az ad group member add --group "<fabric-automation-sg>" --member-id "<sp-object-id>"   # VERIFY',
        "",
        "# 3. Key Vault + Secret (SPN-Secret raus aus dem Repo).",
        '#   az keyvault create --name "$KEY_VAULT_NAME" --resource-group "$RESOURCE_GROUP"          # VERIFY',
        '#   az keyvault secret set --vault-name "$KEY_VAULT_NAME" --name fabric-sp-secret --value "<secret>"',
        "",
        'echo "SPN bootstrap complete. Rollback: az ad sp delete --id <appId> ; az keyvault delete --name $KEY_VAULT_NAME"',
    ]) + "\n"


def _prereq_md() -> str:
    req = [p for p in _PREREQS if p["required"]]
    opt = [p for p in _PREREQS if not p["required"]]
    lines = [
        "# Tag-0 Prereqs — Identity/Secrets-Bootstrap + Gate (generiert — ADR-0050 / I-19.6)", "",
        "Die Tag-0-Voraussetzungen sind IT/Org (kein Code) und **vor Tag 1** (`platform.sh`) zu erfüllen. "
        "Zwei emittierbare Helfer:", "",
        "- **`bootstrap_spn.sh`** — legt den Fabric-Automation-SPN an + scaffoldet Key Vault (az CLI; "
        "tenant-spezifische Werte VERIFY).",
        "- **`prereq_check.sh`** — fail-fast: prüft alle Pflicht-Voraussetzungen und meldet eine klare "
        "Fehlliste, bevor das Setup startet. Prüft zusätzlich, ob der Resource Provider "
        "`Microsoft.Fabric` registriert ist (`BK-F04`) — ohne ihn steht das Kontingent auf 0.",
        "- **`BESCHAFFUNG.md`** — die fünf Entscheidungen, die **vor** diesen Skripten fallen "
        "müssen: Region, Abrechnungsmodell, Kontingent, Overage und Budgetwarnung "
        "(`BK-F02` · `BK-F03` · `BK-F04` · `BK-F07` · `BK-K02`). Keine davon ist Code, und die "
        "Region ist die einzige, deren Korrektur später Daten bewegt.", "",
        "## Pflicht (Gate blockt, wenn fehlt)", "| Prereq | Zweck |", "|---|---|",
    ]
    for p in req:
        lines.append(f"| `{p['name']}` ({p['kind']}) | {p['why']} |")
    lines += ["", "## Optional (advisory)", "| Prereq | Zweck |", "|---|---|"]
    for p in opt:
        lines.append(f"| `{p['name']}` ({p['kind']}) | {p['why']} |")
    lines += [
        "", "## Ablauf",
        "```bash",
        "# 0. BESCHAFFUNG.md beantworten — davor gibt es keine Kapazität, gegen die geprüft wird",
        "bash prereq/bootstrap_spn.sh     # einmalig: SPN + KV (Werte in CI-Secrets / KV)",
        "bash prereq/prereq_check.sh      # vor jedem platform.sh: Fail-fast-Gate",
        "```",
        "Die **Tenant-Settings-Checkliste** wird hier nicht dupliziert — sie steht in "
        "`apply/TENANT_SETUP.md` (`--emit-apply`). Rollback: SPN + KV löschen "
        "(`az ad sp delete` / `az keyvault delete`).", "",
        "> Vollständige Verifikation braucht einen echten Tenant (DoD-`agent`): die Skripte sind "
        "runnable, aber az/fab-Calls + Rechte-Prüfung greifen erst am Tenant.", "",
    ]
    return "\n".join(lines) + "\n"


def emit_prereq(stack: str = "fabric") -> dict[str, str]:
    """Return the Tag-0 prereq artifact set (path → content): bootstrap, fail-fast gate, checklist doc.

    ``BESCHAFFUNG.md`` kommt nur beim Fabric-Stack dazu: Kontingent, Reservierung, Overage und
    Multi-Geo sind Azure-/Fabric-Begriffe und haben auf einem anderen Stack keine Entsprechung.
    """
    out = {
        "prereq/bootstrap_spn.sh": emit_bootstrap_spn_sh(),
        "prereq/prereq_check.sh": emit_prereq_check_sh(),
        "prereq/_PREREQ.md": _prereq_md(),
    }
    if stack == "fabric":
        out[BESCHAFFUNG_PATH] = _beschaffung_md()
    return out
