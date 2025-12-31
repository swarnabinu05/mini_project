from sqlalchemy import create_engine, Column, Integer, String, Float, Date
from sqlalchemy.ext.declarative import declarative_base

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
