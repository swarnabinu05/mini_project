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

    data = {
        'invoice_id': invoice_id.group(1).strip() if invoice_id else None,
        'invoice_date': invoice_date.group(1) if invoice_date else None,
        'due_date': due_date.group(1) if due_date else None,
        'customer_name': customer_name.group(1).strip() if customer_name else None,
        'total_amount': float(total_amount.group(1).replace(',', '')) if total_amount else None,
        'subtotal': float(subtotal.group(1).replace(',', '')) if subtotal else None,
        'tax_amount': float(tax_amount.group(1).replace(',', '')) if tax_amount else None,
        'tax_percentage': float(tax_percentage.group(1)) if tax_percentage else None,
    }

    return data
