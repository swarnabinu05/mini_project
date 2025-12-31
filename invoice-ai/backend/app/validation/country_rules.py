from app.extraction.entities import InvoiceData

# Mock database of banned items for Russia
BANNED_ITEMS_RUSSIA = {"polythene"}

def validate_country_rules(invoice_data: InvoiceData, country: str) -> list[str]:
    """
    Validates invoice items against country-specific rules.

    Args:
        invoice_data: The extracted invoice data.
        country: The destination country.

    Returns:
        A list of error messages, or an empty list if validation passes.
    """
    errors = []
    if country.lower() == "russia":
        for item in invoice_data.line_items:
            if item.description.lower() in BANNED_ITEMS_RUSSIA:
                errors.append(f"Banned item for Russia: {item.description}")
    return errors
