from pydantic import BaseModel, field_validator
from typing import List, Optional
from datetime import date, datetime

class LineItem(BaseModel):
    description: str
    quantity: float
    unit_price: float
    total: float

class InvoiceData(BaseModel):
    invoice_id: Optional[str] = None
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    customer_name: Optional[str] = None
    total_amount: Optional[float] = None
    subtotal: Optional[float] = None
    tax_amount: Optional[float] = None
    tax_percentage: Optional[float] = None
    line_items: List[LineItem] = []
    
    @field_validator('invoice_date', 'due_date', mode='before')
    @classmethod
    def parse_date(cls, v):
        if v is None or v == "":
            return None
        if isinstance(v, str):
            # Try different date formats
            for fmt in ['%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y', '%m-%d-%Y', '%Y-%m-%d']:
                try:
                    return datetime.strptime(v, fmt).date()
                except ValueError:
                    continue
            return None
        return v
