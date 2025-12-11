from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
import os
import logging
from datetime import datetime
from typing import List

from app.database import get_db
from app.models import Invoice, FieldSelection
from app.schemas.invoice import UploadResponse, ProcessingResult
from app.services.pdf_processor import PDFProcessor
from app.services.learning_service import LearningService
from app.services.file_storage import file_storage_service
from app.core.config import settings

router = APIRouter()
pdf_processor = PDFProcessor()
logger = logging.getLogger(__name__)

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_FOLDER, exist_ok=True)

@router.post("/upload", response_model=UploadResponse)
async def upload_invoice(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload and process a PDF invoice."""
    
    try:
        # Validate file
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        if file.size and file.size > settings.MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="File size too large")
        
        logger.info(f"Starting upload process for file: {file.filename}")
        
    except Exception as e:
        logger.error(f"Error in upload validation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload validation error: {str(e)}")
    
    try:
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{file.filename}"
        
        # Save file using storage service (local or S3)
        success, file_path = await file_storage_service.save_file(file, filename)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to save uploaded file")
        
        # Create invoice record
        invoice = Invoice(
            filename=filename,
            original_filename=file.filename,
            file_path=file_path,  # This will be local path or S3 URL
            status="processing"
        )
        db.add(invoice)
        db.commit()
        db.refresh(invoice)
        
        # Process PDF and extract fields
        try:
            logger.info("Starting PDF processing...")
            text = pdf_processor.extract_text_from_pdf(file_path)
            logger.info(f"Text extraction completed, length: {len(text)}")
            
            extracted_fields = pdf_processor.extract_invoice_fields(text)
            logger.info(f"Field extraction completed, fields: {list(extracted_fields.keys())}")
            
            confidence_scores = pdf_processor.get_confidence_scores(extracted_fields, text)
            logger.info("Confidence scoring completed")
            
            # Update invoice with extracted data
            invoice.extracted_data = {
                'raw_text': text[:1000],  # Store first 1000 chars
                'extracted_fields': extracted_fields,
                'confidence_scores': confidence_scores
            }
            invoice.status = "completed"
            invoice.processed_timestamp = datetime.utcnow()
            db.commit()
            
            # Initialize learning service and auto-select fields
            try:
                logger.info("Initializing learning service...")
                learning_service = LearningService(db)
                learning_service.auto_select_fields(invoice.id, extracted_fields)
                user_preferences = learning_service.get_user_preferences()
                logger.info(f"Learning service initialized, preferences: {user_preferences}")
            except Exception as e:
                logger.error(f"Learning service error: {str(e)}")
                user_preferences = []  # Fallback to empty preferences
            
            # Format response
            formatted_fields = []
            try:
                for field_name, field_value in extracted_fields.items():
                    formatted_fields.append({
                        'field_name': field_name,
                        'field_value': field_value,
                        'confidence_score': confidence_scores.get(field_name, 0.5),
                        'is_selected': field_name in user_preferences
                    })
                logger.info(f"Formatted {len(formatted_fields)} fields")
            except Exception as e:
                logger.error(f"Error formatting fields: {str(e)}")
                formatted_fields = []
            
            return UploadResponse(
                invoice_id=invoice.id,
                filename=filename,
                status="completed",
                extracted_fields=formatted_fields,
                message="Invoice processed successfully"
            )
            
        except Exception as e:
            # Update invoice status to error
            logger.error(f"Processing error: {str(e)}")
            try:
                db.rollback()  # Rollback failed transaction
                invoice.status = "error"
                invoice.extracted_data = {'error': str(e)}
                db.commit()
            except Exception as commit_error:
                logger.error(f"Failed to update error status: {commit_error}")
                db.rollback()
            
            raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
            
    except Exception as e:
        # Clean up file if something went wrong
        logger.error(f"Upload error: {str(e)}")
        try:
            db.rollback()  # Ensure clean state
        except:
            pass
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/upload/status/{invoice_id}")
async def get_upload_status(invoice_id: int, db: Session = Depends(get_db)):
    """Get the processing status of an uploaded invoice."""
    
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    return {
        "invoice_id": invoice.id,
        "status": invoice.status,
        "upload_timestamp": invoice.upload_timestamp,
        "processed_timestamp": invoice.processed_timestamp,
        "filename": invoice.original_filename
    }