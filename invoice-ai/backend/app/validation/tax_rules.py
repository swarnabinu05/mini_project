from typing import List
from app.extraction.entities import InvoiceData
from app.validation.country_rules import get_product_tax_rate, COUNTRY_TAX_RATES


def validate_tax(invoice: InvoiceData) -> List[str]:
    """
    Validates tax calculations for an invoice.
    Supports two formats:
    1. Invoice-level tax (subtotal, tax_percentage, tax_amount at invoice level)
    2. Per-item tax (each line item has its own tax_percentage, subtotal, total)
    
    Args:
        invoice: The invoice data to validate.
        
    Returns:
        A list of validation errors, empty if valid.
    """
    errors = []
    
    # Check if invoice has per-item tax (new format)
    has_per_item_tax = any(
        getattr(item, 'tax_percentage', None) is not None 
        for item in invoice.line_items
    )
    
    if has_per_item_tax:
        # Per-item tax validation is handled by validate_product_tax_rates
        # Skip the old invoice-level validation
        print("DEBUG TAX: Invoice has per-item tax, skipping invoice-level tax validation")
        return errors
    
    # Old format: Invoice-level tax validation
    if not invoice.subtotal or not invoice.tax_percentage or not invoice.tax_amount:
        # Only error if we don't have per-item taxes either
        if not has_per_item_tax:
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


def validate_product_tax_rates(invoice: InvoiceData, country: str) -> List[str]:
    """
    Validates that each product in the invoice has the correct tax rate for the destination country.
    Also validates:
    1. Each item's tax rate matches the country rules
    2. Each item's total = subtotal + (subtotal * tax%)
    3. Sum of all item totals = grand total
    
    Args:
        invoice: The invoice data with line items
        country: Destination country
        
    Returns:
        A list of validation errors, empty if valid.
    """
    errors = []
    country_lower = country.lower()
    
    print(f"DEBUG TAX: Validating product tax rates for country: {country}")
    
    # Check if country has tax rules defined
    if country_lower not in COUNTRY_TAX_RATES:
        errors.append(f"TAX ERROR: No tax rules defined for country '{country}'. Cannot validate tax rates.")
        return errors
    
    # Track calculated totals for grand total validation
    calculated_grand_total = 0.0
    
    for item in invoice.line_items:
        description = item.description
        hs_code = getattr(item, 'hs_code', None)
        item_tax_pct = getattr(item, 'tax_percentage', None)
        item_subtotal = getattr(item, 'subtotal', None)
        item_total = item.total
        
        print(f"DEBUG TAX: Checking product: '{description}' (HS: {hs_code})")
        print(f"DEBUG TAX: Item tax: {item_tax_pct}%, subtotal: {item_subtotal}, total: {item_total}")
        
        # 1. Look up the correct tax rate for this product
        tax_info = get_product_tax_rate(country, hs_code, description)
        
        if not tax_info["found"]:
            # Tax info not available - this is an error
            errors.append(
                f"TAX INFO MISSING: No tax rate defined for product '{description}' "
                f"(HS Code: {hs_code}) in {country.title()}. "
                f"Please add tax rate information to country rules."
            )
            print(f"DEBUG TAX: No tax info found for '{description}'")
        else:
            # Tax info found - check if item's tax rate matches the correct rate
            correct_rate = tax_info["rate"]
            source = tax_info["source"]
            
            print(f"DEBUG TAX: Correct tax rate for '{description}': {correct_rate}% (source: {source})")
            
            # Check if item's tax percentage matches the correct rate
            if item_tax_pct is not None and abs(item_tax_pct - correct_rate) > 0.01:
                errors.append(
                    f"TAX RATE ERROR: Product '{description}' should have {correct_rate}% tax rate "
                    f"for {country.title()} (source: {source}), but invoice shows {item_tax_pct}%"
                )
        
        # 2. Validate item total = subtotal + (subtotal * tax%)
        if item_subtotal is not None and item_tax_pct is not None and item_total is not None:
            expected_total = round(item_subtotal + (item_subtotal * item_tax_pct / 100), 2)
            actual_total = round(item_total, 2)
            
            print(f"DEBUG TAX: Expected total for '{description}': {expected_total} (subtotal {item_subtotal} + {item_tax_pct}% tax)")
            print(f"DEBUG TAX: Actual total for '{description}': {actual_total}")
            
            if abs(expected_total - actual_total) > 0.01:  # Allow 1 cent tolerance
                errors.append(
                    f"ITEM TOTAL ERROR: Product '{description}' total calculation mismatch. "
                    f"Expected ${expected_total:.2f} (subtotal ${item_subtotal:.2f} + {item_tax_pct}% tax), "
                    f"but invoice shows ${actual_total:.2f}"
                )
        
        # Add to calculated grand total
        if item_total:
            calculated_grand_total += item_total
    
    # 3. Validate sum of all item totals = grand total
    if invoice.total_amount and calculated_grand_total > 0:
        calculated_grand_total = round(calculated_grand_total, 2)
        invoice_grand_total = round(invoice.total_amount, 2)
        
        print(f"DEBUG TAX: Calculated grand total: ${calculated_grand_total}")
        print(f"DEBUG TAX: Invoice grand total: ${invoice_grand_total}")
        
        if abs(calculated_grand_total - invoice_grand_total) > 0.01:  # Allow 1 cent tolerance
            errors.append(
                f"GRAND TOTAL ERROR: Sum of item totals (${calculated_grand_total:.2f}) "
                f"does not match invoice grand total (${invoice_grand_total:.2f})"
            )
    
    print(f"DEBUG TAX: Validation complete. {len(errors)} errors found.")
    
    return errors
