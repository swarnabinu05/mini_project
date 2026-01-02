"""
Invoice Analytics Dashboard

Provides analytics and statistics for:
- Invoices by country, product category, month
- Tax collected by product type
- Top vendors/importers by volume
"""

from typing import Dict, List, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import datetime, timedelta
from collections import defaultdict

from app.database import models


def get_invoices_by_country(db: Session) -> Dict[str, Any]:
    """Get invoice count and total amount grouped by country."""
    results = db.query(
        models.Invoice.country,
        func.count(models.Invoice.id).label('count'),
        func.sum(models.Invoice.total_amount).label('total_amount')
    ).filter(
        models.Invoice.country.isnot(None)
    ).group_by(
        models.Invoice.country
    ).all()
    
    data = []
    for row in results:
        data.append({
            "country": row.country or "Unknown",
            "invoice_count": row.count,
            "total_amount": round(row.total_amount or 0, 2)
        })
    
    return {
        "title": "Invoices by Country",
        "data": sorted(data, key=lambda x: x['total_amount'], reverse=True),
        "chart_type": "bar"
    }


def get_invoices_by_category(db: Session) -> Dict[str, Any]:
    """Get invoice line items grouped by product category."""
    results = db.query(
        models.InvoiceLineItem.category,
        func.count(models.InvoiceLineItem.id).label('count'),
        func.sum(models.InvoiceLineItem.total).label('total_amount'),
        func.sum(models.InvoiceLineItem.tax_amount).label('total_tax')
    ).filter(
        models.InvoiceLineItem.category.isnot(None)
    ).group_by(
        models.InvoiceLineItem.category
    ).all()
    
    data = []
    for row in results:
        data.append({
            "category": row.category or "Other",
            "item_count": row.count,
            "total_amount": round(row.total_amount or 0, 2),
            "total_tax": round(row.total_tax or 0, 2)
        })
    
    return {
        "title": "Invoices by Product Category",
        "data": sorted(data, key=lambda x: x['total_amount'], reverse=True),
        "chart_type": "pie"
    }


def get_invoices_by_month(db: Session, months: int = 12) -> Dict[str, Any]:
    """Get invoice count and total amount grouped by month."""
    cutoff_date = datetime.utcnow() - timedelta(days=months * 30)
    
    results = db.query(
        extract('year', models.Invoice.created_at).label('year'),
        extract('month', models.Invoice.created_at).label('month'),
        func.count(models.Invoice.id).label('count'),
        func.sum(models.Invoice.total_amount).label('total_amount')
    ).filter(
        models.Invoice.created_at >= cutoff_date
    ).group_by(
        extract('year', models.Invoice.created_at),
        extract('month', models.Invoice.created_at)
    ).order_by(
        extract('year', models.Invoice.created_at),
        extract('month', models.Invoice.created_at)
    ).all()
    
    data = []
    month_names = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    for row in results:
        year = int(row.year) if row.year else 0
        month = int(row.month) if row.month else 0
        data.append({
            "month": f"{month_names[month]} {year}",
            "year": year,
            "month_num": month,
            "invoice_count": row.count,
            "total_amount": round(row.total_amount or 0, 2)
        })
    
    return {
        "title": "Invoices by Month",
        "data": data,
        "chart_type": "line"
    }


def get_tax_by_product_type(db: Session) -> Dict[str, Any]:
    """Get tax collected grouped by product category/HS code."""
    results = db.query(
        models.InvoiceLineItem.category,
        models.InvoiceLineItem.hs_code,
        func.sum(models.InvoiceLineItem.tax_amount).label('total_tax'),
        func.avg(models.InvoiceLineItem.tax_percentage).label('avg_tax_rate'),
        func.count(models.InvoiceLineItem.id).label('item_count')
    ).group_by(
        models.InvoiceLineItem.category,
        models.InvoiceLineItem.hs_code
    ).having(
        func.sum(models.InvoiceLineItem.tax_amount) > 0
    ).all()
    
    data = []
    for row in results:
        data.append({
            "category": row.category or "Other",
            "hs_code": row.hs_code,
            "total_tax_collected": round(row.total_tax or 0, 2),
            "avg_tax_rate": round(row.avg_tax_rate or 0, 2),
            "item_count": row.item_count
        })
    
    return {
        "title": "Tax Collected by Product Type",
        "data": sorted(data, key=lambda x: x['total_tax_collected'], reverse=True),
        "chart_type": "bar"
    }


def get_top_vendors(db: Session, limit: int = 10) -> Dict[str, Any]:
    """Get top vendors by invoice volume and amount."""
    results = db.query(
        models.VendorScore.vendor_name,
        models.VendorScore.total_invoices,
        models.VendorScore.total_amount_processed,
        models.VendorScore.successful_invoices,
        models.VendorScore.failed_invoices,
        models.VendorScore.risk_score
    ).order_by(
        models.VendorScore.total_amount_processed.desc()
    ).limit(limit).all()
    
    data = []
    for row in results:
        success_rate = (row.successful_invoices / row.total_invoices * 100) if row.total_invoices > 0 else 0
        data.append({
            "vendor_name": row.vendor_name,
            "total_invoices": row.total_invoices,
            "total_amount": round(row.total_amount_processed or 0, 2),
            "success_rate": round(success_rate, 1),
            "risk_score": round(row.risk_score or 50, 2)
        })
    
    return {
        "title": "Top Vendors by Volume",
        "data": data,
        "chart_type": "table"
    }


def get_top_importers(db: Session, limit: int = 10) -> Dict[str, Any]:
    """Get top importers (customers) by invoice volume."""
    results = db.query(
        models.Invoice.customer_name,
        func.count(models.Invoice.id).label('invoice_count'),
        func.sum(models.Invoice.total_amount).label('total_amount')
    ).filter(
        models.Invoice.customer_name.isnot(None)
    ).group_by(
        models.Invoice.customer_name
    ).order_by(
        func.sum(models.Invoice.total_amount).desc()
    ).limit(limit).all()
    
    data = []
    for row in results:
        data.append({
            "importer_name": row.customer_name,
            "invoice_count": row.invoice_count,
            "total_amount": round(row.total_amount or 0, 2)
        })
    
    return {
        "title": "Top Importers by Volume",
        "data": data,
        "chart_type": "table"
    }


def get_dashboard_summary(db: Session) -> Dict[str, Any]:
    """Get overall dashboard summary statistics."""
    # Total invoices
    total_invoices = db.query(func.count(models.Invoice.id)).scalar() or 0
    
    # Total amount processed
    total_amount = db.query(func.sum(models.Invoice.total_amount)).scalar() or 0
    
    # Total tax collected
    total_tax = db.query(func.sum(models.InvoiceLineItem.tax_amount)).scalar() or 0
    
    # Invoices this month
    month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    invoices_this_month = db.query(func.count(models.Invoice.id)).filter(
        models.Invoice.created_at >= month_start
    ).scalar() or 0
    
    # Pending approvals
    pending_approvals = db.query(func.count(models.InvoiceApproval.id)).filter(
        models.InvoiceApproval.status == "pending"
    ).scalar() or 0
    
    # High risk invoices
    high_risk = db.query(func.count(models.Invoice.id)).filter(
        models.Invoice.fraud_score >= 70
    ).scalar() or 0
    
    # Unique countries
    unique_countries = db.query(func.count(func.distinct(models.Invoice.country))).scalar() or 0
    
    # Unique vendors
    unique_vendors = db.query(func.count(models.VendorScore.id)).scalar() or 0
    
    return {
        "summary": {
            "total_invoices": total_invoices,
            "total_amount_processed": round(total_amount, 2),
            "total_tax_collected": round(total_tax, 2),
            "invoices_this_month": invoices_this_month,
            "pending_approvals": pending_approvals,
            "high_risk_invoices": high_risk,
            "unique_countries": unique_countries,
            "unique_vendors": unique_vendors
        },
        "generated_at": datetime.utcnow().isoformat()
    }


def get_full_dashboard(db: Session) -> Dict[str, Any]:
    """Get complete dashboard with all analytics."""
    return {
        "summary": get_dashboard_summary(db),
        "charts": {
            "by_country": get_invoices_by_country(db),
            "by_category": get_invoices_by_category(db),
            "by_month": get_invoices_by_month(db),
            "tax_by_product": get_tax_by_product_type(db),
            "top_vendors": get_top_vendors(db),
            "top_importers": get_top_importers(db)
        }
    }
