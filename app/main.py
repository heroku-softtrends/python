from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import os
from dotenv import load_dotenv

from app.database import get_db, engine
from app.models import Base
from app.routers import invoices, upload, export, fields, training, ai_info
from app.core.config import settings

# Load environment variables
load_dotenv()

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="Invoice Reader API",
    description="AI-powered invoice processing system",
    version="1.0.0"
)

# CORS middleware - Allow all origins for Heroku deployment
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (change this in production to specific domains)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(upload.router, prefix="/api", tags=["upload"])
app.include_router(invoices.router, prefix="/api", tags=["invoices"])
app.include_router(export.router, prefix="/api", tags=["export"])
app.include_router(fields.router, prefix="/api", tags=["fields"])
app.include_router(training.router, prefix="/api", tags=["training"])
app.include_router(ai_info.router, prefix="/api", tags=["ai"])

@app.get("/")
async def root():
    return {"message": "Invoice Reader API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)