#!/usr/bin/env python3
"""
Script to check database contents directly
"""

import sqlite3
import os
from datetime import datetime

def check_database():
    """Check database contents"""
    db_path = './instance/exhibit_monitor.db'
    
    if not os.path.exists(db_path):
        print(f"Database file not found at: {db_path}")
        return
    
    print(f"Database file found at: {db_path}")
    print(f"File size: {os.path.getsize(db_path)} bytes")
    print(f"Last modified: {datetime.fromtimestamp(os.path.getmtime(db_path))}")
    print("=" * 60)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"Tables in database: {[table[0] for table in tables]}")
        print("=" * 60)
        
        # Check processed_files table
        print("PROCESSED FILES TABLE:")
        cursor.execute("SELECT * FROM processed_files;")
        rows = cursor.fetchall()
        
        if rows:
            # Get column names
            cursor.execute("PRAGMA table_info(processed_files);")
            columns = [column[1] for column in cursor.fetchall()]
            print(f"Columns: {columns}")
            print("-" * 40)
            
            for row in rows:
                print(f"ID: {row[0]}")
                print(f"Filename: {row[1]}")
                print(f"Processed At: {row[2]}")
                print(f"Status: {row[3]}")
                print(f"Records Processed: {row[4]}")
                print(f"Errors Count: {row[5]}")
                print(f"File Size: {row[6]} bytes")
                print(f"Processing Time: {row[7]} seconds")
                print("-" * 40)
        else:
            print("No records found in processed_files table")
        
        print("\n" + "=" * 60)
        
        # Check error_records table
        print("ERROR RECORDS TABLE:")
        cursor.execute("SELECT * FROM error_records;")
        rows = cursor.fetchall()
        
        if rows:
            # Get column names
            cursor.execute("PRAGMA table_info(error_records);")
            columns = [column[1] for column in cursor.fetchall()]
            print(f"Columns: {columns}")
            print("-" * 40)
            
            for row in rows:
                print(f"ID: {row[0]}")
                print(f"Filename: {row[1]}")
                print(f"Line Number: {row[2]}")
                print(f"Error Message: {row[3]}")
                print(f"Data: {row[4]}")
                print(f"Created At: {row[5]}")
                print("-" * 40)
        else:
            print("No records found in error_records table")
        
        print("\n" + "=" * 60)
        
        # Check file_formats table
        print("FILE FORMATS TABLE:")
        cursor.execute("SELECT * FROM file_formats;")
        rows = cursor.fetchall()
        
        if rows:
            # Get column names
            cursor.execute("PRAGMA table_info(file_formats);")
            columns = [column[1] for column in cursor.fetchall()]
            print(f"Columns: {columns}")
            print("-" * 40)
            
            for row in rows:
                print(f"ID: {row[0]}")
                print(f"Filename Pattern: {row[1]}")
                print(f"Time To Arrive: {row[2]}")
                print(f"Output Filename: {row[3]}")
                print(f"Format Config: {row[4]}")
                print(f"Created At: {row[5]}")
                print(f"Updated At: {row[6]}")
                print("-" * 40)
        else:
            print("No records found in file_formats table")
        
        conn.close()
        
    except Exception as e:
        print(f"Error accessing database: {e}")

if __name__ == "__main__":
    check_database()