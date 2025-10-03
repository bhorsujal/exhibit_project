#!/usr/bin/env python3
"""
Minimal Exhibit Monitor - Text File Processing System
"""

from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import os
import time
import logging
from datetime import datetime
from pathlib import Path
import csv
import io
from lxml import etree

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///exhibit_monitor.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database Models
class ProcessedFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    processed_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), nullable=False)
    records_processed = db.Column(db.Integer, default=0)
    errors_count = db.Column(db.Integer, default=0)

class ErrorRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    line_number = db.Column(db.Integer, nullable=False)
    error_message = db.Column(db.Text, nullable=False)
    data = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class FileFormat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename_pattern = db.Column(db.String(255), nullable=False)
    time_to_arrive = db.Column(db.Time)
    output_filename = db.Column(db.String(255), nullable=False)
    format_config = db.Column(db.JSON)

# Global variables
scheduler = BackgroundScheduler()
file_formats = {}

# Create directories
os.makedirs('input_files', exist_ok=True)
os.makedirs('output_files', exist_ok=True)
os.makedirs('error_files', exist_ok=True)

def load_format_config():
    """Load format configuration from XML"""
    global file_formats
    try:
        tree = etree.parse('sample_format.xml')
        for file_elem in tree.findall('file'):
            filename = file_elem.get('name')
            time_to_arrive = file_elem.get('timeToArrive')
            output_filename = file_elem.get('outfileName')
            
            # Parse time
            arrival_time = None
            if time_to_arrive:
                arrival_time = datetime.strptime(time_to_arrive, '%H:%M').time()
            
            # Parse fields
            fields = []
            for field_elem in file_elem.find('format').findall('field'):
                field_name = field_elem.get('name')
                max_length = field_elem.get('maxlength')
                field_def = {'name': field_name}
                if max_length:
                    field_def['maxlength'] = int(max_length)
                fields.append(field_def)
            
            file_formats[filename] = {
                'time_to_arrive': arrival_time,
                'output_filename': output_filename,
                'fields': fields
            }
        
        logger.info("Format configuration loaded successfully")
    except Exception as e:
        logger.error(f"Error loading format config: {e}")

def validate_file(file_path):
    """Validate file name, time, and format config"""
    filename = file_path.name
    
    # Check format config exists
    if filename not in file_formats:
        return False, "No format configuration found"
    
    # Check arrival time
    format_config = file_formats[filename]
    if format_config['time_to_arrive']:
        file_time = datetime.fromtimestamp(file_path.stat().st_ctime).time()
        if file_time > format_config['time_to_arrive']:
            return False, "File arrived after expected time"
    
    return True, "Valid"

def validate_line(line, fields):
    """Validate a single line against field definitions"""
    try:
        reader = csv.reader(io.StringIO(line))
        data = next(reader)
        
        if len(data) != len(fields):
            return False, f"Expected {len(fields)} fields, got {len(data)}"
        
        for i, (value, field) in enumerate(zip(data, fields)):
            if 'maxlength' in field and len(value) > field['maxlength']:
                return False, f"Field '{field['name']}' exceeds maximum length"
        
        return True, None
    except Exception as e:
        return False, f"Line parsing error: {str(e)}"

def process_file(file_path):
    """Process a single file"""
    filename = file_path.name
    format_config = file_formats[filename]
    
    valid_records = []
    error_records = []
    
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            
            is_valid, error_msg = validate_line(line, format_config['fields'])
            if is_valid:
                valid_records.append(line)
            else:
                error_records.append({
                    'line_number': line_num,
                    'data': line,
                    'error_message': error_msg
                })
    
    # Write output file
    output_path = Path('output_files') / format_config['output_filename']
    with open(output_path, 'a', encoding='utf-8') as f:
        for record in valid_records:
            f.write(record + '\n')
    
    # Write error file
    if error_records:
        error_path = Path('error_files') / f"{filename}_errors.txt"
        with open(error_path, 'w', encoding='utf-8') as f:
            f.write(f"Error records for file: {filename}\n")
            f.write(f"Generated at: {datetime.now().isoformat()}\n")
            f.write("=" * 50 + "\n\n")
            for error in error_records:
                f.write(f"Line {error['line_number']}: {error['error_message']}\n")
                f.write(f"Data: {error['data']}\n")
                f.write("-" * 30 + "\n")
    
    # Save to database
    status = 'success' if not error_records else 'partial' if valid_records else 'failed'
    processed_file = ProcessedFile(
        filename=filename,
        status=status,
        records_processed=len(valid_records),
        errors_count=len(error_records)
    )
    db.session.add(processed_file)
    
    # Save error records
    for error in error_records:
        error_record = ErrorRecord(
            filename=filename,
            line_number=error['line_number'],
            error_message=error['error_message'],
            data=error['data']
        )
        db.session.add(error_record)
    
    db.session.commit()
    logger.info(f"Processed {filename}: {len(valid_records)} valid, {len(error_records)} errors")

def monitor_files():
    """Monitor input directory for new files"""
    try:
        logger.info("Starting file monitoring cycle")
        
        for file_path in Path('input_files').iterdir():
            if file_path.is_file() and not file_path.name.startswith('.'):
                # Check if file is stable (not being written)
                size1 = file_path.stat().st_size
                time.sleep(2)
                size2 = file_path.stat().st_size
                
                if size1 == size2:  # File is stable
                    is_valid, reason = validate_file(file_path)
                    if is_valid:
                        process_file(file_path)
                        file_path.unlink()  # Delete processed file
                        logger.info(f"Successfully processed and deleted: {file_path.name}")
                    else:
                        file_path.unlink()  # Delete invalid file
                        logger.warning(f"Deleted invalid file {file_path.name}: {reason}")
        
        logger.info("File monitoring cycle completed")
    except Exception as e:
        logger.error(f"Error in file monitoring: {e}")

# API Routes
@app.route('/')
def index():
    return jsonify({
        'status': 'running',
        'service': 'Exhibit Monitor',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/status')
def get_status():
    return jsonify({
        'status': 'healthy',
        'monitoring_active': scheduler.running,
        'processed_files_count': ProcessedFile.query.count(),
        'error_records_count': ErrorRecord.query.count(),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/processed-files')
def get_processed_files():
    files = ProcessedFile.query.all()
    return jsonify({
        'files': [{
            'id': f.id,
            'filename': f.filename,
            'processed_at': f.processed_at.isoformat(),
            'status': f.status,
            'records_processed': f.records_processed,
            'errors_count': f.errors_count
        } for f in files]
    })

@app.route('/api/error-records')
def get_error_records():
    errors = ErrorRecord.query.all()
    return jsonify({
        'errors': [{
            'id': e.id,
            'filename': e.filename,
            'line_number': e.line_number,
            'error_message': e.error_message,
            'data': e.data,
            'created_at': e.created_at.isoformat()
        } for e in errors]
    })

def main():
    """Main entry point"""
    with app.app_context():
        # Create database tables
        db.create_all()
        logger.info("Database tables created")
        
        # Load format configuration
        load_format_config()
        
        # Start monitoring
        scheduler.start()
        scheduler.add_job(
            func=monitor_files,
            trigger=IntervalTrigger(seconds=30),
            id='file_monitor',
            name='File Monitor Job',
            replace_existing=True
        )
        
        logger.info("Exhibit Monitor application started")
        app.run(debug=True, host='0.0.0.0', port=5000)

if __name__ == '__main__':
    main()