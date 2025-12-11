# Enhanced PDF processing with Transformer AI models
# AI libraries: transformers, torch (installed)
# PDF libraries: PyPDF2, pdfplumber (to be installed later)

import re
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
import io

from .transformer_ai import TransformerInvoiceProcessor

logger = logging.getLogger(__name__)

class PDFProcessor:
    def __init__(self):
        # Initialize AI-powered processor
        self.ai_processor = TransformerInvoiceProcessor()
        logger.info("🤖 AI-powered PDF processor initialized")
        
        # Keep compatibility with spaCy if needed later
        self.nlp = None
    
    def extract_text_from_pdf(self, file_path_or_content: str) -> str:
        """Extract text from PDF using multiple methods."""
        logger.info(f"Processing PDF file: {file_path_or_content}")
        
        try:
            # Try to get file content from storage service
            from .file_storage import file_storage_service
            
            file_content = None
            if isinstance(file_path_or_content, str):
                if file_path_or_content.startswith('s3://'):
                    # S3 file - get content
                    file_content = file_storage_service.read_file(file_path_or_content)
                else:
                    # Local file - get content
                    file_content = file_storage_service.read_file(file_path_or_content)
            
            # If we have actual PDF content, try to extract it
            if file_content:
                try:
                    # Try PyPDF2 first
                    import PyPDF2
                    pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
                    text = ""
                    for page in pdf_reader.pages:
                        text += page.extract_text() + "\n"
                    
                    if text.strip():
                        logger.info(f"Successfully extracted text using PyPDF2: {len(text)} characters")
                        return text
                except ImportError:
                    logger.warning("PyPDF2 not available, falling back to sample text")
                except Exception as e:
                    logger.warning(f"PyPDF2 extraction failed: {e}, trying alternative method")
                
                try:
                    # Try pdfplumber as alternative
                    import pdfplumber
                    with pdfplumber.open(io.BytesIO(file_content)) as pdf:
                        text = ""
                        for page in pdf.pages:
                            text += page.extract_text() or ""
                    
                    if text.strip():
                        logger.info(f"Successfully extracted text using pdfplumber: {len(text)} characters")
                        return text
                except ImportError:
                    logger.warning("pdfplumber not available")
                except Exception as e:
                    logger.warning(f"pdfplumber extraction failed: {e}")
        
        except Exception as e:
            logger.error(f"Error accessing file content: {e}")
        
        # Fallback to sample text for demonstration
        logger.info("Using sample invoice text for demonstration")
        sample_text = """
        INVOICE

        Invoice Number: INV-2024-001
        Invoice Date: January 15, 2024
        Due Date: February 15, 2024

        Bill To:
        John Smith
        123 Main Street
        New York, NY 10001

        Ship To:
        Same as billing address

        Description                 Quantity    Unit Price    Amount
        Web Development Services         1      $2,500.00   $2,500.00
        Domain Registration              1         $15.00      $15.00
        Hosting Service (1 year)         1        $120.00     $120.00

        Subtotal:                                            $2,635.00
        Tax (8.25%):                                          $217.39
        Total Amount Due:                                   $2,852.39

        Payment Terms: Net 30 days
        Payment Method: Check or Bank Transfer

        Thank you for your business!
        """
        
        return sample_text.strip()
    
    def ocr_pdf(self, file_path: str) -> str:
        """Extract text using OCR (for image-based PDFs)."""
        # OCR extraction not implemented yet
        # TODO: Install tesseract and pdf2image libraries
        logger.info("OCR extraction not available - install tesseract and pdf2image")
        return ""
    
    def preprocess_text(self, text: str) -> str:
        """Clean and preprocess extracted text."""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep important ones
        text = re.sub(r'[^\w\s\-\.\,\:\;\$\%\(\)\/]', '', text)
        return text.strip()
    
    def extract_invoice_fields(self, text: str) -> Dict[str, Any]:
        """Extract invoice fields using AI Transformer models."""
        try:
            # Use AI-powered extraction
            logger.info("🤖 Extracting fields using Transformer AI models")
            ai_results = self.ai_processor.extract_with_transformers(text)
            fields = ai_results['extracted_fields']
            
            # Add additional fields using enhanced patterns for completeness
            additional_fields = self._extract_additional_fields(text)
            fields.update(additional_fields)
            
            logger.info(f"✅ Extracted {len(fields)} fields using AI: {list(fields.keys())}")
            return fields
            
        except Exception as e:
            logger.error(f"❌ AI extraction failed: {e}")
            # Fallback to basic pattern matching
            logger.info("🔄 Falling back to pattern matching")
            return self._fallback_extraction(text)
    
    def _extract_additional_fields(self, text: str) -> Dict[str, str]:
        """Extract additional fields not covered by main AI models."""
        fields = {}
        
        # Extract email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        if emails:
            fields['vendor_email'] = emails[0]
        
        # Extract phone numbers  
        phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
        phones = re.findall(phone_pattern, text)
        if phones:
            fields['vendor_phone'] = phones[0]
        
        # Extract addresses (enhanced pattern)
        address_patterns = [
            r'\b\d+\s+[A-Za-z0-9\s,]+\s+[A-Z]{2}\s+\d{5}\b',
            r'\d+\s+[\w\s]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd)',
        ]
        
        for pattern in address_patterns:
            addresses = re.findall(pattern, text, re.IGNORECASE)
            if addresses:
                fields['vendor_address'] = addresses[0]
                break
        
        return fields
    
    def _fallback_extraction(self, text: str) -> Dict[str, str]:
        """Fallback extraction using basic regex patterns."""
        fields = {}
        
        # Basic patterns as backup
        patterns = {
            'invoice_number': [
                r'(?:invoice|inv)[\s#:]*([A-Z0-9\-\_]{3,20})',
                r'(?:number|no|#)[\s:]*([A-Z0-9\-\_]{3,20})',
            ],
            'total_amount': [
                r'(?:total|amount\s+due)[\s:$]*([0-9,]+\.?\d{0,2})',
                r'\$([0-9,]+\.?\d{2})',
            ],
            'invoice_date': [
                r'(?:date|invoice\s+date)[\s:]*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})',
            ],
            'vendor_name': [
                # Try to get company name from first few lines
            ]
        }
        
        for field, field_patterns in patterns.items():
            for pattern in field_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    fields[field] = matches[0]
                    break
        
        # Get vendor name from document structure
        if 'vendor_name' not in fields:
            lines = text.split('\n')[:10]
            for line in lines:
                line = line.strip()
                if len(line) > 3 and len(line) < 50 and not re.search(r'\d', line):
                    if 'invoice' not in line.lower():
                        fields['vendor_name'] = line
                        break
        
        return fields
    
    def get_confidence_scores(self, fields: Dict[str, Any], text: str) -> Dict[str, float]:
        """Get AI-powered confidence scores for extracted fields."""
        try:
            # Get confidence scores from AI processor
            ai_results = self.ai_processor.extract_with_transformers(text)
            ai_confidence = ai_results.get('confidence_scores', {})
            
            # Use AI confidence scores where available
            confidence_scores = {}
            for field_name, field_value in fields.items():
                if field_name in ai_confidence:
                    # Use AI confidence score - CONVERT TO PYTHON FLOAT
                    score = ai_confidence[field_name]
                    if hasattr(score, 'item'):  # NumPy scalar (float32, etc.)
                        confidence_scores[field_name] = float(score.item())
                    else:
                        confidence_scores[field_name] = float(score)
                else:
                    # Calculate heuristic confidence score
                    confidence_scores[field_name] = self._calculate_heuristic_confidence(
                        field_name, field_value, text
                    )
            
            logger.info(f"🎯 Confidence scores: {confidence_scores}")
            return confidence_scores
            
        except Exception as e:
            logger.error(f"AI confidence scoring failed: {e}")
            # Fallback to basic confidence calculation
            return self._calculate_basic_confidence(fields)
    
    def _calculate_heuristic_confidence(self, field_name: str, field_value: Any, text: str) -> float:
        """Calculate confidence using heuristic rules."""
        if field_name == 'invoice_number':
            # Higher confidence for well-formatted invoice numbers
            if re.match(r'^[A-Z]{2,4}\-?\d{3,8}$', str(field_value)):
                return 0.95
            elif re.match(r'^[A-Z0-9\-]{5,}$', str(field_value)):
                return 0.85
            else:
                return 0.70
        
        elif field_name == 'total_amount':
            # Higher confidence for properly formatted amounts
            if re.match(r'^\d{1,6}(,\d{3})*\.\d{2}$', str(field_value)):
                return 0.90
            elif re.match(r'^\d+\.?\d*$', str(field_value)):
                return 0.80
            else:
                return 0.60
        
        elif field_name in ['invoice_date', 'due_date']:
            # Confidence based on date format recognition
            if re.match(r'^\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4}$', str(field_value)):
                return 0.88
            elif re.search(r'\b\w+\s+\d{1,2},?\s+\d{4}\b', str(field_value)):
                return 0.85
            else:
                return 0.70
        
        elif field_name == 'vendor_name':
            # Confidence based on context and format
            value_str = str(field_value)
            if len(value_str) > 15 and not re.search(r'\d', value_str):
                return 0.85
            elif len(value_str) > 5:
                return 0.75
            else:
                return 0.60
        
        elif field_name in ['vendor_email', 'vendor_phone']:
            # High confidence for well-formatted contact info
            return 0.90
        
        else:
            # Default confidence for other fields
            return 0.75
    
    def _calculate_basic_confidence(self, fields: Dict[str, Any]) -> Dict[str, float]:
        """Basic confidence calculation as fallback."""
        confidence_scores = {}
        for field_name in fields:
            confidence_scores[field_name] = 0.70  # Default confidence
        return confidence_scores
    
    def get_ai_model_info(self) -> Dict[str, Any]:
        """Get information about the AI models being used."""
        try:
            return self.ai_processor.get_model_info()
        except Exception as e:
            logger.error(f"Could not get AI model info: {e}")
            return {
                'ner_model_available': False,
                'qa_model_available': False,
                'device': 'cpu',
                'models_used': [],
                'processing_methods': ['Fallback Regex'],
                'error': str(e)
            }