#!/usr/bin/env python3
"""
Test script for the Exhibit Monitor application
"""

import os
import sys
import time
import shutil
from pathlib import Path

def test_application():
    """Test the application functionality"""
    print("Testing Exhibit Monitor Application...")
    
    # Create test directories
    input_dir = Path("input_files")
    output_dir = Path("output_files")
    error_dir = Path("error_files")
    
    input_dir.mkdir(exist_ok=True)
    output_dir.mkdir(exist_ok=True)
    error_dir.mkdir(exist_ok=True)
    
    # Copy sample files to input directory
    sample_dir = Path("sample_data")
    if sample_dir.exists():
        for sample_file in sample_dir.glob("*.txt"):
            dest_file = input_dir / sample_file.name
            shutil.copy2(sample_file, dest_file)
            print(f"Copied {sample_file.name} to input directory")
    
    print("Sample files copied to input directory")
    print("You can now run the application with: python app.py")
    print("Or use the run script: python run.py")

if __name__ == "__main__":
    test_application()