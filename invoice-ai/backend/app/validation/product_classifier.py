"""
Smart Product Classification System

Automatically classifies products based on:
1. HS Code lookup (6-digit codes map to product categories)
2. Product name/brand recognition
3. Keyword matching

This allows the system to understand that "Mazda 6" or "Hyundai Exter" are cars,
even if the invoice doesn't explicitly say "car".
"""

from typing import Dict, Optional, Tuple, List
import re


# HS Code to Category Mapping (first 2-4 digits determine category)
# Reference: Harmonized System (HS) Code Structure
HS_CODE_CATEGORIES = {
    # Chapter 87: Vehicles other than railway
    "8703": {"category": "passenger_cars", "description": "Motor cars for transport of persons", "keywords": ["car", "vehicle", "automobile"]},
    "870321": {"category": "passenger_cars", "description": "Passenger vehicles <= 1000cc", "keywords": ["car", "small car"]},
    "870322": {"category": "passenger_cars", "description": "Passenger vehicles 1000-1500cc", "keywords": ["car", "sedan"]},
    "870323": {"category": "passenger_cars", "description": "Passenger vehicles 1500-3000cc", "keywords": ["car", "sedan", "suv"]},
    "870324": {"category": "passenger_cars", "description": "Passenger vehicles > 3000cc", "keywords": ["car", "luxury car"]},
    "8704": {"category": "trucks", "description": "Motor vehicles for goods transport", "keywords": ["truck", "lorry", "pickup"]},
    "8711": {"category": "motorcycles", "description": "Motorcycles and cycles", "keywords": ["motorcycle", "bike", "scooter"]},
    
    # Chapter 26: Ores, slag and ash
    "2601": {"category": "iron_ore", "description": "Iron ores and concentrates", "keywords": ["iron ore", "ore", "iron"]},
    "260111": {"category": "iron_ore", "description": "Iron ore non-agglomerated", "keywords": ["iron ore fines", "iron ore"]},
    "260112": {"category": "iron_ore", "description": "Iron ore agglomerated", "keywords": ["iron ore pellets", "iron ore"]},
    
    # Chapter 72: Iron and steel
    "7208": {"category": "steel_products", "description": "Flat-rolled iron/steel products", "keywords": ["steel", "steel sheet", "steel plate"]},
    "720851": {"category": "steel_products", "description": "Steel coils hot-rolled", "keywords": ["steel coil", "hot rolled steel"]},
    "720852": {"category": "steel_products", "description": "Steel sheets hot-rolled", "keywords": ["steel sheet", "hot rolled"]},
    "7209": {"category": "steel_products", "description": "Cold-rolled steel", "keywords": ["cold rolled steel", "steel"]},
    
    # Chapter 30: Pharmaceutical products
    "3004": {"category": "medicines", "description": "Medicaments for therapeutic use", "keywords": ["medicine", "drug", "pharmaceutical"]},
    "300490": {"category": "medicines", "description": "Other medicaments", "keywords": ["medicine", "tablet", "capsule"]},
    "300410": {"category": "medicines", "description": "Antibiotics", "keywords": ["antibiotic", "medicine"]},
    
    # Chapter 84: Machinery and mechanical appliances
    "8471": {"category": "electronics", "description": "Computers and data processing", "keywords": ["computer", "laptop", "server"]},
    "847130": {"category": "electronics", "description": "Portable computers", "keywords": ["laptop", "notebook", "portable computer"]},
    
    # Chapter 85: Electrical machinery
    "8542": {"category": "electronics", "description": "Electronic integrated circuits", "keywords": ["chip", "processor", "ic"]},
    "854231": {"category": "electronics", "description": "Processors and controllers", "keywords": ["processor", "cpu", "microprocessor"]},
    
    # Chapter 39: Plastics
    "3901": {"category": "plastics", "description": "Polymers of ethylene", "keywords": ["polythene", "polyethylene", "plastic"]},
    "390110": {"category": "plastics", "description": "Polyethylene granules", "keywords": ["polythene granules", "plastic granules"]},
    
    # Chapter 52: Cotton
    "5201": {"category": "textiles", "description": "Cotton, not carded or combed", "keywords": ["cotton", "raw cotton"]},
    "5208": {"category": "textiles", "description": "Woven cotton fabrics", "keywords": ["cotton fabric", "cotton cloth"]},
}


# Known brand/model to category mapping
BRAND_CATEGORY_MAP = {
    # Car brands
    "toyota": "passenger_cars",
    "honda": "passenger_cars",
    "hyundai": "passenger_cars",
    "mazda": "passenger_cars",
    "ford": "passenger_cars",
    "chevrolet": "passenger_cars",
    "bmw": "passenger_cars",
    "mercedes": "passenger_cars",
    "audi": "passenger_cars",
    "volkswagen": "passenger_cars",
    "nissan": "passenger_cars",
    "kia": "passenger_cars",
    "suzuki": "passenger_cars",
    "tata": "passenger_cars",
    "mahindra": "passenger_cars",
    "maruti": "passenger_cars",
    "skoda": "passenger_cars",
    "renault": "passenger_cars",
    "peugeot": "passenger_cars",
    "fiat": "passenger_cars",
    "jeep": "passenger_cars",
    "land rover": "passenger_cars",
    "jaguar": "passenger_cars",
    "porsche": "passenger_cars",
    "ferrari": "passenger_cars",
    "lamborghini": "passenger_cars",
    "tesla": "passenger_cars",
    "lexus": "passenger_cars",
    "infiniti": "passenger_cars",
    "acura": "passenger_cars",
    "volvo": "passenger_cars",
    "subaru": "passenger_cars",
    "mitsubishi": "passenger_cars",
    
    # Car models (common ones)
    "camry": "passenger_cars",
    "corolla": "passenger_cars",
    "civic": "passenger_cars",
    "accord": "passenger_cars",
    "exter": "passenger_cars",
    "creta": "passenger_cars",
    "venue": "passenger_cars",
    "i20": "passenger_cars",
    "i10": "passenger_cars",
    "verna": "passenger_cars",
    "tucson": "passenger_cars",
    "mazda 3": "passenger_cars",
    "mazda 6": "passenger_cars",
    "cx-5": "passenger_cars",
    "cx-30": "passenger_cars",
    "mustang": "passenger_cars",
    "f-150": "trucks",
    "silverado": "trucks",
    "ram": "trucks",
    "fortuner": "passenger_cars",
    "innova": "passenger_cars",
    "swift": "passenger_cars",
    "baleno": "passenger_cars",
    "alto": "passenger_cars",
    "wagonr": "passenger_cars",
    "seltos": "passenger_cars",
    "sonet": "passenger_cars",
    "carens": "passenger_cars",
    
    # Motorcycle brands
    "harley": "motorcycles",
    "ducati": "motorcycles",
    "kawasaki": "motorcycles",
    "yamaha": "motorcycles",
    "royal enfield": "motorcycles",
    "bajaj": "motorcycles",
    "hero": "motorcycles",
    "tvs": "motorcycles",
    
    # Electronics brands
    "dell": "electronics",
    "hp": "electronics",
    "lenovo": "electronics",
    "asus": "electronics",
    "acer": "electronics",
    "apple": "electronics",
    "macbook": "electronics",
    "thinkpad": "electronics",
    "intel": "electronics",
    "amd": "electronics",
    "nvidia": "electronics",
    
    # Pharmaceutical companies
    "pfizer": "medicines",
    "novartis": "medicines",
    "roche": "medicines",
    "johnson": "medicines",
    "merck": "medicines",
    "sanofi": "medicines",
    "glaxo": "medicines",
    "cipla": "medicines",
    "sun pharma": "medicines",
    "dr reddy": "medicines",
}


# Category to HS Code prefix mapping (for tax rate lookup)
CATEGORY_TO_HS_PREFIX = {
    "passenger_cars": "8703",
    "trucks": "8704",
    "motorcycles": "8711",
    "iron_ore": "2601",
    "steel_products": "7208",
    "medicines": "3004",
    "electronics": "8471",
    "plastics": "3901",
    "textiles": "5201",
}


def classify_by_hs_code(hs_code: str) -> Optional[Dict]:
    """
    Classify product by its HS code.
    Returns category info or None if not found.
    """
    if not hs_code:
        return None
    
    hs_code = str(hs_code).strip()
    
    # Try exact match first
    if hs_code in HS_CODE_CATEGORIES:
        return {
            "hs_code": hs_code,
            "source": "exact_hs_match",
            **HS_CODE_CATEGORIES[hs_code]
        }
    
    # Try prefix matches (6 -> 4 -> 2 digits)
    for length in [6, 4, 2]:
        prefix = hs_code[:length]
        if prefix in HS_CODE_CATEGORIES:
            return {
                "hs_code": hs_code,
                "matched_prefix": prefix,
                "source": f"hs_prefix_{length}",
                **HS_CODE_CATEGORIES[prefix]
            }
    
    return None


def classify_by_description(description: str) -> Optional[Dict]:
    """
    Classify product by its description using brand/model recognition.
    Returns category info or None if not found.
    """
    if not description:
        return None
    
    desc_lower = description.lower().strip()
    
    # Check for brand/model matches
    for brand, category in BRAND_CATEGORY_MAP.items():
        if brand in desc_lower:
            # Get the HS prefix for this category
            hs_prefix = CATEGORY_TO_HS_PREFIX.get(category, "")
            hs_info = HS_CODE_CATEGORIES.get(hs_prefix, {})
            
            return {
                "category": category,
                "matched_brand": brand,
                "source": "brand_recognition",
                "suggested_hs_prefix": hs_prefix,
                "description": hs_info.get("description", f"Identified as {category}"),
                "keywords": hs_info.get("keywords", [category])
            }
    
    # Check for direct keyword matches in HS categories
    for hs_code, info in HS_CODE_CATEGORIES.items():
        for keyword in info.get("keywords", []):
            if keyword.lower() in desc_lower:
                return {
                    "category": info["category"],
                    "matched_keyword": keyword,
                    "source": "keyword_match",
                    "suggested_hs_prefix": hs_code[:4],
                    **info
                }
    
    return None


def classify_product(description: str, hs_code: str = None) -> Dict:
    """
    Main classification function. Tries multiple methods to classify a product.
    
    Priority:
    1. HS Code lookup (most reliable)
    2. Brand/model recognition
    3. Keyword matching
    
    Returns classification result with category, confidence, and details.
    """
    result = {
        "original_description": description,
        "original_hs_code": hs_code,
        "classified": False,
        "category": None,
        "confidence": "none",
        "details": {}
    }
    
    # Method 1: HS Code lookup
    if hs_code:
        hs_result = classify_by_hs_code(hs_code)
        if hs_result:
            result["classified"] = True
            result["category"] = hs_result["category"]
            result["confidence"] = "high"
            result["details"] = hs_result
            result["classification_method"] = "hs_code"
            return result
    
    # Method 2: Description-based classification
    desc_result = classify_by_description(description)
    if desc_result:
        result["classified"] = True
        result["category"] = desc_result["category"]
        result["confidence"] = "medium" if desc_result["source"] == "brand_recognition" else "low"
        result["details"] = desc_result
        result["classification_method"] = desc_result["source"]
        
        # If we found a category but no HS code was provided, suggest one
        if not hs_code and "suggested_hs_prefix" in desc_result:
            result["suggested_hs_code"] = desc_result["suggested_hs_prefix"]
        
        return result
    
    # No classification found
    result["classification_method"] = "none"
    result["details"]["note"] = "Could not classify product - manual review recommended"
    
    return result


def get_tax_category_for_product(description: str, hs_code: str = None) -> Tuple[str, str]:
    """
    Get the tax category for a product.
    Used by tax validation to find the correct tax rate.
    
    Returns: (category_name, hs_code_prefix)
    """
    classification = classify_product(description, hs_code)
    
    if classification["classified"]:
        category = classification["category"]
        
        # If we have an HS code, use it
        if hs_code:
            return category, hs_code
        
        # Otherwise, use the suggested HS prefix
        suggested_hs = classification.get("suggested_hs_code") or \
                       classification["details"].get("suggested_hs_prefix") or \
                       CATEGORY_TO_HS_PREFIX.get(category, "")
        
        return category, suggested_hs
    
    return None, hs_code


def enrich_line_items(line_items: List) -> List[Dict]:
    """
    Enrich line items with classification data.
    Adds category and suggested HS codes to items that don't have them.
    """
    enriched = []
    
    for item in line_items:
        description = getattr(item, 'description', '') or item.get('description', '')
        hs_code = getattr(item, 'hs_code', None) or item.get('hs_code')
        
        classification = classify_product(description, hs_code)
        
        enriched_item = {
            "description": description,
            "hs_code": hs_code,
            "classification": classification
        }
        
        # Copy other fields
        for field in ['quantity', 'unit_price', 'total', 'tax_percentage', 'subtotal']:
            value = getattr(item, field, None) if hasattr(item, field) else item.get(field)
            if value is not None:
                enriched_item[field] = value
        
        # Add suggested HS code if missing
        if not hs_code and classification["classified"]:
            enriched_item["suggested_hs_code"] = classification.get("suggested_hs_code") or \
                                                  classification["details"].get("suggested_hs_prefix")
        
        enriched.append(enriched_item)
    
    return enriched


# Example usage and testing
if __name__ == "__main__":
    # Test cases
    test_products = [
        ("Hyundai Exter", None),
        ("Mazda 6 Sedan", None),
        ("Iron Ore Fines", "260111"),
        ("Steel Coils Hot Rolled", "720851"),
        ("Dell Laptop XPS 15", None),
        ("Paracetamol Tablets 500mg", None),
        ("Unknown Product XYZ", None),
        ("Toyota Camry 2024", "870323"),
    ]
    
    print("Product Classification Test Results:")
    print("=" * 60)
    
    for desc, hs in test_products:
        result = classify_product(desc, hs)
        print(f"\nProduct: {desc}")
        print(f"  HS Code: {hs or 'Not provided'}")
        print(f"  Category: {result['category'] or 'Unknown'}")
        print(f"  Confidence: {result['confidence']}")
        print(f"  Method: {result['classification_method']}")
        if result.get('suggested_hs_code'):
            print(f"  Suggested HS: {result['suggested_hs_code']}")
