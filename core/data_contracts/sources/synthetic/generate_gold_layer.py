"""
Gold Layer Synthetic Data Generator
====================================

Generates synthetic data for Aurora Group showcase following lakehouse architecture:
- Delta Parquet format
- Conformed dimensions (star schema)
- Grain-explicit facts
- Action aggregates
- Partitioned by time (fiscal_year, fiscal_month)

Output Structure:
    showcases/aurora_group/data/gold/
        ├─ dimensions/
        ├─ facts/
        └─ action_aggregates/

Usage:
    python generate_gold_layer.py --config synthetic_config_core_v1.yaml --output ../../showcases/aurora_group/data/gold
"""

import yaml
import random
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple
import argparse

# Check if Delta Lake is available (optional for local dev)
try:
    from deltalake import write_deltalake
    DELTA_AVAILABLE = True
except ImportError:
    DELTA_AVAILABLE = False
    print("Warning: deltalake package not found. Will write Parquet only.")


class GoldLayerGenerator:
    """Generates synthetic gold layer data conforming to lakehouse architecture."""
    
    def __init__(self, config_path: str, output_path: str):
        self.config = self._load_config(config_path)
        self.output_path = Path(output_path)
        self.random_seed = self.config.get("random_seed", 12345)
        
        # Set seeds for reproducibility
        random.seed(self.random_seed)
        np.random.seed(self.random_seed)
        
        # Storage for dimension dataframes (needed for FK relationships)
        self.dimensions = {}
        
    def _load_config(self, path: str) -> dict:
        """Load YAML configuration."""
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def generate_all(self):
        """Generate complete gold layer: dimensions, facts, action aggregates."""
        print("=" * 80)
        print("Gold Layer Synthetic Data Generator - Aurora Group")
        print("=" * 80)
        
        # Phase 1: Generate Conformed Dimensions (no dependencies)
        print("\n[Phase 1] Generating Conformed Dimensions...")
        self._generate_dimensions()
        
        # Phase 2: Generate Facts (depend on dimensions for FK integrity)
        print("\n[Phase 2] Generating Facts...")
        self._generate_facts()
        
        # Phase 3: Generate Action Aggregates (pre-calculated from facts)
        print("\n[Phase 3] Generating Action Aggregates...")
        self._generate_action_aggregates()
        
        print("\n" + "=" * 80)
        print("✓ Gold Layer generation complete!")
        print(f"Output location: {self.output_path.absolute()}")
        print("=" * 80)
    
    # =========================================================================
    # Phase 1: Conformed Dimensions
    # =========================================================================
    
    def _generate_dimensions(self):
        """Generate all conformed dimensions."""
        self.dimensions['dim_time'] = self._generate_dim_time()
        self.dimensions['dim_organization'] = self._generate_dim_organization()
        self.dimensions['dim_product'] = self._generate_dim_product()
        self.dimensions['dim_customer'] = self._generate_dim_customer()
        self.dimensions['dim_currency'] = self._generate_dim_currency()
        
        # Write dimensions to disk
        for dim_name, df in self.dimensions.items():
            self._write_table(df, f"dimensions/{dim_name}", partition_by=None)
    
    def _generate_dim_time(self) -> pd.DataFrame:
        """
        Generate dim_time with calendar and fiscal hierarchies.
        Grain: One row per calendar date.
        """
        print("  → dim_time")
        
        start_date = pd.to_datetime(self.config['time']['dim_date_start'])
        end_date = pd.to_datetime(self.config['time']['dim_date_end'])
        
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        
        df = pd.DataFrame({
            'date_key': dates.strftime('%Y%m%d').astype(int),
            'date': dates,
            'calendar_year': dates.year,
            'calendar_quarter': dates.quarter,
            'calendar_month': dates.month,
            'calendar_week': dates.isocalendar().week,
            'day_of_week': dates.dayofweek + 1,  # 1=Monday
            'day_name': dates.day_name(),
            'is_weekend': dates.dayofweek.isin([5, 6]).astype(int),
            'is_holiday': 0,  # TODO: Add holiday logic if needed (see internal/technical_backlog.md § Synthetic Data).
        })
        
        # Fiscal calendar (assuming fiscal year starts in April for Aurora Group)
        fiscal_year_start_month = 4
        df['fiscal_year'] = df.apply(
            lambda row: row['calendar_year'] if row['calendar_month'] >= fiscal_year_start_month 
            else row['calendar_year'] - 1, 
            axis=1
        )
        df['fiscal_quarter'] = ((df['calendar_month'] - fiscal_year_start_month) % 12 // 3) + 1
        df['fiscal_month'] = ((df['calendar_month'] - fiscal_year_start_month) % 12) + 1
        
        print(f"     {len(df):,} dates generated ({start_date.date()} to {end_date.date()})")
        return df
    
    def _generate_dim_organization(self) -> pd.DataFrame:
        """
        Generate dim_organization with hierarchy: Group → Region → Country → Store/DC.
        Grain: One row per organizational node.
        """
        print("  → dim_organization")
        
        org_nodes = []
        org_key = 1
        
        # Root node: Group
        org_nodes.append({
            'org_key': org_key,
            'org_code': 'AURORA-GROUP',
            'org_name': 'Aurora Group SE',
            'org_level': 1,
            'org_type': 'Group',
            'parent_org_key': None,
            'region': None,
            'country_code': None,
            'currency_code': 'EUR',
            'is_active': 1,
        })
        group_key = org_key
        org_key += 1
        
        # Regions → Countries → Sites
        for region_cfg in self.config['org']['regions']:
            region_id = region_cfg['id']
            
            # Region node
            region_key = org_key
            org_nodes.append({
                'org_key': region_key,
                'org_code': f'RGN-{region_id}',
                'org_name': f'Region {region_id}',
                'org_level': 2,
                'org_type': 'Region',
                'parent_org_key': group_key,
                'region': region_id,
                'country_code': None,
                'currency_code': 'EUR',
                'is_active': 1,
            })
            org_key += 1
            
            # Countries under region
            for country in region_cfg['countries']:
                country_key = org_key
                currency = 'EUR' if country in ['DE', 'AT', 'NL', 'BE', 'LU'] else 'CHF' if country == 'CH' else 'SEK'
                
                org_nodes.append({
                    'org_key': country_key,
                    'org_code': f'CTRY-{country}',
                    'org_name': f'Country {country}',
                    'org_level': 3,
                    'org_type': 'Country',
                    'parent_org_key': region_key,
                    'region': region_id,
                    'country_code': country,
                    'currency_code': currency,
                    'is_active': 1,
                })
                org_key += 1
                
                # Stores under country
                for store_idx in range(region_cfg['store_count'] // len(region_cfg['countries'])):
                    org_nodes.append({
                        'org_key': org_key,
                        'org_code': f'STORE-{country}-{store_idx+1:03d}',
                        'org_name': f'Store {country} {store_idx+1}',
                        'org_level': 4,
                        'org_type': 'Store',
                        'parent_org_key': country_key,
                        'region': region_id,
                        'country_code': country,
                        'currency_code': currency,
                        'is_active': 1,
                    })
                    org_key += 1
                
                # Distribution Centers under country
                for dc_idx in range(region_cfg['dc_count']):
                    org_nodes.append({
                        'org_key': org_key,
                        'org_code': f'DC-{country}-{dc_idx+1:02d}',
                        'org_name': f'Distribution Center {country} {dc_idx+1}',
                        'org_level': 4,
                        'org_type': 'DC',
                        'parent_org_key': country_key,
                        'region': region_id,
                        'country_code': country,
                        'currency_code': currency,
                        'is_active': 1,
                    })
                    org_key += 1
        
        df = pd.DataFrame(org_nodes)
        print(f"     {len(df):,} organization nodes generated")
        return df
    
    def _generate_dim_product(self) -> pd.DataFrame:
        """
        Generate dim_product with category hierarchy and pricing.
        Grain: One row per product.
        """
        print("  → dim_product")
        
        products = []
        product_key = 1
        
        # Get price range from config
        min_price = self.config['products']['price_points']['min_list_price']
        max_price = self.config['products']['price_points']['max_list_price']
        
        for category_cfg in self.config['products']['categories']:
            category = category_cfg['name']
            product_count = category_cfg['product_count']
            margin_range = category_cfg['gross_margin_range']
            
            # Simple subcategories based on category name
            subcategories = [f'{category} Basic', f'{category} Premium']
            
            for subcategory in subcategories:
                for prod_idx in range(product_count // len(subcategories)):
                    # Price within configured range, weighted toward category's typical price
                    if category == 'Consumer Electronics':
                        list_price = random.uniform(max_price * 0.3, max_price)
                    elif category == 'Home & Living':
                        list_price = random.uniform(min_price * 2, max_price * 0.5)
                    else:  # Fashion
                        list_price = random.uniform(min_price, max_price * 0.4)
                    
                    # Cost based on gross margin range
                    target_margin = random.uniform(margin_range[0], margin_range[1])
                    standard_cost = list_price * (1 - target_margin)
                    
                    products.append({
                        'product_key': product_key,
                        'product_code': f'PRD-{category[:3].upper()}-{product_key:05d}',
                        'product_name': f'{subcategory} {prod_idx+1}',
                        'category': category,
                        'subcategory': subcategory,
                        'brand': f'{category} Brand',
                        'list_price': round(list_price, 2),
                        'standard_cost': round(standard_cost, 2),
                        'target_margin_pct': round(target_margin * 100, 1),
                        'lifecycle_status': random.choice(['Active', 'Active', 'Active', 'EOL']),  # 75% active
                        'is_active': 1,
                    })
                    product_key += 1
        
        df = pd.DataFrame(products)
        print(f"     {len(df):,} products generated")
        return df
    
    def _generate_dim_customer(self) -> pd.DataFrame:
        """
        Generate dim_customer with segments and channel preferences.
        Grain: One row per customer (PII-free).
        """
        print("  → dim_customer")
        
        total_customers = self.config['customers']['total_customers']
        segment_shares = self.config['customers']['segment_shares']
        
        customers = []
        customer_key = 1
        
        for segment, share in segment_shares.items():
            count = int(total_customers * share)
            
            for _ in range(count):
                customers.append({
                    'customer_key': customer_key,
                    'customer_code': f'CUST-{customer_key:08d}',
                    'segment': segment,
                    'channel_preference': random.choice(['Store', 'ECom', 'Mixed']),
                    'tenure_years': random.randint(1, 15),
                    'is_active': 1,
                })
                customer_key += 1
        
        df = pd.DataFrame(customers)
        print(f"     {len(df):,} customers generated")
        return df
    
    def _generate_dim_currency(self) -> pd.DataFrame:
        """
        Generate dim_currency with exchange rates.
        Grain: One row per currency.
        """
        print("  → dim_currency")
        
        currencies = [
            {'currency_code': 'EUR', 'currency_name': 'Euro', 'exchange_rate_to_group': 1.0},
            {'currency_code': 'CHF', 'currency_name': 'Swiss Franc', 'exchange_rate_to_group': 0.95},
            {'currency_code': 'SEK', 'currency_name': 'Swedish Krona', 'exchange_rate_to_group': 0.09},
            {'currency_code': 'GBP', 'currency_name': 'British Pound', 'exchange_rate_to_group': 1.17},
        ]
        
        df = pd.DataFrame(currencies)
        df['currency_key'] = range(1, len(df) + 1)
        print(f"     {len(df)} currencies generated")
        return df
    
    # =========================================================================
    # Phase 2: Facts
    # =========================================================================
    
    def _generate_facts(self):
        """Generate all fact tables with FK integrity."""
        
        # Get dimension references for FK generation
        dim_time = self.dimensions['dim_time']
        dim_org = self.dimensions['dim_organization']
        dim_product = self.dimensions['dim_product']
        dim_customer = self.dimensions['dim_customer']
        
        # Filter time to facts period
        facts_start = pd.to_datetime(self.config['time']['facts_start'])
        facts_end = pd.to_datetime(self.config['time']['facts_end'])
        fact_dates = dim_time[
            (dim_time['date'] >= facts_start) & (dim_time['date'] <= facts_end)
        ]
        
        # Generate facts
        fact_sales = self._generate_fact_sales(fact_dates, dim_org, dim_product, dim_customer)
        self._write_table(fact_sales, "facts/fact_sales", partition_by=['fiscal_year', 'fiscal_month'])
        
        fact_inventory = self._generate_fact_inventory(fact_dates, dim_org, dim_product)
        self._write_table(fact_inventory, "facts/fact_inventory", partition_by=['fiscal_year', 'fiscal_month'])
    
    def _generate_fact_sales(
        self, 
        fact_dates: pd.DataFrame, 
        dim_org: pd.DataFrame, 
        dim_product: pd.DataFrame,
        dim_customer: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Generate fact_sales at transaction grain.
        Grain: One row per sales transaction.
        """
        print("  → fact_sales")
        
        # Configuration
        transactions_per_day_per_store = 50  # Average
        stores = dim_org[dim_org['org_type'] == 'Store']
        
        total_days = len(fact_dates)
        total_stores = len(stores)
        estimated_rows = total_days * total_stores * transactions_per_day_per_store
        
        print(f"     Generating ~{estimated_rows:,} transactions...")
        
        transactions = []
        transaction_key = 1
        
        # Sample dates (take every 7th day to reduce volume for demo)
        sample_dates = fact_dates.iloc[::7]
        
        for _, date_row in sample_dates.iterrows():
            date_key = date_row['date_key']
            fiscal_year = date_row['fiscal_year']
            fiscal_month = date_row['fiscal_month']
            
            # Each store gets random number of transactions this day
            for _, store_row in stores.iterrows():
                org_key = store_row['org_key']
                num_transactions = random.randint(30, 70)
                
                for _ in range(num_transactions):
                    # Random product and customer
                    product = dim_product.sample(n=1).iloc[0]
                    customer = dim_customer.sample(n=1).iloc[0]
                    
                    # Quantity and pricing
                    quantity = random.randint(1, 5)
                    unit_price = product['list_price'] * random.uniform(0.85, 1.0)  # Discounts
                    unit_cost = product['standard_cost']
                    
                    sales_amount = quantity * unit_price
                    cost_amount = quantity * unit_cost
                    margin_amount = sales_amount - cost_amount
                    
                    transactions.append({
                        'transaction_key': transaction_key,
                        'date_key': date_key,
                        'org_key': org_key,
                        'product_key': product['product_key'],
                        'customer_key': customer['customer_key'],
                        'quantity': quantity,
                        'unit_price': round(unit_price, 2),
                        'unit_cost': round(unit_cost, 2),
                        'sales_amount': round(sales_amount, 2),
                        'cost_amount': round(cost_amount, 2),
                        'margin_amount': round(margin_amount, 2),
                        'margin_pct': round(margin_amount / sales_amount * 100, 2) if sales_amount > 0 else 0,
                        'fiscal_year': fiscal_year,
                        'fiscal_month': fiscal_month,
                    })
                    transaction_key += 1
        
        df = pd.DataFrame(transactions)
        print(f"     {len(df):,} sales transactions generated")
        return df
    
    def _generate_fact_inventory(
        self, 
        fact_dates: pd.DataFrame, 
        dim_org: pd.DataFrame, 
        dim_product: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Generate fact_inventory at daily snapshot grain.
        Grain: One row per product per location per day.
        """
        print("  → fact_inventory")
        
        # Configuration: Only DCs hold inventory
        dcs = dim_org[dim_org['org_type'] == 'DC']
        
        # Sample dates (monthly snapshots to reduce volume)
        snapshot_dates = fact_dates[fact_dates['date'].dt.is_month_end]
        
        print(f"     Generating {len(snapshot_dates)} snapshots × {len(dcs)} DCs × {len(dim_product)} products...")
        
        snapshots = []
        snapshot_key = 1
        
        for _, date_row in snapshot_dates.iterrows():
            date_key = date_row['date_key']
            fiscal_year = date_row['fiscal_year']
            fiscal_month = date_row['fiscal_month']
            
            for _, dc_row in dcs.iterrows():
                org_key = dc_row['org_key']
                
                for _, product_row in dim_product.iterrows():
                    product_key = product_row['product_key']
                    unit_cost = product_row['standard_cost']
                    
                    # Inventory quantities (some products might be 0)
                    on_hand_qty = random.randint(0, 1000)
                    reserved_qty = random.randint(0, int(on_hand_qty * 0.3)) if on_hand_qty > 0 else 0
                    available_qty = on_hand_qty - reserved_qty
                    
                    inventory_value = on_hand_qty * unit_cost
                    
                    snapshots.append({
                        'snapshot_key': snapshot_key,
                        'date_key': date_key,
                        'org_key': org_key,
                        'product_key': product_key,
                        'on_hand_qty': on_hand_qty,
                        'reserved_qty': reserved_qty,
                        'available_qty': available_qty,
                        'unit_cost': round(unit_cost, 2),
                        'inventory_value': round(inventory_value, 2),
                        'fiscal_year': fiscal_year,
                        'fiscal_month': fiscal_month,
                    })
                    snapshot_key += 1
        
        df = pd.DataFrame(snapshots)
        print(f"     {len(df):,} inventory snapshots generated")
        return df
    
    # =========================================================================
    # Phase 3: Action Aggregates
    # =========================================================================
    
    def _generate_action_aggregates(self):
        """Generate pre-calculated action aggregates for operational decisions."""
        
        # Load facts for aggregation
        fact_sales = pd.read_parquet(self.output_path / "facts" / "fact_sales")
        
        # Generate aggregates
        agg_margin_variance = self._generate_agg_margin_variance(fact_sales)
        self._write_table(
            agg_margin_variance, 
            "action_aggregates/agg_margin_variance", 
            partition_by=['action_code', 'fiscal_year']
        )
    
    def _generate_agg_margin_variance(self, fact_sales: pd.DataFrame) -> pd.DataFrame:
        """
        Generate margin variance action aggregate.
        Grain: Product × Month (aggregated from transaction detail).
        Action Code: C-C1.1 (Margin below threshold)
        """
        print("  → agg_margin_variance (Action Code: C-C1.1)")
        
        # Aggregate sales by product and month
        agg = fact_sales.groupby(['product_key', 'fiscal_year', 'fiscal_month']).agg({
            'sales_amount': 'sum',
            'cost_amount': 'sum',
            'margin_amount': 'sum',
            'quantity': 'sum',
        }).reset_index()
        
        # Calculate margin %
        agg['margin_pct'] = (agg['margin_amount'] / agg['sales_amount'] * 100).round(2)
        
        # Target margin (from config or hardcoded)
        agg['target_margin_pct'] = 35.0
        agg['margin_variance_pct'] = agg['margin_pct'] - agg['target_margin_pct']
        
        # Flag: Below threshold?
        agg['is_below_threshold'] = (agg['margin_variance_pct'] < -5.0).astype(int)
        
        # Action Code alignment
        agg['action_code'] = 'C-C1.1'
        agg['action_priority'] = agg.apply(
            lambda row: 'High' if row['margin_variance_pct'] < -10 
                        else 'Medium' if row['margin_variance_pct'] < -5 
                        else 'Low', 
            axis=1
        )
        
        # Add aggregate key
        agg.insert(0, 'aggregate_key', range(1, len(agg) + 1))
        
        print(f"     {len(agg):,} margin variance records generated")
        print(f"     {agg['is_below_threshold'].sum():,} products below margin threshold")
        return agg
    
    # =========================================================================
    # Helpers
    # =========================================================================
    
    def _write_table(self, df: pd.DataFrame, table_path: str, partition_by: List[str] = None):
        """
        Write DataFrame to gold layer as Delta Parquet.
        Falls back to plain Parquet if Delta not available.
        """
        full_path = self.output_path / table_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        if DELTA_AVAILABLE and partition_by:
            # Write as Delta Lake with partitioning
            write_deltalake(
                str(full_path),
                df,
                mode='overwrite',
                partition_by=partition_by,
            )
            format_str = f"Delta (partitioned by {', '.join(partition_by)})"
        elif DELTA_AVAILABLE:
            # Write as Delta Lake without partitioning
            write_deltalake(
                str(full_path),
                df,
                mode='overwrite',
            )
            format_str = "Delta"
        else:
            # Fallback to plain Parquet
            if partition_by:
                df.to_parquet(
                    full_path,
                    engine='pyarrow',
                    partition_cols=partition_by,
                    index=False,
                )
                format_str = f"Parquet (partitioned by {', '.join(partition_by)})"
            else:
                df.to_parquet(
                    full_path / "data.parquet",
                    engine='pyarrow',
                    index=False,
                )
                format_str = "Parquet"
        
        print(f"     ✓ Written to {table_path} ({format_str}, {len(df):,} rows)")


def main():
    parser = argparse.ArgumentParser(description='Generate synthetic gold layer data for Aurora Group')
    parser.add_argument(
        '--config', 
        default='synthetic_config_core_v1.yaml',
        help='Path to YAML configuration file'
    )
    parser.add_argument(
        '--output',
        default='../../showcases/aurora_group/data/gold',
        help='Output path for gold layer files'
    )
    
    args = parser.parse_args()
    
    # Resolve paths relative to script location
    script_dir = Path(__file__).parent
    config_path = script_dir / args.config
    output_path = Path(args.output)
    
    if not config_path.exists():
        print(f"Error: Config file not found: {config_path}")
        return 1
    
    # Generate gold layer
    generator = GoldLayerGenerator(str(config_path), str(output_path))
    generator.generate_all()
    
    return 0


if __name__ == '__main__':
    exit(main())
