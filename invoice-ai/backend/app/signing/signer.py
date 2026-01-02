from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from pathlib import Path
from pdf2image import convert_from_path
import pytesseract
import io
import re


def find_signature_position(pdf_path: str) -> tuple:
    """
    Finds the position where signature should be placed by looking for
    text like 'signature', 'manager signature', 'name & signature' etc.
    
    Returns:
        tuple: (x, y) coordinates for signature placement
    """
    try:
        # Convert PDF to image for OCR
        images = convert_from_path(pdf_path)
        if not images:
            return (100, 380)  # Default position if no images
        
        # Get OCR data with bounding boxes
        image = images[0]
        ocr_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
        
        # Get image dimensions
        img_width, img_height = image.size
        
        # PDF coordinates (letter size: 612 x 792 points)
        pdf_width, pdf_height = 612, 792
        
        # Look for signature-related text
        signature_keywords = ['signature', 'manager', 'name &', 'sign here', 'authorized']
        
        best_y = None
        best_x = None
        
        for i, text in enumerate(ocr_data['text']):
            text_lower = text.lower().strip()
            
            for keyword in signature_keywords:
                if keyword in text_lower:
                    # Get bounding box coordinates
                    x = ocr_data['left'][i]
                    y = ocr_data['top'][i]
                    
                    # Convert image coordinates to PDF coordinates
                    # PDF origin is bottom-left, image origin is top-left
                    pdf_x = (x / img_width) * pdf_width
                    pdf_y = pdf_height - ((y / img_height) * pdf_height)
                    
                    # Place signature ABOVE the text (add some offset)
                    signature_y = pdf_y + 30  # 30 points above the text
                    signature_x = pdf_x
                    
                    print(f"DEBUG SIGNER: Found '{text}' at image ({x}, {y}) -> PDF ({pdf_x:.0f}, {pdf_y:.0f})")
                    print(f"DEBUG SIGNER: Placing signature at ({signature_x:.0f}, {signature_y:.0f})")
                    
                    # Keep track of the best position (prefer lower on page for signature line)
                    if best_y is None or signature_y < best_y:
                        best_y = signature_y
                        best_x = signature_x
        
        if best_y is not None:
            return (best_x, best_y)
        
        # Default position if no signature text found
        print("DEBUG SIGNER: No signature text found, using default position")
        return (100, 380)
        
    except Exception as e:
        print(f"DEBUG SIGNER: Error finding signature position: {e}")
        return (100, 380)  # Default fallback position


def add_signature_to_pdf(original_pdf_path: str, signed_pdf_path: str, signature_image_path: str):
    """
    Adds a digital signature image to the first page of a PDF.
    Automatically detects where to place the signature based on text like
    'signature', 'manager signature', etc.

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
        
        # Find the best position for signature
        sig_x, sig_y = find_signature_position(original_pdf_path)
        print(f"DEBUG SIGNER: Final signature position: x={sig_x}, y={sig_y}")
        
        # Create a new PDF with the signature
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=letter)
        
        # Position the signature at the detected location
        can.drawImage(signature_image_path, x=sig_x, y=sig_y, width=150, height=50, mask='auto')
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
