# Business Objects (D-608)

**Purpose:** the business-object layer of the library — business objects such as customer,
product, invoice line with keys, attributes, relationships, the binding to one governed table and
the catalog KPIs that read it (Golden Thread). Base for the ontology delivery to Fabric IQ
(Meridian `meridian/semantics/rdf_owl.py`, D-593) and the later Fabric IQ export (W4.5).

| File | Role |
|---|---|
| `business_objects.yaml` | The layer (derived; `null` = gap to fill, never a guess) |
| `tooling/generator/schemas/business_object.schema.json` | Schema — **peer pair**, byte-identical with Meridian `meridian/core/schemas/business_object.schema.json` |
| `tooling/generator/business_objects.py` | Derivation (`--write`) and gate (`--check`) |
| `tooling/tests/test_business_objects.py` | Schema, gates with counter-probes, drift, stable ids, parity pin |

## Rules

- **Derived, not authored.** One object per governed table (`core/data_contracts/domains/`, one
  definition per table): dimension → `master_data`, fact → `transaction`. Relationships from
  `ref` columns, KPIs from `technical.lineage` of `core/kpi_catalog/kpis/`. The field-by-field
  rules are in the docstring of `tooling/generator/business_objects.py`.
- **Ids** `BO-<NNN>`, unique within the catalog (`catalog: aluca-library`); an id never changes.
  No Kuerzel: a business object has no lever domain (D-594 Nachtrag 4), conformed objects serve
  several domains; the owning domain is the field `domain`.
- **Curate in the file, rerun the derivation.** A value the derivation leaves `null` (names,
  roles, personal-data class, schema/layer) may be filled by hand; `--write` keeps it. Structure
  (tables, columns, relationships, KPIs) changes only through the contracts and the KPI catalog.
- **KPIs are referenced, never defined** (Golden Thread): every `kpi_ids` entry must exist in
  the catalog — `--check` and the test fail otherwise.
- Personal data per attribute uses the bracket vocabulary
  (`data_protection.personal_data_categories`).

```bash
python3 tooling/generator/business_objects.py --check   # gate
python3 tooling/generator/business_objects.py --write   # after contract/KPI changes
```
