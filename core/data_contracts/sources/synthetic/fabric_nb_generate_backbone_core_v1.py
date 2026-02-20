# COMMAND ----------
# nb_generate_backbone_core_v1
# Synthetic backbone generator for Aurora Group — Core Use Cases v1

# PARAMETERS (set to your paths)
CONFIG_PATH = "/lakehouse/default/Files/docs/data_design/synthetic_config_core_v1.yaml"
CONTRACT_PATH = "/lakehouse/default/Files/docs/data_design/synthetic_data_contract.yaml"
SCOPE_PATH = "/lakehouse/default/Files/docs/data_design/synthetic_data_scope_core_v1.yaml"

RUN_MODE = "core_v1"  # later: "full", "core_v1", "esg_only" etc.

# Open items: see internal/technical_backlog.md § Synthetic Data.
LAKEHOUSE_NAME = "lh_aurora_backbone"  # TODO: create first
SCHEMA = "gold"                        # target schema

# COMMAND ----------
# Imports

import yaml
import random
from datetime import datetime

from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql import types as T

# COMMAND ----------
# Helper: YAML loader

def load_yaml(path: str) -> dict:
    """
    Load YAML file from given path into a Python dict.
    Assumes file is accessible via Lakehouse Files or workspace FS.
    """
    # Variant: Spark Files
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

# Seed for reproducibility
random.seed(config.get("random_seed", 12345))

# COMMAND ----------
# Helper: access to contract definitions

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

    # TODO: Generate date range with Spark
    # - Column DateKey (YYYYMMDD int)
    # - Calendar Year/Month/Quarter
    # - Fiscal Year/Period according to settings.fiscal_year_start
    # - Optional: Weekday, Weekend flag, etc.

    # Placeholder: empty DF with schema from contract
    # Implement logic later
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
    # - Group-level node
    # - Regions
    # - Countries per Region
    # - Stores/DCs per country according to config.org.regions.*.store_count, dc_count
    # - OrgLevel, OrgType, Currency Code per country
    # - Distribute open/close DateKeys plausibly

    # Placeholder schema similar to dim_date
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
    # - For each category create products according to product_count
    # - ProductCode, ProductName, Category, Subcategory, Brand
    # - List Price Amount in range min_list_price..max_list_price
    # - Lifecycle Status (Intro/Growth/Mature/EOL) depending on start date

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
    # - total_customers from cfg.customers.total_customers
    # - Segment distribution from cfg.customers.segment_shares
    # - Channel preference (Store/ECom/Mixed)
    # - Tenure bucket via random distribution

    # Placeholder as above
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
    return spark.createDataFrame([], schema)


def generate_dim_promo(cfg: dict, dim_def: dict) -> DataFrame:
    """
    Generate dim_promo with realistic campaign types, durations and discount ranges.
    """
    # TODO:
    # - Use share_of_revenue, avg_discount_pct_range, uplift_range_qty, avg_campaign_duration_days
    return spark.createDataFrame([], T.StructType([]))


def generate_dim_currency(cfg: dict, dim_def: dict) -> DataFrame:
    """
    Generate dim_currency (EUR + some additional currencies).
    """
    return spark.createDataFrame([], T.StructType([]))


def generate_dim_account(cfg: dict, dim_def: dict) -> DataFrame:
    """
    Generate dim_account — simplified chart of accounts for P&L/BS.
    """
    return spark.createDataFrame([], T.StructType([]))


def generate_dim_esg_site(cfg: dict, dim_def: dict, dim_org: DataFrame) -> DataFrame:
    """
    Map selected org nodes (Stores, DCs, Offices) to ESG sites.
    """
    return spark.createDataFrame([], T.StructType([]))


# COMMAND ----------
# Generator: fact_sales (core backbone)

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
    # - Filter date range facts_start..facts_end in dim_date
    # - Retrieve stores from dim_org (OrgType=Store)
    # - Start from base_daily_sales_per_store_eur_range
    # - Apply seasonality * channel mix * randomness
    # - Assign products with category/GM% band
    # - Implement promo share_of_revenue
    # - Compute Net/Gross/Discount/COGS consistently

    # Placeholder: empty DF with schema from contract
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
# Generator: other facts (skeletons)

def generate_fact_inventory_snapshot(cfg, fact_def, dim_date, dim_org, dim_product, fact_sales) -> DataFrame:
    """
    Generate daily store-product inventory snapshots with target DIO and coverage.
    """
    # TODO: derive from sales + config.inventory (target_dio_range, coverage days)
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
# QA checks (skeleton)

def assert_referential_integrity(df: DataFrame, col: str, dim: DataFrame, dim_key: str, min_ratio: float = 0.999):
    """
    Basic RI check: ratio of matching keys must be >= min_ratio.
    """
    # TODO: implement join + ratio, otherwise raise exception
    pass


def assert_margin_ranges(fact_sales: DataFrame):
    """
    Ensure margin % is within plausible ranges per category.
    """
    # TODO: Category join + GM% band check
    pass


def run_core_qa(dims: dict, facts: dict):
    """
    Run all QA checks for Core v1 backbone.
    dims: {"dim_date": df, "dim_org": df, ...}
    facts: {"fact_sales": df, ...}
    """
    # TODO: RI dim_* vs facts, margin bands, DIO/CCC bands etc.
    pass


# COMMAND ----------
# Orchestration

# 1) Get dim definitions from contract
dim_date_def = get_dim_def("dim_date")
dim_org_def = get_dim_def("dim_org")
dim_product_def = get_dim_def("dim_product")
dim_customer_def = get_dim_def("dim_customer")
dim_promo_def = get_dim_def("dim_promo")
dim_currency_def = get_dim_def("dim_currency")
dim_account_def = get_dim_def("dim_account")
dim_esg_site_def = get_dim_def("dim_esg_site")

# 2) Generate dims
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

# 3) Generate facts
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
# Run QA

run_core_qa(dims, facts)

# COMMAND ----------
# Write to Lakehouse (if Lakehouse exists)

def write_table(df: DataFrame, table_name: str, mode: str = "overwrite"):
    """
    Write DataFrame to Delta table in the target Lakehouse.
    """
    # TODO: ensure Lakehouse and schema exist
    # e.g.: df.write.format("delta").mode(mode).saveAsTable(table_name)
    pass


# TODO: map dims/facts to config.lakehouse.tables later
# Example:
# write_table(dim_date_df, config["lakehouse"]["tables"]["dim_date"])
# write_table(fact_sales_df, config["lakehouse"]["tables"]["fact_sales"])
