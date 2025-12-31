from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from pathlib import Path
import io


def add_signature_to_pdf(original_pdf_path: str, signed_pdf_path: str, signature_image_path: str):
    """
    Adds a digital signature image to the first page of a PDF.

    Args:
        original_pdf_path: The path to the original PDF file.
        signed_pdf_path: The path to save the signed PDF file.
        signature_image_path: The path to the signature image file.
    
    Raises:
        Exception: If there's an error during the signing process.
    """
    try:
        # Check if signature image exists
        if not Path(signature_image_path).is_file():
            raise FileNotFoundError(f"Signature image not found: {signature_image_path}")
        
        # Create a new PDF with the signature
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=letter)
        
        # Position the signature at the bottom-right
        can.drawImage(signature_image_path, x=400, y=50, width=150, height=75, mask='auto')
        can.save()

        # Move to the beginning of the buffer
        packet.seek(0)
        new_pdf = PdfReader(packet)

        # Read the existing PDF
        with open(original_pdf_path, "rb") as f:
            existing_pdf = PdfReader(f)
            output = PdfWriter()

            # Add the signature on the first page
            page = existing_pdf.pages[0]
            page.merge_page(new_pdf.pages[0])
            output.add_page(page)

            # Add the rest of the pages
            for i in range(1, len(existing_pdf.pages)):
                output.add_page(existing_pdf.pages[i])

            # Write the result to a new file
            with open(signed_pdf_path, "wb") as outputStream:
                output.write(outputStream)
                
    except Exception as e:
        raise Exception(f"Error during PDF signing: {str(e)}")
