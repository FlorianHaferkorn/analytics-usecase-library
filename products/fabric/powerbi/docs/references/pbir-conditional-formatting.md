# pbir-conditional-formatting.md — PBIR Conditional Formatting

> **Source**: `data-goblin/power-bi-agentic-development` pbir-format/references/schema-patterns/conditional-formatting.md
> **Purpose**: Patterns for adding measure-based, gradient, and rules-based conditional formatting to PBIR visuals.

---

## Overview

Conditional formatting in PBIR visuals is configured in `visual.json` under the `objects` key. There are three approaches:

| Approach | When to Use | Key Element |
|---|---|---|
| **Measure-based** | Dynamic color from a DAX measure | `"Expression"` with measure reference |
| **Gradient (data bars / color scale)** | Continuous color scale over a range | `"FillRule"` with `"Gradient"` |
| **Rules-based** | Discrete conditions (if < X, color Y) | `"FillRule"` with `"StaticList"` |

---

## Critical: dataViewWildcard

All conditional formatting that applies per data point (not per visual) requires:

```json
"selector": {
  "metadata": {
    "dataViewWildcard": { "matchingOption": 1 }
  }
}
```

- `matchingOption: 0` — applies to the whole visual (single value)
- `matchingOption: 1` — applies per data point (row/category)

Using `matchingOption: 0` when you need per-row coloring is a common mistake that results in all rows getting the same color.

---

## 1. Measure-Based Formatting

Uses a DAX measure (or extension measure) that returns a color value (hex string or theme token).

```json
{
  "name": "visualObject",
  "properties": {
    "fontColor": {
      "solid": {
        "color": {
          "expr": {
            "Measure": {
              "Expression": {
                "SourceRef": { "Entity": "_Measures" }
              },
              "Property": "Revenue Color"
            }
          }
        }
      }
    }
  },
  "selector": {
    "metadata": {
      "dataViewWildcard": { "matchingOption": 1 }
    }
  }
}
```

**Supported formatting properties:**
- `fontColor` — text color of the cell/data label
- `background` — cell background color
- `dataBarFormatting` — data bar color
- `iconSet` — icon color/type
- `labelColor` — axis label color (**ANNAHME, ungeprüft**: eine Quelle vom 24.09.2026 sagt, bedingte Formatierung auf Kategorie-Achsenbeschriftungen rendert nicht; Klärung im gerenderten Nachweis, `docs/plans/UMSETZUNGSPLAN_AGENTIC_LOOP.md` AP-8)

---

## 2. Gradient / Color Scale Formatting

Applies a continuous color gradient across a numeric range. Used for heat maps and data bars.

```json
{
  "name": "background",
  "properties": {
    "fill": {
      "solid": {
        "color": {
          "fillRule": {
            "linearGradient2": {
              "min": {
                "color": { "expr": { "Literal": { "Value": "'#FF0000'" } } },
                "value": { "expr": { "Literal": { "Value": "0" } } }
              },
              "max": {
                "color": { "expr": { "Literal": { "Value": "'#00FF00'" } } },
                "value": { "expr": { "Literal": { "Value": "1000000" } } }
              }
            }
          }
        }
      }
    }
  },
  "selector": {
    "metadata": {
      "dataViewWildcard": { "matchingOption": 1 }
    }
  }
}
```

**Gradient types:**
- `linearGradient2` — two-point gradient (min → max)
- `linearGradient3` — three-point gradient (min → center → max)

---

## 3. Rules-Based Formatting

Discrete color rules based on value ranges. Each rule in `StaticList` is evaluated in order; first match wins.

```json
{
  "name": "background",
  "properties": {
    "fill": {
      "solid": {
        "color": {
          "fillRule": {
            "staticList": {
              "rules": [
                {
                  "value": { "expr": { "Literal": { "Value": "0.9" } } },
                  "outputColor": { "expr": { "Literal": { "Value": "'#FF6B6B'" } } },
                  "outputColorLiteralValue": "#FF6B6B",
                  "comparison": "LessThan"
                },
                {
                  "value": { "expr": { "Literal": { "Value": "1.0" } } },
                  "outputColor": { "expr": { "Literal": { "Value": "'#FFE66D'" } } },
                  "outputColorLiteralValue": "#FFE66D",
                  "comparison": "LessThan"
                },
                {
                  "outputColor": { "expr": { "Literal": { "Value": "'#6BCB77'" } } },
                  "outputColorLiteralValue": "#6BCB77"
                }
              ]
            }
          }
        }
      }
    }
  },
  "selector": {
    "metadata": {
      "dataViewWildcard": { "matchingOption": 1 }
    }
  }
}
```

**Comparison operators:** `LessThan`, `LessThanOrEqual`, `GreaterThan`, `GreaterThanOrEqual`, `Equal`, `Contains`, `DoesNotContain`, `StartsWith`, `IsBlank`, `IsNotBlank`

**Last rule without a `comparison`** acts as the default/else case.

---

## Decision Guide

```
Need color per data point?
├── Yes → use dataViewWildcard matchingOption: 1
│   ├── Color comes from a DAX measure? → Measure-based
│   ├── Continuous scale across a range? → Gradient (linearGradient2/3)
│   └── Discrete threshold rules? → Rules-based (staticList)
└── No (whole visual, single color) → use matchingOption: 0, or set color directly
```

---

## Six Common Use Cases

### 1. KPI Card — Status Color from Measure

Use an extension measure that returns `"good"` / `"neutral"` / `"bad"`:

```json
{
  "name": "calloutValue",
  "properties": {
    "color": {
      "solid": {
        "color": {
          "expr": {
            "Measure": {
              "Expression": { "SourceRef": { "Schema": "extension", "Entity": "_Measures" } },
              "Property": "Revenue Status Color"
            }
          }
        }
      }
    }
  },
  "selector": { "metadata": { "dataViewWildcard": { "matchingOption": 0 } } }
}
```

### 2. Matrix Row — Background Heat Map

Apply a gradient background to numeric cells in a matrix:

```json
{
  "name": "values",
  "properties": {
    "backColor": {
      "solid": {
        "color": {
          "fillRule": {
            "linearGradient2": {
              "min": { "color": { "expr": { "Literal": { "Value": "'#FFFFFF'" } } }, "value": { "expr": { "Literal": { "Value": "0" } } } },
              "max": { "color": { "expr": { "Literal": { "Value": "'#2563EB'" } } }, "value": { "expr": { "Literal": { "Value": "1000000" } } } }
            }
          }
        }
      }
    }
  },
  "selector": { "metadata": { "dataViewWildcard": { "matchingOption": 1 } } }
}
```

### 3. Bar Chart — Color by Category Measure

Use a measure per bar:

```json
{
  "name": "dataPoint",
  "properties": {
    "fill": {
      "solid": {
        "color": {
          "expr": {
            "Measure": {
              "Expression": { "SourceRef": { "Entity": "_Measures" } },
              "Property": "Category Color"
            }
          }
        }
      }
    }
  },
  "selector": { "metadata": { "dataViewWildcard": { "matchingOption": 1 } } }
}
```

### 4. Table Cell Font — RAG Status

Rules-based font color for a metric column:

```json
{
  "name": "values",
  "properties": {
    "fontColor": {
      "solid": {
        "color": {
          "fillRule": {
            "staticList": {
              "rules": [
                { "value": { "expr": { "Literal": { "Value": "0.8" } } }, "outputColor": { "expr": { "Literal": { "Value": "'#DC2626'" } } }, "comparison": "LessThan" },
                { "value": { "expr": { "Literal": { "Value": "1.0" } } }, "outputColor": { "expr": { "Literal": { "Value": "'#D97706'" } } }, "comparison": "LessThan" },
                { "outputColor": { "expr": { "Literal": { "Value": "'#16A34A'" } } } }
              ]
            }
          }
        }
      }
    }
  },
  "selector": { "metadata": { "dataViewWildcard": { "matchingOption": 1 } } }
}
```

### 5. Data Bar in Matrix

Enable data bars on a numeric column:

```json
{
  "name": "columnHeaders",
  "properties": {
    "showDataBars": { "expr": { "Literal": { "Value": "true" } } },
    "dataBarColor": {
      "solid": { "color": { "expr": { "Literal": { "Value": "'#2563EB'" } } } }
    }
  },
  "selector": { "metadata": { "dataViewWildcard": { "matchingOption": 1 } } }
}
```

### 6. Icon Set Based on Measure

Reference an icon set measure that returns icon index values (0, 1, 2, …):

```json
{
  "name": "values",
  "properties": {
    "iconSet": {
      "solid": {
        "color": {
          "expr": {
            "Measure": {
              "Expression": { "SourceRef": { "Entity": "_Measures" } },
              "Property": "Trend Icon"
            }
          }
        }
      }
    }
  },
  "selector": { "metadata": { "dataViewWildcard": { "matchingOption": 1 } } }
}
```

---

## Performance Guidance

- Prefer **measure-based** formatting for complex logic — DAX engine is optimised for this
- Avoid many rules in `staticList` — each rule adds evaluation overhead
- Use **gradient** for continuous scales — simpler engine evaluation than many rules
- Extension measures (report-layer) add minimal overhead compared to model measures
- Avoid calling the same measure in both the visual binding AND formatting — it evaluates twice
