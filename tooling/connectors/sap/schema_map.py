"""
SAP → Aurora schema mapping.

Maps SAP source tables (VBAK/VBAP, BKPF/BSEG, MARA/MBEW) to the three
Aurora gold-layer fact tables that the Commercial, Finance, and SupplyChain
semantic models read from.

Each entry is a pair:
  (sap_entity_set, aurora_target)

where sap_entity_set is the OData EntitySet name exposed by SAP Gateway,
and aurora_target is the Arrow schema the connector guarantees to produce.

Column mapping notes
--------------------
* VBAK.VBELN + VBAP.POSNR → InvoiceLineID (synthetic: VBELN + "-" + POSNR)
* BKPF.BELNR + BSEG.BUZEI → JournalLineID (synthetic: BELNR + "-" + BUZEI)
* MARA.MATNR              → MaterialKey (maps to ProductKey in Aurora)
* Fiscal year / period     → FiscalYear, FiscalMonth (YYYYMM → int32)
"""

from __future__ import annotations

import pyarrow as pa

# ── fact_sales (from VBAK + VBAP) ────────────────────────────────────────────

FACT_SALES_SCHEMA = pa.schema([
    pa.field("InvoiceLineID",           pa.string(),  nullable=False),
    pa.field("DateKey",                 pa.int32(),   nullable=True),
    pa.field("OrgKey",                  pa.string(),  nullable=True),
    pa.field("ProductKey",              pa.string(),  nullable=True),
    pa.field("CustomerKey",             pa.string(),  nullable=True),
    pa.field("PromoKey",                pa.string(),  nullable=True),
    pa.field("Quantity",                pa.float64(), nullable=True),
    pa.field("List Price Amount",       pa.float64(), nullable=True),
    pa.field("Net Price Amount",        pa.float64(), nullable=True),
    pa.field("Discount Amount",         pa.float64(), nullable=True),
    pa.field("Net Sales Amount",        pa.float64(), nullable=True),
    pa.field("Cost of Goods Sold Amount", pa.float64(), nullable=True),
    pa.field("FiscalYear",              pa.int32(),   nullable=True),
    pa.field("FiscalMonth",             pa.int32(),   nullable=True),
])

# SAP OData field → Aurora column name
VBAK_VBAP_FIELD_MAP: dict[str, str] = {
    # Synthetic key
    "InvoiceLineID":    "InvoiceLineID",
    # Date
    "FKDAT":            "DateKey",
    # Org
    "VKORG":            "OrgKey",
    # Product
    "MATNR":            "ProductKey",
    # Customer
    "KUNNR":            "CustomerKey",
    # Promo / condition
    "AKTNR":            "PromoKey",
    # Quantity
    "KWMENG":           "Quantity",
    # Pricing amounts (EUR)
    "KBETR_LIST":       "List Price Amount",
    "KBETR_NET":        "Net Price Amount",
    "NETWR":            "Net Sales Amount",
    "KBETR_DISC":       "Discount Amount",
    "VPRSV":            "Cost of Goods Sold Amount",
    # Fiscal period
    "GJAHR":            "FiscalYear",
    "POPER":            "FiscalMonth",
}

# ── fact_gl_journal (from BKPF + BSEG) ───────────────────────────────────────

FACT_GL_JOURNAL_SCHEMA = pa.schema([
    pa.field("JournalLineID",   pa.string(),  nullable=False),
    pa.field("AccountKey",      pa.string(),  nullable=True),
    pa.field("CostCenterKey",   pa.string(),  nullable=True),
    pa.field("ProfitCenterKey", pa.string(),  nullable=True),
    pa.field("DateKey",         pa.int32(),   nullable=True),
    pa.field("Amount",          pa.float64(), nullable=True),
    pa.field("Currency",        pa.string(),  nullable=True),
    pa.field("DebitCredit",     pa.string(),  nullable=True),
    pa.field("FiscalYear",      pa.int32(),   nullable=True),
    pa.field("FiscalPeriod",    pa.int32(),   nullable=True),
    pa.field("DocumentType",    pa.string(),  nullable=True),
])

BKPF_BSEG_FIELD_MAP: dict[str, str] = {
    "JournalLineID": "JournalLineID",
    "HKONT":         "AccountKey",
    "KOSTL":         "CostCenterKey",
    "PRCTR":         "ProfitCenterKey",
    "BUDAT":         "DateKey",
    "DMBTR":         "Amount",
    "WAERS":         "Currency",
    "SHKZG":         "DebitCredit",
    "GJAHR":         "FiscalYear",
    "MONAT":         "FiscalPeriod",
    "BLART":         "DocumentType",
}

# ── fact_inventory (from MARA + MBEW) ─────────────────────────────────────────

FACT_INVENTORY_SCHEMA = pa.schema([
    pa.field("MaterialKey",                  pa.string(),  nullable=False),
    pa.field("PlantKey",                     pa.string(),  nullable=True),
    pa.field("StorageLocationKey",           pa.string(),  nullable=True),
    pa.field("DateKey",                      pa.int32(),   nullable=True),
    pa.field("Average Inventory Amount",     pa.float64(), nullable=True),
    pa.field("Obsolete Inventory Amount",    pa.float64(), nullable=True),
    pa.field("Average Inventory Units",      pa.float64(), nullable=True),
    pa.field("Obsolete Inventory Units",     pa.float64(), nullable=True),
    pa.field("FiscalYear",                   pa.int32(),   nullable=True),
    pa.field("FiscalMonth",                  pa.int32(),   nullable=True),
])

MARA_MBEW_FIELD_MAP: dict[str, str] = {
    "MATNR":   "MaterialKey",
    "WERKS":   "PlantKey",
    "LGORT":   "StorageLocationKey",
    "STICHDAT": "DateKey",
    "LBKUM":   "Average Inventory Units",
    "SALK3":   "Average Inventory Amount",
    "EISBE":   "Obsolete Inventory Units",
    "MLMAA":   "Obsolete Inventory Amount",
    "GJAHR":   "FiscalYear",
    "POPER":   "FiscalMonth",
}

# ── Registry ─────────────────────────────────────────────────────────────────

SAP_SCHEMA_REGISTRY: dict[str, pa.Schema] = {
    "fact_sales":       FACT_SALES_SCHEMA,
    "fact_gl_journal":  FACT_GL_JOURNAL_SCHEMA,
    "fact_inventory":   FACT_INVENTORY_SCHEMA,
}

# ── Reverse look-up: Aurora column name → SAP OData field name ────────────────
# Used by _odata_results_to_batch to translate live SAP responses into the
# Aurora column namespace.  Without this translation every column would silently
# become NULL because OData rows carry SAP technical names (e.g. "NETWR"), not
# Aurora display names (e.g. "Net Sales Amount").

SAP_FIELD_MAP_REGISTRY: dict[str, dict[str, str]] = {
    "fact_sales":      {aurora: sap for sap, aurora in VBAK_VBAP_FIELD_MAP.items()},
    "fact_gl_journal": {aurora: sap for sap, aurora in BKPF_BSEG_FIELD_MAP.items()},
    "fact_inventory":  {aurora: sap for sap, aurora in MARA_MBEW_FIELD_MAP.items()},
}
