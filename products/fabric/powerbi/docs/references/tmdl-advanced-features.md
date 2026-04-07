# TMDL Advanced Features Guide

> **Purpose**: TMDL-Textsyntax für fortgeschrittene Features, die im `TMDL_Allowed_Subset.md` als Policies definiert aber nicht als Syntax-Beispiele dokumentiert sind.
> **Pflichtlektüre vor**: Calculation Groups, Direct Lake Partitions, RLS-Rollen, Calculated Tables.
> **Quelle**: `microsoft/skills-for-fabric` — `tmdl-authoring-guide.md` + `tmdl-advanced-features-guide.md`

---

## 1. Pflicht-Basisdateien: database.tmdl + model.tmdl

Diese Dateien sind bei **jedem** Semantic Model via REST API Pflicht. Ohne sie schlägt `createItemWithDefinition` fehl.

### definition.pbism

```json
{
    "version": "4.2",
    "settings": {
        "qnaEnabled": true
    }
}
```

### definition/database.tmdl

```
database '<DatabaseName>'
 compatibilityLevel: 1702
 compatibilityMode: powerBI
```

> **Pflicht**: `database '<Name>'` muss die erste Zeile sein — kein bare `compatibilityLevel` ohne `database`-Deklaration.

### definition/model.tmdl (Einzel-Datei-Layout)

```
model Model
 culture: en-US
 defaultPowerBIDataSourceVersion: powerBI_V3
 discourageImplicitMeasures

 ref table Sales
 ref table Product
 ref table Date

 ref relationship 'Sales to Date'
 ref relationship 'Sales to Product'
```

> **Kritisch**: `defaultPowerBIDataSourceVersion: powerBI_V3` ist Pflicht für Import-Mode-Modelle.
> Ohne diesen Wert gibt die API den Fehler `Import from JSON supported for V3 models only` zurück.

> **Multi-Datei-Layout**: Bei mehreren Tabellen `ref table <Name>` für jede Tabelle eintragen.
> Relationships, Roles, Perspectives, Cultures ebenfalls als `ref` deklarieren.

---

## 2. TMDL-Textsyntax Grundregeln

> Diese Regeln gelten für **alle** TMDL-Dateien. Violations werden vom PostToolUse-Hook blockiert.

| Regel | Richtig | Falsch |
|---|---|---|
| Einrückung | **Tabs** (`\t`) | Spaces |
| DAX-Zuweisung | `=` | `:=` |
| Descriptions | `/// Kommentar` über dem Objekt | `description:` Property |
| Kommentare | `///` (doc-comment) | `//` (nicht unterstützt) |
| lineageTag | Nie manuell setzen | Auto-generiert |
| Multi-line DAX | Triple-Backticks ` ``` ` | Inline mit `\n` |
| Namen mit Sonderzeichen | `'Order Date'` (Single Quotes) | `Order Date` |
| dataType auf Measures | Nie setzen | `dataType: decimal` |

### Measures vor Columns

In Table-Dateien immer Measures zuerst, dann Columns:

```
table Sales

 /// Gesamtumsatz
 measure 'Net Sales Amount' = SUM(Sales[Net Sales Amount])
  formatString: EUR #,0.00
  displayFolder: 01_Sales

 column SalesKey
  dataType: int64
  isHidden
  isKey
  summarizeBy: none
  sourceColumn: sales_key
```

---

## 3. Import-Mode Tabelle (vollständiges Beispiel)

```
table Product

 /// Stammdaten Produkte — Grain: ein Datensatz pro Produkt
 measure '# Products' = COUNTROWS(Product)
  formatString: #,##0
  displayFolder: 03_Customer

 column ProductKey
  dataType: int64
  isHidden
  isKey
  summarizeBy: none
  sourceColumn: ProductKey

 /// Produktname für Anzeige
 column 'Product Name'
  dataType: string
  sourceColumn: ProductName
  sortByColumn: SortOrder

 column SortOrder
  dataType: int64
  isHidden
  summarizeBy: none
  sourceColumn: SortOrder

 partition Product = m
  mode: import
  source =
   let
    Source = Sql.Database(#"Server", #"Database"),
    Product = Source{[Schema="dbo", Item="Product"]}[Data]
   in
    Product
```

---

## 4. Direct Lake — Entity Partition

Verbindet das Semantic Model direkt mit Delta-Tabellen im Lakehouse — kein Datenimport.

### Named Expression (einmalig in model.tmdl oder eigener expressions.tmdl)

```
expression DL_Lakehouse =
 let
  Source = AzureStorage.DataLake("https://onelake.dfs.fabric.microsoft.com/<WorkspaceId>/<LakehouseId>", [HierarchicalNavigation=true])
 in
  Source
```

> Ersetze `<WorkspaceId>` und `<LakehouseId>` mit den GUIDs des Gold-Lakehouses.

### Tabelle mit Entity Partition

```
table Sales

 /// Umsatzdaten — Grain: Rechnungszeile
 measure 'Net Sales Amount' = ```
   SUMX(
    Sales,
    Sales[Quantity] * Sales[UnitPrice]
   )
   ```
  formatString: EUR #,0.00
  displayFolder: 01_Sales

 column SalesKey
  dataType: int64
  isHidden
  isKey
  summarizeBy: none
  sourceColumn: sales_key

 column Quantity
  dataType: int64
  summarizeBy: none
  sourceColumn: quantity

 column UnitPrice
  dataType: decimal
  summarizeBy: none
  sourceColumn: unit_price

 column OrderDate
  dataType: dateTime
  summarizeBy: none
  sourceColumn: order_date

 partition Sales = entity
  mode: directLake
  source
   entityName: Sales
   schemaName: dbo
   expressionSource: DL_Lakehouse
```

### Direct Lake Regeln

- Alle Partitionen müssen `mode: directLake` mit `EntityPartitionSource` nutzen — kein M/Power Query
- `expressionSource` muss auf die Named Expression zeigen
- `dataType: binary` Spalten werden nicht unterstützt
- Keine Transformationen — Spalten mappen direkt via `sourceColumn`
- SQL-Endpoint des Lakehouses muss `provisioningStatus: "Success"` haben bevor das Modell erstellt wird

---

## 5. Calculated Table (_Measures)

Der `_Measures`-Table enthält alle Measures ohne eigene Datenspalten.

```
table _Measures

 /// Gesamtumsatz Netto
 measure 'Net Sales Amount' = SUM(fact_sales[net_sales_amount])
  formatString: EUR #,0.00
  displayFolder: 01_Sales

 /// Bruttomargen-Anteil
 measure 'Gross Margin %' = ```
   VAR _ns = [Net Sales Amount]
   RETURN IF (_ns = 0, BLANK(), DIVIDE ( [Gross Margin Amount], _ns ) )
   ```
  formatString: 0.0 %
  displayFolder: 02_Margin

 column Dummy
  dataType: string
  isHidden
  sourceColumn: [Dummy]

 partition _Measures = calculated
  mode: import
  source = ROW("Dummy", BLANK())
```

> **Model View Position**: `_Measures`-Tabelle immer bei (0, 0) im Diagramm-Layout — Spaghetti-Prinzip.

---

## 6. Calculation Groups (Zeit-Intelligenz)

Calculation Groups ermöglichen Zeit-Varianten (YTD, LY, etc.) ohne Measures zu duplizieren.

```
table 'Time Intelligence'
 isHidden

 calculationGroup
  precedence: 10

  calculationItem Base = SELECTEDMEASURE()

  /// Year-to-Date
  calculationItem YTD = ```
    CALCULATE (
     SELECTEDMEASURE(),
     DATESYTD ( 'Date'[Date] )
    )
    ```

  /// Vorjahr (gleicher Zeitraum)
  calculationItem 'LY' = ```
    CALCULATE (
     SELECTEDMEASURE(),
     SAMEPERIODLASTYEAR ( 'Date'[Date] )
    )
    ```

  /// Year-over-Year Abweichung absolut
  calculationItem 'YoY Δ' = ```
    SELECTEDMEASURE() - CALCULATE (
     SELECTEDMEASURE(),
     SAMEPERIODLASTYEAR ( 'Date'[Date] )
    )
    ```

  /// Year-over-Year %
  calculationItem 'YoY %' = ```
    VAR _ly = CALCULATE (
     SELECTEDMEASURE(),
     SAMEPERIODLASTYEAR ( 'Date'[Date] )
    )
    RETURN DIVIDE ( SELECTEDMEASURE() - _ly, _ly )
    ```
   formatStringExpression = ```
     IF (
      ISSELECTEDMEASURE ( [Net Sales Amount], [Gross Margin Amount] ),
      "0.0 %",
      "0.0 %"
     )
     ```

 column Name
  dataType: string
  isHidden
  sourceColumn: Name

 column Ordinal
  dataType: int64
  isHidden
  summarizeBy: none
  sourceColumn: Ordinal

 partition 'Time Intelligence' = calculated
  mode: import
  source = CALENDAR(DATE(2020,1,1), DATE(2026,12,31))
```

### Calculation Group Regeln

- `calculationGroup` ist eine spezielle Tabellen-Eigenschaft (kein eigener Typ)
- `precedence` bestimmt die Auswertungsreihenfolge bei mehreren Calculation Groups (höher = zuerst)
- `SELECTEDMEASURE()` referenziert das Measure, das aktuell durch die CG ausgewertet wird
- `formatStringExpression` erlaubt dynamische Formatstrings je nach selektiertem Measure
- Die Tabelle braucht `Name` (string) und `Ordinal` (int64) Pflicht-Spalten

---

## 7. Security Roles / RLS

Rollen werden in separaten Dateien unter `definition/roles/` gespeichert.

### definition/roles/RLS_Sales_Region.tmdl

```
role 'RLS_Sales_Region'
 modelPermission: read

 /// Filtert auf Regionen des eingeloggten Nutzers
 tablePermission Sales
  filterExpression: ```
    'Sales'[RegionCode] = LOOKUPVALUE (
     'User Regions'[RegionCode],
     'User Regions'[Email],
     USERNAME()
    )
    ```
```

### OLS — Object Level Security (Spalten verbergen)

```
role Finance
 modelPermission: read

 /// Kosten-Spalten nur für Finance sichtbar
 tablePermission Sales
  columnPermission 'Unit Cost'
   metadataPermission: read
  columnPermission 'Discount Amount'
   metadataPermission: read

 /// Alle anderen Spalten verbergen
 tablePermission 'Cost Details'
  metadataPermission: none
```

### Regeln

- Rollen nur auf Dimensions-Tabellen — **nie auf Facts** (bestehende Policy in `TMDL_Allowed_Subset.md` §14)
- Naming: `RLS_<Domain>_<Scope>` (z.B. `RLS_Sales_Region`)
- `filterExpression` muss eine DAX-Formel sein die `TRUE/FALSE` zurückgibt
- `metadataPermission: none` = Spalte in Metadaten und Daten unsichtbar (OLS)
- **Role Membership** (User → Rolle) **nicht in TMDL** — immer via Power BI REST API:

```bash
# User zu RLS-Rolle hinzufügen (Power BI Datasets API Audience!)
az rest --method post \
  --resource "https://analysis.windows.net/powerbi/api" \
  --url "https://api.powerbi.com/v1.0/myorg/groups/$WS_ID/datasets/$MODEL_ID/users" \
  --headers "Content-Type=application/json" \
  --body '{
    "principalType": "User",
    "identifier": "user@company.com",
    "datasetUserAccessRight": "ReadRls",
    "roles": ["RLS_Sales_Region"]
  }'
```

> **Gotcha**: `INFO.ROLEMEMBERSHIPS()` (DAX) gibt leere oder unvollständige Ergebnisse zurück.
> Role Memberships werden im Fabric Service gespeichert — immer REST API nutzen.

---

## 8. Hierarchien

Hierarchien werden innerhalb der Tabellen-Datei deklariert.

```
table Geography

 column Continent
  dataType: string
  sourceColumn: Continent

 column Country
  dataType: string
  sourceColumn: Country

 column City
  dataType: string
  sourceColumn: City

 /// Geo-Hierarchie für Drill-Down
 hierarchy 'Geography Hierarchy'

  level Continent
   column: Continent

  level Country
   column: Country

  level City
   column: City
```

---

## 9. Relationships

Relationships werden in `definition/relationships.tmdl` oder inline in model.tmdl deklariert.

```
/// Sales → Date (aktiv)
relationship 'Sales to Date'
 fromColumn: Sales.'Order Date'
 toColumn: 'Date'.'Date'

/// Sales → Date (inaktiv — für Ship Date)
relationship 'Sales - Ship Date to Date'
 isActive: false
 fromColumn: Sales.'Ship Date'
 toColumn: 'Date'.'Date'
```

**Regeln:**
- `fromColumn` = Many-Seite (Fact), `toColumn` = One-Seite (Dimension)
- Default `crossFilteringBehavior: oneDirection` — `bothDirections` nur mit Begründung
- `isActive: false` für Role-Playing Dimensions; im DAX `USERELATIONSHIP()` nutzen

---

## 10. Annotationen

Annotations können an Model, Tabellen und Objekten gesetzt werden.

```
model Model
 annotation PBI_QueryOrder = '["Sales","Product","Date","_Measures"]'
 annotation __PBI_TimeIntelligenceEnabled = "1"

table Sales
 annotation PBI_ResultType = "Table"
```

---

## 11. Format String Referenz

| Typ | formatString | Ausgabe |
|---|---|---|
| Währung (EU) | `EUR #,0.00` | EUR 1.234,56 |
| Währung (US) | `\$#,##0.00` | $1,234.56 |
| Prozent | `0.0 %` | 45,6 % |
| Integer | `#,##0` | 1.234 |
| Dezimal | `#,##0.00` | 1.234,56 |
| Tausend | `#,##0,K` | 1.234K |
| Millionen | `#,##0,,M` | 1M |
| Datum | `dd.MM.yyyy` | 04.04.2026 |

---

## Cross-References

- Projekt-Policies (was erlaubt ist): `core/strategy_operating_model/operating_model/reference/TMDL_Allowed_Subset.md`
- REST API Deploy: `products/fabric/powerbi/docs/references/fabric-powerbi-authoring.md`
- Fabric API Auth/LRO: `products/fabric/powerbi/docs/references/fabric-api-core.md`
