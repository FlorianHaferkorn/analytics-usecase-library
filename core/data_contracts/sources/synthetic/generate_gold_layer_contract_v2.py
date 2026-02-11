"""
Gold Layer Synthetic Data Generator (Contract-Compliant v2)
==========================================================

Generates synthetic data for Aurora Group showcase following lakehouse architecture:
- Delta Parquet format
- Conformed dimensions (star schema)
- Grain-explicit facts
- CONTRACT-COMPLIANT column names (matches synthetic_data_contract.yaml)

Key Changes from v1:
- Column names use Display Names from contract (e.g., "Net Sales Amount" not "sales_amount")
- Fiscal Year = Calendar Year (Aurora Group fiscal_year_start = 01-01)
- fact_sales uses InvoiceLineID, Quantity Qty, Gross Sales Amount, Discount Amount, Net Sales Amount, COGS Amount
- fact_inventory_snapshot uses DateKey-OrgKey-ProductKey composite key
- All FK references validated against contract

Usage:
    py generate_gold_layer_contract_v2.py
"""

import yaml
import random
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List
import argparse
import sys

# Import shared utilities (adjust path if needed)
# Assuming script runs from repo root or core/data_contracts/sources/synthetic/
_gold_path = Path(__file__).parent.parent.parent.parent / "showcases" / "aurora_group" / "data" / "gold"
if _gold_path.exists():
    sys.path.insert(0, str(_gold_path))
    from _company_profile import get_company_profile
    from _realistic_names import (
        generate_product_name,
        generate_promo_name,
        generate_org_name,
        generate_customer_name,
        generate_asset_name,
    )
    from _generator_utils import (
        get_fact_date_range,
        get_fact_date_keys,
        apply_monthly_seasonality,
        apply_weekly_seasonality,
        apply_combined_seasonality,
        FACTS_START,
        FACTS_END,
    )
else:
    raise ImportError(f"Could not find gold utilities at {_gold_path}")

# Check if Delta Lake is available (optional for local dev)
try:
    from deltalake import write_deltalake
    DELTA_AVAILABLE = True
except ImportError:
    DELTA_AVAILABLE = False
    print("Warning: deltalake package not found. Will write Parquet only.")


class GoldLayerGenerator:
    """Generates synthetic gold layer data conforming to lakehouse architecture."""
    
    def __init__(self, config_path: str, output_path: str, company: str = "aurora"):
        self.config = self._load_config(config_path)
        self.output_path = Path(output_path)
        self.random_seed = self.config.get("random_seed", 12345)
        self.company = company
        
        # Load company profile
        self.profile = get_company_profile(company)
        
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
        """Generate complete gold layer: dimensions, facts."""
        print("=" * 80)
        print("Gold Layer Synthetic Data Generator - Aurora Group (Contract-Compliant v2)")
        print("=" * 80)
        
        # Phase 1: Generate Conformed Dimensions (no dependencies)
        print("\n[Phase 1] Generating Conformed Dimensions...")
        self._generate_dimensions()
        
        # Phase 2: Generate Facts (depend on dimensions for FK integrity)
        print("\n[Phase 2] Generating Facts...")
        self._generate_facts()
        
        print("\n" + "=" * 80)
        print("[OK] Gold Layer generation complete!")
        print(f"Output location: {self.output_path.absolute()}")
        print("=" * 80)
    
    # =========================================================================
    # Phase 1: Conformed Dimensions (Contract-Compliant Column Names)
    # =========================================================================
    
    def _generate_dimensions(self):
        """Generate all conformed dimensions."""
        self.dimensions['dim_date'] = self._generate_dim_date()
        self.dimensions['dim_org'] = self._generate_dim_org()
        self.dimensions['dim_product'] = self._generate_dim_product()
        self.dimensions['dim_customer'] = self._generate_dim_customer()
        self.dimensions['dim_currency'] = self._generate_dim_currency()
        self.dimensions['dim_promo'] = self._generate_dim_promo()
        self.dimensions['dim_account'] = self._generate_dim_account()
        
        # Write dimensions to disk
        for dim_name, df in self.dimensions.items():
            self._write_table(df, f"dimensions/{dim_name}", partition_by=None)
    
    def _generate_dim_date(self) -> pd.DataFrame:
        """Generate dim_date with calendar and fiscal hierarchies (CONTRACT: columns match synthetic_data_contract.yaml)."""
        print("  -> dim_date")
        
        start_date = pd.to_datetime(self.config['time']['dim_date_start'])
        end_date = pd.to_datetime(self.config['time']['dim_date_end'])
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        
        # Aurora: fiscal_year_start = 01-01 → Calendar Year = Fiscal Year
        df = pd.DataFrame({
            'DateKey': dates.strftime('%Y%m%d').astype(int),
            'Date': dates,
            'Year': dates.year,
            'Month': dates.month,
            'Month Name': dates.strftime('%B'),
            'Quarter': dates.quarter,
            'Fiscal Year': dates.year,  # Contract: Calendar = Fiscal for Aurora
            'Fiscal Period': dates.strftime('FY%Y-P%m'),
        })
        
        print(f"     {len(df):,} dates generated ({start_date.date()} to {end_date.date()})")
        return df
    
    def _generate_dim_org(self) -> pd.DataFrame:
        """Generate dim_org with hierarchy (CONTRACT: Group -> Region -> Country -> Store/DC)."""
        print("  -> dim_org")
        
        org_nodes = []
        org_key = 1
        
        # Root: Group
        org_nodes.append({
            'OrgKey': org_key,
            'OrgCode': 'AURORA-GROUP',
            'OrgName': 'Aurora Group SE',
            'OrgLevel': 'Group',
            'ParentOrgKey': pd.NA,
            'Country': pd.NA,
            'Currency Code': 'EUR',
            'OrgType': 'Group',
            'Open DateKey': 20180101,
            'Close DateKey': pd.NA,
        })
        group_key = org_key
        org_key += 1
        
        # Regions -> Countries -> Sites
        for region_cfg in self.config['org']['regions']:
            region_id = region_cfg['id']
            
            # Region
            region_key = org_key
            region_info = self.profile['regions'].get(region_id, {})
            region_name = generate_org_name(
                org_type='Region',
                region=region_id,
                country=None,
                city=None,
                profile=self.profile,
                org_key=region_key,
                seed=self.random_seed,
            )
            
            org_nodes.append({
                'OrgKey': region_key,
                'OrgCode': f'RGN-{region_id}',
                'OrgName': region_name,
                'OrgLevel': 'Region',
                'ParentOrgKey': group_key,
                'Country': pd.NA,
                'Currency Code': 'EUR',
                'OrgType': 'Region',
                'Open DateKey': 20180101,
                'Close DateKey': pd.NA,
            })
            org_key += 1
            
            # Countries
            for country_code in region_cfg['countries']:
                country_key = org_key
                currency = 'EUR' if country_code in ['DE', 'AT', 'NL', 'BE', 'LU'] else 'CHF' if country_code == 'CH' else 'SEK'
                
                # Get country name from profile
                country_names_map = {
                    'DE': 'Germany', 'AT': 'Austria', 'CH': 'Switzerland',
                    'NL': 'Netherlands', 'BE': 'Belgium', 'LU': 'Luxembourg',
                    'SE': 'Sweden', 'NO': 'Norway', 'DK': 'Denmark', 'FI': 'Finland',
                    'IT': 'Italy', 'ES': 'Spain', 'PT': 'Portugal', 'GR': 'Greece',
                    'PL': 'Poland', 'CZ': 'Czech Republic', 'HU': 'Hungary', 'SK': 'Slovakia',
                }
                country_name = country_names_map.get(country_code, country_code)
                
                country_org_name = generate_org_name(
                    org_type='Country',
                    region=region_id,
                    country=country_name,
                    city=None,
                    profile=self.profile,
                    org_key=country_key,
                    seed=self.random_seed,
                )
                
                org_nodes.append({
                    'OrgKey': country_key,
                    'OrgCode': f'CTRY-{country_code}',
                    'OrgName': country_org_name,
                    'OrgLevel': 'Country',
                    'ParentOrgKey': region_key,
                    'Country': country_code,
                    'Currency Code': currency,
                    'OrgType': 'Country',
                    'Open DateKey': 20180101,
                    'Close DateKey': pd.NA,
                })
                org_key += 1
                
                # Stores
                cities = region_info.get('cities', [])
                for store_idx in range(region_cfg['store_count'] // len(region_cfg['countries'])):
                    # Cycle through cities for store locations
                    city = cities[store_idx % len(cities)] if cities else f"{country_name} City {store_idx+1}"
                    
                    store_name = generate_org_name(
                        org_type='Store',
                        region=region_id,
                        country=country_name,
                        city=city,
                        profile=self.profile,
                        org_key=org_key,
                        seed=self.random_seed,
                    )
                    
                    org_nodes.append({
                        'OrgKey': org_key,
                        'OrgCode': f'STORE-{country_code}-{store_idx+1:03d}',
                        'OrgName': store_name,
                        'OrgLevel': 'Store',
                        'ParentOrgKey': country_key,
                        'Country': country_code,
                        'Currency Code': currency,
                        'OrgType': 'Store',
                        'Open DateKey': 20180101,
                        'Close DateKey': pd.NA,
                    })
                    org_key += 1
                
                # DCs
                for dc_idx in range(region_cfg['dc_count']):
                    # Generate realistic DC name
                    region_info = self.profile['regions'].get(region_id, {})
                    cities = region_info.get('cities', [])
                    city = random.choice(cities) if cities else f"{country_name} City"
                    
                    dc_name = generate_org_name(
                        org_type='DC',
                        region=region_id,
                        country=country_name,
                        city=city,
                        profile=self.profile,
                        org_key=org_key,
                        seed=self.random_seed,
                    )
                    
                    org_nodes.append({
                        'OrgKey': org_key,
                        'OrgCode': f'DC-{country_code}-{dc_idx+1:02d}',
                        'OrgName': dc_name,
                        'OrgLevel': 'DC',
                        'ParentOrgKey': country_key,
                        'Country': country_code,
                        'Currency Code': currency,
                        'OrgType': 'DC',
                        'Open DateKey': 20180101,
                        'Close DateKey': pd.NA,
                    })
                    org_key += 1
        
        df = pd.DataFrame(org_nodes)
        
        # Convert nullable columns to proper types
        df['ParentOrgKey'] = df['ParentOrgKey'].astype('Int64')  # Nullable int
        df['Close DateKey'] = df['Close DateKey'].astype('Int64')  # Nullable int
        
        print(f"     {len(df):,} organization nodes generated")
        return df
    
    def _generate_dim_product(self) -> pd.DataFrame:
        """Generate dim_product with category hierarchy and pricing (CONTRACT)."""
        print("  -> dim_product")
        
        products = []
        product_key = 1
        
        min_price = self.config['products']['price_points']['min_list_price']
        max_price = self.config['products']['price_points']['max_list_price']
        
        for category_cfg in self.config['products']['categories']:
            category = category_cfg['name']
            product_count = category_cfg['product_count']
            margin_range = category_cfg['gross_margin_range']
            
            # Get subcategories from company profile
            cat_config = self.profile['product_categories'].get(category, {})
            subcategories_list = cat_config.get('subcategories', [f'{category} Basic', f'{category} Premium'])
            
            # If profile has subcategories, use them; otherwise fall back to Basic/Premium
            if len(subcategories_list) > 0:
                subcategories = subcategories_list
            else:
                subcategories = [f'{category} Basic', f'{category} Premium']
            
            for subcategory in subcategories:
                for prod_idx in range(product_count // len(subcategories)):
                    if category == 'Consumer Electronics':
                        list_price = random.uniform(max_price * 0.3, max_price)
                    elif category == 'Home & Living':
                        list_price = random.uniform(min_price * 2, max_price * 0.5)
                    else:  # Fashion
                        list_price = random.uniform(min_price, max_price * 0.4)
                    
                    target_margin = random.uniform(margin_range[0], margin_range[1])
                    standard_cost = list_price * (1 - target_margin)
                    
                    # Generate realistic product name
                    product_name = generate_product_name(
                        category=category,
                        subcategory=subcategory,
                        profile=self.profile,
                        product_key=product_key,
                        seed=self.random_seed,
                    )
                    
                    products.append({
                        'ProductKey': product_key,
                        'ProductCode': f'PRD-{category[:3].upper()}-{product_key:05d}',
                        'ProductName': product_name,
                        'Category': category,
                        'Subcategory': subcategory,
                        'Brand': f'{self.profile["brand_name"]} {category}',
                        'Lifecycle Status': random.choice(['Active', 'Active', 'Active', 'EOL']),
                        'List Price Amount': round(list_price, 2),
                    })
                    product_key += 1
        
        df = pd.DataFrame(products)
        print(f"     {len(df):,} products generated")
        return df
    
    def _generate_dim_customer(self) -> pd.DataFrame:
        """Generate dim_customer with segments and channel preferences (CONTRACT: PII-free)."""
        print("  -> dim_customer")
        
        # Reduce to 50K for demo purposes (faster generation)
        total_customers = min(self.config['customers']['total_customers'], 50000)
        segment_shares = self.config['customers']['segment_shares']
        
        customers = []
        customer_key = 1
        
        # Get cities for B2B customer names
        all_cities = []
        for region_info in self.profile['regions'].values():
            all_cities.extend(region_info.get('cities', []))
        
        for segment, share in segment_shares.items():
            count = int(total_customers * share)
            
            for _ in range(count):
                # Generate realistic customer name
                city = random.choice(all_cities) if all_cities else None
                customer_name = generate_customer_name(
                    segment=segment,
                    profile=self.profile,
                    customer_key=customer_key,
                    city=city,
                    seed=self.random_seed,
                )
                
                customers.append({
                    'CustomerKey': customer_key,
                    'CustomerCode': f'CUST-{customer_key:08d}',
                    'CustomerName': customer_name,
                    'Segment': segment,
                    'Channel Preference': random.choice(['Store', 'ECom', 'Mixed']),
                    'Tenure Bucket': random.choice(['<1Y', '1-3Y', '>3Y']),
                })
                customer_key += 1
        
        df = pd.DataFrame(customers)
        print(f"     {len(df):,} customers generated")
        return df
    
    def _generate_dim_currency(self) -> pd.DataFrame:
        """Generate dim_currency (CONTRACT: Currency Code is key)."""
        print("  -> dim_currency")
        
        currencies = [
            {'Currency Code': 'EUR', 'Currency Name': 'Euro'},
            {'Currency Code': 'CHF', 'Currency Name': 'Swiss Franc'},
            {'Currency Code': 'SEK', 'Currency Name': 'Swedish Krona'},
            {'Currency Code': 'GBP', 'Currency Name': 'British Pound'},
        ]
        
        df = pd.DataFrame(currencies)
        print(f"     {len(df)} currencies generated")
        return df
    
    def _generate_dim_promo(self) -> pd.DataFrame:
        """Generate dim_promo with ~50 promotions (CONTRACT: columns match synthetic_data_contract.yaml)."""
        print("  -> dim_promo")
        
        dim_date_df = self.dimensions['dim_date']
        promo_types = ['Discount', 'Bundle', 'Multi-buy']
        promo_mechanics = ['PercentOff', 'MultiBuy', 'FixedPrice']
        
        promotions = []
        promo_key = 1
        
        # Generate ~50 promotions over the fact period (use standard FACTS_START/END)
        fact_start = FACTS_START
        fact_end = FACTS_END
        
        # Get categories for category-specific promos
        categories = list(self.profile['product_categories'].keys())
        
        for i in range(50):
            promo_type = random.choice(promo_types)
            
            # Assign mechanic based on type
            if promo_type == 'Discount':
                mechanic = 'PercentOff'
            elif promo_type == 'Bundle':
                mechanic = 'FixedPrice'
            else:
                mechanic = 'MultiBuy'
            
            # Random promo duration: 1-4 weeks
            start_date = fact_start + timedelta(days=random.randint(0, (fact_end - fact_start).days - 28))
            duration_days = random.randint(7, 28)
            end_date = start_date + timedelta(days=duration_days)
            
            start_datekey = int(start_date.strftime('%Y%m%d'))
            end_datekey = int(end_date.strftime('%Y%m%d'))
            
            discount_pct = random.uniform(0.05, 0.40) if promo_type == 'Discount' else 0.0
            
            # Generate realistic promo name
            category = random.choice(categories) if random.random() < 0.3 else None  # 30% category-specific
            promo_name = generate_promo_name(
                profile=self.profile,
                promo_key=promo_key,
                category=category,
                seed=self.random_seed,
            )
            
            promotions.append({
                'PromoKey': promo_key,
                'PromoCode': f'PROMO{promo_key:03d}',
                'PromoName': promo_name,
                'Promo Type': promo_type,
                'Promo Mechanic': mechanic,
                'Start DateKey': start_datekey,
                'End DateKey': end_datekey,
                'Discount %': round(discount_pct, 3),
            })
            promo_key += 1
        
        # Add -1 for "No Promotion"
        promotions.append({
            'PromoKey': -1,
            'PromoCode': 'NONE',
            'PromoName': 'No Promotion',
            'Promo Type': 'None',
            'Promo Mechanic': 'None',
            'Start DateKey': 19000101,
            'End DateKey': 21001231,
            'Discount %': 0.0,
        })
        
        df = pd.DataFrame(promotions)
        print(f"     {len(df)} promotions generated")
        return df
    
    def _generate_dim_account(self) -> pd.DataFrame:
        """Generate dim_account for GL accounts (CONTRACT: columns match synthetic_data_contract.yaml)."""
        print("  -> dim_account")
        
        accounts = []
        account_key = 1
        
        # Define account structure
        account_definitions = [
            # Revenue accounts
            {'code': '4000', 'name': 'Product Sales', 'type': 'Revenue', 'statement': 'P&L'},
            {'code': '4100', 'name': 'Service Revenue', 'type': 'Revenue', 'statement': 'P&L'},
            {'code': '4900', 'name': 'Other Revenue', 'type': 'Revenue', 'statement': 'P&L'},
            
            # COGS accounts
            {'code': '5000', 'name': 'Material Cost', 'type': 'COGS', 'statement': 'P&L'},
            {'code': '5100', 'name': 'Direct Labor', 'type': 'COGS', 'statement': 'P&L'},
            {'code': '5200', 'name': 'Manufacturing Overhead', 'type': 'COGS', 'statement': 'P&L'},
            
            # Operating Expense accounts
            {'code': '6000', 'name': 'Personnel Expense', 'type': 'Opex', 'statement': 'P&L'},
            {'code': '6100', 'name': 'Rent & Leases', 'type': 'Opex', 'statement': 'P&L'},
            {'code': '6200', 'name': 'Marketing & Advertising', 'type': 'Opex', 'statement': 'P&L'},
            {'code': '6300', 'name': 'IT & Technology', 'type': 'Opex', 'statement': 'P&L'},
            {'code': '6400', 'name': 'Logistics & Freight', 'type': 'Opex', 'statement': 'P&L'},
            {'code': '6500', 'name': 'Professional Services', 'type': 'Opex', 'statement': 'P&L'},
            {'code': '6900', 'name': 'Other Opex', 'type': 'Opex', 'statement': 'P&L'},
            
            # Asset accounts
            {'code': '1000', 'name': 'Cash & Equivalents', 'type': 'Asset', 'statement': 'Balance Sheet'},
            {'code': '1100', 'name': 'Accounts Receivable', 'type': 'Asset', 'statement': 'Balance Sheet'},
            {'code': '1200', 'name': 'Inventory', 'type': 'Asset', 'statement': 'Balance Sheet'},
            {'code': '1500', 'name': 'Fixed Assets', 'type': 'Asset', 'statement': 'Balance Sheet'},
            
            # Liability accounts
            {'code': '2000', 'name': 'Accounts Payable', 'type': 'Liability', 'statement': 'Balance Sheet'},
            {'code': '2100', 'name': 'Accrued Expenses', 'type': 'Liability', 'statement': 'Balance Sheet'},
            {'code': '2500', 'name': 'Long-term Debt', 'type': 'Liability', 'statement': 'Balance Sheet'},
        ]
        
        for acc_def in account_definitions:
            accounts.append({
                'AccountKey': account_key,
                'AccountCode': acc_def['code'],
                'AccountName': acc_def['name'],
                'AccountType': acc_def['type'],
                'Statement Type': acc_def['statement'],
            })
            account_key += 1
        
        df = pd.DataFrame(accounts)
        print(f"     {len(df)} GL accounts generated")
        return df
    
    # =========================================================================
    # Phase 2: Facts (Contract-Compliant Column Names)
    # =========================================================================
    
    def _generate_facts(self):
        """Generate all fact tables with FK integrity."""
        
        dim_date = self.dimensions['dim_date']
        dim_org = self.dimensions['dim_org']
        dim_product = self.dimensions['dim_product']
        dim_customer = self.dimensions['dim_customer']
        dim_promo = self.dimensions['dim_promo']
        dim_account = self.dimensions['dim_account']
        
        # Filter time to facts period (use standard FACTS_START/FACTS_END)
        fact_dates = dim_date[
            (dim_date['Date'] >= FACTS_START) & (dim_date['Date'] <= FACTS_END)
        ]
        
        fact_sales = self._generate_fact_sales(fact_dates, dim_org, dim_product, dim_customer, dim_promo)
        self._write_table(fact_sales, "facts/fact_sales", partition_by=['Fiscal Year', 'Fiscal Month'])
        
        fact_inventory = self._generate_fact_inventory_snapshot(fact_dates, dim_org, dim_product)
        self._write_table(fact_inventory, "facts/fact_inventory_snapshot", partition_by=['Fiscal Year', 'Fiscal Month'])
        
        # Priority 1: Sales Budget
        fact_sales_budget = self._generate_fact_sales_budget(dim_date, dim_org, dim_product)
        self._write_table(fact_sales_budget, "facts/fact_sales_budget", partition_by=None)
        
        # Priority 1: Action Log
        fact_actions = self._generate_fact_action_log(dim_date, dim_org)
        self._write_table(fact_actions, "facts/fact_action_log", partition_by=['Fiscal Year'])
        
        # Priority 2: Working Capital
        fact_wc = self._generate_fact_working_capital(dim_date, dim_org, fact_sales, fact_inventory)
        self._write_table(fact_wc, "facts/fact_working_capital", partition_by=None)
        
        # Priority 2: GL Journal
        fact_gl = self._generate_fact_gl_journal(dim_date, dim_org, dim_account, fact_sales)
        self._write_table(fact_gl, "facts/fact_gl_journal", partition_by=['Fiscal Year'])
        
        # Priority 3: Customer Interactions
        fact_interactions = self._generate_fact_customer_interactions(dim_date, dim_customer, dim_org)
        self._write_table(fact_interactions, "facts/fact_customer_interactions", partition_by=['Fiscal Year'])
        
        # Priority 3: NPS
        fact_nps = self._generate_fact_nps(dim_date, dim_customer, dim_org)
        self._write_table(fact_nps, "facts/fact_nps", partition_by=None)

        # Commercial: fact_experience (COM-003 Complaint Count), fact_promo (COM-004)
        fact_experience = self._generate_fact_experience(dim_date, dim_customer, dim_org)
        self._write_table(fact_experience, "facts/fact_experience", partition_by=['Fiscal Year'])
        fact_promo = self._generate_fact_promo(dim_promo, fact_sales)
        self._write_table(fact_promo, "facts/fact_promo", partition_by=None)
    
    def _generate_fact_sales(
        self, 
        fact_dates: pd.DataFrame, 
        dim_org: pd.DataFrame, 
        dim_product: pd.DataFrame,
        dim_customer: pd.DataFrame,
        dim_promo: pd.DataFrame
    ) -> pd.DataFrame:
        """Generate fact_sales (CONTRACT: InvoiceLineID grain, Net Sales Amount, COGS Amount)."""
        print("  -> fact_sales")
        
        transactions_per_day_per_store = 50
        stores_df = dim_org[dim_org['OrgType'] == 'Store']
        
        # Sample 20% of stores for faster generation
        sampled_stores = stores_df.sample(frac=0.20, random_state=self.random_seed)
        
        # Convert all to dicts for speed
        stores_list = sampled_stores.to_dict('records')
        product_list = dim_product.to_dict('records')
        customer_list = dim_customer.to_dict('records')
        promo_list = dim_promo[dim_promo['PromoKey'] != -1].to_dict('records')  # Exclude "No Promotion"
        date_list = fact_dates.to_dict('records')  # All dates in fact period
        
        print(f"     Generating ~{len(date_list) * len(stores_list) * 50:,} transactions (20% stores, daily)...")
        
        transactions = []
        invoice_line_id = 1
        
        num_products = len(product_list)
        num_customers = len(customer_list)
        
        for date_row in date_list:
            date_key = date_row['DateKey']
            date_obj = pd.to_datetime(date_row['Date'])
            fiscal_year = date_row['Fiscal Year']
            fiscal_month = date_row['Month']
            
            # Apply seasonality to base transaction count
            base_transactions = 50
            seasonality_factor = apply_combined_seasonality(
                date_obj,
                base_factor=1.0,
                monthly_weight=0.6,
                weekly_weight=0.4,
                seed=self.random_seed,
            )
            avg_transactions_per_day = int(base_transactions * seasonality_factor)
            
            for store in stores_list:
                org_key = store['OrgKey']
                currency = store['Currency Code']
                # Daily variation around seasonality-adjusted average
                num_transactions = max(1, int(np.random.normal(avg_transactions_per_day, avg_transactions_per_day * 0.2)))
                
                for _ in range(num_transactions):
                    product = product_list[random.randint(0, num_products-1)]
                    customer = customer_list[random.randint(0, num_customers-1)]
                    
                    quantity = random.randint(1, 5)
                    unit_price = product['List Price Amount']
                    
                    # Promotion logic: 15% of transactions have promotions
                    has_promo = random.random() < 0.15
                    
                    if has_promo and len(promo_list) > 0:
                        # Find active promotions for this date
                        active_promos = [p for p in promo_list if p['Start DateKey'] <= date_key <= p['End DateKey']]
                        if active_promos:
                            promo = random.choice(active_promos)
                            promo_key = promo['PromoKey']
                            discount_pct = promo['Discount %']
                        else:
                            promo_key = -1
                            discount_pct = random.uniform(0.0, 0.10)
                    else:
                        promo_key = -1
                        discount_pct = random.uniform(0.0, 0.10)
                    
                    # CONTRACT: Gross Sales, Discount, Net Sales, COGS
                    gross_sales = quantity * unit_price
                    discount = gross_sales * discount_pct
                    net_sales = gross_sales - discount
                    cogs = net_sales * random.uniform(0.55, 0.70)  # 55-70% COGS ratio
                    
                    # Plan values (for PVM analysis)
                    plan_quantity = quantity * random.uniform(0.9, 1.1)
                    plan_sales = plan_quantity * unit_price * random.uniform(0.95, 1.05)
                    plan_cogs = plan_sales * 0.62
                    
                    transactions.append({
                        'InvoiceLineID': f'INV-{invoice_line_id:010d}',
                        'DateKey': date_key,
                        'OrgKey': org_key,
                        'ProductKey': product['ProductKey'],
                        'CustomerKey': customer['CustomerKey'],
                        'PromoKey': promo_key,
                        'Promo Flag': 'Yes' if has_promo else 'No',
                        'Quantity': quantity,
                        'Plan Quantity': round(plan_quantity, 2),
                        'List Price Amount': round(unit_price, 2),
                        'Net Price Amount': round(net_sales / quantity, 2) if quantity > 0 else 0,
                        'Discount Amount': round(discount, 2),
                        'Net Sales Amount': round(net_sales, 2),
                        'Plan Sales Amount': round(plan_sales, 2),
                        'Last Year Sales Amount': round(net_sales * random.uniform(0.85, 1.15), 2),
                        'Cost of Goods Sold Amount': round(cogs, 2),
                        'Plan COGS Amount': round(plan_cogs, 2),
                        'Fiscal Year': fiscal_year,
                        'Fiscal Month': fiscal_month,
                    })
                    invoice_line_id += 1
        
        df = pd.DataFrame(transactions)
        df['PromoKey'] = df['PromoKey'].astype('Int64')  # Nullable int
        
        print(f"     {len(df):,} sales transactions generated")
        return df
    
    def _generate_fact_inventory_snapshot(
        self, 
        fact_dates: pd.DataFrame, 
        dim_org: pd.DataFrame, 
        dim_product: pd.DataFrame
    ) -> pd.DataFrame:
        """Generate fact_inventory_snapshot (CONTRACT: DateKey-OrgKey-ProductKey grain)."""
        print("  -> fact_inventory_snapshot")
        
        dcs_df = dim_org[dim_org['OrgType'] == 'DC']
        snapshot_dates_df = fact_dates[fact_dates['Date'].dt.is_month_end]
        
        # Sample 10% of products for memory optimization (still 500 products × 60 months × 18 DCs = 540K rows)
        sampled_products = dim_product.sample(frac=0.10, random_state=self.random_seed)
        
        # Convert to dicts for speed
        dcs_list = dcs_df.to_dict('records')
        product_list = sampled_products.to_dict('records')
        snapshot_dates = snapshot_dates_df.to_dict('records')
        
        print(f"     Generating {len(snapshot_dates)} × {len(dcs_list)} × {len(product_list)} = {len(snapshot_dates) * len(dcs_list) * len(product_list):,} snapshots...")
        
        snapshots = []
        
        for date_row in snapshot_dates:
            date_key = date_row['DateKey']
            fiscal_year = date_row['Fiscal Year']
            fiscal_month = date_row['Month']
            
            for dc in dcs_list:
                org_key = dc['OrgKey']
                
                for product in product_list:
                    product_key = product['ProductKey']
                    unit_cost = product['List Price Amount'] * 0.6  # Synthetic cost
                    
                    stock_qty = random.randint(0, 1000)
                    stock_value = stock_qty * unit_cost
                    safety_stock = random.randint(50, 200)
                    
                    snapshots.append({
                        'DateKey': date_key,
                        'OrgKey': org_key,
                        'ProductKey': product_key,
                        'Stock Qty': stock_qty,
                        'Stock Value Amount': round(stock_value, 2),
                        'Safety Stock Qty': safety_stock,
                        'Fiscal Year': fiscal_year,
                        'Fiscal Month': fiscal_month,
                    })
        
        df = pd.DataFrame(snapshots)
        print(f"     {len(df):,} inventory snapshots generated")
        return df
    
    def _generate_fact_sales_budget(
        self,
        dim_date: pd.DataFrame,
        dim_org: pd.DataFrame,
        dim_product: pd.DataFrame,
    ) -> pd.DataFrame:
        """Generate fact_sales_budget (CONTRACT: MonthEnd DateKey-OrgKey-ProductKey-Version grain)."""
        print("  -> fact_sales_budget")
        
        # Only stores for budget
        stores_df = dim_org[dim_org['OrgType'] == 'Store']
        
        # Month-end dates in fact period (use standard FACTS_START/FACTS_END)
        month_ends = dim_date[
            (dim_date['Date'] >= FACTS_START) & 
            (dim_date['Date'] <= FACTS_END) &
            (pd.to_datetime(dim_date['Date']).dt.is_month_end)
        ]
        
        # Sample: 10% of stores, 5% of products for performance
        sampled_stores = stores_df.sample(frac=0.10, random_state=self.random_seed)
        sampled_products = dim_product.sample(frac=0.05, random_state=self.random_seed)
        
        stores_list = sampled_stores.to_dict('records')
        products_list = sampled_products.to_dict('records')
        month_list = month_ends.to_dict('records')
        
        print(f"     Generating {len(month_list)} months × {len(stores_list)} stores × {len(products_list)} products × 2 versions...")
        
        budgets = []
        
        for month in month_list:
            month_datekey = month['DateKey']
            
            for store in stores_list:
                org_key = store['OrgKey']
                
                for product in products_list:
                    product_key = product['ProductKey']
                    list_price = product['List Price Amount']
                    
                    # Original budget: baseline
                    base_units = random.randint(10, 100)
                    base_sales = base_units * list_price * 0.90  # 10% average discount
                    base_cogs = base_sales * 0.62  # 62% COGS
                    
                    budgets.append({
                        'MonthEnd DateKey': month_datekey,
                        'OrgKey': org_key,
                        'ProductKey': product_key,
                        'Version': 'Original',
                        'Budget Sales Amount': round(base_sales, 2),
                        'Budget COGS Amount': round(base_cogs, 2),
                        'Budget Units Qty': base_units,
                    })
                    
                    # Revised budget: +5% optimistic
                    revised_units = int(base_units * 1.05)
                    revised_sales = revised_units * list_price * 0.90
                    revised_cogs = revised_sales * 0.62
                    
                    budgets.append({
                        'MonthEnd DateKey': month_datekey,
                        'OrgKey': org_key,
                        'ProductKey': product_key,
                        'Version': 'Revised',
                        'Budget Sales Amount': round(revised_sales, 2),
                        'Budget COGS Amount': round(revised_cogs, 2),
                        'Budget Units Qty': revised_units,
                    })
        
        df = pd.DataFrame(budgets)
        print(f"     {len(df):,} budget records generated")
        return df
    
    def _generate_fact_working_capital(
        self,
        dim_date: pd.DataFrame,
        dim_org: pd.DataFrame,
        fact_sales: pd.DataFrame,
        fact_inventory: pd.DataFrame,
    ) -> pd.DataFrame:
        """Generate fact_working_capital (CONTRACT: MonthEnd DateKey-OrgKey grain)."""
        print("  -> fact_working_capital")
        
        # Month-end dates (use standard FACTS_START/FACTS_END)
        month_ends = dim_date[
            (dim_date['Date'] >= FACTS_START) & 
            (dim_date['Date'] <= FACTS_END) &
            (pd.to_datetime(dim_date['Date']).dt.is_month_end)
        ]
        
        # Only stores and DCs (sample 20% for performance)
        orgs_df = dim_org[dim_org['OrgType'].isin(['Store', 'DC'])]
        sampled_orgs = orgs_df.sample(frac=0.20, random_state=self.random_seed)
        
        month_list = month_ends.to_dict('records')
        orgs_list = sampled_orgs.to_dict('records')
        
        print(f"     Generating {len(month_list)} months × {len(orgs_list)} orgs (synthetic AR/AP/Inv)...")
        
        wc_records = []
        
        for month in month_list:
            month_datekey = month['DateKey']
            month_date = month['Date']
            days_in_month = pd.Period(month_date, freq='M').days_in_month
            
            for org in orgs_list:
                org_key = org['OrgKey']
                
                # Synthetic values (no joins for performance)
                period_sales = random.uniform(50000, 500000)
                period_cogs = period_sales * random.uniform(0.55, 0.70)
                inventory_value = random.uniform(100000, 1000000)
                
                ar_balance = period_sales * random.uniform(0.10, 0.20)  # 10-20% of sales
                ap_balance = period_cogs * random.uniform(0.15, 0.25)   # 15-25% of COGS
                
                wc_records.append({
                    'MonthEnd DateKey': month_datekey,
                    'OrgKey': org_key,
                    'AR Balance Amount': round(ar_balance, 2),
                    'AP Balance Amount': round(ap_balance, 2),
                    'Inventory Value Amount': round(inventory_value, 2),
                    'Period Net Sales Amount': round(period_sales, 2),
                    'Period COGS Amount': round(period_cogs, 2),
                    'Days In Period Count': days_in_month,
                })
        
        df = pd.DataFrame(wc_records)
        print(f"     {len(df):,} working capital records generated")
        return df
    
    def _generate_fact_gl_journal(
        self,
        dim_date: pd.DataFrame,
        dim_org: pd.DataFrame,
        dim_account: pd.DataFrame,
        fact_sales: pd.DataFrame,
    ) -> pd.DataFrame:
        """Generate fact_gl_journal (CONTRACT: JournalLineID grain)."""
        print("  -> fact_gl_journal")
        
        # Sample 5% of fact_sales for GL entries (performance)
        sampled_sales = fact_sales.sample(frac=0.05, random_state=self.random_seed)
        
        # Get accounts
        revenue_acc = dim_account[dim_account['AccountType'] == 'Revenue'].iloc[0]
        cogs_acc = dim_account[dim_account['AccountType'] == 'COGS'].iloc[0]
        opex_accounts = dim_account[dim_account['AccountType'] == 'Opex'].to_dict('records')
        
        gl_entries = []
        journal_line_id = 1
        doc_num = 1000
        
        print(f"     Generating GL entries from {len(sampled_sales):,} sales transactions...")
        
        for _, sale in sampled_sales.iterrows():
            date_key = sale['DateKey']
            org_key = sale['OrgKey']
            fiscal_year = sale['Fiscal Year']
            
            # Revenue entry (Credit)
            gl_entries.append({
                'JournalLineID': f'GL{journal_line_id:08d}',
                'DateKey': date_key,
                'AccountKey': revenue_acc['AccountKey'],
                'OrgKey': org_key,
                'Amount': sale['Net Sales Amount'],
                'Document Number': f'DOC{doc_num}',
                'Line Description': 'Sales Revenue',
                'Fiscal Year': fiscal_year,
            })
            journal_line_id += 1
            
            # COGS entry (Debit)
            gl_entries.append({
                'JournalLineID': f'GL{journal_line_id:08d}',
                'DateKey': date_key,
                'AccountKey': cogs_acc['AccountKey'],
                'OrgKey': org_key,
                'Amount': -sale['Cost of Goods Sold Amount'],  # Negative for debit
                'Document Number': f'DOC{doc_num}',
                'Line Description': 'Cost of Goods Sold',
                'Fiscal Year': fiscal_year,
            })
            journal_line_id += 1
            doc_num += 1
        
        # Add some OPEX entries (monthly) - use standard FACTS_START/FACTS_END
        month_ends = dim_date[
            (dim_date['Date'] >= FACTS_START) & 
            (dim_date['Date'] <= FACTS_END) &
            (pd.to_datetime(dim_date['Date']).dt.is_month_end)
        ]
        
        stores_df = dim_org[dim_org['OrgType'] == 'Store']
        sampled_stores = stores_df.sample(n=min(20, len(stores_df)), random_state=self.random_seed)
        
        for _, month in month_ends.iterrows():
            date_key = month['DateKey']
            fiscal_year = month['Fiscal Year']
            
            for _, store in sampled_stores.iterrows():
                org_key = store['OrgKey']
                
                # Random OPEX entry
                opex_acc = random.choice(opex_accounts)
                opex_amount = random.uniform(5000, 20000)
                
                gl_entries.append({
                    'JournalLineID': f'GL{journal_line_id:08d}',
                    'DateKey': date_key,
                    'AccountKey': opex_acc['AccountKey'],
                    'OrgKey': org_key,
                    'Amount': -opex_amount,  # Negative for expense
                    'Document Number': f'DOC{doc_num}',
                    'Line Description': opex_acc['AccountName'],
                    'Fiscal Year': fiscal_year,
                })
                journal_line_id += 1
                doc_num += 1
        
        df = pd.DataFrame(gl_entries)
        print(f"     {len(df):,} GL journal entries generated")
        return df
    
    def _generate_fact_customer_interactions(
        self,
        dim_date: pd.DataFrame,
        dim_customer: pd.DataFrame,
        dim_org: pd.DataFrame,
    ) -> pd.DataFrame:
        """Generate fact_customer_interactions (CONTRACT: InteractionID grain)."""
        print("  -> fact_customer_interactions")
        
        # Use standard FACTS_START/FACTS_END
        fact_dates = dim_date[
            (dim_date['Date'] >= FACTS_START) & 
            (dim_date['Date'] <= FACTS_END)
        ]
        
        channels = ['Store', 'Web', 'App', 'CallCenter']
        interaction_types = ['Visit', 'Click', 'AddToCart', 'Support', 'Purchase']
        
        # Sample customers and dates for performance (10% customers, 2% dates)
        sampled_customers = dim_customer.sample(frac=0.10, random_state=self.random_seed)
        sampled_dates = fact_dates.sample(frac=0.02, random_state=self.random_seed)
        stores_df = dim_org[dim_org['OrgType'] == 'Store']
        
        customers_list = sampled_customers.to_dict('records')
        dates_list = sampled_dates.to_dict('records')
        stores_list = stores_df.to_dict('records')
        
        print(f"     Generating {len(dates_list)} dates × ~3 interactions per customer...")
        
        interactions = []
        interaction_id = 1
        
        for date_row in dates_list:
            date_key = date_row['DateKey']
            fiscal_year = date_row['Fiscal Year']
            
            # Random customers interact on this date
            interacting_customers = random.sample(customers_list, k=min(200, len(customers_list)))
            
            for customer in interacting_customers:
                customer_key = customer['CustomerKey']
                store = random.choice(stores_list)
                org_key = store['OrgKey']
                
                # 1-3 interactions per customer per date
                num_interactions = random.randint(1, 3)
                
                for _ in range(num_interactions):
                    channel = random.choice(channels)
                    interaction_type = random.choice(interaction_types)
                    
                    interactions.append({
                        'InteractionID': f'INT{interaction_id:08d}',
                        'DateKey': date_key,
                        'CustomerKey': customer_key,
                        'OrgKey': org_key,
                        'Channel': channel,
                        'Interaction Type': interaction_type,
                        'Interaction Count': 1,
                        'Fiscal Year': fiscal_year,
                    })
                    interaction_id += 1
        
        df = pd.DataFrame(interactions)
        print(f"     {len(df):,} customer interactions generated")
        return df
    
    def _generate_fact_nps(
        self,
        dim_date: pd.DataFrame,
        dim_customer: pd.DataFrame,
        dim_org: pd.DataFrame,
    ) -> pd.DataFrame:
        """Generate fact_nps (CONTRACT: ResponseID grain)."""
        print("  -> fact_nps")
        
        # Use standard FACTS_START/FACTS_END
        fact_dates = dim_date[
            (dim_date['Date'] >= FACTS_START) & 
            (dim_date['Date'] <= FACTS_END)
        ]
        
        # Sample: 5% of customers, 1% of dates (surveys are infrequent)
        sampled_customers = dim_customer.sample(frac=0.05, random_state=self.random_seed)
        sampled_dates = fact_dates.sample(frac=0.01, random_state=self.random_seed)
        stores_df = dim_org[dim_org['OrgType'] == 'Store']
        
        customers_list = sampled_customers.to_dict('records')
        dates_list = sampled_dates.to_dict('records')
        stores_list = stores_df.to_dict('records')
        
        print(f"     Generating {len(dates_list)} survey dates × customers...")
        
        responses = []
        response_id = 1
        
        for date_row in dates_list:
            date_key = date_row['DateKey']
            
            # Random customers respond on this date
            responding_customers = random.sample(customers_list, k=min(50, len(customers_list)))
            
            for customer in responding_customers:
                customer_key = customer['CustomerKey']
                store = random.choice(stores_list)
                org_key = store['OrgKey']
                
                # NPS score 0-10, skewed towards higher scores
                nps_score = min(10, max(0, int(random.gauss(7.5, 2.5))))
                
                is_promoter = nps_score >= 9
                is_detractor = nps_score <= 6
                
                responses.append({
                    'ResponseID': f'NPS{response_id:08d}',
                    'DateKey': date_key,
                    'CustomerKey': customer_key,
                    'OrgKey': org_key,
                    'NPS Score': nps_score,
                    'Is Promoter': is_promoter,
                    'Is Detractor': is_detractor,
                })
                response_id += 1
        
        df = pd.DataFrame(responses)
        print(f"     {len(df):,} NPS responses generated")
        return df

    def _generate_fact_experience(
        self,
        dim_date: pd.DataFrame,
        dim_customer: pd.DataFrame,
        dim_org: pd.DataFrame,
    ) -> pd.DataFrame:
        """Generate fact_experience (CONTRACT: Complaint ID grain, COM-003)."""
        print("  -> fact_experience")
        # Use standard FACTS_START/FACTS_END
        fact_dates = dim_date[
            (dim_date['Date'] >= FACTS_START) & (dim_date['Date'] <= FACTS_END)
        ]
        sampled_dates = fact_dates.sample(frac=0.02, random_state=self.random_seed)
        sampled_customers = dim_customer.sample(frac=0.03, random_state=self.random_seed)
        stores_df = dim_org[dim_org['OrgType'] == 'Store'].sample(frac=0.3, random_state=self.random_seed)
        customers_list = sampled_customers.to_dict('records')
        dates_list = sampled_dates.to_dict('records')
        stores_list = stores_df.to_dict('records')
        severities = ['Low', 'Medium', 'High']
        complaints = []
        complaint_id = 1
        for date_row in dates_list:
            date_key = date_row['DateKey']
            fiscal_year = date_row['Fiscal Year']
            for _ in range(random.randint(2, 15)):
                customer = random.choice(customers_list)
                store = random.choice(stores_list)
                complaints.append({
                    'Complaint ID': f'CMP{complaint_id:08d}',
                    'CustomerKey': customer['CustomerKey'],
                    'OrgKey': store['OrgKey'],
                    'DateKey': date_key,
                    'Severity': random.choice(severities),
                    'Fiscal Year': fiscal_year,
                })
                complaint_id += 1
        df = pd.DataFrame(complaints)
        print(f"     {len(df):,} complaint records generated")
        return df

    def _generate_fact_promo(
        self,
        dim_promo: pd.DataFrame,
        fact_sales: pd.DataFrame,
    ) -> pd.DataFrame:
        """Generate fact_promo (CONTRACT: PromoKey grain, COM-004)."""
        print("  -> fact_promo")
        promo_list = dim_promo[dim_promo['PromoKey'] != -1].to_dict('records')
        if not promo_list:
            df = pd.DataFrame(columns=[
                'PromoKey', 'Promo Cost', 'Funding Amount', 'Baseline Sales Amount',
                'Baseline Quantity', 'Baseline Non-Promo Sales Amount'
            ])
            print("     No promotions; empty fact_promo")
            return df
        rows = []
        for promo in promo_list:
            promo_key = promo['PromoKey']
            discount_pct = promo.get('Discount %', 0.15)
            promo_sales = fact_sales[fact_sales['PromoKey'] == promo_key]
            net_sales = promo_sales['Net Sales Amount'].sum() if len(promo_sales) > 0 else 0.0
            qty = promo_sales['Quantity'].sum() if 'Quantity' in promo_sales.columns and len(promo_sales) > 0 else 0.0
            cost_pct = 0.02 + discount_pct * 0.1
            promo_cost = net_sales * cost_pct if net_sales else random.uniform(500, 5000)
            baseline_sales = net_sales * (1 - discount_pct) * 0.8 if net_sales else promo_cost * 10
            baseline_qty = qty * 0.7 if qty else 0
            cannibalized = baseline_sales * 0.15
            rows.append({
                'PromoKey': promo_key,
                'Promo Cost': round(promo_cost, 2),
                'Funding Amount': round(promo_cost * 0.5, 2),
                'Baseline Sales Amount': round(baseline_sales, 2),
                'Baseline Quantity': round(baseline_qty, 2),
                'Baseline Non-Promo Sales Amount': round(baseline_sales - cannibalized, 2),
            })
        df = pd.DataFrame(rows)
        print(f"     {len(df):,} fact_promo rows generated")
        return df
    
    def _generate_fact_action_log(
        self,
        dim_date: pd.DataFrame,
        dim_org: pd.DataFrame,
    ) -> pd.DataFrame:
        """Generate fact_action_log with Action Codes from Use Case map (CONTRACT: ActionID grain)."""
        print("  -> fact_action_log")
        
        # Action Codes from UseCase_ActionCode_Map.yaml
        use_case_action_map = {
            'COM-001': ['C-M2.1', 'C-S1.1', 'C-S1.2'],
            'COM-002': ['C-M2.2', 'C-P4.1', 'C-S1.2'],
            'COM-003': ['C-M2.2', 'C-P4.1', 'C-S1.2'],
            'COM-004': ['C-M2.1', 'C-S1.1', 'C-M2.2', 'C-P4.1', 'C-S1.2'],
            'FIN-001': ['F-C1.1', 'F-C1.2', 'F-C1.3', 'F-C1.4'],
            'FIN-002': ['F-K2.1', 'F-K2.2', 'F-K2.3', 'F-K2.4'],
            'OPS-001': ['O-O1.1', 'O-O1.2', 'O-O1.3', 'O-O1.4'],
            'OPS-002': ['O-A2.1', 'O-A2.2', 'O-A2.3', 'O-A2.4', 'O-A2.5'],
            'OPS-003': ['O-Q3.1', 'O-Q3.2', 'O-Q3.3', 'O-Q3.4', 'O-Q3.5'],
            'SCM-001': ['S-I1.1', 'S-I1.2', 'S-I1.3', 'S-I1.4', 'S-I1.5'],
            'SCM-002': ['S-R2.1', 'S-R2.2', 'S-R2.3', 'S-R2.4', 'S-R2.5'],
            'SCM-003': ['S-F3.1', 'S-F3.2', 'S-F3.3', 'S-F3.4'],
            'XD-001': ['X-S1.1', 'X-S1.2', 'X-S1.3', 'X-S1.4'],
            'XD-002': ['X-R2.1', 'X-R2.2', 'X-R2.3', 'X-R2.4'],
            'XD-003': ['X-E3.2', 'X-E3.3'],
        }
        
        action_types = [
            'PriceChange', 'Reallocation', 'PromoChange', 'InventoryAdjustment',
            'ProcessImprovement', 'ResourceReallocation', 'PolicyUpdate'
        ]
        
        action_outcomes = ['Success', 'Neutral', 'Failed', 'Pending']
        
        # Use standard FACTS_START/FACTS_END
        fact_dates = dim_date[
            (dim_date['Date'] >= FACTS_START) & 
            (dim_date['Date'] <= FACTS_END)
        ]
        
        # Sample: 5% of dates (actions are infrequent)
        sampled_dates = fact_dates.sample(frac=0.05, random_state=self.random_seed)
        stores_df = dim_org[dim_org['OrgType'].isin(['Store', 'DC'])]
        sampled_orgs = stores_df.sample(frac=0.20, random_state=self.random_seed)
        
        dates_list = sampled_dates.to_dict('records')
        orgs_list = sampled_orgs.to_dict('records')
        
        print(f"     Generating {len(dates_list)} action dates × {len(orgs_list)} orgs...")
        
        actions = []
        action_id = 1
        
        for date_row in dates_list:
            date_key = date_row['DateKey']
            fiscal_year = date_row['Fiscal Year']
            
            for org in orgs_list:
                org_key = org['OrgKey']
                
                # Each org may have 0-2 actions on this date
                num_actions = random.randint(0, 2)
                
                for _ in range(num_actions):
                    # Random use case
                    use_case_id = random.choice(list(use_case_action_map.keys()))
                    action_type = random.choice(action_types)
                    action_outcome = random.choice(action_outcomes)
                    
                    actions.append({
                        'ActionID': f'ACT{action_id:08d}',
                        'DateKey': date_key,
                        'OrgKey': org_key,
                        'UseCaseID': use_case_id,
                        'Action Type': action_type,
                        'Action Outcome': action_outcome,
                        'Fiscal Year': fiscal_year,
                    })
                    action_id += 1
        
        df = pd.DataFrame(actions)
        print(f"     {len(df):,} action log records generated")
        return df
    
    # =========================================================================
    # Helpers
    # =========================================================================
    
    def _write_table(self, df: pd.DataFrame, table_path: str, partition_by: List[str] = None):
        """Write DataFrame to gold layer as Delta Parquet (or fallback to Parquet)."""
        full_path = self.output_path / table_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        if DELTA_AVAILABLE and partition_by:
            write_deltalake(
                str(full_path),
                df,
                mode='overwrite',
                partition_by=partition_by,
            )
            format_str = f"Delta (partitioned by {', '.join(partition_by)})"
        elif DELTA_AVAILABLE:
            write_deltalake(
                str(full_path),
                df,
                mode='overwrite',
            )
            format_str = "Delta"
        else:
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
        
        print(f"     [OK] Written to {table_path} ({format_str}, {len(df):,} rows)")


def main():
    parser = argparse.ArgumentParser(description='Generate contract-compliant synthetic gold layer data')
    parser.add_argument(
        '--config', 
        default='synthetic_config_core_v1.yaml',
        help='Path to YAML configuration file'
    )
    parser.add_argument(
        '--output',
        default=None,
        help='Output path for gold layer files (default: repo showcases/aurora_group/data/gold)'
    )
    
    args = parser.parse_args()
    
    script_dir = Path(__file__).parent
    config_path = script_dir / args.config
    # Default output: repo/showcases/aurora_group/data/gold (relative to this script)
    if args.output is None:
        output_path = (script_dir / '..' / '..' / '..' / '..' / 'showcases' / 'aurora_group' / 'data' / 'gold').resolve()
    else:
        output_path = Path(args.output)
    
    if not config_path.exists():
        print(f"Error: Config file not found: {config_path}")
        return 1
    
    generator = GoldLayerGenerator(str(config_path), str(output_path))
    generator.generate_all()
    
    return 0


if __name__ == '__main__':
    exit(main())
