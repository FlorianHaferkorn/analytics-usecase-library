# COM-001 Report – Visual Binding Audit

## Semantic Model Reference (Commercial.SemanticModel)

- **Measures (_Measures):** Gross Margin %, Cost of Goods Sold Amount, Net Sales Amount, Net Sales % vs Plan, Delta% Net Sales, Price Effect Amount, Volume Effect Amount, Mix Effect Amount, Action_*_Text
- **Dimensions:** dim_date (Date, Year, Quarter, …), dim_product (ProductName, Category, …), fact_sales (Net Sales Amount, …)

---

## Page: Page_COM001_Overview

| Visual        | Type           | Bindings | Status |
|---------------|----------------|----------|--------|
| KPI_1         | cardVisual     | _Measures.**Gross Margin %** | OK |
| KPI_2         | cardVisual     | _Measures.**Cost of Goods Sold Amount** | OK |
| KPI_3         | cardVisual     | _Measures.**Net Sales Amount** | OK |
| KPI_4         | cardVisual     | _Measures.**Net Sales % vs Plan** | OK |
| Net Sales Amount | lineChart   | **dim_date.Date** (X), **_Measures.Net Sales Amount** (Y) | OK |
| Net Sales % vs Plan, … | clusteredBarChart | **dim_date.Date** (Category), **_Measures.Net Sales % vs Plan**, **Delta% Net Sales**, **Price Effect Amount** | OK |
| Slicer_Date   | slicer         | **dim_date.Date** | OK |
| ActionPanel   | textbox        | (no data) | OK |

---

## Page: Page_COM001_Detail

| Visual        | Type           | Bindings | Status |
|---------------|----------------|----------|--------|
| KPI_1–KPI_4   | cardVisual     | _Measures.**Gross Margin %**, **Cost of Goods Sold Amount**, **Net Sales Amount**, **Net Sales % vs Plan** (wie Overview) | OK (nach Fix) |
| DetailMatrix  | tableEx        | **dim_date.Date**, **dim_product.ProductName**, **_Measures.Net Sales Amount**, **_Measures.Gross Margin %** | OK (nach Fix) |
| Prescriptive  | tableEx        | **dim_date.Date**, **dim_product.ProductName**, **_Measures.Net Sales Amount** | OK (nach Fix) |
| Slicer_Date   | slicer         | dim_date.Date | OK |
| ActionPanel   | textbox        | (no data) | OK |

---

## Durchgeführte Anpassungen

1. **Detail-KPI-Cards:** get_page_config("detail") liefert dieselben card_kpi_ids/card_measure_names wie Overview (aus Bracket/Orchestration); Page Builder befüllt die Karten damit.
2. **DetailMatrix / Prescriptive:** build_table(columns=..., measures=...) mit Defaults: dim_date.Date, dim_product.ProductName, Net Sales Amount (Prescriptive + DetailMatrix), Gross Margin % (nur DetailMatrix).
