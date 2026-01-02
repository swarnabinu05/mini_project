# Invoice AI System

An intelligent invoice processing system that uses OCR to read invoices, validates data against business rules, and automatically updates company databases.

## Features

- **OCR-based invoice text extraction** - Reads PDF and image invoices
- **Smart Product Classification** - Recognizes brands like "Hyundai Exter" as cars
- **Automated data validation** - Tax rules, country regulations, calculation checks
- **Fraud Detection** - Duplicate detection, price anomaly alerts, vendor risk scoring
- **Approval Workflow** - Multi-level approval (Manager → Finance → Compliance)
- **Digital signature application** - Auto-signs approved invoices
- **Analytics Dashboard** - Visual charts and statistics
- **Quality Certificate Validation** - For restricted items

## Project Structure

```
invoice-ai/
├── backend/          # Python FastAPI backend
├── frontend/         # React frontend (with Tailwind CSS)
├── docs/            # Documentation
└── README.md
```

## Quick Start

### 1. Start Backend
```bash
cd d:\minipro\invoice-ai\backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8001
```

### 2. Start Frontend
```bash
cd d:\minipro\invoice-ai\frontend
npm install
npm start
```

### 3. Access the Application
- **Frontend UI**: http://localhost:3000
- **Backend API**: http://127.0.0.1:8001
- **API Docs**: http://127.0.0.1:8001/docs

## Frontend Pages

| Page | Description |
|------|-------------|
| **Dashboard** | Overview with stats and quick actions |
| **Upload Invoice** | Upload invoices with optional quality certificate |
| **Analytics** | Charts for invoices by country, category, month |
| **Approvals** | Review and approve/reject pending invoices |
| **Vendors & Fraud** | Vendor risk scores and fraud detection stats |
| **Signed Invoices** | Download signed PDFs and export to Excel |
| **Product Classifier** | Test smart product classification |

## Troubleshooting

**If Port 8001 is Busy:**
```bash
python -m uvicorn app.main:app --reload --port 8002
```
Then update `API_BASE_URL` in `frontend/src/services/api.js`
Then use port 8002 in all URLs.

If Database Errors Occur:
Stop server (Ctrl+C)
Delete database: del "d:\minipro\invoice-ai\backend\data\invoices.db"
Restart server

## urls
http://127.0.0.1:8001/docs
http://127.0.0.1:8001/docs (POST /invoice/)
http://127.0.0.1:8001/invoices/
http://127.0.0.1:8001/invoices/export
http://127.0.0.1:8001/docs (DELETE /invoices/)


## Development Status

🚧 Project structure created - ready for development
