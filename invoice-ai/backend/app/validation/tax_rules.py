from typing import List
from app.extraction.entities import InvoiceData

def validate_tax(invoice: InvoiceData) -> List[str]:
    """
    Validates tax calculations for an invoice by comparing calculated tax with actual tax.
    
    Args:
        invoice: The invoice data to validate.
        
    Returns:
        A list of validation errors, empty if valid.
    """
    errors = []
    
    # Check if we have all required fields for tax validation
    if not invoice.subtotal or not invoice.tax_percentage or not invoice.tax_amount:
        errors.append("Missing required fields for tax validation: subtotal, tax_percentage, or tax_amount")
        return errors
    
    # Calculate expected tax amount
    expected_tax = round((invoice.subtotal * invoice.tax_percentage / 100), 2)
    actual_tax = round(invoice.tax_amount, 2)
    
    # Compare with 2 decimal precision
    if abs(expected_tax - actual_tax) > 0.01:  # Allow 1 cent tolerance for rounding
        errors.append(f"Tax calculation mismatch: Expected ${expected_tax:.2f} ({invoice.tax_percentage}% of ${invoice.subtotal:.2f}), but found ${actual_tax:.2f}")
    
    # Additional validation: Check if tax rate is reasonable (between 0% and 50%)
    if invoice.tax_percentage < 0 or invoice.tax_percentage > 50:
        errors.append(f"Tax rate {invoice.tax_percentage}% seems unreasonable (should be 0-50%)")
    
    return errors
