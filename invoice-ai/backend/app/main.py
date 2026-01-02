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
from app.signing.signer import add_signature_to_pdf
from app.database import crud, models
from app.database.session import engine, get_db

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

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

        # Combine all validation errors
        all_errors = validation_errors + certificate_validation_errors + product_tax_errors
        if all_errors:
            return {"filename": file.filename, "status": "validation_failed", "errors": all_errors}
        
        # Process valid invoice (only save if tax validation passes)
        try:
            # Save to database
            crud.create_invoice(db=db, invoice=invoice_data)

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
                        "signed_filename": signed_filename
                    }
                except Exception as e:
                    # If signing fails, still save to database but return without signing
                    return {"filename": file.filename, "status": "processed_and_saved", "message": f"Saved to database but signing failed: {str(e)}"}
            else:
                return {"filename": file.filename, "status": "processed_and_saved", "data": invoice_data.dict()}
                
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
            "api_docs": "GET /docs - Interactive API documentation"
        },
        "quick_links": {
            "upload": "http://127.0.0.1:8001/docs",
            "download": "http://127.0.0.1:8001/download-center",
            "signed_files": "http://127.0.0.1:8001/invoices/signed"
        }
    }
