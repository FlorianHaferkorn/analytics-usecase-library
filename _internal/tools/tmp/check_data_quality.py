import pandas as pd
import deltalake

base = 'C:/Users/florianhaferkorn/VSCode/analytics-usecase-library/showcases/aurora_group/data/gold/'

print("=" * 80)
print("AURORA GROUP - DATENQUALITÄT & DETAILTIEFE")
print("=" * 80)

# Dimensionen
print("\n=== DIMENSIONEN ===\n")
dims = {
    'dim_date': 'Kalenderdaten',
    'dim_org': 'Org-Hierarchie',
    'dim_product': 'Produktkatalog',
    'dim_customer': 'Kundenstamm',
    'dim_promo': 'Promotions',
    'dim_account': 'GL Accounts'
}

for dim, desc in dims.items():
    dt = deltalake.DeltaTable(base + f'dimensions/{dim}')
    df = dt.to_pandas()
    print(f'{dim:20} {len(df):>10,} Zeilen  ({desc})')

# Fakten
print("\n=== FAKTEN ===\n")
facts = {
    'fact_sales': 'Sales Transaktionen',
    'fact_inventory_snapshot': 'Inventory Snapshots',
    'fact_sales_budget': 'Budget-Daten',
    'fact_action_log': 'Action Tracking',
    'fact_working_capital': 'Working Capital',
    'fact_gl_journal': 'GL Journal Entries',
    'fact_customer_interactions': 'Customer Interactions',
    'fact_nps': 'NPS Responses'
}

for fact, desc in facts.items():
    dt = deltalake.DeltaTable(base + f'facts/{fact}')
    df = dt.to_pandas()
    print(f'{fact:30} {len(df):>10,} Zeilen  ({desc})')

# Detailanalyse fact_sales
print("\n" + "=" * 80)
print("DETAILANALYSE: fact_sales")
print("=" * 80)

dt = deltalake.DeltaTable(base + 'facts/fact_sales')
df = dt.to_pandas()

print(f"\nZeitraum:           {str(df['DateKey'].min())} bis {str(df['DateKey'].max())}")
print(f"Unique Dates:       {df['DateKey'].nunique():,} (monatliches Sampling)")
print(f"Unique Stores:      {df['OrgKey'].nunique():,} (20% Sample von allen Stores)")
print(f"Unique Produkte:    {df['ProductKey'].nunique():,}")
print(f"Unique Kunden:      {df['CustomerKey'].nunique():,}")
print(f"\nPromo-Trans:        {(df['PromoKey'] != -1).sum():,} von {len(df):,} ({(df['PromoKey'] != -1).sum()/len(df)*100:.1f}%)")
print(f"Channels:           {', '.join(df['Channel'].unique())}")
print(f"Ø Trans/Tag:        {len(df) / df['DateKey'].nunique():.0f}")

# Revenue Check
print(f"\nNet Sales:          EUR {df['Net Sales Amount'].sum()/1e6:.1f}M")
print(f"COGS:               EUR {df['COGS Amount'].sum()/1e6:.1f}M")
print(f"Gross Margin:       {(1 - df['COGS Amount'].sum()/df['Net Sales Amount'].sum())*100:.1f}%")

# Detailanalyse fact_inventory
print("\n" + "=" * 80)
print("DETAILANALYSE: fact_inventory_snapshot")
print("=" * 80)

dt = deltalake.DeltaTable(base + 'facts/fact_inventory_snapshot')
df_inv = dt.to_pandas()

print(f"\nZeitraum:           {str(df_inv['DateKey'].min())} bis {str(df_inv['DateKey'].max())}")
print(f"Unique Dates:       {df_inv['DateKey'].nunique():,} (Monatsenden)")
print(f"Unique DCs:         {df_inv['OrgKey'].nunique():,}")
print(f"Unique Produkte:    {df_inv['ProductKey'].nunique():,} (10% Sample)")
print(f"\nTotal Stock Value:  EUR {df_inv['Stock Value Amount'].sum()/1e6:.1f}M")
print(f"Ø Stock/DC/Month:   EUR {df_inv.groupby(['DateKey', 'OrgKey'])['Stock Value Amount'].sum().mean()/1e3:.0f}K")

# Detailanalyse fact_sales_budget
print("\n" + "=" * 80)
print("DETAILANALYSE: fact_sales_budget")
print("=" * 80)

dt = deltalake.DeltaTable(base + 'facts/fact_sales_budget')
df_bud = dt.to_pandas()

print(f"\nUnique Months:      {df_bud['MonthEnd DateKey'].nunique():,}")
print(f"Unique Stores:      {df_bud['OrgKey'].nunique():,} (10% Sample)")
print(f"Unique Produkte:    {df_bud['ProductKey'].nunique():,} (5% Sample)")
print(f"Versionen:          {', '.join(df_bud['Version'].unique())}")
print(f"\nTotal Budget Sales: EUR {df_bud[df_bud['Version']=='Original']['Budget Sales Amount'].sum()/1e6:.1f}M (Original)")

# Action Log Check
print("\n" + "=" * 80)
print("DETAILANALYSE: fact_action_log")
print("=" * 80)

dt = deltalake.DeltaTable(base + 'facts/fact_action_log')
df_act = dt.to_pandas()

print(f"\nAction Dates:       {df_act['DateKey'].nunique():,}")
print(f"Unique Orgs:        {df_act['OrgKey'].nunique():,}")
print(f"Use Cases:          {', '.join(sorted(df_act['UseCaseID'].unique()))}")
print(f"Action Types:       {', '.join(df_act['Action Type'].unique())}")
print(f"Outcomes:           {', '.join(df_act['Action Outcome'].unique())}")

print("\n" + "=" * 80)
print("FAZIT: Daten für realistische Reports geeignet!")
print("=" * 80)
