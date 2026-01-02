import re
from typing import Dict, List, Optional
from app.extraction.entities import LineItem

class QualityCertificate:
    def __init__(self):
        self.exporter_name: Optional[str] = None
        self.hs_codes: List[Dict[str, str]] = []  # [{"hs_code": "1234", "description": "Steel"}]
        self.validity_date: Optional[str] = None
        self.has_signature: bool = False

def parse_quality_certificate(text: str) -> QualityCertificate:
    """
    Parses quality certificate text to extract HS codes, exporter info, and signature.
    
    Args:
        text: Raw OCR text from quality certificate
        
    Returns:
        QualityCertificate object with extracted data
    """
    certificate = QualityCertificate()
    
    # Extract exporter name
    exporter_pattern = re.compile(r'presented\s+to\s*:\s*([^\n\r]+)', re.IGNORECASE)
    exporter_match = exporter_pattern.search(text)
    if exporter_match:
        certificate.exporter_name = exporter_match.group(1).strip()
    
    # Extract validity/expiry date
    validity_pattern = re.compile(r'validity\s*:\s*(\d{1,2}[-/]\d{1,2}[-/]\d{4})', re.IGNORECASE)
    validity_match = validity_pattern.search(text)
    if validity_match:
        certificate.validity_date = validity_match.group(1)
    
    # Extract HS codes and descriptions from table
    # Pattern for HS code entries: "HS Code: 1234" followed by description
    hs_patterns = [
        re.compile(r'hs\s+code\s*:\s*(\d{4,8})\s*([^\n\r]+)', re.IGNORECASE),
        re.compile(r'(\d{4,8})\s*[-–]\s*([A-Za-z\s]+(?:Steel|Iron|Granules|Plastic|Cotton|Textile|Electronics))', re.IGNORECASE),
        re.compile(r'(\d{4,8})\s+([A-Za-z\s]+)', re.IGNORECASE)
    ]
    
    for pattern in hs_patterns:
        matches = pattern.findall(text)
        for match in matches:
            hs_code, description = match
            certificate.hs_codes.append({
                "hs_code": hs_code.strip(),
                "description": description.strip()
            })
    
    # Check for signature presence
    signature_patterns = [
        re.compile(r'signature', re.IGNORECASE),
        re.compile(r'certificating\s+authority', re.IGNORECASE),
        re.compile(r'authorized\s+signatory', re.IGNORECASE)
    ]
    
    certificate.has_signature = any(pattern.search(text) for pattern in signature_patterns)
    
    return certificate

def validate_restricted_items_against_certificate(
    restricted_items: List[LineItem], 
    certificate: QualityCertificate
) -> List[str]:
    """
    Validates that all restricted items in invoice are covered by quality certificate.
    
    Args:
        restricted_items: List of restricted items from invoice
        certificate: Parsed quality certificate data
        
    Returns:
        List of validation errors
    """
    errors = []
    
    # Debug logging
    print(f"DEBUG: Validating {len(restricted_items)} restricted items against certificate")
    for item in restricted_items:
        print(f"DEBUG: Restricted item: '{item.description}'")
    
    print(f"DEBUG: Certificate has {len(certificate.hs_codes)} entries:")
    for entry in certificate.hs_codes:
        print(f"DEBUG: Certificate entry: '{entry['description']}' (HS: {entry['hs_code']})")
    
    # Check if certificate has signature
    if not certificate.has_signature:
        errors.append("INVALID CERTIFICATE: Quality certificate missing required signature from certificating authority")
        return errors  # If no signature, reject immediately
    
    # Check each restricted item against certificate
    for item in restricted_items:
        item_covered = False
        item_desc_lower = item.description.lower().strip()
        item_hs_code = getattr(item, 'hs_code', None)
        
        print(f"DEBUG CERT: Checking item '{item.description}' (HS: {item_hs_code}) against certificate entries...")
        
        for cert_entry in certificate.hs_codes:
            cert_desc_lower = cert_entry["description"].lower().strip()
            cert_hs_code = cert_entry.get("hs_code", "")
            
            print(f"DEBUG CERT: Comparing invoice '{item_desc_lower}' with cert '{cert_desc_lower}'")
            
            # Method 1: HS Code matching (most reliable)
            if item_hs_code and cert_hs_code and item_hs_code == cert_hs_code:
                item_covered = True
                print(f"DEBUG CERT: HS CODE MATCH for '{item.description}' (HS: {item_hs_code})")
                break
            
            # Method 2: Exact or substring matching
            if item_desc_lower in cert_desc_lower or cert_desc_lower in item_desc_lower:
                item_covered = True
                print(f"DEBUG CERT: EXACT/SUBSTRING MATCH for '{item.description}'")
                break
            
            # Method 3: Keyword matching - at least 2 common words
            item_words = set(item_desc_lower.split())
            cert_words = set(cert_desc_lower.split())
            common_words = item_words.intersection(cert_words)
            
            print(f"DEBUG CERT: Common words: {common_words}")
            
            if len(common_words) >= 2:
                item_covered = True
                print(f"DEBUG CERT: KEYWORD MATCH (2+ words) for '{item.description}'")
                break
            
            # Method 4: Primary product word matching (iron, steel, ore, coil, fines)
            primary_words = {'iron', 'steel', 'ore', 'coil', 'coils', 'fines', 'fine'}
            item_primary = item_words.intersection(primary_words)
            cert_primary = cert_words.intersection(primary_words)
            
            if item_primary and item_primary == cert_primary:
                item_covered = True
                print(f"DEBUG CERT: PRIMARY WORD MATCH for '{item.description}' ({item_primary})")
                break
        
        if not item_covered:
            print(f"DEBUG CERT: Item '{item.description}' is NOT COVERED by certificate")
            errors.append(f"CERTIFICATE MISSING: Restricted item '{item.description}' not found in quality certificate")
    
    return errors
