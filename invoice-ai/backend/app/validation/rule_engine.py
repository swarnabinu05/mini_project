from app.extraction.entities import InvoiceData
from .tax_rules import validate_tax
from .country_rules import validate_country_rules

def validate_invoice(invoice_data: InvoiceData, country: str) -> list[str]:
    """
    Runs all validation rules against the invoice data.

    Args:
        invoice_data: The extracted invoice data.
        country: The destination country.

    Returns:
        A list of all validation errors.
    """
    errors = []
    errors.extend(validate_tax(invoice_data))
    errors.extend(validate_country_rules(invoice_data, country))
    return errors
