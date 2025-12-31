from sqlalchemy.orm import Session
from . import models
from app.extraction.entities import InvoiceData
from typing import List

def create_invoice(db: Session, invoice: InvoiceData):
    db_invoice = models.Invoice(
        invoice_id=invoice.invoice_id,
        invoice_date=invoice.invoice_date,
        due_date=invoice.due_date,
        customer_name=invoice.customer_name,
        total_amount=invoice.total_amount,
        subtotal=invoice.subtotal,
        tax_amount=invoice.tax_amount,
        tax_percentage=invoice.tax_percentage
    )
    db.add(db_invoice)
    db.commit()
    db.refresh(db_invoice)
    return db_invoice

def get_all_invoices(db: Session) -> List[models.Invoice]:
    """Get all invoices from the database."""
    return db.query(models.Invoice).all()

def get_invoice_by_id(db: Session, invoice_id: str) -> models.Invoice:
    """Get a specific invoice by its invoice_id."""
    return db.query(models.Invoice).filter(models.Invoice.invoice_id == invoice_id).first()

def delete_all_invoices(db: Session) -> int:
    """Delete all invoices from the database."""
    count = db.query(models.Invoice).count()
    db.query(models.Invoice).delete()
    db.commit()
    return count
