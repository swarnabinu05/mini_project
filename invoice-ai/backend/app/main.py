import os
import shutil
from fastapi import FastAPI, File, UploadFile, Form, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pdf2image import convert_from_path
from openpyxl import Workbook
from pathlib import Path

from app.ocr.text_ocr import extract_text_from_image
from app.extraction.invoice_parser import parse_invoice
from app.extraction.entities import InvoiceData
from app.validation.rule_engine import validate_invoice
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
async def process_invoice(country: str = Form(...), file: UploadFile = File(...), db: Session = Depends(get_db)):
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
            parsed_data_dict = parse_invoice(extracted_text)
            invoice_data = InvoiceData(**parsed_data_dict)
        except Exception as e:
            return {"filename": file.filename, "status": "error", "message": f"Data parsing failed: {str(e)}"}

        # Validate invoice data
        try:
            validation_errors = validate_invoice(invoice_data, country)
        except Exception as e:
            return {"filename": file.filename, "status": "error", "message": f"Validation failed: {str(e)}"}

        if validation_errors:
            return {"filename": file.filename, "status": "validation_failed", "errors": validation_errors}
        
        # Process valid invoice (only save if tax validation passes)
        try:
            # Save to database
            crud.create_invoice(db=db, invoice=invoice_data)

            if file.content_type == "application/pdf":
                signed_pdf_path = os.path.join(SIGNED_INVOICES_DIR, f"signed_{file.filename}")
                try:
                    add_signature_to_pdf(temp_file_path, signed_pdf_path, SIGNATURE_PATH)
                    return {"filename": file.filename, "status": "processed_and_saved", "path": signed_pdf_path}
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
