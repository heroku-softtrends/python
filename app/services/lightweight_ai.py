import re
import logging
from typing import Dict, Any
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

logger = logging.getLogger(__name__)

class LightweightInvoiceProcessor:
    """Lightweight invoice processor using NLTK and scikit-learn instead of transformers."""
    
    def __init__(self):
        self.setup_nltk()
        self.stemmer = PorterStemmer()
        logger.info("🚀 Lightweight AI processor initialized (NLTK + scikit-learn)")
    
    def setup_nltk(self):
        """Download required NLTK data."""
        try:
            import ssl
            try:
                _create_unverified_https_context = ssl._create_unverified_context
            except AttributeError:
                pass
            else:
                ssl._create_default_https_context = _create_unverified_https_context
            
            nltk.download('punkt', quiet=True)
            nltk.download('stopwords', quiet=True)
            nltk.download('averaged_perceptron_tagger', quiet=True)
        except Exception as e:
            logger.warning(f"NLTK setup warning: {e}")
    
    def extract_with_lightweight_ai(self, text: str) -> Dict[str, Any]:
        """Extract invoice fields using lightweight NLP methods."""
        
        # Enhanced regex patterns with confidence scoring
        patterns = {
            'vendor_name': [
                (r'(?:from|bill\s+to|vendor|company)[:\s]+([A-Za-z\s]{3,30})', 0.8),
                (r'^([A-Za-z\s&]{3,30})(?:\s*\n|\s*address)', 0.7),
                (r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*\n', 0.6)
            ],
            'invoice_number': [
                (r'(?:invoice\s+(?:number|#|no\.?)[:\s]*)([\w\-]+)', 0.9),
                (r'(?:inv\.?\s*#?\s*)[:\s]*([\w\-]+)', 0.8),
                (r'#\s*(INV[\w\-]+)', 0.9)
            ],
            'total_amount': [
                (r'(?:total\s*amount?\s*(?:due)?[:\s]*)\$?([0-9,]+\.?[0-9]*)', 0.9),
                (r'(?:amount\s*due[:\s]*)\$?([0-9,]+\.?[0-9]*)', 0.8),
                (r'(?:total[:\s]*)\$?([0-9,]+\.?[0-9]*)', 0.7),
                (r'\$([0-9,]+\.[0-9]{2})(?:\s*$|\s*\n)', 0.6)
            ],
            'vendor_address': [
                (r'(?:address[:\s]*)(.*?)(?:\n|$)', 0.8),
                (r'([0-9]+\s+[A-Za-z\s]+(?:street|st|avenue|ave|road|rd|boulevard|blvd).*?)(?:\n|$)', 0.7),
                (r'([A-Za-z\s]+,\s*[A-Z]{2}\s*[0-9]{5})', 0.9)
            ]
        }
        
        extracted_fields = {}
        confidence_scores = {}
        
        # Clean text for better matching
        clean_text = re.sub(r'\s+', ' ', text.lower().strip())
        
        for field_name, field_patterns in patterns.items():
            best_match = None
            best_confidence = 0.0
            
            for pattern, base_confidence in field_patterns:
                match = re.search(pattern, clean_text, re.IGNORECASE | re.MULTILINE)
                if match:
                    value = match.group(1).strip()
                    
                    # Apply confidence modifiers based on context
                    confidence = self._calculate_confidence(field_name, value, text, base_confidence)
                    
                    if confidence > best_confidence:
                        best_match = value
                        best_confidence = confidence
            
            if best_match:
                # Clean up the extracted value
                cleaned_value = self._clean_extracted_value(field_name, best_match)
                extracted_fields[field_name] = cleaned_value
                confidence_scores[field_name] = round(best_confidence, 2)
        
        logger.info(f"🎯 Lightweight AI extracted {len(extracted_fields)} fields: {list(extracted_fields.keys())}")
        
        return {
            'extracted_fields': extracted_fields,
            'confidence_scores': confidence_scores,
            'method': 'lightweight_nlp'
        }
    
    def _calculate_confidence(self, field_name: str, value: str, full_text: str, base_confidence: float) -> float:
        """Calculate confidence score based on context and value characteristics."""
        
        confidence_modifiers = {
            'invoice_number': {
                'patterns': [r'INV', r'[0-9]{4}', r'-'],
                'boost': 0.1
            },
            'total_amount': {
                'patterns': [r'\.[0-9]{2}$', r'^[0-9,]+'],
                'boost': 0.15
            },
            'vendor_name': {
                'patterns': [r'^[A-Z]', r'[a-z]{3,}'],
                'boost': 0.05
            }
        }
        
        confidence = base_confidence
        
        # Apply field-specific modifiers
        if field_name in confidence_modifiers:
            for pattern in confidence_modifiers[field_name]['patterns']:
                if re.search(pattern, value):
                    confidence += confidence_modifiers[field_name]['boost']
        
        # General validation
        if len(value.strip()) < 2:
            confidence *= 0.5
        elif len(value.strip()) > 100:
            confidence *= 0.7
        
        return min(confidence, 1.0)
    
    def _clean_extracted_value(self, field_name: str, value: str) -> str:
        """Clean and format extracted values."""
        
        # Remove extra whitespace
        value = re.sub(r'\s+', ' ', value.strip())
        
        if field_name == 'total_amount':
            # Clean amount: remove commas, ensure decimal format
            value = re.sub(r'[^\d.]', '', value)
            if '.' not in value and len(value) > 2:
                # Assume last two digits are cents
                value = value[:-2] + '.' + value[-2:]
        
        elif field_name == 'vendor_name':
            # Capitalize properly
            value = ' '.join(word.capitalize() for word in value.split())
        
        elif field_name == 'invoice_number':
            # Remove extra spaces and normalize
            value = re.sub(r'\s+', '', value.upper())
        
        return value

# Global lightweight processor instance
lightweight_processor = None

def get_lightweight_processor():
    """Get lightweight processor instance (lazy initialization)."""
    global lightweight_processor
    if lightweight_processor is None:
        lightweight_processor = LightweightInvoiceProcessor()
    return lightweight_processor