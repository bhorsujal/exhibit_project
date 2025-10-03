#!/usr/bin/env python3
"""
Test script to manually test file processing
"""

import os
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, create_tables, initialize_services, monitor_files_with_context

def test_file_processing():
    """Test file processing manually"""
    print("Testing file processing...")
    
    # Create database tables
    create_tables()
    
    # Initialize services
    file_monitor, file_processor = initialize_services()
    
    # Load format configuration
    format_xml_path = 'sample_format.xml'
    if os.path.exists(format_xml_path):
        with app.app_context():
            file_processor.load_format_from_xml(format_xml_path)
            print("Loaded format configuration from XML")
    
    # Test file processing
    with app.app_context():
        print("Running file monitoring cycle...")
        monitor_files_with_context()
    
    # Check results
    print("\nChecking results...")
    print("Input files:")
    for file in Path("input_files").glob("*.txt"):
        print(f"  {file.name}")
    
    print("Output files:")
    for file in Path("output_files").glob("*.txt"):
        print(f"  {file.name}")
    
    print("Error files:")
    for file in Path("error_files").glob("*.txt"):
        print(f"  {file.name}")

if __name__ == "__main__":
    test_file_processing()