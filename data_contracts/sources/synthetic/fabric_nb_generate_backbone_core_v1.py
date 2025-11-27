# COMMAND ----------
# nb_generate_backbone_core_v1
# Synthetic backbone generator for Aurora Group – Core Use Cases v1

# PARAMETERS (anpassen auf deine Pfade)
CONFIG_PATH = "/lakehouse/default/Files/docs/data_design/synthetic_config_core_v1.yaml"
CONTRACT_PATH = "/lakehouse/default/Files/docs/data_design/synthetic_data_contract.yaml"
SCOPE_PATH = "/lakehouse/default/Files/docs/data_design/synthetic_data_scope_core_v1.yaml"

RUN_MODE = "core_v1"  # später: "full", "core_v1", "esg_only" etc.

LAKEHOUSE_NAME = "lh_aurora_backbone"  # TODO: erst erstellen
SCHEMA = "gold"                        # logisches Zielschema

# COMMAND ----------
# Imports

import yaml
import random
from datetime import datetime

from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql import types as T

# COMMAND ----------
# Helper: YAML laden

def load_yaml(path: str) -> dict:
    """
    Load YAML file from given path into a Python dict.
    Assumes file is accessible via Lakehouse Files or workspace FS.
    """
    # Variante: Spark Files
    content = (
        spark.read.text(path)
        .select(F.collect_list("value").alias("lines"))
        .collect()[0]["lines"]
    )
    text = "\n".join(content)
    return yaml.safe_load(text)


config = load_yaml(CONFIG_PATH)
contract = load_yaml(CONTRACT_PATH)
scope_core = load_yaml(SCOPE_PATH)

# Seed setzen für Reproduzierbarkeit
random.seed(config.get("random_seed", 12345))

# COMMAND ----------
# Helper: Zugriff auf Contract-Definitionen

def get_dim_def(name: str) -> dict:
    for d in contract.get("dimensions", []):
        if d["name"] == name:
            return d
    raise KeyError(f"Dimension not found in contract: {name}")


def get_fact_def(name: str) -> dict:
    for f in contract.get("facts", []):
        if f["name"] == name:
            return f
    raise KeyError(f"Fact not found in contract: {name}")


# COMMAND ----------
# Generator: dim_date

def generate_dim_date(cfg: dict, dim_def: dict) -> DataFrame:
    """
    Generate dim_date according to config.time and dim_date definition in contract.
    Grain: one row per calendar date.
    """
    start = cfg["time"]["dim_date_start"]
    end = cfg["time"]["dim_date_end"]

    # TODO: Datumsrange mit Spark erzeugen
    # - Spalte DateKey (YYYYMMDD int)
    # - Calendar Year/Month/Quarter
    # - Fiscal Year/Period laut settings.fiscal_year_start
    # - ggf. Weekday, Weekend-Flag etc.

    # Placeholder: leeres DF mit Schema aus Contract
    # Hier später Logik implementieren
    schema_fields = []
    for col in dim_def["columns"]:
        name = col["name"]
        typ = col["type"]
        if typ in ("int", "number"):
            dt = T.IntegerType()
        elif typ == "date":
            dt = T.DateType()
        elif typ in ("currency", "float"):
            dt = T.DoubleType()
        elif typ == "bool":
            dt = T.BooleanType()
        else:
            dt = T.StringType()
        schema_fields.append(T.StructField(name, dt, True))
    schema = T.StructType(schema_fields)
    df = spark.createDataFrame([], schema)

    return df


# COMMAND ----------
# Generator: dim_org

def generate_dim_org(cfg: dict, dim_def: dict) -> DataFrame:
    """
    Generate dim_org from config.org definitions (regions, countries, store_count, dc_count).
    Grain: org_node (Group, Region, Country, Store, DC, ESG Site).
    """
    # TODO:
    # - Group-Level Node
    # - Regions
    # - Countries per Region
    # - Stores/DCs pro Country gemäß config.org.regions.*.store_count, dc_count
    # - OrgLevel, OrgType, Currency Code per Country
    # - Open/Close DateKeys plausibel verteilen

    # Placeholder-Schema analog zu dim_date
    schema_fields = []
    for col in dim_def["columns"]:
        name = col["name"]
        typ = col["type"]
        if typ in ("int", "number"):
            dt = T.IntegerType()
        elif typ == "date":
            dt = T.DateType()
        elif typ in ("currency", "float"):
            dt = T.DoubleType()
        elif typ == "bool":
            dt = T.BooleanType()
        else:
            dt = T.StringType()
        schema_fields.append(T.StructField(name, dt, True))
    schema = T.StructType(schema_fields)
    df = spark.createDataFrame([], schema)

    return df


# COMMAND ----------
# Generator: dim_product

def generate_dim_product(cfg: dict, dim_def: dict) -> DataFrame:
    """
    Generate dim_product based on config.products (categories, product_count, margin ranges).
    Grain: product.
    """
    # TODO:
    # - Für jede Category Anzahl Produkte laut product_count
    # - ProductCode, ProductName, Category, Subcategory, Brand
    # - List Price Amount in range min_list_price..max_list_price
    # - Lifecycle Status (Intro/Growth/Mature/EOL) abhängig von Startdatum

    schema_fields = []
    for col in dim_def["columns"]:
        name = col["name"]
        typ = col["type"]
        if typ in ("int", "number"):
            dt = T.IntegerType()
        elif typ == "date":
            dt = T.DateType()
        elif typ in ("currency", "float"):
            dt = T.DoubleType()
        elif typ == "bool":
            dt = T.BooleanType()
        else:
            dt = T.StringType()
        schema_fields.append(T.StructField(name, dt, True))
    schema = T.StructType(schema_fields)
    df = spark.createDataFrame([], schema)

    return df


# COMMAND ----------
# Generator: dim_customer, dim_promo, dim_currency, dim_account, dim_esg_site

def generate_dim_customer(cfg: dict, dim_def: dict) -> DataFrame:
    """
    Generate dim_customer with synthetic segments, channel preferences and tenure buckets.
    PII-free.
    """
    # TODO:
    # - total_customers aus cfg.customers.total_customers
    # - Segment-Verteilung aus cfg.customers.segment_shares
    # - Channel Preference (Store/ECom/Mixed)
    # - Tenure Bucket über zufällige Verteilung

    # Placeholder wie oben
    schema_fields = []
    for col in dim_def["columns"]:
        name = col["name"]
        typ = col["type"]
        if typ in ("int", "number"):
            dt = T.IntegerType()
        elif typ == "date":
            dt = T.DateType()
        elif typ in ("currency", "float"):
            dt = T.DoubleType()
        elif typ == "bool":
            dt = T.BooleanType()
        else:
            dt = T.StringType()
        schema_fields.append(T.StructField(name, dt, True))
    schema = T.StructType(schema_fields)
    return spark.createDataFrame([], T.StructType(schema_fields))


def generate_dim_promo(cfg: dict, dim_def: dict) -> DataFrame:
    """
    Generate dim_promo with realistic campaign types, durations and discount ranges.
    """
    # TODO:
    # - share_of_revenue, avg_discount_pct_range, uplift_range_qty, avg_campaign_duration_days nutzen
    return spark.createDataFrame([], T.StructType([]))


def generate_dim_currency(cfg: dict, dim_def: dict) -> DataFrame:
    """
    Generate dim_currency (EUR + einige zusätzliche Währungen).
    """
    return spark.createDataFrame([], T.StructType([]))


def generate_dim_account(cfg: dict, dim_def: dict) -> DataFrame:
    """
    Generate dim_account – simplified chart of accounts for P&L/BS.
    """
    return spark.createDataFrame([], T.StructType([]))


def generate_dim_esg_site(cfg: dict, dim_def: dict, dim_org: DataFrame) -> DataFrame:
    """
    Map selected org nodes (Stores, DCs, Offices) to ESG sites.
    """
    return spark.createDataFrame([], T.StructType([]))


# COMMAND ----------
# Generator: fact_sales (Kern-Backbone)

def generate_fact_sales(cfg: dict,
                        fact_def: dict,
                        dim_date: DataFrame,
                        dim_org: DataFrame,
                        dim_product: DataFrame,
                        dim_customer: DataFrame,
                        dim_promo: DataFrame) -> DataFrame:
    """
    Generate fact_sales according to config:
    - Seasonality (month_index, weekday_index)
    - Channel mix
    - Category GM% ranges
    - Promotion uplift and discounts
    Grain: 1 row = invoice line.
    """
    facts_start = cfg["time"]["facts_start"]
    facts_end = cfg["time"]["facts_end"]

    # TODO:
    # - Datumsrange facts_start..facts_end filtern in dim_date
    # - Stores aus dim_org (OrgType=Store) holen
    # - base_daily_sales_per_store_eur_range als Ausgang
    # - Seasonality * Channel-Mix * Zufall verwenden
    # - Product-Zuordnung mit Category/GM%-Band
    # - Promo-Anteil share_of_revenue implementieren
    # - Net/Gross/Discount/COGS konsistent berechnen

    # Placeholder: leeres DF mit Schema aus Contract
    schema_fields = []
    for col in fact_def["columns"]:
        name = col["name"]
        typ = col["type"]
        if typ in ("int", "number"):
            dt = T.IntegerType()
        elif typ == "date":
            dt = T.DateType()
        elif typ in ("currency", "float"):
            dt = T.DoubleType()
        elif typ == "bool":
            dt = T.BooleanType()
        else:
            dt = T.StringType()
        schema_fields.append(T.StructField(name, dt, True))
    schema = T.StructType(schema_fields)
    df = spark.createDataFrame([], schema)

    return df


# COMMAND ----------
# Generator: weitere Facts (Skeleton)

def generate_fact_inventory_snapshot(cfg, fact_def, dim_date, dim_org, dim_product, fact_sales) -> DataFrame:
    """
    Generate daily store-product inventory snapshots with target DIO and coverage.
    """
    # TODO: ableiten aus Sales + config.inventory (target_dio_range, coverage days)
    return spark.createDataFrame([], T.StructType([]))


def generate_fact_working_capital(cfg, fact_def, dim_date, dim_org, fact_sales, fact_inventory) -> DataFrame:
    """
    Generate AR/AP/Inventory balances and CCC ranges based on config.working_capital.
    """
    return spark.createDataFrame([], T.StructType([]))


def generate_fact_gl_journal(cfg, fact_def, dim_date, dim_org, dim_account, fact_sales) -> DataFrame:
    """
    Generate GL journal lines from aggregated sales and working capital.
    """
    return spark.createDataFrame([], T.StructType([]))


def generate_fact_customer_interactions(cfg, fact_def, dim_date, dim_org, dim_customer, fact_sales) -> DataFrame:
    """
    Generate funnel events (visits, clicks, add-to-cart, purchases, support).
    """
    return spark.createDataFrame([], T.StructType([]))


def generate_fact_nps(cfg, fact_def, dim_date, dim_org, dim_customer) -> DataFrame:
    """
    Generate NPS responses according to config.nps.score_distribution.
    """
    return spark.createDataFrame([], T.StructType([]))


def generate_fact_esg_emissions(cfg, fact_def, dim_date, dim_esg_site) -> DataFrame:
    """
    Generate ESG emissions based on config.esg intensities.
    """
    return spark.createDataFrame([], T.StructType([]))


def generate_fact_innovation_pipeline(cfg, fact_def, dim_date, dim_org) -> DataFrame:
    """
    Generate innovation project pipeline data.
    """
    return spark.createDataFrame([], T.StructType([]))


# COMMAND ----------
# QA-Checks (Skeleton)

def assert_referential_integrity(df: DataFrame, col: str, dim: DataFrame, dim_key: str, min_ratio: float = 0.999):
    """
    Basic RI check: ratio of matching keys must be >= min_ratio.
    """
    # TODO: implement join + ratio, ansonsten Exception werfen
    pass


def assert_margin_ranges(fact_sales: DataFrame):
    """
    Ensure margin % is within plausible ranges per category.
    """
    # TODO: Category-Join + GM%-Band prüfen
    pass


def run_core_qa(dims: dict, facts: dict):
    """
    Run all QA checks for Core v1 backbone.
    dims: {"dim_date": df, "dim_org": df, ...}
    facts: {"fact_sales": df, ...}
    """
    # TODO: RI dim_* vs facts, Margin-Bänder, DIO/CCC-Bänder etc.
    pass


# COMMAND ----------
# Orchestrierung

# 1) Dims aus Contract holen
dim_date_def = get_dim_def("dim_date")
dim_org_def = get_dim_def("dim_org")
dim_product_def = get_dim_def("dim_product")
dim_customer_def = get_dim_def("dim_customer")
dim_promo_def = get_dim_def("dim_promo")
dim_currency_def = get_dim_def("dim_currency")
dim_account_def = get_dim_def("dim_account")
dim_esg_site_def = get_dim_def("dim_esg_site")

# 2) Dims generieren
dim_date_df = generate_dim_date(config, dim_date_def)
dim_org_df = generate_dim_org(config, dim_org_def)
dim_product_df = generate_dim_product(config, dim_product_def)
dim_customer_df = generate_dim_customer(config, dim_customer_def)
dim_promo_df = generate_dim_promo(config, dim_promo_def)
dim_currency_df = generate_dim_currency(config, dim_currency_def)
dim_account_df = generate_dim_account(config, dim_account_def)
dim_esg_site_df = generate_dim_esg_site(config, dim_esg_site_def, dim_org_df)

dims = {
    "dim_date": dim_date_df,
    "dim_org": dim_org_df,
    "dim_product": dim_product_df,
    "dim_customer": dim_customer_df,
    "dim_promo": dim_promo_df,
    "dim_currency": dim_currency_df,
    "dim_account": dim_account_df,
    "dim_esg_site": dim_esg_site_df,
}

# 3) Facts generieren
fact_sales_def = get_fact_def("fact_sales")
fact_inventory_def = get_fact_def("fact_inventory_snapshot")
fact_wc_def = get_fact_def("fact_working_capital")
fact_gl_def = get_fact_def("fact_gl_journal")
fact_cust_int_def = get_fact_def("fact_customer_interactions")
fact_nps_def = get_fact_def("fact_nps")
fact_esg_def = get_fact_def("fact_esg_emissions")
fact_inn_def = get_fact_def("fact_innovation_pipeline")

fact_sales_df = generate_fact_sales(
    config,
    fact_sales_def,
    dim_date_df,
    dim_org_df,
    dim_product_df,
    dim_customer_df,
    dim_promo_df,
)

fact_inventory_df = generate_fact_inventory_snapshot(
    config, fact_inventory_def, dim_date_df, dim_org_df, dim_product_df, fact_sales_df
)
fact_wc_df = generate_fact_working_capital(
    config, fact_wc_def, dim_date_df, dim_org_df, fact_sales_df, fact_inventory_df
)
fact_gl_df = generate_fact_gl_journal(
    config, fact_gl_def, dim_date_df, dim_org_df, dim_account_df, fact_sales_df
)
fact_cust_int_df = generate_fact_customer_interactions(
    config, fact_cust_int_def, dim_date_df, dim_org_df, dim_customer_df, fact_sales_df
)
fact_nps_df = generate_fact_nps(
    config, fact_nps_def, dim_date_df, dim_org_df, dim_customer_df
)
fact_esg_df = generate_fact_esg_emissions(
    config, fact_esg_def, dim_date_df, dim_esg_site_df
)
fact_inn_df = generate_fact_innovation_pipeline(
    config, fact_inn_def, dim_date_df, dim_org_df
)

facts = {
    "fact_sales": fact_sales_df,
    "fact_inventory_snapshot": fact_inventory_df,
    "fact_working_capital": fact_wc_df,
    "fact_gl_journal": fact_gl_df,
    "fact_customer_interactions": fact_cust_int_df,
    "fact_nps": fact_nps_df,
    "fact_esg_emissions": fact_esg_df,
    "fact_innovation_pipeline": fact_inn_df,
}

# COMMAND ----------
# QA ausführen

run_core_qa(dims, facts)

# COMMAND ----------
# Schreiben ins Lakehouse (wenn Lakehouse vorhanden ist)

def write_table(df: DataFrame, table_name: str, mode: str = "overwrite"):
    """
    Write DataFrame to Delta table in the target Lakehouse.
    """
    # TODO: sicherstellen, dass Lakehouse und Schema existieren
    # z. B.: df.write.format("delta").mode(mode).saveAsTable(table_name)
    pass


# TODO: hier später mapping von dims/facts auf config.lakehouse.tables verwenden
# Beispiel:
# write_table(dim_date_df, config["lakehouse"]["tables"]["dim_date"])
# write_table(fact_sales_df, config["lakehouse"]["tables"]["fact_sales"])
