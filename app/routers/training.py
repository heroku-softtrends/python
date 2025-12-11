from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.database import get_db
from app.models import ModelTraining, FieldSelection, Invoice
from app.services.learning_service import LearningService

router = APIRouter()

@router.post("/train/feedback")
async def submit_training_feedback(
    invoice_id: int,
    field_corrections: List[Dict[str, Any]],
    db: Session = Depends(get_db)
):
    """Submit user feedback for model training."""
    
    # Validate invoice exists
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    learning_service = LearningService(db)
    
    # Process corrections
    training_data = []
    for correction in field_corrections:
        field_name = correction.get('field_name')
        correct_value = correction.get('correct_value')
        original_value = correction.get('original_value')
        confidence_feedback = correction.get('confidence_feedback')  # good, bad, neutral
        
        if not field_name or not correct_value:
            continue
        
        # Update the field selection with correct value
        field_selection = db.query(FieldSelection).filter(
            FieldSelection.invoice_id == invoice_id,
            FieldSelection.field_name == field_name
        ).first()
        
        if field_selection:
            field_selection.field_value = correct_value
            field_selection.user_verified = True
            # Adjust confidence based on feedback
            if confidence_feedback == 'good':
                field_selection.confidence_score = min(1.0, field_selection.confidence_score + 0.1)
            elif confidence_feedback == 'bad':
                field_selection.confidence_score = max(0.0, field_selection.confidence_score - 0.2)
        
        # Add to training data
        training_data.append({
            'field_name': field_name,
            'correct_value': correct_value,
            'original_value': original_value,
            'confidence_feedback': confidence_feedback,
            'invoice_context': invoice.extracted_data
        })
    
    db.commit()
    
    # Update model training
    for data in training_data:
        learning_service.update_model_training(
            data['field_name'],
            data['correct_value'],
            data['invoice_context'] or {}
        )
    
    return {
        "message": "Training feedback submitted successfully",
        "corrections_processed": len(training_data)
    }

@router.get("/train/status")
async def get_training_status(db: Session = Depends(get_db)):
    """Get current model training status."""
    
    # Get training data summary
    from sqlalchemy import func
    
    training_summary = db.query(
        ModelTraining.field_name,
        ModelTraining.version,
        func.json_array_length(ModelTraining.training_data).label('data_count'),
        ModelTraining.accuracy_score,
        ModelTraining.created_at
    ).filter(ModelTraining.is_active == True).all()
    
    training_status = []
    for summary in training_summary:
        training_status.append({
            "field_name": summary.field_name,
            "version": summary.version,
            "training_examples": summary.data_count or 0,
            "accuracy_score": summary.accuracy_score,
            "last_updated": summary.created_at
        })
    
    # Get overall statistics
    total_examples = sum(status["training_examples"] for status in training_status)
    avg_accuracy = sum(
        status["accuracy_score"] for status in training_status 
        if status["accuracy_score"] is not None
    ) / len([s for s in training_status if s["accuracy_score"] is not None]) if training_status else 0
    
    return {
        "training_status": training_status,
        "summary": {
            "total_fields_trained": len(training_status),
            "total_training_examples": total_examples,
            "average_accuracy": round(avg_accuracy, 3)
        }
    }

@router.post("/train/retrain/{field_name}")
async def retrain_field_model(
    field_name: str,
    db: Session = Depends(get_db)
):
    """Trigger retraining for a specific field."""
    
    # Get training data for the field
    training_data = db.query(ModelTraining).filter(
        ModelTraining.field_name == field_name,
        ModelTraining.is_active == True
    ).first()
    
    if not training_data or not training_data.training_data:
        raise HTTPException(
            status_code=400, 
            detail="No training data available for this field"
        )
    
    # Simple retraining simulation
    # In a real implementation, you would run actual ML training here
    examples = training_data.training_data
    
    if len(examples) < 5:
        accuracy = 0.6  # Low accuracy for few examples
    elif len(examples) < 20:
        accuracy = 0.75  # Medium accuracy
    else:
        accuracy = 0.85 + (len(examples) * 0.001)  # High accuracy, capped at reasonable level
        accuracy = min(accuracy, 0.95)  # Cap at 95%
    
    # Update training record
    training_data.accuracy_score = accuracy
    training_data.version += 1
    
    db.commit()
    
    return {
        "message": f"Retraining completed for field '{field_name}'",
        "new_accuracy": round(accuracy, 3),
        "version": training_data.version,
        "training_examples": len(examples)
    }

@router.get("/train/insights/{field_name}")
async def get_field_training_insights(
    field_name: str,
    db: Session = Depends(get_db)
):
    """Get training insights for a specific field."""
    
    # Get field statistics
    field_selections = db.query(FieldSelection).filter(
        FieldSelection.field_name == field_name
    ).all()
    
    if not field_selections:
        raise HTTPException(status_code=404, detail="No data found for this field")
    
    # Calculate insights
    total_extractions = len(field_selections)
    verified_count = len([fs for fs in field_selections if fs.user_verified])
    selected_count = len([fs for fs in field_selections if fs.is_selected])
    
    confidence_scores = [fs.confidence_score for fs in field_selections if fs.confidence_score]
    avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
    
    # Get unique values to identify patterns
    values = [fs.field_value for fs in field_selections if fs.field_value]
    unique_values = len(set(values))
    
    # Get training data
    training_data = db.query(ModelTraining).filter(
        ModelTraining.field_name == field_name,
        ModelTraining.is_active == True
    ).first()
    
    training_examples = 0
    current_accuracy = 0
    if training_data:
        training_examples = len(training_data.training_data or [])
        current_accuracy = training_data.accuracy_score or 0
    
    return {
        "field_name": field_name,
        "extraction_stats": {
            "total_extractions": total_extractions,
            "verified_extractions": verified_count,
            "selected_count": selected_count,
            "verification_rate": round(verified_count / total_extractions * 100, 1) if total_extractions > 0 else 0,
            "selection_rate": round(selected_count / total_extractions * 100, 1) if total_extractions > 0 else 0
        },
        "quality_metrics": {
            "average_confidence": round(avg_confidence, 3),
            "unique_values": unique_values,
            "current_accuracy": round(current_accuracy, 3)
        },
        "training_info": {
            "training_examples": training_examples,
            "model_version": training_data.version if training_data else 0,
            "is_trained": training_examples > 0
        },
        "recommendations": {
            "needs_more_data": training_examples < 10,
            "low_confidence": avg_confidence < 0.7,
            "high_variability": unique_values > total_extractions * 0.8 if total_extractions > 0 else False
        }
    }

@router.post("/train/bulk-retrain")
async def bulk_retrain_models(
    field_names: List[str] = None,
    db: Session = Depends(get_db)
):
    """Retrain multiple field models."""
    
    if not field_names:
        # Retrain all active models
        active_models = db.query(ModelTraining).filter(
            ModelTraining.is_active == True
        ).all()
        field_names = [model.field_name for model in active_models]
    
    results = []
    
    for field_name in field_names:
        try:
            # Use the existing retrain function
            result = await retrain_field_model(field_name, db)
            results.append({
                "field_name": field_name,
                "status": "success",
                **result
            })
        except HTTPException as e:
            results.append({
                "field_name": field_name,
                "status": "error",
                "error": e.detail
            })
    
    success_count = len([r for r in results if r["status"] == "success"])
    
    return {
        "message": f"Bulk retraining completed. {success_count}/{len(field_names)} models retrained successfully.",
        "results": results
    }