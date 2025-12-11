# Invoice Reader Backend

An AI-powered invoice processing backend built with FastAPI.

## Features

- PDF invoice upload and processing
- AI-powered text extraction and field detection
- PostgreSQL database integration
- Learning system for user preferences
- RESTful API for frontend integration

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Set up environment variables (see .env.example)

3. Initialize database:
   ```
   alembic upgrade head
   ```

4. Run the server:
   ```
   uvicorn app.main:app --reload
   ```

## API Endpoints

- `POST /api/upload` - Upload PDF invoice
- `GET /api/invoices` - List processed invoices
- `POST /api/export` - Export selected data
- `GET /api/fields` - Get available fields
- `POST /api/train` - Train model with user feedback

## Database

The system uses PostgreSQL to store:
- Extracted invoice data (JSON format)
- User preferences and selections
- Model training data and feedback