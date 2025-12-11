from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class InvoiceBase(BaseModel):
    filename: str
    original_filename: str

class InvoiceCreate(InvoiceBase):
    pass

class Invoice(InvoiceBase):
    id: int
    file_path: str
    upload_timestamp: datetime
    processed_timestamp: Optional[datetime] = None
    status: str
    extracted_data: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True

class ExtractedFieldBase(BaseModel):
    field_name: str
    field_type: str
    description: Optional[str] = None
    is_system_field: bool = False

class ExtractedField(ExtractedFieldBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class FieldSelectionBase(BaseModel):
    field_name: str
    is_selected: bool = False
    field_value: Optional[str] = None
    confidence_score: Optional[float] = None
    user_verified: bool = False

class FieldSelection(FieldSelectionBase):
    id: int
    invoice_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class FieldSelectionCreate(FieldSelectionBase):
    invoice_id: int

class FieldSelectionUpdate(BaseModel):
    is_selected: Optional[bool] = None
    field_value: Optional[str] = None
    user_verified: Optional[bool] = None

class ExportRequest(BaseModel):
    invoice_id: int
    selected_fields: List[str]
    export_format: str = "json"

class ExportResponse(BaseModel):
    id: int
    export_data: Dict[str, Any]
    export_timestamp: datetime
    export_format: str
    
    class Config:
        from_attributes = True

class UserPreferenceBase(BaseModel):
    preferred_fields: List[str]
    auto_select: bool = True

class UserPreference(UserPreferenceBase):
    id: int
    user_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ProcessingResult(BaseModel):
    success: bool
    message: str
    extracted_fields: List[Dict[str, Any]]
    confidence_scores: Dict[str, float]

class UploadResponse(BaseModel):
    invoice_id: int
    filename: str
    status: str
    extracted_fields: List[Dict[str, Any]]
    message: str