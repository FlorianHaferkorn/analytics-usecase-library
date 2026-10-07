# Lakehouse Architecture

The lakehouse architecture defines how analytical data is structured, stored, and consumed in a cloud-native, tool-agnostic manner.

**Data layers (entry point):** We start from **Silver** (defined by data contracts). Gold is derived from Silver for consumption. Staging/Bronze are out of scope unless explicitly included. See `data_layers_standard.md`.

This architecture enables the Golden Thread and Operating Model to be implemented across platforms (Fabric, Databricks, Snowflake) while maintaining consistency and performance. It does not define strategy, KPIs, or actions; it provides the technical foundation for their analytical execution.

## 1. Role in the Framework

The lakehouse architecture operationalizes the data foundation for the semantic layer and measure system.

- **Data contracts define Silver** (conformed, validated domain data); see `core/data_contracts/`.
- The lakehouse implements **Silver → Gold** in a scalable, performant manner.
- Semantic models consume **Gold** (and thus Silver) without redefining structure or meaning.

The lakehouse acts as the bridge between source systems and analytical consumption.

## 2. Medallion Architecture

Data flows through three layers of progressive refinement.

### 2.1. Bronze Layer (Raw/Staging)

Bronze contains raw ingested data with minimal transformation.

- Preserves source format and structure
- Maintains full historical record of all ingests
- Enables reprocessing and auditing
- Multiple source formats supported (CSV, JSON, Parquet, APIs)

Bronze is optimized for durability and traceability, not performance.

### 2.2. Silver Layer (Curated/Enriched)

Silver contains cleansed, harmonized, and enriched data.

- Business keys are standardized
- Data quality rules are applied
- Temporal partitioning is introduced
- Delta Lake format is standard
- Relationships are established but not enforced

Silver is optimized for consistency and integration.

### 2.3. Gold Layer (Analytics-Ready)

Gold contains dimensional models ready for analytical consumption.

- Star/snowflake schemas (fact + dimension tables)
- Grain is explicit and documented
- Conformed dimensions are shared across domains
- Action aggregates support deviation detection
- Delta Parquet format (tool-agnostic)
- Partitioning optimized for query patterns

Gold is optimized for analytical performance and consistency.

## 3. Gold Layer Structure

The gold layer follows a consistent structural pattern across all domains.

### 3.1. Dimensions

Dimensions are conformed and reused across domains.

```
gold/dimensions/
├─ dim_time/           # Fiscal + calendar hierarchies
├─ dim_product/        # Product catalog + hierarchies
├─ dim_customer/       # Customer master + hierarchies
├─ dim_supplier/       # Supplier master
├─ dim_organization/   # Org structure + cost centers
└─ dim_geography/      # Location hierarchies
```

**Characteristics:**
- Slowly changing dimensions (SCD Type 2 where needed)
- Surrogate keys for relationships
- Natural keys for business user reference
- Hierarchies for drill-down analysis
- No partitioning (typically small enough)
- Delta Parquet format

### 3.2. Facts

Facts represent business events or measurements at explicit grains.

```
gold/facts/
├─ fact_sales/              # Sales transactions
├─ fact_production/         # Production orders/outputs
├─ fact_inventory/          # Inventory snapshots
├─ fact_financials/         # GL entries/balances
├─ fact_quality/            # Quality events/defects
└─ fact_supply_deliveries/  # Inbound deliveries
```

**Characteristics:**
- Explicit grain documented in data contract
- Foreign keys to conformed dimensions
- Additive measures where possible
- Partitioned by time (fiscal_year, fiscal_month)
- Delta Parquet format
- Z-ordered by frequently filtered dimensions

### 3.3. Action Aggregates

Action aggregates are pre-calculated summaries aligned with Action Codes.

```
gold/action_aggregates/
├─ agg_margin_variance/        # Margin deviations by product/time
├─ agg_quality_alerts/         # Quality threshold breaches
├─ agg_forecast_deviation/     # Plan vs actual analysis
├─ agg_inventory_risk/         # Stockout/obsolescence signals
└─ agg_customer_churn_risk/    # Retention signals
```

**Characteristics:**
- Pre-calculated for performance
- Aligned with specific Action Codes
- Deviation/threshold logic applied
- Partitioned by action_code and time
- Smaller volumes than base facts
- Optimized for operational decision support

## 4. Technical Format Standards

All gold layer tables follow consistent technical standards.

### 4.1. File Format

**Delta Parquet** is the standard format for all gold layer tables.

Benefits:
- ACID transactions (consistency)
- Time travel (versioning)
- Schema evolution (flexibility)
- Optimized compression (cost)
- Tool-agnostic (portability)
- Native to Fabric OneLake, Databricks, and supported by Snowflake/Synapse

### 4.2. Partitioning Strategy

Partitioning is applied based on query patterns and data volume.

**Dimensions:**
- No partitioning (typically < 1M rows)
- Single folder per dimension

**Facts (< 100M rows):**
```
partition_by:
  - fiscal_year    # 4-6 partitions
  - fiscal_month   # 12 partitions per year
```

**Facts (> 100M rows):**
```
partition_by:
  - fiscal_year
  - fiscal_quarter  # Fewer partitions than month
```

**Action Aggregates:**
```
partition_by:
  - action_code     # Logical grouping
  - snapshot_month  # Temporal slice
```

**Anti-patterns to avoid:**
- Daily partitioning (too many small files)
- Customer/product partitioning (cardinality too high)
- Multi-level hierarchical partitioning (complexity)

### 4.3. Optimization Techniques

**Z-Ordering (Delta Lake):**
```sql
-- Applied to frequently filtered columns
OPTIMIZE fact_sales ZORDER BY (product_key, customer_key);
```

**Auto-Compaction:**
- Target file size: 128MB - 1GB
- Runs automatically in Fabric/Databricks
- Reduces small file overhead

**Liquid Clustering (Delta Lake 3.0+):**
- Alternative to Z-ordering
- Self-optimizing based on query patterns

## 5. Handling Large/Granular Data

When dealing with high-volume, granular data, apply aggregation layering.

### 5.1. Aggregation Layers

```
Detail Layer      → Transaction-level (fact_sales)
                    - Full grain, all dimensions
                    - Partitioned by time
                    - For drilldown only

Daily Summary     → Daily aggregates (fact_sales_daily)
                    - Reduced volume (365x smaller)
                    - Most queries start here
                    - Pre-joined key dimensions

Monthly Summary   → Monthly aggregates (fact_sales_monthly)
                    - Further reduced volume
                    - Strategic/executive views
                    - Pre-calculated KPIs

Action Aggregates → Deviation-focused (agg_margin_variance)
                    - Exception-based filtering
                    - Action Code aligned
                    - Operational interventions
```

This layering enables:
- Sub-second query performance for common patterns
- Drilldown capability when needed
- Cost optimization (smaller hot datasets)

### 5.2. Volume Thresholds

Apply aggregation layers when:
- Transaction detail > 100M rows
- Daily queries span > 1 year of data
- Common queries filter by time + 2-3 dimensions

Keep transaction detail when:
- Ad-hoc analysis is frequent
- Grain is already relatively high
- Direct Lake mode performance is acceptable

## 6. Fabric-Specific Integration

The lakehouse architecture is designed to leverage Fabric capabilities while remaining portable.

### 6.1. OneLake Structure

```
Lakehouse: analytics_gold
├─ Files/
│  ├─ dimensions/
│  ├─ facts/
│  └─ action_aggregates/
└─ Tables/  (Delta Lake metadata)
   ├─ dim_time
   ├─ fact_sales
   └─ agg_margin_variance
```

### 6.2. Direct Lake Mode

Gold layer tables are optimized for Direct Lake consumption.

**Requirements:**
- Delta Parquet format ✓
- Max 300 columns per table ✓
- Partitioning compatible ✓
- Auto-compaction enabled ✓

**Benefits:**
- Zero data duplication
- Sub-second query response
- Automatic refresh on data changes
- Seamless semantic model binding

### 6.3. OneLake Shortcuts

Shortcuts enable logical data integration without duplication.

```
Lakehouse A (Gold Layer)
    └─ Shortcut → External ADLS/S3 (if external sources)

Lakehouse B (Semantic Model)
    └─ Shortcut → Lakehouse A/gold/* (consumption layer)
```

### 6.3.1 Access Unification: Shortcut vs. Mirror (ADR-0015, pattern P1)

Every external source is integrated by an explicit, recorded **access mode** — *virtualize,
don't duplicate*. The choice is a governed field (`ingestion[].access_mode` in the
Architecture Blueprint IR), not an ad-hoc pipeline decision:

| Access mode | Use when | Effect |
|---|---|---|
| **Shortcut** (default) | Source is already a lake (ADLS Gen2, S3, GCS) or another OneLake item; virtual access meets performance needs | Zero-copy reference; no second physical copy |
| **Mirror** | Azure/operational database needing reliable, isolated, low-latency analytics access | Managed replicated copy in OneLake |
| **Copy** (exception) | Only when performance, isolation, or compliance genuinely require it | Physical copy — requires an explicit rationale |

Default to **shortcut**; choose **mirror** for databases; **copy** must carry a written
justification. This never overrides the no-layer-skip rule (`data_layers_standard.md` §2.1).

### 6.4. Lakehouse vs. Warehouse

Decision 02.10.2026 (ADR-0024 §8): **Lakehouse is the recommendation, Warehouse stays a
selectable option.** Microsoft Learn does not recommend either across the board; *Choose
between Warehouse and Lakehouse* (`fabric/fundamentals/decision-guide-lakehouse-warehouse`,
read 02.10.2026) decides on three questions: Spark development → Lakehouse, T-SQL → Warehouse;
multi-table transactions → Warehouse; unstructured or unclear data → Lakehouse.

**Lakehouse (recommended):**
- Spark/notebooks, Delta tables, shortcuts without copying; Materialized Lake Views
- Learn's recommended use includes the "Medallion lakehouse architecture with bronze, silver,
  and gold zones"
- Its SQL analytics endpoint is read-only: "Full DQL, no DML, and limited DDL"

**Warehouse (option):**
- T-SQL development with "Full DQL, DML, and DDL T-SQL support with full transaction support",
  including multi-table ACID transactions
- Learn's recommended use: "Enterprise data warehousing", SQL-based BI
- Also stores Delta in OneLake and can be read by Direct Lake ("Direct Lake is ideal for
  semantic models connecting to large Fabric lakehouses, warehouses, …", Learn *Direct Lake
  overview*) — Direct Lake does not separate the two

For this framework, **Lakehouse** is the recommended choice: the stack is Spark/notebook-first,
MLV and shortcuts are lakehouse features, and no gold path needs multi-table transactions.
Where generated: `domains[].gold_target` (`lakehouse` default, `mlv`, `warehouse` refused until
generated) in the architecture-blueprint inputs; `gold_target` in
`products/fabric/orchestrator/config.yaml`.

## 6.5 Data Mesh: Domains, Workspaces & Publishing (ADR-0015, pattern P3)

The estate is organized as a **data mesh**: business domains own their data products across
dedicated workspaces, and Gold products are **published** so they are discoverable and
trustworthy — not just present.

- **Domain → workspace topology.** Each business domain (Commercial, Finance, Operations,
  SupplyChain, Experience) maps to one or more workspaces; the workspace is the
  security/ownership/cost boundary. Convention: `ws-<domain>-<role>` where `role` follows the
  medallion layer (`gold`, `reporting`, `mixed`).
- **Publish Gold as data products.** Register Gold products in the OneLake Catalog (and
  Purview where present) with:
  - **Endorsement** — *Promoted* for domain-recommended, *Certified* for products that
    passed a formal governance review (executive/regulatory Gold).
  - **Metadata enrichment** — owner, description, tags (business domain / initiative).
  - **Intended audience** — `internal` / `partner` / `public`.
- **External sharing (P5) is separate.** Externally-shared products are sanitized (masked/
  reduced), labeled, and live in their own workspaces — never the internal operational data.

These fields are carried by the Architecture Blueprint IR (`mesh` / `sharing`) and scored by
the `blueprint_conformance` audit.

## 7. Tool-Agnostic Design

The lakehouse architecture is designed to work across platforms.

**Format Portability:**
- Delta Parquet is supported by Fabric, Databricks, Synapse, Snowflake, Athena
- Schema definitions are exported as data contracts (YAML)
- Relationships are defined logically, not enforced in storage

**Semantic Layer Binding:**
- Power BI: Direct Lake Mode (Delta Lake)
- Tableau: Direct connection to Delta/Parquet
- Databricks SQL: Native Delta Lake queries
- Snowflake: External tables over Delta/Parquet

**Migration Path:**
- Gold layer structure remains constant
- Only connection/authentication changes
- Semantic model logic (DAX/SQL) is preserved

## 8. Data Contracts and Silver → Gold

**Silver** is defined by data contracts (`data_contracts/domains/`): schema, grain, keys, quality expectations. **Gold** is derived from Silver and may differ (different grain, subset of columns, action aggregates, star layout). See `data_layers_standard.md` (Silver vs Gold).

**Contract (Silver) elements:** schema (columns, types, nullability), grain, relationships (foreign keys), partitioning, quality rules.

**Silver → Gold:** Transformation (mapping, aggregation, action aggregates) should be defined per domain so Gold is reproducible. Gold structure (folders, format) follows this document; transformation rules are not yet a single standard in the repo.

**Validation:** Automated checks should ensure Silver matches contracts and Gold is consistent with the defined Silver→Gold rules; schema drift and relationship integrity validated.

## 9. Governance and Validation

Lakehouse standards are enforced through automated validation.

**Schema Validation:**
- Column names, types, nullability match contracts
- Surrogate and natural keys are present
- Partitioning columns exist

**Relationship Validation:**
- Foreign keys reference existing dimension records
- Referential integrity is maintained
- Orphaned records are identified

**Data Quality Validation:**
- Null checks on required fields
- Range checks on measures
- Duplicate detection on keys

Validation runs post-load and alerts on failures.

## 10. Synthetic Data Generation

For showcases and testing, synthetic data is generated conforming to lakehouse standards.

**Generator Input:**
- `synthetic_config_core_v1.yaml` - volume, distribution, constraints
- `data_contracts/domains/*.yaml` - schema and relationships
- `synthetic_data_scope_core_v1.yaml` - domain scope

**Generator Output:**
- Delta Parquet files in `showcases/aurora_group/data/gold/`
- Conformed dimensions generated first
- Facts generated with FK integrity
- Action aggregates pre-calculated

**Generator Location:**
- `data_contracts/sources/synthetic/fabric_nb_generate_backbone_core_v1.py`

Generator ensures:
- Realistic distributions (not random noise)
- Business rule compliance (margins, ratios)
- Relationship integrity (no orphans)
- Volume scalability (configurable)

## 11. Usage Guidance

The lakehouse architecture blueprint serves as a reference for all implementations.

**For Showcases:**
- Use synthetic data generator to create gold layer
- Validate against data contracts
- Bind semantic model via Direct Lake

**For Client Projects:**
- Replace synthetic generator with real ETL/ELT
- Preserve gold layer structure
- Maintain data contract alignment

**For Multi-Domain Implementations:**
- Reuse conformed dimensions
- Partition facts by domain if needed
- Share action aggregate patterns

## 12. Outcome

When applied consistently, the lakehouse architecture ensures that:

- analytical data is structured for performance and consistency,
- semantic models consume governed, high-quality data,
- and analytical logic is portable across platforms.

The lakehouse architecture enables scale by providing structure, not constraint.

---

## Sources & Grounding

This architecture applies the industry **lakehouse + medallion** pattern (bronze/silver/gold quality layers) with Delta Lake / Parquet storage and Kimball dimensional modelling at the Gold layer. The specific claims in this document are grounded in the following primary sources:

- **Medallion lakehouse architecture** (bronze raw → silver enriched → gold curated quality layers) — Databricks: <https://docs.databricks.com/aws/en/lakehouse/medallion> · Microsoft Learn (Azure Databricks): <https://learn.microsoft.com/en-us/azure/databricks/lakehouse/medallion>
- **Medallion architecture on Microsoft Fabric OneLake** (lakehouse per layer; silver/gold stored as Delta tables; partitioning vs. Liquid Clustering guidance) — Microsoft Learn: <https://learn.microsoft.com/en-us/fabric/onelake/onelake-medallion-lakehouse-architecture>
- **Delta Lake / Parquet storage format** (ACID transactions, time travel, schema evolution; Delta stores data internally as Parquet) — Delta Lake project home: <https://delta.io/> · GitHub (delta-io/delta): <https://github.com/delta-io/delta> · Microsoft Learn (Fabric Delta Lake storage): <https://learn.microsoft.com/en-us/fabric/onelake/onelake-medallion-lakehouse-architecture#delta-lake-storage>
- **Partitioning, OPTIMIZE & Z-Ordering / data skipping** (co-locate related data to reduce files read) — Delta Lake documentation (Optimizations): <https://docs.delta.io/latest/optimizations-oss.html>
- **Gold-layer dimensional modelling** (star schema, fact/dimension tables, conformed dimensions, explicit grain) — Kimball Group, Dimensional Modeling Techniques: <https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/>
- **Direct Lake mode for semantic-model consumption of the Gold layer** (Power BI semantic model storage mode reading Delta tables directly from OneLake; gold layer cited as the ideal Direct Lake source) — Microsoft Learn: <https://learn.microsoft.com/en-us/fabric/fundamentals/direct-lake-overview>
