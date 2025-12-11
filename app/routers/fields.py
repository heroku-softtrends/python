from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.database import get_db
from app.models import FieldSelection, ExtractedField, ModelTraining
from app.services.learning_service import LearningService

router = APIRouter()

@router.get("/fields/available")
async def get_available_fields(db: Session = Depends(get_db)):
    """Get all available field types that can be extracted."""
    
    # Get system-defined fields
    system_fields = [
        {
            "field_name": "invoice_number",
            "field_type": "text",
            "description": "Unique invoice identifier",
            "is_system_field": True
        },
        {
            "field_name": "invoice_date",
            "field_type": "date",
            "description": "Date when the invoice was issued",
            "is_system_field": True
        },
        {
            "field_name": "due_date",
            "field_type": "date", 
            "description": "Payment due date",
            "is_system_field": True
        },
        {
            "field_name": "total_amount",
            "field_type": "currency",
            "description": "Total invoice amount",
            "is_system_field": True
        },
        {
            "field_name": "subtotal",
            "field_type": "currency",
            "description": "Subtotal before taxes",
            "is_system_field": True
        },
        {
            "field_name": "tax_amount",
            "field_type": "currency",
            "description": "Tax amount",
            "is_system_field": True
        },
        {
            "field_name": "vendor_name",
            "field_type": "text",
            "description": "Name of the vendor/supplier",
            "is_system_field": True
        },
        {
            "field_name": "vendor_address",
            "field_type": "text",
            "description": "Vendor's address",
            "is_system_field": True
        },
        {
            "field_name": "vendor_email",
            "field_type": "email",
            "description": "Vendor's email address",
            "is_system_field": True
        },
        {
            "field_name": "vendor_phone",
            "field_type": "phone",
            "description": "Vendor's phone number",
            "is_system_field": True
        },
        {
            "field_name": "bill_to_name",
            "field_type": "text",
            "description": "Bill to company/person name",
            "is_system_field": True
        },
        {
            "field_name": "bill_to_address",
            "field_type": "text",
            "description": "Billing address",
            "is_system_field": True
        },
        {
            "field_name": "po_number",
            "field_type": "text",
            "description": "Purchase order number",
            "is_system_field": True
        },
        {
            "field_name": "payment_terms",
            "field_type": "text",
            "description": "Payment terms and conditions",
            "is_system_field": True
        }
    ]
    
    # Get custom fields from database
    custom_fields = db.query(ExtractedField).filter(
        ExtractedField.is_system_field == False
    ).all()
    
    custom_field_list = [
        {
            "field_name": field.field_name,
            "field_type": field.field_type,
            "description": field.description,
            "is_system_field": field.is_system_field
        }
        for field in custom_fields
    ]
    
    return {
        "system_fields": system_fields,
        "custom_fields": custom_field_list,
        "total_count": len(system_fields) + len(custom_field_list)
    }

@router.post("/fields/update")
async def update_field_selections(
    invoice_id: int,
    field_updates: List[Dict[str, Any]],
    db: Session = Depends(get_db)
):
    """Update field selections for an invoice."""
    
    learning_service = LearningService(db)
    
    # Process each field update
    for update in field_updates:
        field_name = update.get('field_name')
        is_selected = update.get('is_selected', False)
        field_value = update.get('field_value')
        user_verified = update.get('user_verified', False)
        
        # Find existing field selection
        field_selection = db.query(FieldSelection).filter(
            FieldSelection.invoice_id == invoice_id,
            FieldSelection.field_name == field_name
        ).first()
        
        if field_selection:
            # Update existing selection
            field_selection.is_selected = is_selected
            if field_value is not None:
                field_selection.field_value = field_value
            field_selection.user_verified = user_verified
        else:
            # Create new field selection
            new_selection = FieldSelection(
                invoice_id=invoice_id,
                field_name=field_name,
                is_selected=is_selected,
                field_value=field_value,
                user_verified=user_verified,
                confidence_score=0.5  # Default confidence for user-created fields
            )
            db.add(new_selection)
    
    db.commit()
    
    # Learn from user feedback
    learning_service.learn_from_user_feedback(invoice_id, field_updates)
    
    return {"message": "Field selections updated successfully"}

@router.get("/fields/recommendations")
async def get_field_recommendations(
    user_id: int = None,
    db: Session = Depends(get_db)
):
    """Get field selection recommendations based on user history."""
    
    learning_service = LearningService(db)
    recommendations = learning_service.get_auto_select_recommendations(user_id)
    
    return {
        "recommendations": recommendations,
        "message": "Recommendations based on your previous selections"
    }

@router.post("/fields/custom")
async def create_custom_field(
    field_name: str,
    field_type: str,
    description: str = None,
    db: Session = Depends(get_db)
):
    """Create a new custom field type."""
    
    # Check if field already exists
    existing_field = db.query(ExtractedField).filter(
        ExtractedField.field_name == field_name
    ).first()
    
    if existing_field:
        raise HTTPException(status_code=400, detail="Field already exists")
    
    # Validate field type
    valid_types = ["text", "number", "date", "currency", "email", "phone", "url"]
    if field_type not in valid_types:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid field type. Must be one of: {', '.join(valid_types)}"
        )
    
    # Create new custom field
    new_field = ExtractedField(
        field_name=field_name,
        field_type=field_type,
        description=description,
        is_system_field=False
    )
    
    db.add(new_field)
    db.commit()
    db.refresh(new_field)
    
    return {
        "id": new_field.id,
        "field_name": new_field.field_name,
        "field_type": new_field.field_type,
        "description": new_field.description,
        "message": "Custom field created successfully"
    }

@router.get("/fields/statistics")
async def get_field_statistics(db: Session = Depends(get_db)):
    """Get statistics about field usage and accuracy."""
    
    # Get field selection statistics
    from sqlalchemy import func
    
    stats = db.query(
        FieldSelection.field_name,
        func.count(FieldSelection.id).label('total_count'),
        func.avg(FieldSelection.confidence_score).label('avg_confidence'),
        func.sum(func.cast(FieldSelection.is_selected, db.Integer)).label('selected_count'),
        func.sum(func.cast(FieldSelection.user_verified, db.Integer)).label('verified_count')
    ).group_by(FieldSelection.field_name).all()
    
    field_stats = []
    for stat in stats:
        selection_rate = (stat.selected_count / stat.total_count * 100) if stat.total_count > 0 else 0
        verification_rate = (stat.verified_count / stat.total_count * 100) if stat.total_count > 0 else 0
        
        field_stats.append({
            "field_name": stat.field_name,
            "total_extractions": stat.total_count,
            "average_confidence": round(stat.avg_confidence or 0, 2),
            "selection_rate": round(selection_rate, 1),
            "verification_rate": round(verification_rate, 1),
            "selected_count": stat.selected_count,
            "verified_count": stat.verified_count
        })
    
    return {
        "field_statistics": field_stats,
        "total_fields": len(field_stats)
    }