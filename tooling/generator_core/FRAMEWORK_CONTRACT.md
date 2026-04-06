# generator_core Framework Contract

> **Rule:** Every product generator (Power BI, Metabase, Grafana, Superset, …)
> speaks TO generator_core. generator_core knows nothing about any specific product.

---

## What generator_core provides

| Module | Responsibility |
|---|---|
| `ir/specs.py` | Tool-agnostic IR dataclasses: `DashboardSpec`, `PageSpec`, `VisualSpec`, `MeasureSpec`, `Position` |
| `ir/compiler.py` | `BracketCompiler` — compiles `UseCase_Bracket.yaml` + KPI catalog → `DashboardSpec` |
| `adapters/base.py` | `GeneratorAdapter` abstract base + `RenderResult` |
| `preflight/validator.py` | `PreflightValidator` — 9 checks before generation |
| `preflight/checks.py` | Individual check functions (composable) |
| `intelligence/telemetry.py` | `TelemetryCollector` — records every run to `internal/metrics/` |
| `intelligence/classifier.py` | `ErrorClassifier` — maps error strings → `ErrorCategory` |
| `intelligence/suggester.py` | `FixSuggester` — maps categories → `FixSuggestion` with commands |
| `intelligence/scorer.py` | `QualityScorer` — 6-dimension score for generated output |
| `intelligence/kb.py` | `KnowledgeBase` — reads/writes `knowledge_base/errors.yaml` |
| `knowledge_base/errors.yaml` | Machine-readable error knowledge base (self-learning) |

---

## What generator_core does NOT contain

- No concrete adapters (no `PBIPAdapter`, `MetabaseAdapter`, etc.)
- No product-specific schemas, type strings, or file formats
- No references to PBIP, TMDL, Metabase JSON, Grafana panels, etc.
- No imports from `products/`

---

## Adapter contract

Every concrete adapter MUST:

1. **Inherit** from `tooling.generator_core.adapters.base.GeneratorAdapter`
2. **Implement** all four abstract members:

   | Member | Signature | Purpose |
   |---|---|---|
   | `name` | `@property → str` | Short ID: `"pbip"`, `"metabase"`, … |
   | `target` | `@property → AdapterTarget` | Enum value matching the adapter |
   | `validate_ir(spec)` | `→ List[str]` | Platform-specific IR checks before render |
   | `render(spec)` | `→ RenderResult` | `DashboardSpec → {relative_path: bytes}` |
   | `visual_type_map()` | `→ Dict[VisualType, List[str]]` | IR type → platform type strings |

3. **Live** in its product directory, not in `generator_core`:

   | Adapter | Location |
   |---|---|
   | `PBIPAdapter` | `products/fabric/powerbi/tooling/adapters/pbip.py` |
   | `MetabaseAdapter` | `products/oss_adapters/tooling/adapters/metabase.py` |
   | `GrafanaAdapter` | `products/oss_adapters/tooling/adapters/grafana.py` |
   | `SupersetAdapter` | `products/oss_adapters/tooling/adapters/superset.py` |

4. **Use absolute imports** for generator_core types:
   ```python
   from tooling.generator_core.adapters.base import GeneratorAdapter, RenderResult
   from tooling.generator_core.ir.specs import AdapterTarget, DashboardSpec, VisualType
   ```

5. **Keep `render()` pure** — no side effects on `DashboardSpec`, no file I/O.
   The caller calls `result.write_to(dest_dir)`.

---

## IR coordinate system

Positions are stored as **canvas fractions** (0.0 – 1.0):

```
(0,0) ─────────────────────── (1,0)
  │                              │
  │  Position(x, y, w, h)        │
  │  all values in [0.0, 1.0]    │
  │                              │
(0,1) ─────────────────────── (1,1)
```

Each adapter scales to its own pixel / grid dimensions:

| Adapter | Canvas | Scale method |
|---|---|---|
| PBIP | 1280 × 720 px | `round(pos.x * 1280)` |
| Metabase | 24-column grid | `round(pos.x * 24)` |
| Grafana | 24-column grid | `round(pos.x * 24)` |
| Superset | 12-column grid | `round(pos.x * 12)` |

---

## Pipeline flow

```
UseCase_Bracket.yaml
        │
        ▼
┌─────────────────────────┐
│  PreflightValidator     │  ← generator_core (shared)
│  (9 checks, fail-fast)  │
└──────────┬──────────────┘
           │ passed
           ▼
┌─────────────────────────┐
│  BracketCompiler        │  ← generator_core (shared)
│  Bracket + KPI catalog  │
│  → DashboardSpec (IR)   │
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│  ConcreteAdapter        │  ← product directory (PBI / OSS)
│  validate_ir(spec)      │
│  render(spec)           │
│  → RenderResult         │
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│  RenderResult.write_to  │  ← generator_core (shared)
│  → dist/ files          │
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│  TelemetryCollector     │  ← generator_core (shared)
│  + QualityScorer        │
│  → internal/metrics/    │
└─────────────────────────┘
```

---

## Directory mirror principle

Both product generators follow the same folder structure so developers
familiar with one can navigate the other:

```
products/
  fabric/powerbi/
    orchestrator/          ← orchestrate_full_model.ps1
    tooling/
      adapters/pbip.py     ← PBIPAdapter
      validation/          ← PBI-specific output checks
      run_fabric_checks.ps1
    dist/                  ← generated PBIP output

  oss/
    orchestrator/          ← orchestrate_oss.py
    tooling/
      adapters/
        metabase.py        ← MetabaseAdapter
        grafana.py         ← GrafanaAdapter
        superset.py        ← SupersetAdapter
      validation/          ← OSS-specific output checks
      run_oss_checks.py
    dist/                  ← generated OSS output
```

---

## Self-learning loop

Every generation run records to `internal/metrics/generation_runs/`. The
intelligence layer reads these runs to:

1. Identify recurring errors across runs (`TelemetryCollector.recurring_errors()`)
2. Classify errors into categories (`ErrorClassifier.classify_batch()`)
3. Look up fixes from the knowledge base (`FixSuggester.suggest_for_buckets()`)
4. Auto-append new error patterns as skeleton entries (`KnowledgeBase.append_unknown()`)

Over time, `knowledge_base/errors.yaml` grows richer and `FixSuggester`
provides better guidance without any code changes.

---

## Adding a new adapter (checklist)

- [ ] Create `products/<product>/tooling/adapters/<name>.py`
- [ ] Inherit from `GeneratorAdapter`, implement all 5 abstract members
- [ ] Add `AdapterTarget.<NAME>` to `tooling/generator_core/ir/specs.py`
- [ ] Add adapter to `__main__.py` `cmd_compile()` dispatch
- [ ] Add `validate_ir()` — at minimum check Overview + Detail pages exist
- [ ] Implement `visual_type_map()` with all `VisualType` values
- [ ] Implement `render()` — returns `{relative_path: bytes}`
- [ ] Add OSS-specific output checks to `products/oss_adapters/tooling/validation/`
- [ ] Write at least one smoke test in `products/<product>/tooling/tests/`
