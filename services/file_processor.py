import os
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple
import csv
import io

# Import models locally to avoid circular imports

logger = logging.getLogger(__name__)

class FileProcessorService:
    """Service for processing validated files"""
    
    def __init__(self):
        self.output_dir = os.environ.get('OUTPUT_DIR', 'output_files')
        self.error_dir = os.environ.get('ERROR_DIR', 'error_files')
        
        # Create output directories if they don't exist
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.error_dir, exist_ok=True)
    
    def process_file(self, file_path: Path):
        """Process a validated file"""
        start_time = datetime.now()
        logger.info(f"Starting to process file: {file_path.name}")
        
        try:
            # Get format configuration
            format_config = self._get_format_config(file_path.name)
            if not format_config:
                raise ValueError(f"No format configuration found for {file_path.name}")
            
            # Process file line by line
            valid_records = []
            error_records = []
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                for line_num, line in enumerate(file, 1):
                    line = line.strip()
                    if not line:  # Skip empty lines
                        continue
                    
                    # Validate and process line
                    validation_result = self._validate_line(line, format_config.format_config, line_num)
                    
                    if validation_result['valid']:
                        valid_records.append(line)
                    else:
                        error_records.append({
                            'line_number': line_num,
                            'data': line,
                            'error_message': validation_result['error']
                        })
            
            # Write valid records to output file
            output_file = self._write_output_file(file_path.name, valid_records, format_config.output_filename)
            
            # Write error records to error file and database
            error_file = self._write_error_file(file_path.name, error_records)
            
            # Record processing results in database
            processing_time = (datetime.now() - start_time).total_seconds()
            self._record_processing_result(
                file_path, 
                len(valid_records), 
                len(error_records), 
                processing_time
            )
            
            # Save error records to database
            self._save_error_records(file_path.name, error_records)
            
            logger.info(f"Successfully processed {file_path.name}: {len(valid_records)} valid, {len(error_records)} errors")
            
        except Exception as e:
            logger.error(f"Error processing file {file_path.name}: {str(e)}")
            raise
    
    def _get_format_config(self, filename: str):
        """Get format configuration for file"""
        try:
            from models import FileFormat
            config = FileFormat.query.filter_by(filename_pattern=filename).first()
            return config
        except Exception as e:
            logger.error(f"Error getting format config for {filename}: {str(e)}")
            return None
    
    def _validate_line(self, line: str, format_config: Dict[str, Any], line_number: int) -> Dict[str, Any]:
        """Validate a single line against format configuration"""
        try:
            # Parse CSV line
            reader = csv.reader(io.StringIO(line))
            fields = next(reader)
            
            # Get field definitions from format config
            field_definitions = format_config.get('fields', [])
            
            if len(fields) != len(field_definitions):
                return {
                    'valid': False,
                    'error': f'Expected {len(field_definitions)} fields, got {len(fields)}'
                }
            
            # Validate each field
            for i, (field, definition) in enumerate(zip(fields, field_definitions)):
                field_name = definition.get('name', f'field_{i}')
                max_length = definition.get('maxlength')
                
                if max_length and len(field) > max_length:
                    return {
                        'valid': False,
                        'error': f'Field "{field_name}" exceeds maximum length of {max_length}'
                    }
                
                # Additional field validation can be added here
                # e.g., data type validation, format validation, etc.
            
            return {'valid': True, 'error': None}
            
        except Exception as e:
            return {
                'valid': False,
                'error': f'Line parsing error: {str(e)}'
            }
    
    def _write_output_file(self, input_filename: str, valid_records: List[str], output_filename: str) -> str:
        """Write valid records to output file"""
        try:
            output_path = Path(self.output_dir) / output_filename
            
            # Append to output file
            with open(output_path, 'a', encoding='utf-8') as f:
                for record in valid_records:
                    f.write(record + '\n')
            
            logger.info(f"Wrote {len(valid_records)} records to {output_filename}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Error writing output file: {str(e)}")
            raise
    
    def _write_error_file(self, input_filename: str, error_records: List[Dict[str, Any]]) -> str:
        """Write error records to error file"""
        try:
            if not error_records:
                return None
            
            error_filename = f"{input_filename}_errors.txt"
            error_path = Path(self.error_dir) / error_filename
            
            with open(error_path, 'w', encoding='utf-8') as f:
                f.write(f"Error records for file: {input_filename}\n")
                f.write(f"Generated at: {datetime.now().isoformat()}\n")
                f.write("=" * 50 + "\n\n")
                
                for error in error_records:
                    f.write(f"Line {error['line_number']}: {error['error_message']}\n")
                    f.write(f"Data: {error['data']}\n")
                    f.write("-" * 30 + "\n")
            
            logger.info(f"Wrote {len(error_records)} error records to {error_filename}")
            return str(error_path)
            
        except Exception as e:
            logger.error(f"Error writing error file: {str(e)}")
            raise
    
    def _record_processing_result(self, file_path: Path, valid_count: int, error_count: int, processing_time: float):
        """Record processing result in database"""
        try:
            from models import ProcessedFile, db
            file_size = file_path.stat().st_size
            status = 'success' if error_count == 0 else 'partial' if valid_count > 0 else 'failed'
            
            processed_file = ProcessedFile(
                filename=file_path.name,
                status=status,
                records_processed=valid_count,
                errors_count=error_count,
                file_size=file_size,
                processing_time=processing_time
            )
            
            db.session.add(processed_file)
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Error recording processing result: {str(e)}")
            db.session.rollback()
    
    def _save_error_records(self, filename: str, error_records: List[Dict[str, Any]]):
        """Save error records to database"""
        try:
            from models import ErrorRecord, db
            for error in error_records:
                error_record = ErrorRecord(
                    filename=filename,
                    line_number=error['line_number'],
                    error_message=error['error_message'],
                    data=error['data']
                )
                db.session.add(error_record)
            
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Error saving error records: {str(e)}")
            db.session.rollback()
    
    def load_format_from_xml(self, xml_file_path: str):
        """Load file format configuration from XML file"""
        try:
            from lxml import etree
            
            tree = etree.parse(xml_file_path)
            root = tree.getroot()
            
            for file_elem in root.findall('file'):
                filename = file_elem.get('name')
                time_to_arrive = file_elem.get('timeToArrive')
                output_filename = file_elem.get('outfileName')
                
                # Parse time if provided
                arrival_time = None
                if time_to_arrive:
                    try:
                        arrival_time = datetime.strptime(time_to_arrive, '%H:%M').time()
                    except ValueError:
                        logger.warning(f"Invalid time format: {time_to_arrive}")
                
                # Parse field definitions
                fields = []
                format_elem = file_elem.find('format')
                if format_elem is not None:
                    for field_elem in format_elem.findall('field'):
                        field_name = field_elem.get('name')
                        max_length = field_elem.get('maxlength')
                        
                        if field_name:
                            field_def = {'name': field_name}
                            if max_length:
                                field_def['maxlength'] = int(max_length)
                            fields.append(field_def)
                
                # Save or update format configuration
                from models import FileFormat, db
                existing_config = FileFormat.query.filter_by(filename_pattern=filename).first()
                if existing_config:
                    existing_config.time_to_arrive = arrival_time
                    existing_config.output_filename = output_filename
                    existing_config.format_config = {'fields': fields}
                    existing_config.updated_at = datetime.utcnow()
                else:
                    new_config = FileFormat(
                        filename_pattern=filename,
                        time_to_arrive=arrival_time,
                        output_filename=output_filename,
                        format_config={'fields': fields}
                    )
                    db.session.add(new_config)
            
            db.session.commit()
            logger.info(f"Successfully loaded format configuration from {xml_file_path}")
            
        except Exception as e:
            logger.error(f"Error loading format from XML: {str(e)}")
            db.session.rollback()
            raise