"""
Company Profile Configuration Module
====================================

Centralized company-specific configuration for synthetic data generation.
Designed to be swappable for different showcases (Aurora, future companies).

Usage:
    from _company_profile import AURORA_PROFILE, get_company_profile
    
    profile = get_company_profile("aurora")
    # Use profile["brand_name"], profile["regions"], etc.
"""

AURORA_PROFILE = {
    "company_name": "Aurora Group SE",
    "brand_name": "Aurora",
    "regions": {
        "DACH": {
            "countries": ["Germany", "Austria", "Switzerland"],
            "cities": ["Munich", "Berlin", "Vienna", "Zurich", "Frankfurt", "Hamburg", "Stuttgart", "Cologne"],
            "country_codes": ["DE", "AT", "CH"],
        },
        "Benelux": {
            "countries": ["Netherlands", "Belgium", "Luxembourg"],
            "cities": ["Amsterdam", "Rotterdam", "Brussels", "Antwerp", "The Hague", "Utrecht", "Eindhoven"],
            "country_codes": ["NL", "BE", "LU"],
        },
        "Nordics": {
            "countries": ["Sweden", "Denmark", "Norway", "Finland"],
            "cities": ["Stockholm", "Gothenburg", "Copenhagen", "Oslo", "Helsinki", "Malmö", "Bergen"],
            "country_codes": ["SE", "NO", "DK", "FI"],
        },
        "SouthernEurope": {
            "countries": ["Italy", "Spain", "Portugal", "Greece"],
            "cities": ["Milan", "Rome", "Madrid", "Barcelona", "Lisbon", "Porto", "Athens", "Naples"],
            "country_codes": ["IT", "ES", "PT", "GR"],
        },
        "CEE": {
            "countries": ["Poland", "Czech Republic", "Hungary", "Slovakia"],
            "cities": ["Warsaw", "Krakow", "Prague", "Budapest", "Bratislava", "Wroclaw", "Gdansk"],
            "country_codes": ["PL", "CZ", "HU", "SK"],
        },
    },
    "store_naming": {
        "pattern": "{brand} {store_type} {city}",
        "store_types": ["Flagship", "Express", "Outlet", "Superstore", "Premium"],
    },
    "dc_naming": {
        "pattern": "DC {city}",
    },
    "promo_naming": {
        "patterns": [
            "{season} Sale",
            "Clearance {category}",
            "{brand} Days",
            "{season} {category} Collection",
            "Holiday {category} Special",
            "{brand} {season} Fashion Week",
            "End of Season {category}",
            "{brand} Black Friday",
            "{brand} Cyber Monday",
            "{season} Essentials",
        ],
        "seasons": ["Spring", "Summer", "Autumn", "Winter", "Holiday"],
    },
    "asset_naming": {
        "patterns": [
            "Production Line {code}",
            "Packaging Station {code}",
            "Quality Control {code}",
            "Warehouse {code}",
            "Assembly Line {code}",
            "Finishing Station {code}",
        ],
        "code_formats": ["A-{num:02d}", "B-{num:02d}", "C-{num:02d}", "P-{num:02d}", "Q-{num:02d}"],
    },
    "customer_naming": {
        "b2c_patterns": [
            "Retail Customer #{id}",
            "Loyalty Member - {tier}",
            "VIP Customer #{id}",
        ],
        "b2b_patterns": [
            "B2B Account - {company_name}",
            "Wholesale Partner - {name}",
            "Corporate Account - {name}",
        ],
        "company_name_templates": [
            "{city} Trading GmbH",
            "{city} Retail Solutions",
            "{city} Wholesale Co.",
            "TechCorp {city}",
            "{city} Business Partners",
        ],
    },
    "product_categories": {
        "Fashion": {
            "subcategories": ["Apparel", "Footwear", "Accessories", "Jewelry"],
            "attributes": {
                "sizes": ["XS", "S", "M", "L", "XL", "XXL"],
                "colors": ["Black", "White", "Navy", "Gray", "Beige", "Red", "Blue", "Green"],
                "materials": ["Cotton", "Polyester", "Wool", "Leather", "Denim", "Silk"],
            },
        },
        "Home & Living": {
            "subcategories": ["Furniture", "Decor", "Kitchenware", "Bedding", "Lighting"],
            "attributes": {
                "sizes": ["Small", "Medium", "Large", "Extra Large"],
                "colors": ["White", "Black", "Brown", "Gray", "Beige", "Natural"],
                "materials": ["Wood", "Metal", "Glass", "Fabric", "Ceramic"],
            },
        },
        "Consumer Electronics": {
            "subcategories": ["TVs", "Audio", "Computers", "Smartphones", "Gaming", "Accessories"],
            "attributes": {
                "sizes": ["32\"", "43\"", "55\"", "65\"", "75\"", "85\""],
                "colors": ["Black", "Silver", "White"],
                "specs": ["4K UHD", "8K", "OLED", "QLED", "Smart", "HDR"],
            },
        },
    },
}


def get_company_profile(company: str = "aurora") -> dict:
    """
    Get company profile configuration.
    
    Args:
        company: Company identifier ("aurora" or future companies)
    
    Returns:
        Dictionary with company-specific configuration
    
    Raises:
        ValueError: If company profile not found
    """
    profiles = {
        "aurora": AURORA_PROFILE,
    }
    
    if company.lower() not in profiles:
        raise ValueError(f"Company profile '{company}' not found. Available: {list(profiles.keys())}")
    
    return profiles[company.lower()]
