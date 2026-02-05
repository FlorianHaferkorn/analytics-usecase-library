"""
Realistic Names Generator Module
=================================

Generates realistic, context-aware names for dimensions (Product, Promo, Org, Customer, Asset).
Uses company profile for brand consistency and regional flavor.

Usage:
    from _realistic_names import generate_product_name, generate_promo_name, generate_org_name
    
    name = generate_product_name(category="Fashion", subcategory="Apparel", profile=profile, seed=123)
"""

import random
from typing import Optional


def generate_product_name(
    category: str,
    subcategory: str,
    profile: dict,
    product_key: int,
    seed: Optional[int] = None,
) -> str:
    """
    Generate realistic product name based on category, subcategory, and company profile.
    
    Args:
        category: Product category (Fashion, Home & Living, Consumer Electronics)
        subcategory: Product subcategory (e.g., Apparel, Footwear, Furniture)
        profile: Company profile dictionary
        product_key: Unique product key for deterministic generation
        seed: Optional seed for reproducibility
    
    Returns:
        Realistic product name (e.g., "Aurora Premium Cotton T-Shirt - Navy - M")
    """
    if seed is not None:
        rng = random.Random(seed + product_key)
    else:
        rng = random.Random(product_key)
    
    brand = profile["brand_name"]
    cat_config = profile["product_categories"].get(category, {})
    attrs = cat_config.get("attributes", {})
    
    if category == "Fashion":
        # Fashion: Brand + Style + Material + Color + Size
        styles = ["Classic", "Premium", "Essential", "Designer", "Signature", "Luxury", "Casual", "Formal"]
        style = rng.choice(styles)
        material = rng.choice(attrs.get("materials", ["Cotton"]))
        color = rng.choice(attrs.get("colors", ["Black"]))
        size = rng.choice(attrs.get("sizes", ["M"]))
        
        if subcategory == "Footwear":
            types = ["Sneakers", "Boots", "Loafers", "Sandals", "Heels", "Flats"]
            type_name = rng.choice(types)
            return f"{brand} {style} {type_name} - {color}"
        elif subcategory == "Accessories":
            types = ["Handbag", "Wallet", "Belt", "Watch", "Sunglasses", "Scarf"]
            type_name = rng.choice(types)
            return f"{brand} {style} {type_name} - {color}"
        else:  # Apparel
            types = ["T-Shirt", "Shirt", "Dress", "Pants", "Jacket", "Sweater", "Jeans"]
            type_name = rng.choice(types)
            return f"{brand} {style} {material} {type_name} - {color} - {size}"
    
    elif category == "Home & Living":
        # Home & Living: Brand + Style + Type + Material/Color
        styles = ["Modern", "Classic", "Scandinavian", "Industrial", "Minimalist", "Rustic"]
        style = rng.choice(styles)
        material = rng.choice(attrs.get("materials", ["Wood"]))
        color = rng.choice(attrs.get("colors", ["Natural"]))
        
        if subcategory == "Furniture":
            types = ["Sofa", "Table", "Chair", "Cabinet", "Shelf", "Desk", "Bed"]
            type_name = rng.choice(types)
            return f"{brand} {style} {material} {type_name} - {color}"
        elif subcategory == "Decor":
            types = ["Vase", "Frame", "Mirror", "Rug", "Cushion", "Lamp"]
            type_name = rng.choice(types)
            return f"{brand} {style} {type_name} - {color}"
        else:
            types = ["Set", "Collection", "Bundle"]
            type_name = rng.choice(types)
            return f"{brand} {style} {subcategory} {type_name} - {color}"
    
    elif category == "Consumer Electronics":
        # Consumer Electronics: Brand + Specs + Type + Size
        specs = attrs.get("specs", ["Smart"])
        spec = rng.choice(specs)
        size = rng.choice(attrs.get("sizes", ["55\""]))
        
        if subcategory == "TVs":
            return f"{brand} {spec} {size} TV"
        elif subcategory == "Audio":
            types = ["Soundbar", "Speaker", "Headphones", "Earbuds"]
            type_name = rng.choice(types)
            return f"{brand} {spec} {type_name}"
        elif subcategory == "Computers":
            types = ["Laptop", "Desktop", "Tablet"]
            type_name = rng.choice(types)
            return f"{brand} {spec} {type_name}"
        else:
            return f"{brand} {spec} {subcategory}"
    
    # Fallback
    return f"{brand} {subcategory} {product_key}"


def generate_promo_name(
    profile: dict,
    promo_key: int,
    category: Optional[str] = None,
    seed: Optional[int] = None,
) -> str:
    """
    Generate realistic promotion name using company profile patterns.
    
    Args:
        profile: Company profile dictionary
        promo_key: Unique promo key for deterministic generation
        category: Optional product category for category-specific promos
        seed: Optional seed for reproducibility
    
    Returns:
        Realistic promo name (e.g., "Aurora Spring Sale", "Clearance Fashion")
    """
    if seed is not None:
        rng = random.Random(seed + promo_key)
    else:
        rng = random.Random(promo_key)
    
    brand = profile["brand_name"]
    patterns = profile["promo_naming"]["patterns"]
    seasons = profile["promo_naming"]["seasons"]
    
    pattern = rng.choice(patterns)
    season = rng.choice(seasons)
    
    # Replace placeholders
    name = pattern.format(
        brand=brand,
        season=season,
        category=category or rng.choice(["Fashion", "Home & Living", "Electronics"]),
    )
    
    return name


def generate_org_name(
    org_type: str,
    region: Optional[str],
    country: Optional[str],
    city: Optional[str],
    profile: dict,
    org_key: int,
    seed: Optional[int] = None,
) -> str:
    """
    Generate realistic organization name (store, DC, region).
    
    Args:
        org_type: Organization type (Store, DC, Region, Country)
        region: Region name (DACH, Benelux, etc.)
        country: Country name
        city: City name
        profile: Company profile dictionary
        org_key: Unique org key for deterministic generation
        seed: Optional seed for reproducibility
    
    Returns:
        Realistic org name (e.g., "Aurora Flagship Munich", "DC Amsterdam")
    """
    if seed is not None:
        rng = random.Random(seed + org_key)
    else:
        rng = random.Random(org_key)
    
    brand = profile["brand_name"]
    
    if org_type == "Store":
        store_types = profile["store_naming"]["store_types"]
        store_type = rng.choice(store_types)
        city_name = city or rng.choice(profile["regions"].get(region or "DACH", {}).get("cities", ["Unknown"]))
        return profile["store_naming"]["pattern"].format(
            brand=brand,
            store_type=store_type,
            city=city_name,
        )
    elif org_type == "DC":
        city_name = city or rng.choice(profile["regions"].get(region or "DACH", {}).get("cities", ["Unknown"]))
        return profile["dc_naming"]["pattern"].format(city=city_name)
    elif org_type == "Region":
        return f"Region {region}" if region else f"Region {org_key}"
    elif org_type == "Country":
        return country or f"Country {org_key}"
    elif org_type == "Group":
        return profile["company_name"]
    else:
        return f"{org_type} {org_key}"


def generate_customer_name(
    segment: str,
    profile: dict,
    customer_key: int,
    city: Optional[str] = None,
    seed: Optional[int] = None,
) -> str:
    """
    Generate realistic customer name (B2C or B2B).
    
    Args:
        segment: Customer segment (Loyalty, HighValue, B2B, etc.)
        profile: Company profile dictionary
        customer_key: Unique customer key for deterministic generation
        city: Optional city for B2B company names
        seed: Optional seed for reproducibility
    
    Returns:
        Realistic customer name
    """
    if seed is not None:
        rng = random.Random(seed + customer_key)
    else:
        rng = random.Random(customer_key)
    
    if segment in ["B2B", "Wholesale"]:
        # B2B: Use company name templates
        templates = profile["customer_naming"]["b2b_patterns"]
        company_templates = profile["customer_naming"]["company_name_templates"]
        pattern = rng.choice(templates)
        company_template = rng.choice(company_templates)
        city_name = city or rng.choice(["Berlin", "Munich", "Amsterdam"])
        company_name = company_template.format(city=city_name)
        return pattern.format(company_name=company_name, name=company_name)
    else:
        # B2C: Use retail customer patterns
        patterns = profile["customer_naming"]["b2c_patterns"]
        pattern = rng.choice(patterns)
        tier = rng.choice(["Gold", "Silver", "Platinum", "Standard"]) if "Loyalty" in segment else None
        return pattern.format(id=customer_key, tier=tier or "")


def generate_asset_name(
    asset_class: str,
    profile: dict,
    asset_key: int,
    seed: Optional[int] = None,
) -> str:
    """
    Generate realistic asset name (production line, warehouse, etc.).
    
    Args:
        asset_class: Asset class (Production Line, Warehouse, etc.)
        profile: Company profile dictionary
        asset_key: Unique asset key for deterministic generation
        seed: Optional seed for reproducibility
    
    Returns:
        Realistic asset name (e.g., "Production Line A-01")
    """
    if seed is not None:
        rng = random.Random(seed + asset_key)
    else:
        rng = random.Random(asset_key)
    
    patterns = profile["asset_naming"]["patterns"]
    code_formats = profile["asset_naming"]["code_formats"]
    
    # Find matching pattern or use first
    pattern = None
    for p in patterns:
        if asset_class.lower() in p.lower():
            pattern = p
            break
    if not pattern:
        pattern = rng.choice(patterns)
    
    code_format = rng.choice(code_formats)
    code = code_format.format(num=(asset_key % 100))
    
    return pattern.format(code=code)
