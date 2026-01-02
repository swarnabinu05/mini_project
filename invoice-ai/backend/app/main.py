import os
import shutil
from fastapi import FastAPI, File, UploadFile, Form, Depends
from typing import Optional
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from pdf2image import convert_from_path
from openpyxl import Workbook
from pathlib import Path

from app.ocr.text_ocr import extract_text_from_image
from app.extraction.invoice_parser import parse_invoice
from app.extraction.entities import InvoiceData
from app.extraction.certificate_parser import parse_quality_certificate, validate_restricted_items_against_certificate
from app.validation.rule_engine import validate_invoice
from app.validation.tax_rules import validate_product_tax_rates
from app.validation.fraud_detection import run_fraud_detection, update_vendor_score, record_price_history
from app.validation.product_classifier import classify_product, enrich_line_items
from app.signing.signer import add_signature_to_pdf
from app.database import crud, models
from app.database.session import engine, get_db
from app.analytics.dashboard import get_full_dashboard, get_dashboard_summary, get_invoices_by_country, get_invoices_by_category, get_invoices_by_month, get_tax_by_product_type, get_top_vendors, get_top_importers
from app.workflow.approval import create_approval_request, approve_invoice, reject_invoice, get_pending_approvals, get_approval_status, get_approval_dashboard, configure_email, set_approver_email, APPROVAL_LEVELS

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Invoice AI API", description="Intelligent Invoice Processing System")

# Add CORS middleware for frontend communication
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directories
TEMP_DIR = "d:\\minipro\\invoice-ai\\backend\\temp"
SIGNED_INVOICES_DIR = "d:\\minipro\\invoice-ai\\backend\\data\\signed_invoices"
ASSETS_DIR = "d:\\minipro\\invoice-ai\\backend\\assets"
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(SIGNED_INVOICES_DIR, exist_ok=True)
os.makedirs(ASSETS_DIR, exist_ok=True)

SIGNATURE_PATH = os.path.join(ASSETS_DIR, "signature.png")

@app.post("/invoice/")
async def upload_invoice(
    file: UploadFile = File(...),
    country: str = Form(...),
    quality_certificate: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """
    Receives an invoice file, processes it, and if valid, signs it and updates the database.
    """
    temp_file_path = os.path.join(TEMP_DIR, file.filename)
    try:
        # Save uploaded file
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Extract text from file
        try:
            if file.content_type == "application/pdf":
                images = convert_from_path(temp_file_path)
                extracted_text = extract_text_from_image(images[0]) if images else ""
            else:
                extracted_text = extract_text_from_image(temp_file_path)
        except Exception as e:
            return {"filename": file.filename, "status": "error", "message": f"OCR processing failed: {str(e)}"}

        # Parse extracted text
        try:
            print(f"DEBUG MAIN: Raw OCR text from invoice:")
            print(f"=== START OCR TEXT ===")
            print(extracted_text)
            print(f"=== END OCR TEXT ===")
            
            parsed_data_dict = parse_invoice(extracted_text)
            invoice_data = InvoiceData(**parsed_data_dict)
            
            print(f"DEBUG MAIN: Parsed invoice data:")
            print(f"DEBUG MAIN: Line items count: {len(invoice_data.line_items)}")
            for item in invoice_data.line_items:
                print(f"DEBUG MAIN: Line item: {item}")
        except Exception as e:
            return {"filename": file.filename, "status": "error", "message": f"Data parsing failed: {str(e)}"}

        # Process quality certificate if provided
        certificate_validation_errors = []
        if quality_certificate:
            try:
                # Save quality certificate temporarily
                cert_temp_path = os.path.join(TEMP_DIR, quality_certificate.filename)
                with open(cert_temp_path, "wb") as buffer:
                    shutil.copyfileobj(quality_certificate.file, buffer)
                
                # Extract text from certificate
                if quality_certificate.content_type == "application/pdf":
                    cert_images = convert_from_path(cert_temp_path)
                    cert_text = extract_text_from_image(cert_images[0]) if cert_images else ""
                else:
                    cert_text = extract_text_from_image(cert_temp_path)
                
                # Parse quality certificate
                parsed_certificate = parse_quality_certificate(cert_text)
                
                # Get restricted items from invoice for validation
                from app.validation.country_rules import COUNTRY_RULES
                country_lower = country.lower()
                print(f"DEBUG MAIN: Processing country: {country_lower}")
                
                if country_lower in COUNTRY_RULES:
                    restricted_item_names = COUNTRY_RULES[country_lower]["restricted_items"]
                    print(f"DEBUG MAIN: Restricted item names for {country_lower}: {restricted_item_names}")
                    
                    restricted_items = []
                    print(f"DEBUG MAIN: Checking {len(invoice_data.line_items)} invoice items...")
                    
                    for item in invoice_data.line_items:
                        item_desc_lower = item.description.lower()
                        print(f"DEBUG MAIN: Checking item: '{item.description}' (lowercase: '{item_desc_lower}')")
                        
                        for restricted_name in restricted_item_names:
                            if restricted_name in item_desc_lower:
                                print(f"DEBUG MAIN: FOUND restricted item: '{item.description}' matches '{restricted_name}'")
                                restricted_items.append(item)
                                break
                    
                    print(f"DEBUG MAIN: Total restricted items found: {len(restricted_items)}")
                    for item in restricted_items:
                        print(f"DEBUG MAIN: Restricted item: '{item.description}'")
                    
                    # Validate restricted items against certificate
                    if restricted_items:
                        print(f"DEBUG MAIN: Starting certificate validation for {len(restricted_items)} restricted items...")
                        certificate_validation_errors = validate_restricted_items_against_certificate(
                            restricted_items, parsed_certificate
                        )
                        print(f"DEBUG MAIN: Certificate validation errors: {certificate_validation_errors}")
                    else:
                        print("DEBUG MAIN: No restricted items found, skipping certificate validation")
                
                # Clean up certificate temp file
                if os.path.exists(cert_temp_path):
                    os.remove(cert_temp_path)
                    
            except Exception as e:
                return {"filename": file.filename, "status": "error", "message": f"Certificate processing failed: {str(e)}"}

        # Validate invoice data
        try:
            validation_errors = validate_invoice(invoice_data, country)
        except Exception as e:
            return {"filename": file.filename, "status": "error", "message": f"Validation failed: {str(e)}"}

        # Validate product-specific tax rates for the destination country
        product_tax_errors = []
        try:
            product_tax_errors = validate_product_tax_rates(invoice_data, country)
            print(f"DEBUG MAIN: Product tax validation errors: {product_tax_errors}")
        except Exception as e:
            print(f"DEBUG MAIN: Product tax validation failed: {str(e)}")
            product_tax_errors = [f"Product tax validation error: {str(e)}"]

        # Run AI-Powered Fraud Detection
        fraud_result = None
        vendor_name = None
        try:
            # Extract vendor name from invoice text or customer field
            vendor_name = invoice_data.customer_name  # Could be exporter name
            
            fraud_result = run_fraud_detection(db, invoice_data, vendor_name, country)
            print(f"DEBUG MAIN: Fraud detection score: {fraud_result.fraud_score}")
            print(f"DEBUG MAIN: Fraud flags: {fraud_result.flags}")
            
            # Add fraud flags as errors if high risk
            if fraud_result.is_high_risk():
                for flag in fraud_result.flags:
                    validation_errors.append(f"FRAUD ALERT: {flag}")
        except Exception as e:
            print(f"DEBUG MAIN: Fraud detection failed: {str(e)}")

        # Combine all validation errors
        all_errors = validation_errors + certificate_validation_errors + product_tax_errors
        
        # Prepare response with fraud analysis
        fraud_analysis = fraud_result.to_dict() if fraud_result else None
        
        if all_errors:
            # Update vendor score (failed)
            if vendor_name:
                try:
                    update_vendor_score(db, vendor_name, invoice_passed=False, amount=invoice_data.total_amount or 0)
                except:
                    pass
            
            return {
                "filename": file.filename, 
                "status": "validation_failed", 
                "errors": all_errors,
                "fraud_analysis": fraud_analysis
            }
        
        # Process valid invoice (only save if tax validation passes)
        try:
            # Update vendor score (passed)
            if vendor_name:
                try:
                    update_vendor_score(db, vendor_name, invoice_passed=True, amount=invoice_data.total_amount or 0)
                except:
                    pass
            
            # Record price history for future anomaly detection
            try:
                record_price_history(db, invoice_data.line_items, vendor_name, country)
            except:
                pass
            
            # Save line items for analytics
            try:
                for item in invoice_data.line_items:
                    classification = classify_product(item.description, getattr(item, 'hs_code', None))
                    tax_amount = None
                    if getattr(item, 'subtotal', None) and getattr(item, 'tax_percentage', None):
                        tax_amount = item.subtotal * item.tax_percentage / 100
                    
                    line_item_record = models.InvoiceLineItem(
                        invoice_id=invoice_data.invoice_id,
                        description=item.description,
                        hs_code=getattr(item, 'hs_code', None),
                        category=classification.get('category') if classification.get('classified') else None,
                        quantity=getattr(item, 'quantity', 1.0),
                        unit_price=getattr(item, 'unit_price', None),
                        subtotal=getattr(item, 'subtotal', None),
                        tax_percentage=getattr(item, 'tax_percentage', None),
                        tax_amount=tax_amount,
                        total=item.total,
                        country=country
                    )
                    db.add(line_item_record)
                db.commit()
            except Exception as e:
                print(f"DEBUG: Failed to save line items: {e}")
            
            # Save to database
            crud.create_invoice(db=db, invoice=invoice_data)
            
            # Create approval request for workflow
            approval_info = None
            try:
                approval = create_approval_request(
                    db=db,
                    invoice_id=invoice_data.invoice_id or f"INV-{file.filename}",
                    vendor_name=vendor_name,
                    country=country,
                    total_amount=invoice_data.total_amount,
                    fraud_score=fraud_result.fraud_score if fraud_result else 0
                )
                approval_info = {
                    "approval_id": approval.id,
                    "status": approval.status,
                    "level": approval.level,
                    "current_approver": approval.current_approver,
                    "message": "Invoice submitted for approval"
                }
            except Exception as e:
                print(f"DEBUG: Failed to create approval: {e}")

            if file.content_type == "application/pdf":
                signed_pdf_path = os.path.join(SIGNED_INVOICES_DIR, f"signed_{file.filename}")
                try:
                    add_signature_to_pdf(temp_file_path, signed_pdf_path, SIGNATURE_PATH)
                    signed_filename = f"signed_{file.filename}"
                    return {
                        "filename": file.filename, 
                        "status": "processed_and_saved", 
                        "path": signed_pdf_path,
                        "download_url": f"http://127.0.0.1:8001/invoices/signed/{signed_filename}",
                        "signed_filename": signed_filename,
                        "fraud_analysis": fraud_analysis,
                        "approval": approval_info
                    }
                except Exception as e:
                    # If signing fails, still save to database but return without signing
                    return {"filename": file.filename, "status": "processed_and_saved", "message": f"Saved to database but signing failed: {str(e)}", "approval": approval_info}
            else:
                return {"filename": file.filename, "status": "processed_and_saved", "data": invoice_data.dict(), "approval": approval_info}
                
        except Exception as e:
            return {"filename": file.filename, "status": "error", "message": f"Database operation failed: {str(e)}"}

    except Exception as e:
        return {"filename": file.filename, "status": "error", "message": f"Unexpected error: {str(e)}"}
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)


@app.get("/invoices/")
async def get_all_invoices(db: Session = Depends(get_db)):
    """Get all invoices from the database."""
    invoices = crud.get_all_invoices(db)
    return [
        {
            "id": inv.id,
            "invoice_id": inv.invoice_id,
            "invoice_date": str(inv.invoice_date) if inv.invoice_date else None,
            "due_date": str(inv.due_date) if inv.due_date else None,
            "customer_name": inv.customer_name,
            "total_amount": inv.total_amount,
            "tax_amount": inv.tax_amount
        }
        for inv in invoices
    ]


@app.get("/invoices/export")
async def export_invoices_to_excel(db: Session = Depends(get_db)):
    """Export all invoices to an Excel file."""
    invoices = crud.get_all_invoices(db)
    
    # Create Excel workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Invoices"
    
    # Add headers
    headers = ["ID", "Invoice ID", "Invoice Date", "Due Date", "Customer Name", "Total Amount", "Tax Amount"]
    ws.append(headers)
    
    # Add data rows
    for inv in invoices:
        ws.append([
            inv.id,
            inv.invoice_id,
            str(inv.invoice_date) if inv.invoice_date else "",
            str(inv.due_date) if inv.due_date else "",
            inv.customer_name or "",
            inv.total_amount or 0,
            inv.tax_amount or 0
        ])
    
    # Style the header row
    for cell in ws[1]:
        cell.font = cell.font.copy(bold=True)
    
    # Auto-adjust column widths
    for column in ws.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = (max_length + 2)
        ws.column_dimensions[column_letter].width = adjusted_width
    
    # Save the file
    export_path = Path(TEMP_DIR) / "invoices_export.xlsx"
    wb.save(export_path)
    
    return FileResponse(
        path=str(export_path),
        filename="invoices_export.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@app.delete("/invoices/")
async def delete_all_invoices(db: Session = Depends(get_db)):
    """Delete all invoices from the database."""
    count = crud.delete_all_invoices(db)
    return {"message": f"Deleted {count} invoices from database"}


@app.get("/invoices/signed")
async def list_signed_invoices():
    """List all signed PDF invoices available for download with clickable links."""
    signed_dir = Path(SIGNED_INVOICES_DIR)
    if not signed_dir.exists():
        return {"signed_invoices": [], "message": "No signed invoices directory found"}
    
    signed_files = []
    for pdf_file in signed_dir.glob("*.pdf"):
        signed_files.append({
            "filename": pdf_file.name,
            "download_url": f"http://127.0.0.1:8001/invoices/signed/{pdf_file.name}",
            "size_kb": round(pdf_file.stat().st_size / 1024, 2),
            "created": pdf_file.stat().st_mtime,
            "download_instruction": f"Click or copy this URL: http://127.0.0.1:8001/invoices/signed/{pdf_file.name}"
        })
    
    if not signed_files:
        return {"signed_invoices": [], "message": "No signed PDF files found"}
    
    return {
        "signed_invoices": signed_files,
        "total_files": len(signed_files),
        "instructions": "Copy any download_url and paste in browser, or use the /docs interface"
    }


@app.get("/invoices/signed/{filename}")
async def download_signed_invoice(filename: str):
    """Download a specific signed PDF invoice."""
    file_path = Path(SIGNED_INVOICES_DIR) / filename
    
    if not file_path.exists():
        return {"error": "Signed invoice not found"}
    
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="application/pdf"
    )


@app.get("/download-center", response_class=HTMLResponse)
async def download_center():
    """User-friendly download interface for signed PDFs."""
    html_path = Path("app/templates/signed_invoices.html")
    if html_path.exists():
        with open(html_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    else:
        return HTMLResponse(content="""
        <html>
            <body>
                <h1>Download Center</h1>
                <p>Go to <a href="/invoices/signed">/invoices/signed</a> to see available files</p>
                <p>Or use <a href="/docs">/docs</a> for API interface</p>
            </body>
        </html>
        """)


@app.get("/vendors/")
async def get_vendor_scores(db: Session = Depends(get_db)):
    """
    Get all vendor risk scores and statistics.
    
    Vendor Risk Scoring tracks:
    - Total invoices processed per vendor
    - Success/failure rate
    - Risk score (0-100, lower is better)
    """
    vendors = db.query(models.VendorScore).all()
    return {
        "total_vendors": len(vendors),
        "vendors": [
            {
                "vendor_name": v.vendor_name,
                "total_invoices": v.total_invoices,
                "successful_invoices": v.successful_invoices,
                "failed_invoices": v.failed_invoices,
                "success_rate": f"{(v.successful_invoices / v.total_invoices * 100):.1f}%" if v.total_invoices > 0 else "N/A",
                "risk_score": round(v.risk_score, 2),
                "risk_level": "HIGH" if v.risk_score >= 70 else "MEDIUM" if v.risk_score >= 40 else "LOW",
                "total_amount_processed": v.total_amount_processed,
                "last_invoice_date": v.last_invoice_date.isoformat() if v.last_invoice_date else None
            }
            for v in vendors
        ]
    }


@app.get("/vendors/{vendor_name}")
async def get_vendor_details(vendor_name: str, db: Session = Depends(get_db)):
    """Get detailed risk analysis for a specific vendor."""
    from app.validation.fraud_detection import get_vendor_risk_score
    
    risk_score, details = get_vendor_risk_score(db, vendor_name)
    
    return {
        "vendor_name": vendor_name,
        "risk_score": round(risk_score, 2),
        "risk_level": "HIGH" if risk_score >= 70 else "MEDIUM" if risk_score >= 40 else "LOW",
        "details": details
    }


@app.get("/fraud-stats/")
async def get_fraud_statistics(db: Session = Depends(get_db)):
    """
    Get overall fraud detection statistics.
    
    Shows:
    - Total invoices processed
    - High/Medium/Low risk breakdown
    - Price history records
    - Vendor statistics
    """
    from sqlalchemy import func
    
    # Count invoices by risk level (if fraud_score is stored)
    total_invoices = db.query(models.Invoice).count()
    
    # Count vendors
    total_vendors = db.query(models.VendorScore).count()
    high_risk_vendors = db.query(models.VendorScore).filter(models.VendorScore.risk_score >= 70).count()
    
    # Count price history records
    price_records = db.query(models.PriceHistory).count()
    
    return {
        "summary": {
            "total_invoices_processed": total_invoices,
            "total_vendors_tracked": total_vendors,
            "high_risk_vendors": high_risk_vendors,
            "price_history_records": price_records
        },
        "fraud_detection_features": {
            "duplicate_detection": "Flags invoices with same ID, amount+date, or similar patterns",
            "price_anomaly_detection": "Alerts when prices deviate >30% from historical average",
            "vendor_risk_scoring": "Tracks vendor reliability based on invoice success/failure rate"
        },
        "endpoints": {
            "view_vendors": "GET /vendors/ - View all vendor risk scores",
            "vendor_details": "GET /vendors/{name} - Get specific vendor analysis",
            "classify_product": "GET /classify/{description} - Test product classification"
        }
    }


@app.get("/classify/{description}")
async def classify_product_endpoint(description: str, hs_code: str = None):
    """
    Test the smart product classification system.
    
    Examples:
    - /classify/Hyundai%20Exter → Classified as passenger_cars
    - /classify/Mazda%206 → Classified as passenger_cars
    - /classify/Dell%20Laptop → Classified as electronics
    """
    result = classify_product(description, hs_code)
    return {
        "input": {
            "description": description,
            "hs_code": hs_code
        },
        "classification": result
    }


# ==================== ANALYTICS DASHBOARD ENDPOINTS ====================

@app.get("/analytics/")
async def get_analytics_dashboard(db: Session = Depends(get_db)):
    """
    Get full analytics dashboard with all charts and statistics.
    
    Includes:
    - Summary statistics (total invoices, amount, tax collected)
    - Invoices by country (bar chart)
    - Invoices by product category (pie chart)
    - Invoices by month (line chart)
    - Tax collected by product type
    - Top vendors and importers
    """
    return get_full_dashboard(db)


@app.get("/analytics/summary")
async def get_analytics_summary(db: Session = Depends(get_db)):
    """Get summary statistics only."""
    return get_dashboard_summary(db)


@app.get("/analytics/by-country")
async def get_analytics_by_country(db: Session = Depends(get_db)):
    """Get invoices grouped by country."""
    return get_invoices_by_country(db)


@app.get("/analytics/by-category")
async def get_analytics_by_category(db: Session = Depends(get_db)):
    """Get invoices grouped by product category."""
    return get_invoices_by_category(db)


@app.get("/analytics/by-month")
async def get_analytics_by_month(months: int = 12, db: Session = Depends(get_db)):
    """Get invoices grouped by month."""
    return get_invoices_by_month(db, months)


@app.get("/analytics/tax-by-product")
async def get_analytics_tax_by_product(db: Session = Depends(get_db)):
    """Get tax collected grouped by product type."""
    return get_tax_by_product_type(db)


@app.get("/analytics/top-vendors")
async def get_analytics_top_vendors(limit: int = 10, db: Session = Depends(get_db)):
    """Get top vendors by volume."""
    return get_top_vendors(db, limit)


@app.get("/analytics/top-importers")
async def get_analytics_top_importers(limit: int = 10, db: Session = Depends(get_db)):
    """Get top importers by volume."""
    return get_top_importers(db, limit)


# ==================== APPROVAL WORKFLOW ENDPOINTS ====================

@app.get("/approvals/")
async def get_approvals_dashboard(db: Session = Depends(get_db)):
    """
    Get approval workflow dashboard.
    
    Shows:
    - Summary (pending, approved, rejected counts)
    - Pending approvals by level (Manager, Finance, Compliance)
    - List of pending approvals
    - Overdue approvals (waiting > 3 days)
    """
    return get_approval_dashboard(db)


@app.get("/approvals/pending")
async def get_all_pending_approvals(level: int = None, db: Session = Depends(get_db)):
    """
    Get all pending approval requests.
    
    Optional filter by level:
    - 1 = Manager
    - 2 = Finance
    - 3 = Compliance
    """
    return {
        "pending_approvals": get_pending_approvals(db, level),
        "filter_level": level,
        "level_name": APPROVAL_LEVELS[level]["name"] if level else "All"
    }


@app.get("/approvals/{invoice_id}")
async def get_invoice_approval_status(invoice_id: str, db: Session = Depends(get_db)):
    """Get approval status for a specific invoice."""
    status = get_approval_status(db, invoice_id)
    if not status:
        return {"error": f"No approval request found for invoice {invoice_id}"}
    return status


@app.post("/approvals/{approval_id}/approve")
async def approve_invoice_endpoint(
    approval_id: int,
    approver_name: str = Form(...),
    comments: str = Form(None),
    db: Session = Depends(get_db)
):
    """
    Approve an invoice at the current level.
    
    If higher approval is needed (based on amount/risk), it will be escalated.
    """
    result = approve_invoice(db, approval_id, approver_name, comments)
    return result


@app.post("/approvals/{approval_id}/reject")
async def reject_invoice_endpoint(
    approval_id: int,
    rejector_name: str = Form(...),
    reason: str = Form(...),
    db: Session = Depends(get_db)
):
    """Reject an invoice with a reason."""
    result = reject_invoice(db, approval_id, rejector_name, reason)
    return result


@app.post("/approvals/create")
async def create_approval_endpoint(
    invoice_id: str = Form(...),
    vendor_name: str = Form(None),
    country: str = Form(None),
    total_amount: float = Form(None),
    fraud_score: float = Form(None),
    db: Session = Depends(get_db)
):
    """Manually create an approval request for an invoice."""
    approval = create_approval_request(
        db, invoice_id, None, vendor_name, country, total_amount, fraud_score
    )
    return {
        "success": True,
        "approval_id": approval.id,
        "status": approval.status,
        "level": approval.level,
        "current_approver": approval.current_approver
    }


@app.post("/approvals/configure-email")
async def configure_email_endpoint(
    smtp_server: str = Form(...),
    smtp_port: int = Form(587),
    sender_email: str = Form(...),
    sender_password: str = Form(...)
):
    """
    Configure email settings for approval notifications.
    
    Example for Gmail:
    - smtp_server: smtp.gmail.com
    - smtp_port: 587
    - sender_email: your-email@gmail.com
    - sender_password: your-app-password (not regular password)
    """
    configure_email(smtp_server, smtp_port, sender_email, sender_password)
    return {"success": True, "message": "Email notifications configured"}


@app.post("/approvals/set-approver")
async def set_approver_endpoint(
    level: int = Form(...),
    name: str = Form(...),
    email: str = Form(...)
):
    """
    Set approver details for a specific level.
    
    Levels:
    - 1 = Manager (all invoices)
    - 2 = Finance (invoices > $50,000)
    - 3 = Compliance (invoices > $100,000 or high fraud risk)
    """
    if level not in [1, 2, 3]:
        return {"error": "Level must be 1, 2, or 3"}
    set_approver_email(level, name, email)
    return {"success": True, "message": f"Level {level} approver set to {name} ({email})"}


@app.get("/")
async def root():
    """Root endpoint with navigation links."""
    return {
        "message": "Invoice Processing API",
        "endpoints": {
            "upload_invoice": "POST /invoice/ - Upload invoice and certificate",
            "view_invoices": "GET /invoices/ - View all processed invoices", 
            "export_excel": "GET /invoices/export - Export invoices to Excel",
            "signed_invoices": "GET /invoices/signed - List signed PDFs",
            "download_center": "GET /download-center - User-friendly download interface",
            "fraud_stats": "GET /fraud-stats/ - View fraud detection statistics",
            "vendors": "GET /vendors/ - View vendor risk scores",
            "classify": "GET /classify/{description} - Test product classification",
            "analytics": "GET /analytics/ - Full analytics dashboard",
            "approvals": "GET /approvals/ - Approval workflow dashboard",
            "api_docs": "GET /docs - Interactive API documentation"
        },
        "quick_links": {
            "upload": "http://127.0.0.1:8001/docs",
            "download": "http://127.0.0.1:8001/download-center",
            "signed_files": "http://127.0.0.1:8001/invoices/signed",
            "fraud_dashboard": "http://127.0.0.1:8001/fraud-stats/",
            "analytics": "http://127.0.0.1:8001/analytics/",
            "approvals": "http://127.0.0.1:8001/approvals/"
        }
    }
