# Tesseract OCR implementation

from PIL import Image
import pytesseract

from typing import Union

def extract_text_from_image(image: Union[str, Image.Image]) -> str:
    """
    Extracts text from an image file or PIL Image object using Tesseract OCR.

    Args:
        image: The path to the image file or a PIL Image object.

    Returns:
        The extracted text as a string.
    """
    try:
        if isinstance(image, str):
            image = Image.open(image)
        text = pytesseract.image_to_string(image)
        return text
    except Exception as e:
        print(f"Error during OCR: {e}")
        return ""
