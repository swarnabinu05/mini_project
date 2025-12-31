# Invoice AI Backend

Python FastAPI backend for intelligent invoice processing.

## Features

- OCR text extraction (Tesseract)
- Table extraction (Camelot/Tabula)
- Business rule validation
- Digital signature application
- PDF error highlighting
- Database integration

## Setup

1. Create virtual environment: `python -m venv venv`
2. Activate: `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Linux/Mac)
3. Install dependencies: `pip install -r requirements.txt`
4. Run server: `python app/main.py`

## Project Structure

- `app/` - Main application code
- `data/` - Data storage directories
- `tests/` - Test files
