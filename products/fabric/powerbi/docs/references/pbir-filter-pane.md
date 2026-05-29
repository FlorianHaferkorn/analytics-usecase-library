# Filter Pane and Filters

> Source: data-goblin/power-bi-agentic-development — pbir-format skill reference

> For slicer visuals (on-canvas filters), slicer visual documentation is not yet available.

## General Guidance

- The filter pane is the preferred place to set filters for Power BI reports.
- Slicers should only be used when a filter is so important that the user must see it on the page, or when the UX mandates it (button slicers, conditional formatting, specific designs).
- The filter pane is generally preferred because it's a more effective use of space and provides a clear UX.
- If the report is not using the filter pane, hide it by setting `visible: false` in report.json.
- Filter pane styling must be done in the theme JSON — see `pbir-theme.md` "Filter Pane and Filter Card Formatting in Themes".

## Filter Types

Seven filter types are supported. In practice, `Categorical` and `Advanced` cover the vast majority of use cases.

| Type | Description | Use Case |
|------|-------------|----------|
| `Categorical` | Select from a list of values (In/NotIn) | Most common — year, category, brand |
| `Advanced` | Comparison conditions on measures or columns | Measure > threshold, between ranges |
| `TopN` | Top/bottom N by a measure | Top 10 customers by revenue |
| `VisualTopN` | Visual-level top N | Applied automatically by some visuals |
| `RelativeDate` | Relative date window (last N days/months/years) | Rolling time windows |
| `RelativeTime` | Relative time window (last N hours/minutes) | Near-real-time dashboards |
| `Tuple` | Multi-column composite filter | Rare — compound key filtering |

## Filter Scope

Filters can be scoped to three levels:

| Scope | Location | Applies to |
|-------|----------|------------|
| Report | `report.json` -> `filterConfig.filters[]` | All pages and visuals |
| Page | `page.json` -> `filterConfig.filters[]` | All visuals on the page |
| Visual | `visual.json` -> `filterConfig.filters[]` | Single visual only |

## Filter Structure

Every filter has the same core structure regardless of scope:

```json
{
  "name": "d3f20cea05c37b47123a",
  "displayName": "Currency",
  "field": {
    "Column": {
      "Expression": {"SourceRef": {"Entity": "Exchange Rate"}},
      "Property": "From Currency"
    }
  },
  "type": "Categorical",
  "filter": {},
  "isHiddenInViewMode": false,
  "isLockedInViewMode": false,
  "howCreated": "User",
  "objects": {}
}
```

## Setting Default Selected Values

Default filter values are set in the `filter` property using a `Where` clause with `In` condition.

### Categorical Filter with Default Values (In)

```json
{
  "name": "d3f20cea05c37b47123a",
  "field": {
    "Column": {
      "Expression": {"SourceRef": {"Entity": "Exchange Rate"}},
      "Property": "From Currency"
    }
  },
  "type": "Categorical",
  "filter": {
    "Version": 2,
    "From": [{"Name": "e", "Entity": "Exchange Rate", "Type": 0}],
    "Where": [{
      "Condition": {
        "In": {
          "Expressions": [{
            "Column": {
              "Expression": {"SourceRef": {"Source": "e"}},
              "Property": "From Currency"
            }
          }],
          "Values": [
            [{"Literal": {"Value": "'EUR'"}}],
            [{"Literal": {"Value": "'USD'"}}]
          ]
        }
      }
    }]
  }
}
```

**Rules:**
- `From` defines table aliases: `{"Name": "e", "Entity": "Exchange Rate", "Type": 0}`
- `Where.Condition` uses `SourceRef.Source` (the alias), NOT `SourceRef.Entity`
- Each value in `Values` is wrapped in its own array: `[[{val1}], [{val2}]]`
- String values use inner single quotes: `"'EUR'"`
- Integer values use L suffix: `"2022L"`

### Advanced Filter (Comparison)

```json
{
  "type": "Advanced",
  "filter": {
    "Version": 2,
    "From": [{"Name": "d", "Entity": "Budget", "Type": 0}],
    "Where": [{
      "Condition": {
        "Comparison": {
          "ComparisonKind": 1,
          "Left": {
            "Measure": {
              "Expression": {"SourceRef": {"Source": "d"}},
              "Property": "Budget vs. Turnover (%)"
            }
          },
          "Right": {"Literal": {"Value": "0D"}}
        }
      }
    }]
  }
}
```

ComparisonKind: `0`=Equal, `1`=GreaterThan, `2`=GreaterThanOrEqual, `3`=LessThanOrEqual, `4`=LessThan.

### Relative Date Filter

```json
{
  "type": "RelativeDate",
  "filter": {
    "Version": 2,
    "From": [{"Name": "d", "Entity": "Date", "Type": 0}],
    "Where": [{
      "Condition": {
        "Comparison": {
          "ComparisonKind": 2,
          "Left": {
            "Column": {
              "Expression": {"SourceRef": {"Source": "d"}},
              "Property": "Date"
            }
          },
          "Right": {
            "DateSpan": {
              "Expression": {"Now": {}},
              "TimeUnit": 2
            }
          }
        }
      }
    }]
  }
}
```

TimeUnit: `0`=Day, `1`=Week, `2`=Month, `3`=Year, `4`=Decade, `5`=Second, `6`=Minute, `7`=Hour.

## Report Level — Filter Pane Visibility

**CRITICAL:** At report level, ONLY `visible` and `expanded` are allowed on `outspacePane`. Styling properties cause deployment errors.

```json
"objects": {
  "outspacePane": [{
    "properties": {
      "visible": {"expr": {"Literal": {"Value": "true"}}},
      "expanded": {"expr": {"Literal": {"Value": "false"}}}
    }
  }]
}
```

All filter pane styling (colors, fonts, width, borders) must be done in the theme — see `pbir-theme.md`.

## Filter Configuration Options

| Property | Effect |
|----------|--------|
| `isHiddenInViewMode: true` | Filter hidden from pane in reading view |
| `isLockedInViewMode: true` | Filter visible but viewers cannot change it |
| `requireSingleSelect: true` | Force exactly one value selection |
