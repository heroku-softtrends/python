from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.pdf_processor import PDFProcessor

router = APIRouter()

@router.get("/ai/model-info")
async def get_ai_model_info():
    """Get information about the AI models currently being used."""
    
    processor = PDFProcessor()
    model_info = processor.get_ai_model_info()
    
    return {
        "message": "AI Model Information",
        "ai_enabled": model_info.get('ner_model_available', False) or model_info.get('qa_model_available', False),
        "models": model_info,
        "description": {
            "ner_model": "Named Entity Recognition for extracting organizations, money, dates",
            "qa_model": "Question Answering for specific field extraction",
            "processing_methods": "AI extraction methods available"
        }
    }

@router.get("/ai/test-extraction")
async def test_ai_extraction():
    """Test the AI extraction with sample invoice text."""
    
    sample_text = """
    ACME CORPORATION
    123 Business Street
    New York, NY 10001
    
    INVOICE
    
    Invoice Number: INV-2024-12345
    Invoice Date: November 6, 2025
    Due Date: December 6, 2025
    
    Bill To:
    John Smith Company
    456 Client Avenue
    Boston, MA 02101
    
    Description                 Quantity    Unit Price    Amount
    Consulting Services              10      $150.00   $1,500.00
    Software License                  1      $500.00     $500.00
    
    Subtotal:                                          $2,000.00
    Tax (8.25%):                                        $165.00
    Total Amount Due:                                 $2,165.00
    
    Payment Terms: Net 30 days
    Contact: support@acme.com
    Phone: 555-123-4567
    """
    
    processor = PDFProcessor()
    
    try:
        # Extract fields using AI
        extracted_fields = processor.extract_invoice_fields(sample_text)
        confidence_scores = processor.get_confidence_scores(extracted_fields, sample_text)
        model_info = processor.get_ai_model_info()
        
        return {
            "message": "AI Extraction Test Results",
            "sample_processed": True,
            "extracted_fields": extracted_fields,
            "confidence_scores": confidence_scores,
            "ai_models_used": model_info.get('processing_methods', []),
            "model_availability": {
                "ner_available": model_info.get('ner_model_available', False),
                "qa_available": model_info.get('qa_model_available', False),
                "device": model_info.get('device', 'cpu')
            }
        }
        
    except Exception as e:
        return {
            "message": "AI Extraction Test Failed", 
            "error": str(e),
            "sample_processed": False
        }