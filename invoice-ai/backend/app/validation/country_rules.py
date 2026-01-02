from app.extraction.entities import InvoiceData

# Comprehensive country-specific rules database
COUNTRY_RULES = {
    "russia": {
        "banned_items": ["polythene", "plastic", "synthetic polymer"],
        "restricted_items": ["steel", "iron"],
        "max_value_usd": 2350000,
        "required_certificates": ["phytosanitary", "quality_certificate"]
    },
    "china": {
        "banned_items": ["cotton", "textile"],
        "restricted_items": ["electronics"],
        "max_value_usd": 100000,
        "required_certificates": ["origin_certificate"]
    },
    "usa": {
        "banned_items": ["certain_chemicals"],
        "restricted_items": ["food_products"],
        "max_value_usd": 200000,
        "required_certificates": ["fda_approval"]
    },
    "india": {
        "banned_items": ["gold", "silver"],
        "restricted_items": ["pharmaceuticals"],
        "max_value_usd": 75000,
        "required_certificates": ["import_license"]
    }
}

# Product-specific tax rates by country
# Tax rates are defined by HS Code (primary) or product keywords (secondary)
COUNTRY_TAX_RATES = {
    "russia": {
        "default_tax_rate": 20.0,  # Default VAT for Russia
        "hs_code_rates": {
            "870321": {"rate": 10.0, "description": "Passenger Cars"},
            "870322": {"rate": 10.0, "description": "Passenger Vehicles 1000-1500cc"},
            "870323": {"rate": 10.0, "description": "Passenger Vehicles 1500-3000cc"},
            "260111": {"rate": 5.0, "description": "Iron Ore Fines"},
            "260112": {"rate": 5.0, "description": "Iron Ore Agglomerated"},
            "720851": {"rate": 8.0, "description": "Steel Coils"},
            "720852": {"rate": 15.0, "description": "Steel Hot-Rolled"},
            "300490": {"rate": 50.0, "description": "Medicines/Pharmaceuticals"},
            "300410": {"rate": 50.0, "description": "Antibiotics"},
            "854231": {"rate": 18.0, "description": "Electronic Processors"},
            "847130": {"rate": 18.0, "description": "Laptops/Computers"},
        },
        "category_rates": {
            "automotive": {"rate": 10.0, "keywords": ["car", "vehicle", "automobile", "passenger"]},
            "metals": {"rate": 5.0, "keywords": ["iron ore", "ore fines"]},
            "steel": {"rate": 15.0, "keywords": ["steel", "coil", "hot-rolled"]},
            "medicines": {"rate": 50.0, "keywords": ["medicine", "drug", "pharmaceutical", "antibiotic"]},
            "electronics": {"rate": 18.0, "keywords": ["electronic", "computer", "laptop", "processor"]},
            "food": {"rate": 10.0, "keywords": ["food", "grain", "meat", "vegetable"]},
        }
    },
    "china": {
        "default_tax_rate": 13.0,  # Default VAT for China
        "hs_code_rates": {
            "870321": {"rate": 25.0, "description": "Passenger Cars"},
            "870322": {"rate": 25.0, "description": "Passenger Vehicles"},
            "260111": {"rate": 3.0, "description": "Iron Ore Fines"},
            "720851": {"rate": 13.0, "description": "Steel Coils"},
            "854231": {"rate": 13.0, "description": "Electronic Processors"},
            "520100": {"rate": 16.0, "description": "Cotton"},
        },
        "category_rates": {
            "automotive": {"rate": 25.0, "keywords": ["car", "vehicle", "automobile"]},
            "metals": {"rate": 3.0, "keywords": ["iron ore", "ore"]},
            "steel": {"rate": 13.0, "keywords": ["steel", "coil"]},
            "electronics": {"rate": 13.0, "keywords": ["electronic", "computer"]},
            "textiles": {"rate": 16.0, "keywords": ["cotton", "textile", "fabric"]},
        }
    },
    "usa": {
        "default_tax_rate": 0.0,  # No federal VAT in USA (state taxes vary)
        "hs_code_rates": {
            "870321": {"rate": 2.5, "description": "Passenger Cars"},
            "260111": {"rate": 0.0, "description": "Iron Ore Fines"},
            "720851": {"rate": 0.0, "description": "Steel Coils"},
            "300490": {"rate": 0.0, "description": "Medicines"},
        },
        "category_rates": {
            "automotive": {"rate": 2.5, "keywords": ["car", "vehicle"]},
            "metals": {"rate": 0.0, "keywords": ["iron", "steel", "metal"]},
            "medicines": {"rate": 0.0, "keywords": ["medicine", "drug"]},
        }
    },
    "india": {
        "default_tax_rate": 18.0,  # Default GST for India
        "hs_code_rates": {
            "870321": {"rate": 28.0, "description": "Passenger Cars"},
            "260111": {"rate": 5.0, "description": "Iron Ore Fines"},
            "720851": {"rate": 18.0, "description": "Steel Coils"},
            "300490": {"rate": 12.0, "description": "Medicines"},
            "710812": {"rate": 3.0, "description": "Gold"},
        },
        "category_rates": {
            "automotive": {"rate": 28.0, "keywords": ["car", "vehicle", "automobile"]},
            "metals": {"rate": 5.0, "keywords": ["iron ore", "ore"]},
            "steel": {"rate": 18.0, "keywords": ["steel", "coil"]},
            "medicines": {"rate": 12.0, "keywords": ["medicine", "drug", "pharmaceutical"]},
            "gold": {"rate": 3.0, "keywords": ["gold", "silver", "precious"]},
        }
    }
}


def get_product_tax_rate(country: str, hs_code: str = None, description: str = None) -> dict:
    """
    Get the tax rate for a product based on country, HS code, or description.
    
    Args:
        country: Destination country
        hs_code: HS Code of the product (optional)
        description: Product description (optional)
    
    Returns:
        dict with 'rate', 'source', and 'found' keys
        If tax info not found, returns {'found': False}
    """
    country_lower = country.lower()
    
    if country_lower not in COUNTRY_TAX_RATES:
        return {"found": False, "error": f"No tax rules defined for country: {country}"}
    
    tax_rules = COUNTRY_TAX_RATES[country_lower]
    
    # Priority 1: Match by HS Code (most precise)
    if hs_code:
        hs_code_clean = str(hs_code).strip()
        if hs_code_clean in tax_rules["hs_code_rates"]:
            rate_info = tax_rules["hs_code_rates"][hs_code_clean]
            return {
                "found": True,
                "rate": rate_info["rate"],
                "source": f"HS Code {hs_code_clean}",
                "description": rate_info["description"]
            }
    
    # Priority 2: Match by product category keywords
    if description:
        desc_lower = description.lower()
        for category, cat_info in tax_rules["category_rates"].items():
            for keyword in cat_info["keywords"]:
                if keyword in desc_lower:
                    return {
                        "found": True,
                        "rate": cat_info["rate"],
                        "source": f"Category: {category}",
                        "matched_keyword": keyword
                    }
    
    # No match found - return not found (will raise error)
    return {
        "found": False, 
        "error": f"No tax rate defined for product '{description}' (HS: {hs_code}) in {country}"
    }

def validate_country_rules(invoice_data: InvoiceData, country: str) -> list[str]:
    """
    Validates invoice items against comprehensive country-specific rules.

    Args:
        invoice_data: The extracted invoice data.
        country: The destination country.

    Returns:
        A list of error messages, or an empty list if validation passes.
    """
    errors = []
    country_lower = country.lower()
    
    if country_lower not in COUNTRY_RULES:
        return errors  # No rules defined for this country
    
    rules = COUNTRY_RULES[country_lower]
    
    # Check banned items
    for item in invoice_data.line_items:
        item_desc = item.description.lower()
        for banned_item in rules["banned_items"]:
            if banned_item in item_desc:
                errors.append(f"BANNED: '{item.description}' is prohibited for export to {country.title()}")
    
    # Check total value limits
    if invoice_data.total_amount and invoice_data.total_amount > rules["max_value_usd"]:
        errors.append(f"VALUE LIMIT EXCEEDED: Invoice total ${invoice_data.total_amount:.2f} exceeds maximum allowed ${rules['max_value_usd']:,} for {country.title()}")
    
    # Note: Restricted item validation is now handled separately in main.py with quality certificate
    
    return errors
