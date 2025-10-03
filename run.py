#!/usr/bin/env python3
"""
Entry point for the Exhibit Monitor application
"""

import os
import sys
from app import app, create_tables, scheduler, initialize_services, logger, monitor_files_with_context
from apscheduler.triggers.interval import IntervalTrigger

def main():
    """Main entry point"""
    try:
        # Create database tables
        create_tables()
        
        # Load format configuration from XML
        format_xml_path = 'sample_format.xml'
        if os.path.exists(format_xml_path):
            with app.app_context():
                from services.file_processor import FileProcessorService
                processor = FileProcessorService()
                processor.load_format_from_xml(format_xml_path)
                logger.info("Loaded format configuration from XML")
        
        # Start monitoring
        scheduler.start()
        scheduler.add_job(
            func=monitor_files_with_context,
            trigger=IntervalTrigger(seconds=30),
            id='file_monitor',
            name='File Monitor Job',
            replace_existing=True
        )
        
        logger.info("Exhibit Monitor application started successfully")
        logger.info("File monitoring is active")
        logger.info("Flask server starting on http://localhost:5000")
        
        # Run Flask application
        app.run(debug=True, host='0.0.0.0', port=5000)
        
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
        scheduler.shutdown()
    except Exception as e:
        logger.error(f"Error starting application: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()