import os
import time
import logging
from datetime import datetime, time as dt_time
from pathlib import Path
import hashlib
from typing import List, Dict, Any
from lxml import etree

# Import models locally to avoid circular imports

logger = logging.getLogger(__name__)

class FileMonitorService:
    """Service for monitoring and validating incoming files"""
    
    def __init__(self):
        self.input_dir = os.environ.get('INPUT_DIR', 'input_files')
        self.processed_hashes = set()
        self.file_processor = None  # Will be initialized when needed
        
        # Create input directory if it doesn't exist
        os.makedirs(self.input_dir, exist_ok=True)
        
        # Load existing file hashes to prevent reprocessing
        self._load_processed_hashes()
    
    def monitor_files(self):
        """Monitor input directory for new files every 30 seconds"""
        try:
            logger.info("Starting file monitoring cycle")
            
            # Get list of files in input directory
            files = self._get_new_files()
            
            for file_path in files:
                try:
                    self._process_file(file_path)
                except Exception as e:
                    logger.error(f"Error processing file {file_path}: {str(e)}")
                    # Delete file if processing fails
                    self._delete_file(file_path)
            
            logger.info(f"File monitoring cycle completed. Processed {len(files)} files")
            
        except Exception as e:
            logger.error(f"Error in file monitoring: {str(e)}")
    
    def _get_new_files(self) -> List[Path]:
        """Get list of new files in input directory"""
        files = []
        
        try:
            for file_path in Path(self.input_dir).iterdir():
                if file_path.is_file() and not file_path.name.startswith('.'):
                    # Check if file is not currently being written (size stable)
                    if self._is_file_stable(file_path):
                        files.append(file_path)
        except Exception as e:
            logger.error(f"Error getting files from directory: {str(e)}")
        
        return files
    
    def _is_file_stable(self, file_path: Path, check_interval: float = 2.0) -> bool:
        """Check if file size is stable (not being written)"""
        try:
            size1 = file_path.stat().st_size
            time.sleep(check_interval)
            size2 = file_path.stat().st_size
            return size1 == size2
        except Exception:
            return False
    
    def _process_file(self, file_path: Path):
        """Process a single file through validation and processing"""
        logger.info(f"Processing file: {file_path.name}")
        
        # Step 1: Validate file
        validation_result = self._validate_file(file_path)
        
        if not validation_result['valid']:
            logger.warning(f"File validation failed for {file_path.name}: {validation_result['reason']}")
            self._delete_file(file_path)
            return
        
        # Step 2: Check for duplicates
        if self._is_duplicate(file_path):
            logger.warning(f"Duplicate file detected: {file_path.name}")
            self._delete_file(file_path)
            return
        
        # Step 3: Process the file
        try:
            if self.file_processor is None:
                from .file_processor import FileProcessorService
                self.file_processor = FileProcessorService()
            
            self.file_processor.process_file(file_path)
            self._record_processed_file(file_path)
            logger.info(f"Successfully processed file: {file_path.name}")
        except Exception as e:
            logger.error(f"Error processing file {file_path.name}: {str(e)}")
            self._delete_file(file_path)
    
    def _validate_file(self, file_path: Path) -> Dict[str, Any]:
        """Validate file name, time of arrival, and other criteria"""
        try:
            # Check valid name (basic validation)
            if not self._is_valid_filename(file_path.name):
                return {'valid': False, 'reason': 'Invalid filename'}
            
            # Check time of arrival
            if not self._check_arrival_time(file_path):
                return {'valid': False, 'reason': 'File arrived after expected time'}
            
            # Check if file format is configured
            if not self._has_format_config(file_path.name):
                return {'valid': False, 'reason': 'No format configuration found'}
            
            return {'valid': True, 'reason': 'All validations passed'}
            
        except Exception as e:
            logger.error(f"Error validating file {file_path.name}: {str(e)}")
            return {'valid': False, 'reason': f'Validation error: {str(e)}'}
    
    def _is_valid_filename(self, filename: str) -> bool:
        """Check if filename is valid"""
        # Basic validation - can be extended
        if not filename or len(filename) > 255:
            return False
        
        # Check for invalid characters
        invalid_chars = ['<', '>', ':', '"', '|', '?', '*']
        if any(char in filename for char in invalid_chars):
            return False
        
        return True
    
    def _check_arrival_time(self, file_path: Path) -> bool:
        """Check if file arrived before expected time"""
        try:
            # Get file format configuration
            format_config = self._get_format_config(file_path.name)
            if not format_config:
                return True  # If no time specified, allow any time
            
            expected_time = format_config.time_to_arrive
            if not expected_time:
                return True  # If no time specified, allow any time
            
            # Get file creation time
            file_time = datetime.fromtimestamp(file_path.stat().st_ctime).time()
            
            # Check if file arrived before expected time
            return file_time <= expected_time
            
        except Exception as e:
            logger.error(f"Error checking arrival time for {file_path.name}: {str(e)}")
            return False
    
    def _has_format_config(self, filename: str) -> bool:
        """Check if format configuration exists for file"""
        return self._get_format_config(filename) is not None
    
    def _get_format_config(self, filename: str):
        """Get format configuration for file"""
        try:
            from models import FileFormat
            # Try to find exact match first
            config = FileFormat.query.filter_by(filename_pattern=filename).first()
            if config:
                return config
            
            # Try pattern matching (can be extended for wildcards)
            # For now, just return None if no exact match
            return None
            
        except Exception as e:
            logger.error(f"Error getting format config for {filename}: {str(e)}")
            return None
    
    def _is_duplicate(self, file_path: Path) -> bool:
        """Check if file is a duplicate using hash"""
        try:
            file_hash = self._calculate_file_hash(file_path)
            
            if file_hash in self.processed_hashes:
                return True
            
            # Check database for duplicates
            from models import ProcessedFile
            existing_file = ProcessedFile.query.filter_by(filename=file_path.name).first()
            if existing_file:
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking duplicate for {file_path.name}: {str(e)}")
            return False
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file"""
        hash_sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            logger.error(f"Error calculating hash for {file_path.name}: {str(e)}")
            return ""
    
    def _delete_file(self, file_path: Path):
        """Delete file from filesystem"""
        try:
            file_path.unlink()
            logger.info(f"Deleted file: {file_path.name}")
        except Exception as e:
            logger.error(f"Error deleting file {file_path.name}: {str(e)}")
    
    def _record_processed_file(self, file_path: Path):
        """Record processed file hash to prevent reprocessing"""
        try:
            file_hash = self._calculate_file_hash(file_path)
            self.processed_hashes.add(file_hash)
        except Exception as e:
            logger.error(f"Error recording processed file {file_path.name}: {str(e)}")
    
    def _load_processed_hashes(self):
        """Load processed file hashes from database"""
        try:
            # This could be extended to load from database
            # For now, just initialize empty set
            self.processed_hashes = set()
        except Exception as e:
            logger.error(f"Error loading processed hashes: {str(e)}")
            self.processed_hashes = set()