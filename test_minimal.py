#!/usr/bin/env python3
"""
Test script for minimal exhibit monitor
"""

import os
import sys
import time
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from minimal_app import app, db, load_format_config, validate_file, process_file, file_formats

def test_minimal_app():
    """Test the minimal application"""
    print("Testing Minimal Exhibit Monitor...")
    
    with app.app_context():
        # Create database tables
        db.create_all()
        print("✓ Database tables created")
        
        # Load format configuration
        load_format_config()
        print("✓ Format configuration loaded")
        print(f"  Loaded formats for: {list(file_formats.keys())}")
        
        # Test file validation
        test_file = Path("sample_data/A.txt")
        if test_file.exists():
            is_valid, reason = validate_file(test_file)
            print(f"✓ File validation test: {is_valid} - {reason}")
        
        # Test file processing
        if test_file.exists():
            print("✓ Processing test file...")
            process_file(test_file)
            print("✓ File processing completed")
        
        # Check results
        from minimal_app import ProcessedFile, ErrorRecord
        processed_count = ProcessedFile.query.count()
        error_count = ErrorRecord.query.count()
        
        print(f"✓ Database results: {processed_count} processed files, {error_count} error records")
        
        # Check output files
        output_files = list(Path("output_files").glob("*.txt"))
        error_files = list(Path("error_files").glob("*.txt"))
        
        print(f"✓ Output files created: {len(output_files)}")
        print(f"✓ Error files created: {len(error_files)}")
        
        if output_files:
            print("  Sample output:")
            with open(output_files[0], 'r') as f:
                print(f"    {f.readline().strip()}")
        
        if error_files:
            print("  Sample error:")
            with open(error_files[0], 'r') as f:
                lines = f.readlines()
                if len(lines) > 4:
                    print(f"    {lines[4].strip()}")

if __name__ == "__main__":
    test_minimal_app()