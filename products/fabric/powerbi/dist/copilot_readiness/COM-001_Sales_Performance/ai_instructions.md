# AI Instructions — COM-001 Sales Performance vs Plan & LY

> Quelle: ALUCA (Adapter über den Meridian-Kern) — core/usecases/core/COM-001_Sales_Performance/UseCase_Bracket.yaml, core/kpi_catalog/kpis/KPI-COM-013.yaml, core/kpi_catalog/kpis/KPI-COM-005.yaml, core/kpi_catalog/kpis/KPI-COM-009.yaml, core/kpi_catalog/kpis/KPI-COM-008.yaml, core/kpi_catalog/kpis/KPI-COM-010.yaml, core/kpi_catalog/kpis/KPI-COM-011.yaml, core/kpi_catalog/kpis/KPI-COM-004.yaml, core/kpi_catalog/kpis/KPI-FIN-011.yaml, core/kpi_catalog/kpis/KPI-COM-006.yaml, core/kpi_catalog/kpis/KPI-COM-007.yaml, core/kpi_catalog/kpis/KPI-COM-001.yaml, core/kpi_catalog/kpis/KPI-COM-002.yaml, core/action_codes/Commercial/C-M2.1.yaml, core/action_codes/Commercial/C-S1.1.yaml, core/action_codes/Commercial/C-S1.2.yaml, core/organization/org_roles.yaml, core/data_contracts/domains/commercial_sales.yaml. Deterministisch generiert (kein LLM).

## Geschäftskontext

COM-001 Sales Performance vs Plan & LY — ALUCA Use Case, Domäne Commercial.
Strategische Ziele:
- Sales Performance vs Plan & LY (Owner: Commercial Controlling Lead): Improving KPI-COM-005 is the primary lever for maximizing KPI-COM-013.
Nordstern-KPI: Gross Margin % (KPI-COM-013).

## Verbindliche Begriffsdefinitionen (Glossar)

Die folgenden Begriffe sind unternehmensweit verbindlich definiert und von den Data Ownern freigegeben:
- **GM%** (Commercial Data Product; freigegeben: Head of Controlling, —): Synonym für Gross Margin % (KPI-COM-013): (Net Sales Amount - COGS Amount) / Net Sales Amount
- **Gross Margin Rate** (Commercial Data Product; freigegeben: Head of Controlling, —): Synonym für Gross Margin % (KPI-COM-013): (Net Sales Amount - COGS Amount) / Net Sales Amount
- **Bruttomarge %** (Commercial Data Product; freigegeben: Head of Controlling, —): Synonym für Gross Margin % (KPI-COM-013): (Net Sales Amount - COGS Amount) / Net Sales Amount

## KPI-Definitionen und Schwellenwerte

- **Gross Margin % (KPI-COM-013)** — Formel: (Net Sales Amount - COGS Amount) / Net Sales Amount. Einheit: %. Richtung: höher ist besser.
  Datenquelle: commercial_sales (Commercial Data Product), Feld `Cost of Goods Sold Amount`; verantwortlich: Head of Controlling.
- **Net Sales Amount (KPI-COM-005)** — Formel: Sum of all invoice line amounts net of VAT and returns. Einheit: EUR. Richtung: —.
  Datenquelle: commercial_sales (Commercial Data Product), Feld `Net Sales Amount`; verantwortlich: Head of Sales.
- **Net Sales % vs Plan (KPI-COM-009)** — Formel: (Net Sales Amount - Plan Sales Amount) / Plan Sales Amount. Einheit: %. Richtung: höher ist besser.
  Alert bei Unterschreitung von -2.0 %.
  Datenquelle: commercial_sales (Commercial Data Product), Feld `Plan Sales Amount`; verantwortlich: Head of Sales Controlling.
- **Delta% Net Sales (KPI-COM-008)** — Formel: (Net Sales - LY) / LY. Einheit: %. Richtung: höher ist besser.
  Datenquelle: commercial_sales (Commercial Data Product), Feld `Net Sales Amount`; verantwortlich: Head of Sales Controlling.
- **Price Effect Amount (KPI-COM-010)** — Formel: (Actual Price - Plan Price) x Actual Quantity. Einheit: EUR. Richtung: höher ist besser.
  Datenquelle: commercial_sales (Commercial Data Product), Feld `Net Sales Amount`; verantwortlich: Head of Sales Controlling.
- **Volume Effect Amount (KPI-COM-011)** — Formel: (Actual Quantity - Plan Quantity) x Plan Price. Einheit: EUR. Richtung: höher ist besser.
  Datenquelle: commercial_sales (Commercial Data Product), Feld `Plan Quantity`; verantwortlich: Head of Sales Controlling.
- **Mix Effect Amount (KPI-COM-004)** — Formel: Total variance - Price Effect - Volume Effect. Einheit: EUR. Richtung: höher ist besser.
  Datenquelle: commercial_sales (Commercial Data Product), Feld `Net Sales Amount`; verantwortlich: Head of Sales Controlling.
- **Cost of Goods Sold Amount (KPI-FIN-011)** — Formel: Sum of invoice line COGS amounts. Einheit: EUR. Richtung: —.
  Datenquelle: commercial_sales (Commercial Data Product), Feld `Cost of Goods Sold Amount`; verantwortlich: Head of Controlling.
- **Plan Net Sales Amount (KPI-COM-006)** — Formel: Sum of approved Plan Sales Amount at invoice-line planning grain. Einheit: EUR. Richtung: —.
  Datenquelle: commercial_sales (Commercial Data Product), Feld `Plan Sales Amount`; verantwortlich: Head of Sales Controlling.
- **Prior-Year Net Sales Amount (KPI-COM-007)** — Formel: Sum of Net Sales Amount for the corresponding prior-year reporting period. Einheit: EUR. Richtung: —.
  Datenquelle: commercial_sales (Commercial Data Product), Feld `Last Year Sales Amount`; verantwortlich: Head of Sales Controlling.
- **List Price Amount (KPI-COM-001)** — Formel: Sum of list price amount at invoice line grain. Einheit: EUR. Richtung: —.
  Datenquelle: commercial_sales (Commercial Data Product), Feld `List Price Amount`; verantwortlich: Head of Sales Controlling.
- **Net Price Amount (KPI-COM-002)** — Formel: Sum of net price amount at invoice line grain. Einheit: EUR. Richtung: —.
  Datenquelle: commercial_sales (Commercial Data Product), Feld `Net Price Amount`; verantwortlich: Head of Sales Controlling.

## Antwortregeln

- Verwende für Begriffe und KPIs ausschließlich die obigen Definitionen; erfinde keine abweichenden Berechnungen oder Synonyme.
- Bewerte KPI-Werte immer relativ zu Ziel und Alert-Schwelle (im Ziel / unter Ziel / Alert), nie absolut ohne Bezug.
- Nenne bei KPI-Antworten Einheit und Bezugszeitraum.
- Wenn eine Frage einen Begriff verwendet, der nicht im Glossar steht, weise auf die fehlende verbindliche Definition hin, statt zu raten.
- Antworte in der Sprache der Frage; Standardsprache ist Englisch.
