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
    fiscal_year_start_month = 4  # April fiscal year start for Aurora Group

    # Generate date range using Spark sequence
    df = spark.sql(f"""
        SELECT explode(sequence(
            to_date('{start}'), to_date('{end}'), interval 1 day
        )) AS date
    """)

    df = (
        df
        .withColumn("DateKey", F.date_format("date", "yyyyMMdd").cast(T.IntegerType()))
        .withColumn("CalendarYear", F.year("date"))
        .withColumn("CalendarQuarter", F.quarter("date"))
        .withColumn("CalendarMonth", F.month("date"))
        .withColumn("CalendarWeek", F.weekofyear("date"))
        .withColumn("DayOfWeek", F.dayofweek("date"))  # 1=Sun in Spark
        .withColumn("DayName", F.date_format("date", "EEEE"))
        .withColumn("IsWeekend", F.when(F.dayofweek("date").isin(1, 7), 1).otherwise(0))
        .withColumn("FiscalYear",
            F.when(F.month("date") >= fiscal_year_start_month, F.year("date"))
             .otherwise(F.year("date") - 1))
        .withColumn("FiscalQuarter",
            ((F.month("date") - fiscal_year_start_month + 12) % 12 / 3).cast(T.IntegerType()) + 1)
        .withColumn("FiscalMonth",
            ((F.month("date") - fiscal_year_start_month + 12) % 12).cast(T.IntegerType()) + 1)
    )

    return df


# COMMAND ----------
# Generator: dim_org

def generate_dim_org(cfg: dict, dim_def: dict) -> DataFrame:
    """
    Generate dim_org from config.org definitions (regions, countries, store_count, dc_count).
    Grain: org_node (Group, Region, Country, Store, DC).
    """
    currency_map = {
        "DE": "EUR", "AT": "EUR", "NL": "EUR", "BE": "EUR", "LU": "EUR",
        "ES": "EUR", "IT": "EUR", "PT": "EUR",
        "CH": "CHF", "SE": "SEK", "NO": "NOK", "DK": "DKK",
        "PL": "PLN", "CZ": "CZK", "HU": "HUF",
    }
    rows = []
    org_key = 1

    # Group node
    rows.append((org_key, "AURORA-GROUP", "Aurora Group SE", 1, "Group",
                  None, None, None, "EUR", 1))
    group_key = org_key
    org_key += 1

    for region_cfg in cfg["org"]["regions"]:
        region_id = region_cfg["id"]
        region_key = org_key
        rows.append((region_key, f"RGN-{region_id}", f"Region {region_id}", 2, "Region",
                      group_key, region_id, None, "EUR", 1))
        org_key += 1

        countries = region_cfg["countries"]
        stores_per_country = region_cfg["store_count"] // len(countries)

        for country in countries:
            country_key = org_key
            currency = currency_map.get(country, "EUR")
            rows.append((country_key, f"CTRY-{country}", f"Country {country}", 3, "Country",
                          region_key, region_id, country, currency, 1))
            org_key += 1

            for si in range(stores_per_country):
                rows.append((org_key, f"STORE-{country}-{si+1:03d}", f"Store {country} {si+1}",
                              4, "Store", country_key, region_id, country, currency, 1))
                org_key += 1

            for di in range(region_cfg["dc_count"]):
                rows.append((org_key, f"DC-{country}-{di+1:02d}", f"DC {country} {di+1}",
                              4, "DC", country_key, region_id, country, currency, 1))
                org_key += 1

    schema = T.StructType([
        T.StructField("OrgKey", T.IntegerType()),
        T.StructField("OrgCode", T.StringType()),
        T.StructField("OrgName", T.StringType()),
        T.StructField("OrgLevel", T.IntegerType()),
        T.StructField("OrgType", T.StringType()),
        T.StructField("ParentOrgKey", T.IntegerType()),
        T.StructField("Region", T.StringType()),
        T.StructField("CountryCode", T.StringType()),
        T.StructField("CurrencyCode", T.StringType()),
        T.StructField("IsActive", T.IntegerType()),
    ])
    return spark.createDataFrame(rows, schema)


# COMMAND ----------
# Generator: dim_product

def generate_dim_product(cfg: dict, dim_def: dict) -> DataFrame:
    """
    Generate dim_product based on config.products (categories, product_count, margin ranges).
    Grain: product.
    """
    min_price = cfg["products"]["price_points"]["min_list_price"]
    max_price = cfg["products"]["price_points"]["max_list_price"]
    lifecycle_choices = ["Active", "Active", "Active", "EOL"]  # 75% active

    rows = []
    product_key = 1

    for cat_cfg in cfg["products"]["categories"]:
        category = cat_cfg["name"]
        count = cat_cfg["product_count"]
        gm_lo, gm_hi = cat_cfg["gross_margin_range"]
        subcategories = [f"{category} Basic", f"{category} Premium"]

        # Dieselbe Ganzzahldivision hat in generate_gold_layer_contract_v2.py vier Produkte
        # verschluckt und ProductKey 4999 zur Waise gemacht. Hier geht sie heute auf (zwei
        # Subkategorien, gerade Stueckzahlen) — der Rest wird trotzdem verteilt, damit die
        # Falle nicht auf die naechste ungerade Konfiguration wartet.
        je_subcat, rest = divmod(count, len(subcategories))

        for sub_idx, subcat in enumerate(subcategories):
            for _ in range(je_subcat + (rest if sub_idx == len(subcategories) - 1 else 0)):
                if category == "Consumer Electronics":
                    list_price = random.uniform(max_price * 0.3, max_price)
                elif category == "Home & Living":
                    list_price = random.uniform(min_price * 2, max_price * 0.5)
                else:
                    list_price = random.uniform(min_price, max_price * 0.4)
                target_margin = random.uniform(gm_lo, gm_hi)
                standard_cost = list_price * (1 - target_margin)
                rows.append((
                    product_key,
                    f"PRD-{category[:3].upper()}-{product_key:05d}",
                    f"{subcat} {product_key}",
                    category, subcat, f"{category} Brand",
                    round(list_price, 2), round(standard_cost, 2),
                    round(target_margin * 100, 1),
                    random.choice(lifecycle_choices), 1,
                ))
                product_key += 1

    schema = T.StructType([
        T.StructField("ProductKey", T.IntegerType()),
        T.StructField("ProductCode", T.StringType()),
        T.StructField("ProductName", T.StringType()),
        T.StructField("Category", T.StringType()),
        T.StructField("Subcategory", T.StringType()),
        T.StructField("Brand", T.StringType()),
        T.StructField("ListPriceAmount", T.DoubleType()),
        T.StructField("StandardCostAmount", T.DoubleType()),
        T.StructField("TargetMarginPct", T.DoubleType()),
        T.StructField("LifecycleStatus", T.StringType()),
        T.StructField("IsActive", T.IntegerType()),
    ])
    return spark.createDataFrame(rows, schema)


# COMMAND ----------
# Generator: dim_customer, dim_promo, dim_currency, dim_account, dim_esg_site

def generate_dim_customer(cfg: dict, dim_def: dict) -> DataFrame:
    """
    Generate dim_customer with synthetic segments, channel preferences and tenure buckets.
    PII-free.
    """
    total = cfg["customers"]["total_customers"]
    segment_shares = cfg["customers"]["segment_shares"]
    channels = ["Store", "ECom", "Mixed"]

    rows = []
    customer_key = 1
    for segment, share in segment_shares.items():
        count = int(total * share)
        for _ in range(count):
            rows.append((
                customer_key,
                f"CUST-{customer_key:08d}",
                segment,
                random.choice(channels),
                random.randint(1, 15),
                1,
            ))
            customer_key += 1

    schema = T.StructType([
        T.StructField("CustomerKey", T.IntegerType()),
        T.StructField("CustomerCode", T.StringType()),
        T.StructField("Segment", T.StringType()),
        T.StructField("ChannelPreference", T.StringType()),
        T.StructField("TenureYears", T.IntegerType()),
        T.StructField("IsActive", T.IntegerType()),
    ])
    return spark.createDataFrame(rows, schema)


def generate_dim_promo(cfg: dict, dim_def: dict) -> DataFrame:
    """
    Generate dim_promo with realistic campaign types, durations and discount ranges.
    """
    promo_cfg = cfg["promotions"]
    discount_lo, discount_hi = promo_cfg["avg_discount_pct_range"]
    uplift_lo, uplift_hi = promo_cfg["uplift_range_qty"]
    avg_duration = promo_cfg["avg_campaign_duration_days"]
    campaign_types = ["Seasonal", "Clearance", "Flash", "Loyalty", "Bundle"]

    rows = []
    for pk in range(1, 101):  # 100 promo campaigns
        discount = round(random.uniform(discount_lo, discount_hi) * 100, 1)
        uplift = round(random.uniform(uplift_lo, uplift_hi) * 100, 1)
        duration = random.randint(max(1, avg_duration - 7), avg_duration + 7)
        rows.append((
            pk, f"PROMO-{pk:04d}",
            random.choice(campaign_types),
            discount, uplift, duration, 1,
        ))

    schema = T.StructType([
        T.StructField("PromoKey", T.IntegerType()),
        T.StructField("PromoCode", T.StringType()),
        T.StructField("CampaignType", T.StringType()),
        T.StructField("DiscountPct", T.DoubleType()),
        T.StructField("UpliftPct", T.DoubleType()),
        T.StructField("DurationDays", T.IntegerType()),
        T.StructField("IsActive", T.IntegerType()),
    ])
    return spark.createDataFrame(rows, schema)


def generate_dim_currency(cfg: dict, dim_def: dict) -> DataFrame:
    """
    Generate dim_currency (EUR + regional currencies).
    """
    rows = [
        (1, "EUR", "Euro", 1.0),
        (2, "CHF", "Swiss Franc", 0.95),
        (3, "SEK", "Swedish Krona", 0.09),
        (4, "GBP", "British Pound", 1.17),
        (5, "NOK", "Norwegian Krone", 0.09),
        (6, "DKK", "Danish Krone", 0.13),
        (7, "PLN", "Polish Zloty", 0.22),
        (8, "CZK", "Czech Koruna", 0.04),
        (9, "HUF", "Hungarian Forint", 0.0025),
    ]
    schema = T.StructType([
        T.StructField("CurrencyKey", T.IntegerType()),
        T.StructField("CurrencyCode", T.StringType()),
        T.StructField("CurrencyName", T.StringType()),
        T.StructField("ExchangeRateToGroup", T.DoubleType()),
    ])
    return spark.createDataFrame(rows, schema)


def generate_dim_account(cfg: dict, dim_def: dict) -> DataFrame:
    """
    Generate dim_account — simplified chart of accounts for P&L/BS.
    """
    accounts = [
        (1, "4000", "Revenue", "P&L", "Revenue", "Credit"),
        (2, "5000", "COGS", "P&L", "Cost of Sales", "Debit"),
        (3, "6000", "Operating Expenses", "P&L", "OpEx", "Debit"),
        (4, "6100", "Personnel Costs", "P&L", "OpEx", "Debit"),
        (5, "6200", "Depreciation", "P&L", "OpEx", "Debit"),
        (6, "1100", "Accounts Receivable", "BS", "Current Assets", "Debit"),
        (7, "1200", "Inventory", "BS", "Current Assets", "Debit"),
        (8, "1300", "Cash", "BS", "Current Assets", "Debit"),
        (9, "2100", "Accounts Payable", "BS", "Current Liabilities", "Credit"),
        (10, "3000", "Equity", "BS", "Equity", "Credit"),
    ]
    schema = T.StructType([
        T.StructField("AccountKey", T.IntegerType()),
        T.StructField("AccountCode", T.StringType()),
        T.StructField("AccountName", T.StringType()),
        T.StructField("StatementType", T.StringType()),
        T.StructField("AccountGroup", T.StringType()),
        T.StructField("NormalBalance", T.StringType()),
    ])
    return spark.createDataFrame(accounts, schema)


def generate_dim_esg_site(cfg: dict, dim_def: dict, dim_org: DataFrame) -> DataFrame:
    """
    Map selected org nodes (Stores, DCs) to ESG sites with area and energy data.
    """
    esg_cfg = cfg.get("esg", {})
    energy_lo, energy_hi = esg_cfg.get("energy_intensity_kwh_per_m2_range", [50, 350])

    # Filter org to physical sites (Stores and DCs)
    sites = dim_org.filter(F.col("OrgType").isin("Store", "DC"))
    df = (
        sites
        .withColumn("SiteKey", F.monotonically_increasing_id().cast(T.IntegerType()) + 1)
        .withColumn("SiteArea_m2",
            F.when(F.col("OrgType") == "Store", F.lit(random.randint(500, 3000)))
             .otherwise(F.lit(random.randint(5000, 20000))))
        .withColumn("EnergyIntensity_kWh_m2",
            F.round(F.rand() * (energy_hi - energy_lo) + energy_lo, 2))
        .select("SiteKey", "OrgKey", "OrgCode", "OrgType", "CountryCode",
                "SiteArea_m2", "EnergyIntensity_kWh_m2")
    )
    return df


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
    Generate fact_sales with seasonality, channel mix, and margin bands.
    Grain: 1 row = invoice line.
    """
    facts_start = cfg["time"]["facts_start"]
    facts_end = cfg["time"]["facts_end"]
    base_lo, base_hi = cfg["sales_generation"]["base_daily_sales_per_store_eur_range"]
    volatility = cfg["sales_generation"]["volatility_std_pct"]
    month_index = cfg["seasonality"]["month_index"]

    # Filter dates to fact period and sample every 7th day to control volume
    fact_dates = (
        dim_date
        .filter((F.col("date") >= facts_start) & (F.col("date") <= facts_end))
        .withColumn("row_num", F.row_number().over(
            __import__("pyspark.sql", fromlist=["Window"]).Window.orderBy("DateKey")))
        .filter(F.col("row_num") % 7 == 1)
        .drop("row_num")
    )
    stores = dim_org.filter(F.col("OrgType") == "Store").select("OrgKey", "CountryCode")

    # Cross join dates x stores, then explode into ~50 transactions per store-day
    base = fact_dates.crossJoin(stores)
    # Add month seasonality factor
    month_rows = [(str(k).zfill(2), float(v)) for k, v in month_index.items()]
    month_df = spark.createDataFrame(month_rows, ["mm", "seasonality"])
    base = (
        base
        .withColumn("mm", F.date_format("date", "MM"))
        .join(F.broadcast(month_df), "mm", "left")
        .withColumn("num_txn", (F.rand() * 40 + 30).cast(T.IntegerType()))  # 30-70
        .withColumn("txn_array", F.expr("sequence(1, num_txn)"))
        .select("*", F.explode("txn_array").alias("txn_idx"))
    )

    # Assign random product and customer keys
    product_keys = dim_product.select("ProductKey", "ListPriceAmount", "StandardCostAmount")
    customer_keys = dim_customer.select("CustomerKey")
    total_products = dim_product.count()
    total_customers = dim_customer.count()

    df = (
        base
        .withColumn("TransactionKey", F.monotonically_increasing_id() + 1)
        .withColumn("_prod_idx", (F.rand() * total_products).cast(T.IntegerType()) + 1)
        .withColumn("_cust_idx", (F.rand() * total_customers).cast(T.IntegerType()) + 1)
        .withColumn("Quantity", (F.rand() * 4 + 1).cast(T.IntegerType()))
        .withColumn("DiscountPct", F.round(F.rand() * 0.15, 4))
    )

    # Join product for pricing
    product_indexed = product_keys.withColumn("_prod_idx",
        F.row_number().over(F.Window.orderBy("ProductKey")))
    df = df.join(F.broadcast(product_indexed), "_prod_idx", "left")

    df = (
        df
        .withColumn("UnitPrice", F.round(F.col("ListPriceAmount") * (1 - F.col("DiscountPct")), 2))
        .withColumn("UnitCost", F.col("StandardCostAmount"))
        .withColumn("SalesAmount", F.round(F.col("Quantity") * F.col("UnitPrice"), 2))
        .withColumn("CostAmount", F.round(F.col("Quantity") * F.col("UnitCost"), 2))
        .withColumn("MarginAmount", F.round(F.col("SalesAmount") - F.col("CostAmount"), 2))
        .withColumn("MarginPct",
            F.when(F.col("SalesAmount") > 0,
                   F.round(F.col("MarginAmount") / F.col("SalesAmount") * 100, 2))
             .otherwise(0))
        .withColumn("FiscalYear", F.col("FiscalYear"))
        .withColumn("FiscalMonth", F.col("FiscalMonth"))
        .select("TransactionKey", "DateKey", "OrgKey", "ProductKey", "_cust_idx",
                "Quantity", "UnitPrice", "UnitCost", "SalesAmount", "CostAmount",
                "MarginAmount", "MarginPct", "FiscalYear", "FiscalMonth")
        .withColumnRenamed("_cust_idx", "CustomerKey")
    )
    return df


# COMMAND ----------
# Generator: other facts (skeletons)

def generate_fact_inventory_snapshot(cfg, fact_def, dim_date, dim_org, dim_product, fact_sales) -> DataFrame:
    """
    Generate monthly inventory snapshots per DC x product.
    Grain: 1 row = product x DC x month-end date.
    """
    inv_cfg = cfg["inventory"]
    dio_lo, dio_hi = inv_cfg["target_dio_range"]

    # Month-end dates in fact period
    facts_start, facts_end = cfg["time"]["facts_start"], cfg["time"]["facts_end"]
    month_ends = (
        dim_date
        .filter((F.col("date") >= facts_start) & (F.col("date") <= facts_end))
        .groupBy("CalendarYear", "CalendarMonth", "FiscalYear", "FiscalMonth")
        .agg(F.max("DateKey").alias("DateKey"))
    )
    dcs = dim_org.filter(F.col("OrgType") == "DC").select("OrgKey")
    products = dim_product.select("ProductKey", "StandardCostAmount")

    base = month_ends.crossJoin(dcs).crossJoin(F.broadcast(products))
    df = (
        base
        .withColumn("SnapshotKey", F.monotonically_increasing_id() + 1)
        .withColumn("OnHandQty", (F.rand() * 1000).cast(T.IntegerType()))
        .withColumn("ReservedQty",
            (F.col("OnHandQty") * F.rand() * 0.3).cast(T.IntegerType()))
        .withColumn("AvailableQty", F.col("OnHandQty") - F.col("ReservedQty"))
        .withColumn("InventoryValue",
            F.round(F.col("OnHandQty") * F.col("StandardCostAmount"), 2))
        .select("SnapshotKey", "DateKey", "OrgKey", "ProductKey",
                "OnHandQty", "ReservedQty", "AvailableQty",
                "StandardCostAmount", "InventoryValue",
                "FiscalYear", "FiscalMonth")
    )
    return df


def generate_fact_working_capital(cfg, fact_def, dim_date, dim_org, fact_sales, fact_inventory) -> DataFrame:
    """
    Generate monthly AR/AP/Inventory balances per org.
    Grain: 1 row = org x month.
    """
    wc_cfg = cfg["working_capital"]
    ar_lo, ar_hi = wc_cfg["ar_days_range"]
    ap_lo, ap_hi = wc_cfg["ap_days_range"]

    facts_start, facts_end = cfg["time"]["facts_start"], cfg["time"]["facts_end"]
    month_ends = (
        dim_date
        .filter((F.col("date") >= facts_start) & (F.col("date") <= facts_end))
        .groupBy("CalendarYear", "CalendarMonth", "FiscalYear", "FiscalMonth")
        .agg(F.max("DateKey").alias("DateKey"))
    )
    countries = dim_org.filter(F.col("OrgType") == "Country").select("OrgKey")

    base = month_ends.crossJoin(countries)
    df = (
        base
        .withColumn("WCKey", F.monotonically_increasing_id() + 1)
        .withColumn("AR_Amount", F.round(F.rand() * 5000000 + 500000, 2))
        .withColumn("AP_Amount", F.round(F.rand() * 4000000 + 400000, 2))
        .withColumn("Inventory_Amount", F.round(F.rand() * 8000000 + 1000000, 2))
        .withColumn("AR_Days", (F.rand() * (ar_hi - ar_lo) + ar_lo).cast(T.IntegerType()))
        .withColumn("AP_Days", (F.rand() * (ap_hi - ap_lo) + ap_lo).cast(T.IntegerType()))
        .withColumn("DIO_Days", (F.rand() * 30 + 45).cast(T.IntegerType()))
        .withColumn("CCC_Days", F.col("AR_Days") + F.col("DIO_Days") - F.col("AP_Days"))
        .select("WCKey", "DateKey", "OrgKey",
                "AR_Amount", "AP_Amount", "Inventory_Amount",
                "AR_Days", "AP_Days", "DIO_Days", "CCC_Days",
                "FiscalYear", "FiscalMonth")
    )
    return df


def generate_fact_gl_journal(cfg, fact_def, dim_date, dim_org, dim_account, fact_sales) -> DataFrame:
    """
    Generate GL journal lines from aggregated monthly sales.
    Grain: 1 row = journal line (account x org x month).
    """
    # Aggregate sales by org and month
    monthly = (
        fact_sales
        .groupBy("OrgKey", "FiscalYear", "FiscalMonth")
        .agg(
            F.sum("SalesAmount").alias("Revenue"),
            F.sum("CostAmount").alias("COGS"),
            F.max("DateKey").alias("DateKey"),
        )
    )

    # Revenue line (account 4000) and COGS line (account 5000)
    revenue = (
        monthly
        .withColumn("AccountKey", F.lit(1))  # Revenue
        .withColumn("DebitAmount", F.lit(0.0))
        .withColumn("CreditAmount", F.col("Revenue"))
        .select("DateKey", "OrgKey", "AccountKey", "DebitAmount", "CreditAmount",
                "FiscalYear", "FiscalMonth")
    )
    cogs = (
        monthly
        .withColumn("AccountKey", F.lit(2))  # COGS
        .withColumn("DebitAmount", F.col("COGS"))
        .withColumn("CreditAmount", F.lit(0.0))
        .select("DateKey", "OrgKey", "AccountKey", "DebitAmount", "CreditAmount",
                "FiscalYear", "FiscalMonth")
    )
    df = (
        revenue.unionByName(cogs)
        .withColumn("JournalKey", F.monotonically_increasing_id() + 1)
    )
    return df


def generate_fact_customer_interactions(cfg, fact_def, dim_date, dim_org, dim_customer, fact_sales) -> DataFrame:
    """
    Generate customer funnel events: visit, click, add_to_cart, purchase, support.
    Grain: 1 row = interaction event.
    """
    facts_start, facts_end = cfg["time"]["facts_start"], cfg["time"]["facts_end"]
    event_types = ["visit", "click", "add_to_cart", "purchase", "support_ticket"]
    event_weights = [0.40, 0.25, 0.15, 0.15, 0.05]

    # Sample dates (weekly)
    dates = (
        dim_date
        .filter((F.col("date") >= facts_start) & (F.col("date") <= facts_end))
        .filter(F.col("DayOfWeek") == 2)  # Mondays
        .select("DateKey")
    )
    stores = dim_org.filter(F.col("OrgType") == "Store").select("OrgKey")
    total_customers = dim_customer.count()

    # Create event type reference
    evt_rows = [(i + 1, e, w) for i, (e, w) in enumerate(zip(event_types, event_weights))]
    evt_df = spark.createDataFrame(evt_rows, ["evt_idx", "EventType", "weight"])

    base = dates.crossJoin(stores).crossJoin(evt_df)
    df = (
        base
        .withColumn("EventCount", (F.col("weight") * F.rand() * 200 + 10).cast(T.IntegerType()))
        .withColumn("InteractionKey", F.monotonically_increasing_id() + 1)
        .withColumn("CustomerKey", (F.rand() * total_customers + 1).cast(T.IntegerType()))
        .select("InteractionKey", "DateKey", "OrgKey", "CustomerKey",
                "EventType", "EventCount")
    )
    return df


def generate_fact_nps(cfg, fact_def, dim_date, dim_org, dim_customer) -> DataFrame:
    """
    Generate NPS responses according to config.nps.score_distribution.
    Grain: 1 row = NPS survey response.
    """
    nps_dist = cfg["nps"]["score_distribution"]
    facts_start, facts_end = cfg["time"]["facts_start"], cfg["time"]["facts_end"]
    total_customers = dim_customer.count()

    # Quarterly survey dates
    dates = (
        dim_date
        .filter((F.col("date") >= facts_start) & (F.col("date") <= facts_end))
        .filter((F.col("CalendarMonth").isin(3, 6, 9, 12)) & (F.col("DayOfWeek") == 2))
        .groupBy("CalendarYear", "CalendarQuarter")
        .agg(F.first("DateKey").alias("DateKey"))
    )
    stores = dim_org.filter(F.col("OrgType") == "Store").select("OrgKey")

    # ~20 responses per store per quarter
    base = dates.crossJoin(stores)
    base = (
        base
        .withColumn("resp_array", F.expr("sequence(1, 20)"))
        .select("*", F.explode("resp_array").alias("resp_idx"))
    )

    # Assign NPS category and score based on distribution
    promoter_threshold = nps_dist["promoter"]
    passive_threshold = promoter_threshold + nps_dist["passive"]

    df = (
        base
        .withColumn("NPSKey", F.monotonically_increasing_id() + 1)
        .withColumn("CustomerKey", (F.rand() * total_customers + 1).cast(T.IntegerType()))
        .withColumn("_r", F.rand())
        .withColumn("NPSScore",
            F.when(F.col("_r") < promoter_threshold, (F.rand() * 2 + 9).cast(T.IntegerType()))  # 9-10
             .when(F.col("_r") < passive_threshold, (F.rand() * 2 + 7).cast(T.IntegerType()))   # 7-8
             .otherwise((F.rand() * 7).cast(T.IntegerType())))  # 0-6
        .withColumn("NPSCategory",
            F.when(F.col("NPSScore") >= 9, "Promoter")
             .when(F.col("NPSScore") >= 7, "Passive")
             .otherwise("Detractor"))
        .select("NPSKey", "DateKey", "OrgKey", "CustomerKey", "NPSScore", "NPSCategory")
    )
    return df


def generate_fact_esg_emissions(cfg, fact_def, dim_date, dim_esg_site) -> DataFrame:
    """
    Generate monthly ESG emissions per site.
    Grain: 1 row = site x month.
    """
    esg_cfg = cfg.get("esg", {})
    intensity_lo, intensity_hi = esg_cfg.get("emission_intensity_kg_per_eur_range", [0.20, 1.50])
    facts_start, facts_end = cfg["time"]["facts_start"], cfg["time"]["facts_end"]

    # Monthly periods
    from pyspark.sql import Window
    month_ends = (
        spark.sql(f"""
            SELECT explode(sequence(
                to_date('{facts_start}'), to_date('{facts_end}'), interval 1 month
            )) AS month_date
        """)
        .withColumn("DateKey", F.date_format("month_date", "yyyyMMdd").cast(T.IntegerType()))
        .withColumn("FiscalYear", F.year("month_date"))
        .withColumn("FiscalMonth", F.month("month_date"))
    )

    base = month_ends.crossJoin(dim_esg_site)
    df = (
        base
        .withColumn("ESGKey", F.monotonically_increasing_id() + 1)
        .withColumn("EmissionIntensity_kgCO2e",
            F.round(F.rand() * (intensity_hi - intensity_lo) + intensity_lo, 4))
        .withColumn("EnergyConsumption_kWh",
            F.round(F.col("SiteArea_m2") * F.col("EnergyIntensity_kWh_m2") / 12, 2))
        .withColumn("CO2e_tonnes",
            F.round(F.col("EnergyConsumption_kWh") * F.col("EmissionIntensity_kgCO2e") / 1000, 2))
        .select("ESGKey", "DateKey", "SiteKey", "OrgKey",
                "EnergyConsumption_kWh", "EmissionIntensity_kgCO2e", "CO2e_tonnes",
                "FiscalYear", "FiscalMonth")
    )
    return df


def generate_fact_innovation_pipeline(cfg, fact_def, dim_date, dim_org) -> DataFrame:
    """
    Generate innovation project pipeline data.
    Grain: 1 row = project x quarter snapshot.
    """
    inn_cfg = cfg.get("innovation", {})
    project_lo, project_hi = inn_cfg.get("active_projects_range", [20, 80])
    dur_lo, dur_hi = inn_cfg.get("avg_project_duration_months_range", [6, 24])
    facts_start, facts_end = cfg["time"]["facts_start"], cfg["time"]["facts_end"]

    num_projects = random.randint(project_lo, project_hi)
    stages = ["Ideation", "Feasibility", "Development", "Pilot", "Scaled"]
    regions = dim_org.filter(F.col("OrgType") == "Region").select("OrgKey").collect()
    region_keys = [r["OrgKey"] for r in regions] if regions else [1]

    rows = []
    pk = 1
    for proj_id in range(1, num_projects + 1):
        duration = random.randint(dur_lo, dur_hi)
        stage = random.choice(stages)
        budget = round(random.uniform(50000, 2000000), 2)
        spent_pct = random.uniform(0.1, 0.95)
        org_key = random.choice(region_keys)
        rows.append((
            pk, proj_id, f"INNOV-{proj_id:04d}", stage,
            duration, budget, round(budget * spent_pct, 2),
            round(spent_pct * 100, 1), org_key,
        ))
        pk += 1

    schema = T.StructType([
        T.StructField("PipelineKey", T.IntegerType()),
        T.StructField("ProjectID", T.IntegerType()),
        T.StructField("ProjectCode", T.StringType()),
        T.StructField("Stage", T.StringType()),
        T.StructField("DurationMonths", T.IntegerType()),
        T.StructField("BudgetAmount", T.DoubleType()),
        T.StructField("SpentAmount", T.DoubleType()),
        T.StructField("SpentPct", T.DoubleType()),
        T.StructField("OrgKey", T.IntegerType()),
    ])
    return spark.createDataFrame(rows, schema)


# COMMAND ----------
# QA checks (skeleton)

def assert_referential_integrity(df: DataFrame, col: str, dim: DataFrame, dim_key: str, min_ratio: float = 0.999):
    """
    Basic RI check: ratio of matching keys must be >= min_ratio.
    """
    total = df.select(col).distinct().count()
    if total == 0:
        print(f"    ⚠ RI skip: {col} has no rows")
        return
    matched = df.select(col).distinct().join(dim.select(dim_key), df[col] == dim[dim_key], "inner").count()
    ratio = matched / total if total > 0 else 0
    status = "✓" if ratio >= min_ratio else "✗"
    print(f"    {status} RI {col} → {dim_key}: {matched}/{total} ({ratio:.4f}, min={min_ratio})")
    if ratio < min_ratio:
        raise AssertionError(f"RI failed: {col} → {dim_key}, ratio={ratio:.4f} < {min_ratio}")


def assert_margin_ranges(fact_sales: DataFrame, dim_product: DataFrame):
    """
    Ensure margin % is within plausible ranges (-10% to 80%).
    """
    stats = fact_sales.select(
        F.min("MarginPct").alias("min_margin"),
        F.max("MarginPct").alias("max_margin"),
        F.avg("MarginPct").alias("avg_margin"),
    ).collect()[0]
    print(f"    Margin range: {stats['min_margin']:.1f}% to {stats['max_margin']:.1f}% (avg {stats['avg_margin']:.1f}%)")
    if stats["min_margin"] < -50:
        raise AssertionError(f"Implausible negative margin: {stats['min_margin']:.1f}%")
    if stats["max_margin"] > 95:
        raise AssertionError(f"Implausible high margin: {stats['max_margin']:.1f}%")


def run_core_qa(dims: dict, facts: dict):
    """
    Run all QA checks for Core v1 backbone.
    """
    print("\n  QA Checks:")
    print("  " + "─" * 60)

    # Row counts
    for name, df in {**dims, **facts}.items():
        count = df.count()
        print(f"    {name}: {count:,} rows")

    # Referential integrity: fact_sales keys
    if facts.get("fact_sales") and facts["fact_sales"].count() > 0:
        assert_referential_integrity(facts["fact_sales"], "OrgKey", dims["dim_org"], "OrgKey")
        assert_referential_integrity(facts["fact_sales"], "ProductKey", dims["dim_product"], "ProductKey")
        assert_margin_ranges(facts["fact_sales"], dims["dim_product"])

    print("  " + "─" * 60)
    print("  ✓ QA checks complete")


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
    count = df.count()
    print(f"  Writing {table_name} ({count:,} rows)...")
    df.write.format("delta").mode(mode).saveAsTable(table_name)
    print(f"  ✓ {table_name} written.")


# Write all dims and facts to Lakehouse tables
tables = config.get("lakehouse", {}).get("tables", {})
for name, df in {**dims, **facts}.items():
    table_ref = tables.get(name)
    if table_ref:
        write_table(df, table_ref)
    else:
        print(f"  ⚠ No lakehouse table mapping for '{name}', skipping write.")
