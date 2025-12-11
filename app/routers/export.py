from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import FieldSelection, Invoice, Export
from app.schemas.invoice import ExportRequest, ExportResponse
import json
from datetime import datetime

router = APIRouter()

@router.post("/export", response_model=ExportResponse)
async def export_selected_data(
    export_request: ExportRequest,
    db: Session = Depends(get_db)
):
    """Export selected fields from an invoice to PostgreSQL as JSON."""
    
    # Validate invoice exists
    invoice = db.query(Invoice).filter(Invoice.id == export_request.invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Get selected field data
    selected_fields = db.query(FieldSelection).filter(
        FieldSelection.invoice_id == export_request.invoice_id,
        FieldSelection.field_name.in_(export_request.selected_fields)
    ).all()
    
    if not selected_fields:
        raise HTTPException(status_code=400, detail="No selected fields found")
    
    # Build export data
    export_data = {
        "invoice_id": export_request.invoice_id,
        "invoice_filename": invoice.original_filename,
        "export_timestamp": datetime.utcnow().isoformat(),
        "fields": {}
    }
    
    for field in selected_fields:
        export_data["fields"][field.field_name] = {
            "value": field.field_value,
            "confidence_score": field.confidence_score,
            "user_verified": field.user_verified
        }
    
    # Create export record
    export_record = Export(
        invoice_id=export_request.invoice_id,
        export_data=export_data,
        export_format=export_request.export_format
    )
    db.add(export_record)
    db.commit()
    db.refresh(export_record)
    
    # Update field selections to mark as selected
    for field_name in export_request.selected_fields:
        field_selection = db.query(FieldSelection).filter(
            FieldSelection.invoice_id == export_request.invoice_id,
            FieldSelection.field_name == field_name
        ).first()
        if field_selection:
            field_selection.is_selected = True
    
    db.commit()
    
    return ExportResponse(
        id=export_record.id,
        export_data=export_record.export_data,
        export_timestamp=export_record.export_timestamp,
        export_format=export_record.export_format
    )

@router.get("/exports")
async def get_exports(
    invoice_id: int = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get list of exports."""
    
    query = db.query(Export)
    
    if invoice_id:
        query = query.filter(Export.invoice_id == invoice_id)
    
    exports = query.offset(skip).limit(limit).all()
    
    return [
        {
            "id": export.id,
            "invoice_id": export.invoice_id,
            "export_data": export.export_data,
            "export_timestamp": export.export_timestamp,
            "export_format": export.export_format
        }
        for export in exports
    ]

@router.get("/exports/{export_id}")
async def get_export(export_id: int, db: Session = Depends(get_db)):
    """Get specific export data."""
    
    export = db.query(Export).filter(Export.id == export_id).first()
    if not export:
        raise HTTPException(status_code=404, detail="Export not found")
    
    return {
        "id": export.id,
        "invoice_id": export.invoice_id,
        "export_data": export.export_data,
        "export_timestamp": export.export_timestamp,
        "export_format": export.export_format
    }

@router.post("/export/bulk")
async def bulk_export(
    invoice_ids: List[int],
    selected_fields: List[str],
    export_format: str = "json",
    db: Session = Depends(get_db)
):
    """Export data from multiple invoices."""
    
    exports = []
    
    for invoice_id in invoice_ids:
        try:
            export_request = ExportRequest(
                invoice_id=invoice_id,
                selected_fields=selected_fields,
                export_format=export_format
            )
            
            # Use the existing export function
            export_result = await export_selected_data(export_request, db)
            exports.append(export_result)
            
        except HTTPException as e:
            # Continue with other invoices if one fails
            exports.append({
                "invoice_id": invoice_id,
                "error": e.detail,
                "status": "failed"
            })
    
    return {
        "message": f"Bulk export completed for {len(invoice_ids)} invoices",
        "exports": exports,
        "success_count": len([e for e in exports if "error" not in e]),
        "failure_count": len([e for e in exports if "error" in e])
    }