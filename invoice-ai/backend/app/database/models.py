from sqlalchemy import create_engine, Column, Integer, String, Float, Date, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(String, unique=True, index=True)
    invoice_date = Column(Date)
    due_date = Column(Date, nullable=True)
    customer_name = Column(String, nullable=True)
    total_amount = Column(Float)
    subtotal = Column(Float, nullable=True)
    tax_amount = Column(Float, nullable=True)
    tax_percentage = Column(Float, nullable=True)
    # New fields for fraud detection
    vendor_name = Column(String, nullable=True)  # Exporter name
    country = Column(String, nullable=True)  # Destination country
    created_at = Column(DateTime, default=datetime.utcnow)
    fraud_score = Column(Float, default=0.0)  # 0-100 risk score
    fraud_flags = Column(Text, nullable=True)  # JSON string of detected issues


class PriceHistory(Base):
    """Stores historical prices for products to detect anomalies"""
    __tablename__ = "price_history"
    
    id = Column(Integer, primary_key=True, index=True)
    hs_code = Column(String, index=True)
    product_description = Column(String)
    unit_price = Column(Float)
    vendor_name = Column(String, nullable=True)
    country = Column(String, nullable=True)
    recorded_at = Column(DateTime, default=datetime.utcnow)


class VendorScore(Base):
    """Tracks vendor reliability and risk scores"""
    __tablename__ = "vendor_scores"
    
    id = Column(Integer, primary_key=True, index=True)
    vendor_name = Column(String, unique=True, index=True)
    total_invoices = Column(Integer, default=0)
    successful_invoices = Column(Integer, default=0)  # Passed all validations
    failed_invoices = Column(Integer, default=0)  # Had validation errors
    total_amount_processed = Column(Float, default=0.0)
    risk_score = Column(Float, default=50.0)  # 0-100, lower is better
    last_invoice_date = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)


class InvoiceApproval(Base):
    """Workflow approval system for invoices"""
    __tablename__ = "invoice_approvals"
    
    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(String, index=True)
    invoice_db_id = Column(Integer, nullable=True)  # Reference to Invoice.id
    
    # Approval status: pending, approved, rejected, escalated
    status = Column(String, default="pending", index=True)
    
    # Approval levels
    level = Column(Integer, default=1)  # 1=Manager, 2=Finance, 3=Compliance
    current_approver = Column(String, nullable=True)
    
    # Invoice details for quick reference
    vendor_name = Column(String, nullable=True)
    country = Column(String, nullable=True)
    total_amount = Column(Float, nullable=True)
    fraud_score = Column(Float, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    approved_at = Column(DateTime, nullable=True)
    
    # Approver details
    approved_by = Column(String, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    comments = Column(Text, nullable=True)
    
    # Email notification tracking
    email_sent = Column(Boolean, default=False)
    email_sent_at = Column(DateTime, nullable=True)


class InvoiceLineItem(Base):
    """Stores line items for analytics"""
    __tablename__ = "invoice_line_items"
    
    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(String, index=True)
    description = Column(String)
    hs_code = Column(String, nullable=True, index=True)
    category = Column(String, nullable=True, index=True)  # passenger_cars, electronics, etc.
    quantity = Column(Float, default=1.0)
    unit_price = Column(Float, nullable=True)
    subtotal = Column(Float, nullable=True)
    tax_percentage = Column(Float, nullable=True)
    tax_amount = Column(Float, nullable=True)
    total = Column(Float, nullable=True)
    country = Column(String, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
