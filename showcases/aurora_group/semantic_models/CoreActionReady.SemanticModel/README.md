# CoreActionReady Semantic Model - Aurora Group

## Überblick

Dieses Semantic Model demonstriert die vollständige Implementierung von 4 Commercial Use Cases für die Aurora Group:

- **COM-001**: Sales Performance vs Plan & LY (7 KPIs)
- **COM-002**: Margin & Price Performance (6 KPIs)  
- **COM-003**: Customer Value (8 KPIs)
- **COM-004**: Promotion Effectiveness (5 KPIs)

**Total: 26 KPIs** mit vollständigen DAX-Ausdrücken

## Aurora Group Kontext

- **Regionen**: DACH, Benelux, Nordics, Southern Europe, CEE
- **Länder**: Deutschland, Österreich, Schweiz, Belgien, Niederlande, Luxemburg, Schweden, Dänemark, Norwegen, Finnland, Italien, Spanien, Portugal, Griechenland, Polen, Tschechien, Ungarn, Slowakei
- **Channels**: Retail Stores (~500), E-Commerce, Marketplaces, Wholesale
- **Infrastruktur**: 6 DCs, 40 Cross-Docks, 3 E-Commerce FCs
- **HQ**: Amsterdam

## Struktur

```
CoreActionReady.SemanticModel/
├── definition/
│   ├── model.tmdl                    # Model-Definition
│   ├── relationships.tmdl            # Alle Relationships
│   ├── tables/
│   │   ├── dim_date.tmdl            # ✅ Mit Fiscal Calendar Hierarchy
│   │   ├── dim_org.tmdl             # ✅ Mit Aurora Organization Hierarchy
│   │   ├── dim_product.tmdl         # ✅ Mit Product Hierarchy
│   │   ├── dim_customer.tmdl
│   │   ├── fact_sales.tmdl
│   │   ├── security_user_org.tmdl   # ✅ RLS Security Table
│   │   └── _Measures.tmdl           # ✅ All measures (grouped by display folder)
│   ├── relationships/
│   │   └── security_user_org_dim_org.tmdl  # ✅ RLS Relationship
│   └── roles/
│       └── Aurora Organization Access.tmdl  # ✅ RLS Role
```

## Gold data path (Parameter)

Partition sources use the **M query parameter** `GoldDataPath`, defined in `definition/expressions.tmdl`. All tables use `Folder.Files(GoldDataPath & "/dimensions/...")` or `Folder.Files(GoldDataPath & "/facts/...")`.

- **Default:** The parameter is set to the repo path to `showcases/aurora_group/data/gold` (edit `expressions.tmdl` to change the default).
- **In Power BI Desktop:** Nach dem Öffnen des PBIP: **Transform data** (oder **Datentransformation**) öffnen → **Parameter verwalten** → **GoldDataPath** auf deinen lokalen Pfad setzen (z. B. `C:/YourUser/YourRepo/.../showcases/aurora_group/data/gold`). Danach **Alle aktualisieren** ausführen.
- Beim Klonen des Repos: Entweder `expressions.tmdl` anpassen (Standardwert) oder in Power BI den Parameter einmal setzen.
- **Fehlende Gold-Daten** (dim_queue, dim_issue, fact_cases, fact_wfm, fact_ap, fact_ar, fact_cash, fact_cashflow) einmalig erzeugen: vom Repo-Root `py showcases/aurora_group/data/scripts/generate_missing_gold_xd_finance.py` ausführen. Danach liegen die Ordner unter `data/gold/dimensions/` bzw. `data/gold/facts/` und das Modell lädt ohne Fehler.

## Hierarchies

### 1. Fiscal Calendar (dim_date)
```
Fiscal Year
  └── Fiscal Quarter
      └── Fiscal Month (sorted by MonthNumber)
          └── Date
```

### 2. Aurora Organization (dim_org)
```
Region (DACH, Benelux, Nordics, Southern Europe, CEE)
  └── Country
      └── Channel (Retail Stores, E-Commerce, Marketplaces, Wholesale)
          └── Org Name
```

### 3. Product Hierarchy (dim_product)
```
Category
  └── Sub Category
      └── Brand
          └── Product Name
```

## Row-Level Security (RLS)

### Security Table: security_user_org

Die Tabelle `security_user_org` definiert welche User Zugriff auf welche Organisationen haben:

| UserPrincipalName | OrgKey | Region | Country | Channel |
|-------------------|--------|--------|---------|---------|
| sofia.berger@aurora-group.com | 1 | DACH | Germany | Retail Stores |
| isabella.conti@aurora-group.com | 1 | DACH | Germany | E-Commerce |
| katharina.steiner@aurora-group.com | 100 | DACH | Germany | Retail Stores |
| jeroen.vandijk@aurora-group.com | 200 | Benelux | Netherlands | Retail Stores |
| anneli.virtanen@aurora-group.com | 300 | Nordics | Sweden | Retail Stores |
| marco.santoro@aurora-group.com | 400 | Southern Europe | Italy | Retail Stores |
| petra.kovacs@aurora-group.com | 500 | CEE | Poland | Retail Stores |

### RLS Role: "Aurora Organization Access"

**DAX-Filter auf dim_org:**
```dax
[OrgKey] IN CALCULATETABLE(
    VALUES(security_user_org[OrgKey]),
    security_user_org[UserPrincipalName] = USERPRINCIPALNAME()
)
```

**Relationship:**
- `security_user_org[OrgKey]` → `dim_org[OrgKey]`
- Cross-filtering: Both Directions
- Security filtering: Both Directions

**Wirkung:**
- Filter auf dim_org propagiert automatisch zu fact_sales
- User sehen nur Daten ihrer zugewiesenen Organisationen
- Testbar mit "View as Role" in Power BI Desktop

## Measures

### Display Folders (Use Case IDs)

| Folder | Use Case | Measures | Status |
|--------|----------|----------|--------|
| **COM-001** | COM-001 | 7 KPIs | ✅ Komplett |
| **COM-002** | COM-002 | 6 KPIs | ✅ Komplett |
| **COM-003** | COM-003 | 8 KPIs | ✅ Komplett |
| **COM-004** | COM-004 | 5 KPIs | ✅ Komplett |

### COM-001: Sales Performance (7 Measures)

1. **Net Sales Amount** - `SUM(fact_sales[Net Sales Amount])`
2. **Net Sales % vs Plan** - Delta zu Plan Sales
3. **Delta% Net Sales** - Delta zu Last Year
4. **Gross Margin %** - GM-Rate
5. **Price Effect Amount** - PVM-Bridge Komponente
6. **Volume Effect Amount** - PVM-Bridge Komponente
7. **Mix Effect Amount** - PVM-Bridge Residual

### COM-002: Margin Analysis (6 Measures)

1. **Gross Margin %** - Margin Rate
2. **Gross Margin Amount** - Absolute Margin
3. **Price Realization %** - Net Price / List Price
4. **Mix Effect Amount** - Product/Channel Mix Impact
5. **COGS per Unit** - Unit Cost Monitoring
6. **Gross Margin % vs Plan** - Plan Variance

### COM-003: Customer Value (8 Measures)

1. **CLV** - Customer Lifetime Value (vereinfacht: 3x Gross Margin)
2. **Customer Lifetime Revenue Amount** - Kumulierter Umsatz
3. **Customer Retention %** - Retention-Rate
4. **Churned Customers** - Abgewanderte Kunden
5. **Revenue at Risk Amount** - CLV * Churn Risk (15%)
6. **Active Customers** - DISTINCTCOUNT Kunden
7. **NPS Score** - Net Promoter Score
8. **Complaint Count** - Beschwerden

### COM-004: Promotion Effectiveness (5 Measures)

1. **Promo ROI %** - Incremental GM / Promo Cost
2. **Incremental Sales Amount** - Uplift durch Promotion
3. **GM % During Promo** - Margin-Rate während Promo
4. **Price Realization %** - Discount-Disziplin
5. **Cannibalization %** - Negativer Impact auf Rest-Portfolio

## Data Source

**Synthetic Aurora Data:**
- Path: `C:\Users\florianhaferkorn\VSCode\analytics-usecase-library\showcases\aurora_group\data\gold\`
- Format: Delta Lake (Parquet + _delta_log)
- Volume:
  - fact_sales: 302,439 transactions
  - dim_date: 4,018 dates (2018-2028)
  - dim_org: 534 organizations
  - dim_product: 5,000 products
  - dim_customer: 50,000 customers

## Testing

### 1. Hierarchies testen
- Drill-down in visuals verwenden
- Jahr → Quartal → Monat → Tag (dim_date)
- Region → Land → Channel → Org (dim_org)
- Kategorie → Subkategorie → Brand → Produkt (dim_product)

### 2. RLS testen
- **Power BI Desktop**: "View as Role" → "Aurora Organization Access"
- **Test Users**: sofia.berger@aurora-group.com (CEO - Full Access)
- **Regional Test**: katharina.steiner@aurora-group.com (nur DACH)

### 3. DAX validieren
- Alle 26 Measures sollten Werte liefern (kein BLANK)
- PVM-Bridge: Price + Volume + Mix = Net Sales - Plan Sales
- Gross Margin %: Zwischen 20-40% für Aurora (realistisch)

## Deployment

### Power BI Desktop
1. Öffne `CoreActionReady.pbip`
2. Aktualisiere alle Datenquellen
3. Teste Hierarchies und Measures
4. Teste RLS mit "View as Role"

### Power BI Service
1. Veröffentliche zu Workspace
2. Konfiguriere Gateway (falls on-premises)
3. Weise Users zu "Aurora Organization Access" Role
4. Teste RLS mit verschiedenen User-Accounts

### Microsoft Fabric
1. Upload PBIP zu Fabric Workspace
2. Konvertiere zu Fabric Semantic Model (optional)
3. Nutze DirectLake für Performance (falls Lakehouse verfügbar)

## Best Practices Angewendet

✅ **Hierarchies**: Alle Dimensionen mit Business-Hierarchien  
✅ **Sort-By Columns**: Month nach MonthNumber sortiert  
✅ **Hidden Columns**: Surrogate Keys (DateKey, OrgKey, etc.) ausgeblendet  
✅ **Display Folders**: Business-orientierte Namen statt Use Case IDs  
✅ **RLS**: Bidirektionale Security mit security_user_org  
✅ **DAX Best Practices**: VAR-Statements, DIVIDE statt `/`, keine Division durch 0  
✅ **Aurora Context**: Region-Namen, Channel-Namen aus org_chart.md  
✅ **Naming Conventions**: Keine technischen Präfixe, Business-Namen  

## Known Limitations

🟡 **COM-003 Customer Measures**: Vereinfachte CLV-Berechnung (Faktor 3), keine externe fact_customer_value Tabelle  
🟡 **COM-004 Promotion**: Benötigt fact_promo für Baseline Sales (aktuell Platzhalter-Logik)  
🟡 **Security**: Demo-User-Liste, in Produktion aus Azure AD / Entra ID synchronisieren  

## Nächste Schritte

1. **Erweiterung auf Finance Domain** (FIN-001, FIN-002)
2. **Operations Domain** (OPS-001, OPS-002, OPS-003)
3. **Supply Chain Domain** (SCM-001, SCM-002, SCM-003)
4. **Calculation Groups** für Time Intelligence (YTD, QTD, MAT)
5. **What-If Parameters** für Scenario Planning
6. **Aggregations** für große Datenvolumen (>1M Zeilen)

## Governance

- **Business Owner**: Chief Commercial Officer (Isabella Conti)
- **Technical Owner**: VP Data, Analytics & AI (Dilan Yılmaz)
- **Maintainer**: Analytics Core Team
- **Review Cycle**: Monthly
- **Version**: v1.0
- **Last Updated**: 2026-02-04

---

**Aurora Group**: Leading European Omnichannel Retail & Consumer Goods Company
