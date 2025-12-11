from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import json
from datetime import datetime

from app.models import UserPreference, ModelTraining, FieldSelection, Invoice
from app.services.pdf_processor import PDFProcessor

class LearningService:
    def __init__(self, db: Session):
        self.db = db
        self.pdf_processor = PDFProcessor()
    
    def get_user_preferences(self, user_id: Optional[int] = None) -> List[str]:
        """Get user's preferred fields for auto-selection."""
        preference = self.db.query(UserPreference).filter(
            UserPreference.user_id == user_id
        ).first()
        
        if preference:
            return preference.preferred_fields
        
        # Return default common fields if no preferences found
        return [
            'invoice_number',
            'invoice_date', 
            'total_amount',
            'vendor_name'
        ]
    
    def update_user_preferences(self, selected_fields: List[str], user_id: Optional[int] = None):
        """Update user preferences based on their selections."""
        existing_preference = self.db.query(UserPreference).filter(
            UserPreference.user_id == user_id
        ).first()
        
        if existing_preference:
            # Update existing preference with new selections
            current_fields = set(existing_preference.preferred_fields)
            new_fields = set(selected_fields)
            
            # Combine and prioritize frequently selected fields
            combined_fields = list(current_fields.union(new_fields))
            
            existing_preference.preferred_fields = combined_fields
            existing_preference.updated_at = datetime.utcnow()
        else:
            # Create new preference
            new_preference = UserPreference(
                user_id=user_id,
                preferred_fields=selected_fields,
                auto_select=True
            )
            self.db.add(new_preference)
        
        self.db.commit()
    
    def auto_select_fields(self, invoice_id: int, extracted_fields: Dict[str, Any], user_id: Optional[int] = None):
        """Automatically select fields based on user preferences and model learning."""
        preferred_fields = self.get_user_preferences(user_id)
        
        # Get existing field selections for this invoice
        existing_selections = self.db.query(FieldSelection).filter(
            FieldSelection.invoice_id == invoice_id
        ).all()
        
        # Convert to dict for easier lookup
        existing_dict = {fs.field_name: fs for fs in existing_selections}
        
        for field_name, field_value in extracted_fields.items():
            if field_name in existing_dict:
                # Update existing selection
                selection = existing_dict[field_name]
                selection.field_value = str(field_value) if field_value else None
                selection.is_selected = field_name in preferred_fields
            else:
                # Create new field selection
                confidence_scores = self.pdf_processor.get_confidence_scores(
                    {field_name: field_value}, ""
                )
                
                new_selection = FieldSelection(
                    invoice_id=invoice_id,
                    field_name=field_name,
                    field_value=str(field_value) if field_value else None,
                    is_selected=field_name in preferred_fields,
                    confidence_score=confidence_scores.get(field_name, 0.5)
                )
                self.db.add(new_selection)
        
        self.db.commit()
    
    def learn_from_user_feedback(self, invoice_id: int, field_selections: List[Dict[str, Any]]):
        """Learn from user's field selections and corrections."""
        # Get invoice text for training
        invoice = self.db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice or not invoice.extracted_data:
            return
        
        # Update model training data
        for selection in field_selections:
            field_name = selection.get('field_name')
            is_selected = selection.get('is_selected', False)
            field_value = selection.get('field_value')
            user_verified = selection.get('user_verified', False)
            
            if user_verified and field_value:
                # This is verified training data
                self.update_model_training(field_name, field_value, invoice.extracted_data)
        
        # Update field selections in database
        for selection_data in field_selections:
            field_name = selection_data.get('field_name')
            selection = self.db.query(FieldSelection).filter(
                FieldSelection.invoice_id == invoice_id,
                FieldSelection.field_name == field_name
            ).first()
            
            if selection:
                selection.is_selected = selection_data.get('is_selected', False)
                selection.field_value = selection_data.get('field_value')
                selection.user_verified = selection_data.get('user_verified', False)
        
        self.db.commit()
        
        # Update user preferences based on selections
        selected_fields = [
            sel['field_name'] for sel in field_selections 
            if sel.get('is_selected', False)
        ]
        self.update_user_preferences(selected_fields)
    
    def update_model_training(self, field_name: str, correct_value: str, context_data: Dict[str, Any]):
        """Update model training data with user corrections."""
        existing_training = self.db.query(ModelTraining).filter(
            ModelTraining.field_name == field_name,
            ModelTraining.is_active == True
        ).first()
        
        training_example = {
            'value': correct_value,
            'context': context_data,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if existing_training:
            # Add to existing training data
            current_data = existing_training.training_data or []
            current_data.append(training_example)
            
            # Keep only last 100 examples to prevent data from growing too large
            if len(current_data) > 100:
                current_data = current_data[-100:]
            
            existing_training.training_data = current_data
            existing_training.version += 1
        else:
            # Create new training record
            new_training = ModelTraining(
                field_name=field_name,
                training_data=[training_example],
                version=1,
                is_active=True
            )
            self.db.add(new_training)
        
        self.db.commit()
    
    def get_field_patterns(self, field_name: str) -> List[Dict[str, Any]]:
        """Get learned patterns for a specific field."""
        training_data = self.db.query(ModelTraining).filter(
            ModelTraining.field_name == field_name,
            ModelTraining.is_active == True
        ).first()
        
        if training_data and training_data.training_data:
            return training_data.training_data
        
        return []
    
    def improve_field_extraction(self, text: str, field_name: str) -> Optional[str]:
        """Use learned patterns to improve field extraction."""
        patterns = self.get_field_patterns(field_name)
        
        if not patterns:
            return None
        
        # Simple pattern matching improvement
        # In a real implementation, you might use ML models here
        for pattern in patterns[-10:]:  # Use last 10 patterns
            value = pattern.get('value', '')
            if value and len(value) > 2:
                # Simple substring matching
                if value.lower() in text.lower():
                    return value
        
        return None
    
    def get_auto_select_recommendations(self, user_id: Optional[int] = None) -> Dict[str, bool]:
        """Get recommendations for which fields to auto-select."""
        preferences = self.get_user_preferences(user_id)
        
        # Create recommendation dict
        all_possible_fields = [
            'invoice_number', 'invoice_date', 'total_amount', 'subtotal',
            'tax_amount', 'vendor_name', 'vendor_address', 'vendor_email',
            'vendor_phone', 'bill_to_name', 'bill_to_address', 'due_date',
            'payment_terms', 'po_number', 'line_items'
        ]
        
        recommendations = {}
        for field in all_possible_fields:
            recommendations[field] = field in preferences
        
        return recommendations