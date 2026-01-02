import re
from typing import Dict, Any
from .entities import InvoiceData

def parse_invoice(text: str) -> Dict[str, Any]:
    """
    Parses raw text from an invoice to extract structured data.
    This is a simple example using regular expressions.

    Args:
        text: The raw text extracted from the invoice.

    Returns:
        A dictionary containing the extracted invoice data.
    """
    # Enhanced regex patterns for common invoice fields
    invoice_id_pattern = re.compile(r'Invoice\s+(?:No|Number)[:.]?\s*([\w-]+)', re.IGNORECASE)
    date_pattern = re.compile(r'(?:Invoice\s+)?Date[:.]?\s*(\d{1,2}[-/]\d{1,2}[-/]\d{4})', re.IGNORECASE)
    due_date_pattern = re.compile(r'Due\s+Date[:.]?\s*(\d{1,2}[-/]\d{1,2}[-/]\d{4})', re.IGNORECASE)
    total_pattern = re.compile(r'(?:Grand\s+)?Total[:.]?\s*\$?([\d,]+\.?\d{0,2})', re.IGNORECASE)
    subtotal_pattern = re.compile(r'Subtotal[:.]?\s*\$?([\d,]+\.?\d{0,2})', re.IGNORECASE)
    tax_pattern = re.compile(r'Tax\s+Amount\s*(?:\([^)]*\))?\s*:\s*\$?([\d,]+\.?\d*)', re.IGNORECASE)
    tax_percentage_pattern = re.compile(r'Tax\s+Percentage\s*:\s*(\d+(?:\.\d+)?)%', re.IGNORECASE)
    customer_pattern = re.compile(r'(?:Bill\s+to|Customer|Importer)[:.]?\s*([^\n\r]+)', re.IGNORECASE)

    # Search for patterns
    invoice_id = invoice_id_pattern.search(text)
    invoice_date = date_pattern.search(text)
    due_date = due_date_pattern.search(text)
    total_amount = total_pattern.search(text)
    subtotal = subtotal_pattern.search(text)
    tax_amount = tax_pattern.search(text)
    tax_percentage = tax_percentage_pattern.search(text)
    customer_name = customer_pattern.search(text)

    # Extract line items from invoice text with HS codes, tax percentage, subtotal, and total
    line_items = []
    
    print(f"DEBUG PARSER: Searching for line items in text...")
    print(f"DEBUG PARSER: Full OCR text:\n{text}\n")
    
    # Process line by line to extract items from table
    lines = text.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check if line contains an HS code (6 digits) - indicates a product row
        hs_match = re.search(r'\b(\d{6})\b', line)
        if not hs_match:
            continue
            
        hs_code = hs_match.group(1)
        print(f"DEBUG PARSER: Found line with HS code {hs_code}: '{line}'")
        
        # Extract product name (text before the HS code)
        name_part = line[:hs_match.start()].strip()
        # Clean up the name
        name_match = re.match(r'^([A-Za-z\s]+)', name_part)
        item_description = name_match.group(1).strip() if name_match else name_part
        
        # Skip header rows
        if item_description.lower() in ['item', 'description', 'item description', 'item de', 'scription']:
            continue
        
        # Extract tax percentage
        tax_match = re.search(r'(\d+(?:\.\d+)?)\s*%', line)
        item_tax_pct = float(tax_match.group(1)) if tax_match else None
        
        # Extract all numbers from the line (after HS code)
        after_hs = line[hs_match.end():]
        numbers = re.findall(r'([\d,]+\.?\d*)', after_hs)
        numbers = [float(n.replace(',', '')) for n in numbers if n and '.' in n or float(n.replace(',', '')) > 0]
        
        print(f"DEBUG PARSER: Numbers found after HS code: {numbers}")
        
        # Expected order: Quantity, Unit Price, Tax%, Subtotal, Total
        # But tax% is already extracted, so remaining numbers are: Quantity(int), UnitPrice, Subtotal, Total
        item_quantity = 1.0
        item_unit_price = 0.0
        item_subtotal = 0.0
        item_total = 0.0
        
        # Filter out the tax percentage value from numbers if present
        if item_tax_pct and item_tax_pct in numbers:
            numbers = [n for n in numbers if n != item_tax_pct]
        
        # Parse numbers based on position and value
        # Last number is Total, second-to-last is Subtotal
        if len(numbers) >= 2:
            item_total = numbers[-1]
            item_subtotal = numbers[-2]
            if len(numbers) >= 3:
                item_unit_price = numbers[-3]
            if len(numbers) >= 4:
                item_quantity = numbers[-4]
        elif len(numbers) == 1:
            item_total = numbers[0]
        
        print(f"DEBUG PARSER: Parsed - qty:{item_quantity}, price:{item_unit_price}, subtotal:{item_subtotal}, total:{item_total}, tax:{item_tax_pct}%")
        
        # Avoid duplicates
        if item_description and not any(item['description'].lower() == item_description.lower() for item in line_items):
            item_data = {
                'description': item_description,
                'quantity': item_quantity,
                'unit_price': item_unit_price,
                'total': item_total,
                'hs_code': hs_code,
                'tax_percentage': item_tax_pct,
                'subtotal': item_subtotal
            }
            line_items.append(item_data)
            print(f"DEBUG PARSER: Added item: {item_data}")
    
    # Fallback: keyword-based extraction for items without full format
    if not line_items:
        restricted_keywords = ['iron ore', 'steel coil', 'steel sheet', 'iron', 'steel', 
                              'polythene', 'plastic', 'cotton', 'textile', 'electronics',
                              'passenger car', 'car', 'granule', 'medicine', 'pharmaceutical']
        
        lines = text.split('\n')
        print(f"DEBUG PARSER: Processing {len(lines)} lines from OCR text (fallback)")
        
        for line in lines:
            line_lower = line.lower().strip()
            
            for keyword in restricted_keywords:
                if keyword in line_lower:
                    print(f"DEBUG PARSER: Found keyword '{keyword}' in line: '{line}'")
                    
                    # Try to extract all fields from the line
                    hs_match = re.search(r'\b(\d{6})\b', line)
                    hs_code = hs_match.group(1) if hs_match else None
                    
                    # Try to extract tax percentage
                    tax_match = re.search(r'(\d+(?:\.\d+)?)\s*%', line)
                    tax_pct = float(tax_match.group(1)) if tax_match else None
                    
                    # Try to extract numbers (subtotal and total)
                    numbers = re.findall(r'([\d,]+\.?\d*)', line)
                    numbers = [float(n.replace(',', '')) for n in numbers if n and float(n.replace(',', '')) > 0]
                    
                    # Extract description
                    name_match = re.match(r'^([A-Za-z\s]+)', line.strip())
                    description = name_match.group(1).strip() if name_match else line.strip()
                    
                    # Avoid duplicates
                    if not any(item['description'].lower() == description.lower() for item in line_items):
                        item_data = {
                            'description': description,
                            'quantity': 1.0,
                            'unit_price': 0.0,
                            'total': numbers[-1] if numbers else 0.0,
                            'hs_code': hs_code,
                            'tax_percentage': tax_pct,
                            'subtotal': numbers[-2] if len(numbers) >= 2 else 0.0
                        }
                        line_items.append(item_data)
                        print(f"DEBUG PARSER: Added item from keyword: {item_data}")
                    break
    
    print(f"DEBUG PARSER: Total line items extracted: {len(line_items)}")

    data = {
        'invoice_id': invoice_id.group(1).strip() if invoice_id else None,
        'invoice_date': invoice_date.group(1) if invoice_date else None,
        'due_date': due_date.group(1) if due_date else None,
        'customer_name': customer_name.group(1).strip() if customer_name else None,
        'total_amount': float(total_amount.group(1).replace(',', '')) if total_amount else None,
        'subtotal': float(subtotal.group(1).replace(',', '')) if subtotal else None,
        'tax_amount': float(tax_amount.group(1).replace(',', '')) if tax_amount else None,
        'tax_percentage': float(tax_percentage.group(1)) if tax_percentage else None,
        'line_items': line_items,
    }

    return data
