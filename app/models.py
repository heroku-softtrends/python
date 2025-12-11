from sqlalchemy import Column, Integer, String, DateTime, JSON, Boolean, Text, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Invoice(Base):
    __tablename__ = "invoices"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    upload_timestamp = Column(DateTime, default=datetime.utcnow)
    processed_timestamp = Column(DateTime, nullable=True)
    status = Column(String, default="uploaded")  # uploaded, processing, completed, error
    extracted_data = Column(JSON, nullable=True)
    user_id = Column(Integer, nullable=True)  # For future user authentication
    
    # Relationships
    exports = relationship("Export", back_populates="invoice")
    field_selections = relationship("FieldSelection", back_populates="invoice")

class ExtractedField(Base):
    __tablename__ = "extracted_fields"
    
    id = Column(Integer, primary_key=True, index=True)
    field_name = Column(String, nullable=False)
    field_type = Column(String, nullable=False)  # text, number, date, currency
    description = Column(String, nullable=True)
    is_system_field = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class FieldSelection(Base):
    __tablename__ = "field_selections"
    
    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"))
    field_name = Column(String, nullable=False)
    is_selected = Column(Boolean, default=False)
    field_value = Column(Text, nullable=True)
    confidence_score = Column(Float, nullable=True)
    user_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    invoice = relationship("Invoice", back_populates="field_selections")

class Export(Base):
    __tablename__ = "exports"
    
    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"))
    export_data = Column(JSON, nullable=False)
    export_timestamp = Column(DateTime, default=datetime.utcnow)
    export_format = Column(String, default="json")  # json, csv, excel
    user_id = Column(Integer, nullable=True)
    
    # Relationships
    invoice = relationship("Invoice", back_populates="exports")

class UserPreference(Base):
    __tablename__ = "user_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)
    preferred_fields = Column(JSON, nullable=False)  # List of preferred field names
    auto_select = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ModelTraining(Base):
    __tablename__ = "model_training"
    
    id = Column(Integer, primary_key=True, index=True)
    field_name = Column(String, nullable=False)
    training_data = Column(JSON, nullable=False)  # Contains text patterns and examples
    accuracy_score = Column(Float, nullable=True)
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)