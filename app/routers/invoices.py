from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models import Invoice, FieldSelection
from app.schemas.invoice import Invoice as InvoiceSchema

router = APIRouter()

@router.get("/invoices", response_model=List[InvoiceSchema])
async def get_invoices(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get list of processed invoices."""
    
    query = db.query(Invoice)
    
    if status:
        query = query.filter(Invoice.status == status)
    
    invoices = query.offset(skip).limit(limit).all()
    return invoices

@router.get("/invoices/{invoice_id}", response_model=InvoiceSchema)
async def get_invoice(invoice_id: int, db: Session = Depends(get_db)):
    """Get details of a specific invoice."""
    
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    return invoice

@router.get("/invoices/{invoice_id}/fields")
async def get_invoice_fields(invoice_id: int, db: Session = Depends(get_db)):
    """Get extracted fields for a specific invoice."""
    
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Get field selections
    field_selections = db.query(FieldSelection).filter(
        FieldSelection.invoice_id == invoice_id
    ).all()
    
    # Format response
    fields = []
    for selection in field_selections:
        fields.append({
            'field_name': selection.field_name,
            'field_value': selection.field_value,
            'is_selected': selection.is_selected,
            'confidence_score': selection.confidence_score,
            'user_verified': selection.user_verified
        })
    
    return {
        'invoice_id': invoice_id,
        'fields': fields,
        'raw_data': invoice.extracted_data
    }

@router.delete("/invoices/{invoice_id}")
async def delete_invoice(invoice_id: int, db: Session = Depends(get_db)):
    """Delete an invoice and its associated data."""
    
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Delete associated field selections
    db.query(FieldSelection).filter(FieldSelection.invoice_id == invoice_id).delete()
    
    # Delete file if it exists
    import os
    if os.path.exists(invoice.file_path):
        os.remove(invoice.file_path)
    
    # Delete invoice record
    db.delete(invoice)
    db.commit()
    
    return {"message": "Invoice deleted successfully"}