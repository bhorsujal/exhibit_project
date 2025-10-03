from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# This will be set by the app
db = SQLAlchemy()

class ProcessedFile(db.Model):
    """Model for tracking processed files"""
    __tablename__ = 'processed_files'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False, unique=True)
    processed_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), nullable=False)  # 'success', 'failed', 'partial'
    records_processed = db.Column(db.Integer, default=0)
    errors_count = db.Column(db.Integer, default=0)
    file_size = db.Column(db.BigInteger)
    processing_time = db.Column(db.Float)  # in seconds
    
    def __repr__(self):
        return f'<ProcessedFile {self.filename}>'

class ErrorRecord(db.Model):
    """Model for tracking error records"""
    __tablename__ = 'error_records'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    line_number = db.Column(db.Integer, nullable=False)
    error_message = db.Column(db.Text, nullable=False)
    data = db.Column(db.Text)  # The actual line data that caused the error
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ErrorRecord {self.filename}:{self.line_number}>'

class FileFormat(db.Model):
    """Model for storing file format configurations"""
    __tablename__ = 'file_formats'
    
    id = db.Column(db.Integer, primary_key=True)
    filename_pattern = db.Column(db.String(255), nullable=False)
    time_to_arrive = db.Column(db.Time)
    output_filename = db.Column(db.String(255), nullable=False)
    format_config = db.Column(db.JSON)  # Store field definitions as JSON
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<FileFormat {self.filename_pattern}>'