"""
AI-powered invoice field extraction using Transformer models.
This replaces regex patterns with advanced NLP models.
Falls back to lightweight AI when heavy models aren't available.
"""

import re
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

# Try to import heavy AI libraries, fallback to lightweight if not available
try:
    from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline
    import torch
    TRANSFORMERS_AVAILABLE = True
    logger = logging.getLogger(__name__)
    logger.info("🤖 Heavy AI libraries available (transformers, torch)")
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.info("🚀 Using lightweight AI mode (transformers not available)")

# Import lightweight fallback
from .lightweight_ai import get_lightweight_processor

class TransformerInvoiceProcessor:
    """
    AI-powered invoice processing using Transformer models.
    Falls back to lightweight AI when heavy models aren't available.
    """
    
    def __init__(self):
        """Initialize AI models for invoice processing."""
        
        if not TRANSFORMERS_AVAILABLE:
            logger.info("🚀 Initializing lightweight AI processor")
            self.lightweight_processor = get_lightweight_processor()
            self.ner_pipeline = None
            self.qa_pipeline = None
            self.use_lightweight = True
            return
        
        # Heavy AI initialization
        self.use_lightweight = False
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"🤖 Using device: {self.device}")
        
        # Initialize NER pipeline for entity extraction
        try:
            # Use a model trained on financial documents
            self.ner_pipeline = pipeline(
                "ner",
                model="dbmdz/bert-large-cased-finetuned-conll03-english",
                tokenizer="dbmdz/bert-large-cased-finetuned-conll03-english",
                aggregation_strategy="simple",
                device=0 if self.device == "cuda" else -1
            )
            logger.info("✅ NER model loaded successfully")
        except Exception as e:
            logger.warning(f"⚠️ Could not load NER model: {e}")
            self.ner_pipeline = None
        
        # Initialize question-answering pipeline for specific field extraction
        try:
            self.qa_pipeline = pipeline(
                "question-answering",
                model="distilbert-base-cased-distilled-squad",
                device=0 if self.device == "cuda" else -1
            )
            logger.info("✅ QA model loaded successfully")
        except Exception as e:
            logger.warning(f"⚠️ Could not load QA model: {e}")
            self.qa_pipeline = None
            
        # Fallback regex patterns (enhanced versions)
        self.fallback_patterns = {
            'invoice_number': [
                r'(?:invoice|inv)[\s#:]*([A-Z0-9\-\_]{3,20})',
                r'(?:number|no|#)[\s:]*([A-Z0-9\-\_]{3,20})',
                r'(\b[A-Z]{2,4}\-\d{3,8}\b)',
            ],
            'total_amount': [
                r'(?:total|amount\s+due|grand\s+total)[\s:$]*([0-9,]+\.?\d{0,2})',
                r'\$([0-9,]+\.?\d{2})',
                r'([0-9,]+\.?\d{2})(?=\s*$)',  # End of line amounts
            ],
            'invoice_date': [
                r'(?:date|invoice\s+date)[\s:]*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})',
                r'(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})',
                r'(\b\w+\s+\d{1,2},?\s+\d{4}\b)',  # "January 15, 2024"
            ],
            'due_date': [
                r'(?:due|payment\s+due)[\s:]*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})',
                r'(?:due\s+date)[\s:]*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})',
            ]
        }
    
    def extract_with_transformers(self, text: str) -> Dict[str, Any]:
        """
        Extract invoice fields using AI models.
        Falls back to lightweight AI when heavy models aren't available.
        """
        
        # Use lightweight processor if heavy AI isn't available
        if self.use_lightweight:
            logger.info("🚀 Using lightweight AI extraction")
            return self.lightweight_processor.extract_with_lightweight_ai(text)
        
        # Heavy AI extraction
        logger.info("🤖 Using heavy AI extraction (transformers)")
        extracted_fields = {}
        confidence_scores = {}
        
        # Method 1: Named Entity Recognition
        if self.ner_pipeline:
            ner_results = self._extract_with_ner(text)
            extracted_fields.update(ner_results['fields'])
            confidence_scores.update(ner_results['confidence'])
        
        # Method 2: Question Answering approach
        if self.qa_pipeline:
            qa_results = self._extract_with_qa(text)
            # Merge QA results, prioritizing higher confidence
            for field, data in qa_results.items():
                if field not in extracted_fields or data['confidence'] > confidence_scores.get(field, 0):
                    extracted_fields[field] = data['value']
                    confidence_scores[field] = data['confidence']
        
        # Method 3: Enhanced regex fallback with AI confidence scoring
        regex_results = self._extract_with_enhanced_regex(text)
        for field, data in regex_results.items():
            if field not in extracted_fields:
                extracted_fields[field] = data['value']
                confidence_scores[field] = data['confidence']
        
        # Post-process and validate results
        validated_results = self._validate_and_enhance_fields(extracted_fields, text)
        
        return {
            'extracted_fields': validated_results,
            'confidence_scores': confidence_scores,
            'processing_method': 'transformers_ai'
        }
    
    def _extract_with_ner(self, text: str) -> Dict[str, Any]:
        """Extract entities using Named Entity Recognition."""
        try:
            # Process text in chunks to handle long documents
            max_length = 512
            chunks = [text[i:i+max_length] for i in range(0, len(text), max_length)]
            
            all_entities = []
            for chunk in chunks:
                entities = self.ner_pipeline(chunk)
                all_entities.extend(entities)
            
            # Process entities and map to invoice fields
            fields = {}
            confidence = {}
            
            for entity in all_entities:
                entity_text = entity['word']
                entity_type = entity['entity_group']
                score = entity['score']
                
                # Map NER labels to invoice fields - CONVERT SCORES TO PYTHON FLOAT
                if entity_type in ['ORG', 'ORGANIZATION']:
                    if 'vendor_name' not in fields or score > confidence.get('vendor_name', 0):
                        fields['vendor_name'] = entity_text
                        confidence['vendor_name'] = float(score)
                
                elif entity_type in ['MONEY', 'CARDINAL']:
                    # Check if it looks like a monetary amount
                    if re.search(r'[\d,]+\.?\d*', entity_text):
                        if 'total_amount' not in fields or score > confidence.get('total_amount', 0):
                            fields['total_amount'] = re.sub(r'[^\d,.]', '', entity_text)
                            confidence['total_amount'] = float(score * 0.8)  # Lower confidence for NER amounts
                
                elif entity_type in ['DATE']:
                    if 'invoice_date' not in fields or score > confidence.get('invoice_date', 0):
                        fields['invoice_date'] = entity_text
                        confidence['invoice_date'] = float(score)
            
            return {'fields': fields, 'confidence': confidence}
            
        except Exception as e:
            logger.error(f"NER extraction failed: {e}")
            return {'fields': {}, 'confidence': {}}
    
    def _extract_with_qa(self, text: str) -> Dict[str, Dict[str, Any]]:
        """Extract specific fields using Question Answering."""
        questions = {
            'invoice_number': "What is the invoice number?",
            'total_amount': "What is the total amount or total due?",
            'invoice_date': "What is the invoice date?",
            'due_date': "What is the due date or payment due date?",
            'vendor_name': "What is the company name or vendor name?",
            'vendor_address': "What is the company address?",
        }
        
        results = {}
        
        try:
            for field, question in questions.items():
                try:
                    answer = self.qa_pipeline(
                        question=question,
                        context=text[:2000],  # Limit context length
                        max_answer_len=50
                    )
                    
                    # Filter out low-confidence or nonsensical answers
                    if answer['score'] > 0.1 and len(answer['answer'].strip()) > 0:
                        # Post-process the answer
                        processed_answer = self._post_process_qa_answer(field, answer['answer'])
                        if processed_answer:
                            results[field] = {
                                'value': processed_answer,
                                'confidence': float(answer['score'])  # Convert to Python float
                            }
                
                except Exception as e:
                    logger.warning(f"QA extraction failed for {field}: {e}")
                    continue
            
            return results
            
        except Exception as e:
            logger.error(f"QA pipeline failed: {e}")
            return {}
    
    def _post_process_qa_answer(self, field_type: str, answer: str) -> Optional[str]:
        """Post-process QA answers to clean and validate them."""
        answer = answer.strip()
        
        if field_type == 'invoice_number':
            # Extract alphanumeric invoice number
            match = re.search(r'[A-Z0-9\-\_]{3,20}', answer.upper())
            return match.group(0) if match else None
        
        elif field_type in ['total_amount']:
            # Extract monetary amount
            match = re.search(r'[\d,]+\.?\d*', answer.replace(',', ''))
            return match.group(0) if match else None
        
        elif field_type in ['invoice_date', 'due_date']:
            # Validate date format
            if re.search(r'\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}', answer):
                return answer
            elif re.search(r'\b\w+\s+\d{1,2},?\s+\d{4}\b', answer):
                return answer
            return None
        
        elif field_type in ['vendor_name', 'vendor_address']:
            # Clean up company names and addresses
            if len(answer) > 2 and len(answer) < 100:
                return answer
            return None
        
        return answer if len(answer) > 0 else None
    
    def _extract_with_enhanced_regex(self, text: str) -> Dict[str, Dict[str, Any]]:
        """Enhanced regex extraction with AI-based confidence scoring."""
        results = {}
        
        for field_type, patterns in self.fallback_patterns.items():
            best_match = None
            best_confidence = 0
            
            for i, pattern in enumerate(patterns):
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    # Calculate confidence based on pattern specificity and position
                    pattern_confidence = (len(patterns) - i) / len(patterns)  # Earlier patterns = higher confidence
                    context_confidence = self._calculate_context_confidence(field_type, matches[0], text)
                    
                    confidence = (pattern_confidence + context_confidence) / 2
                    
                    if confidence > best_confidence:
                        best_match = matches[0]
                        best_confidence = confidence
            
            if best_match:
                results[field_type] = {
                    'value': best_match,
                    'confidence': best_confidence
                }
        
        return results
    
    def _calculate_context_confidence(self, field_type: str, value: str, text: str) -> float:
        """Calculate confidence based on context around the extracted value."""
        # Find the position of the value in text
        value_pos = text.lower().find(value.lower())
        if value_pos == -1:
            return 0.5
        
        # Get context around the value
        start = max(0, value_pos - 50)
        end = min(len(text), value_pos + len(value) + 50)
        context = text[start:end].lower()
        
        # Field-specific context keywords that increase confidence
        context_keywords = {
            'invoice_number': ['invoice', 'number', 'inv', '#'],
            'total_amount': ['total', 'amount', 'due', '$', 'sum'],
            'invoice_date': ['date', 'invoice', 'issued'],
            'due_date': ['due', 'payment', 'deadline'],
            'vendor_name': ['from', 'company', 'vendor'],
        }
        
        if field_type in context_keywords:
            keyword_count = sum(1 for keyword in context_keywords[field_type] if keyword in context)
            return min(1.0, 0.5 + (keyword_count * 0.2))
        
        return 0.5
    
    def _validate_and_enhance_fields(self, fields: Dict[str, str], text: str) -> Dict[str, str]:
        """Validate and enhance extracted fields using business rules."""
        validated = {}
        
        for field, value in fields.items():
            if field == 'total_amount':
                # Clean and validate amounts
                clean_amount = re.sub(r'[^\d,.]', '', str(value))
                if re.match(r'^\d{1,10}(,\d{3})*(\.\d{2})?$', clean_amount):
                    validated[field] = clean_amount
            
            elif field in ['invoice_date', 'due_date']:
                # Validate dates
                if re.search(r'\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}', str(value)):
                    validated[field] = str(value)
            
            elif field == 'invoice_number':
                # Validate invoice numbers
                clean_invoice = re.sub(r'[^\w\-]', '', str(value))
                if len(clean_invoice) >= 3:
                    validated[field] = clean_invoice
            
            else:
                # General validation
                if isinstance(value, str) and len(value.strip()) > 0:
                    validated[field] = value.strip()
        
        return validated
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about loaded models."""
        return {
            'ner_model_available': self.ner_pipeline is not None,
            'qa_model_available': self.qa_pipeline is not None,
            'device': self.device,
            'models_used': [
                'dbmdz/bert-large-cased-finetuned-conll03-english' if self.ner_pipeline else None,
                'distilbert-base-cased-distilled-squad' if self.qa_pipeline else None
            ],
            'processing_methods': ['NER', 'QA', 'Enhanced Regex'],
        }