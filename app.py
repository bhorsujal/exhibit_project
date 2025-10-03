from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import os
from dotenv import load_dotenv
import logging
from datetime import datetime

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///exhibit_monitor.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
from models import db
db.init_app(app)
migrate = Migrate(app, db)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('exhibit_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize scheduler
scheduler = BackgroundScheduler()

# Global variables for services (will be initialized later)
file_monitor = None
file_processor = None

@app.route('/')
def index():
    """Health check endpoint"""
    return jsonify({
        'status': 'running',
        'service': 'Exhibit Monitor',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/status')
def get_status():
    """Get application status"""
    from models import ProcessedFile, ErrorRecord
    return jsonify({
        'status': 'healthy',
        'monitoring_active': scheduler.running,
        'processed_files_count': ProcessedFile.query.count(),
        'error_records_count': ErrorRecord.query.count(),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/processed-files')
def get_processed_files():
    """Get list of processed files"""
    from models import ProcessedFile
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    files = ProcessedFile.query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'files': [{
            'id': file.id,
            'filename': file.filename,
            'processed_at': file.processed_at.isoformat(),
            'status': file.status,
            'records_processed': file.records_processed,
            'errors_count': file.errors_count
        } for file in files.items],
        'total': files.total,
        'pages': files.pages,
        'current_page': page
    })

@app.route('/api/error-records')
def get_error_records():
    """Get list of error records"""
    from models import ErrorRecord
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    errors = ErrorRecord.query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'errors': [{
            'id': error.id,
            'filename': error.filename,
            'line_number': error.line_number,
            'error_message': error.error_message,
            'data': error.data,
            'created_at': error.created_at.isoformat()
        } for error in errors.items],
        'total': errors.total,
        'pages': errors.pages,
        'current_page': page
    })

@app.route('/api/start-monitoring', methods=['POST'])
def start_monitoring():
    """Start file monitoring"""
    try:
        global file_monitor
        if file_monitor is None:
            from services.file_monitor import FileMonitorService
            file_monitor = FileMonitorService()
        
        if not scheduler.running:
            scheduler.start()
            scheduler.add_job(
                func=monitor_files_with_context,
                trigger=IntervalTrigger(seconds=30),
                id='file_monitor',
                name='File Monitor Job',
                replace_existing=True
            )
            logger.info("File monitoring started")
            return jsonify({'message': 'File monitoring started successfully'})
        else:
            return jsonify({'message': 'File monitoring is already running'})
    except Exception as e:
        logger.error(f"Error starting monitoring: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/stop-monitoring', methods=['POST'])
def stop_monitoring():
    """Stop file monitoring"""
    try:
        if scheduler.running:
            scheduler.shutdown()
            logger.info("File monitoring stopped")
            return jsonify({'message': 'File monitoring stopped successfully'})
        else:
            return jsonify({'message': 'File monitoring is not running'})
    except Exception as e:
        logger.error(f"Error stopping monitoring: {str(e)}")
        return jsonify({'error': str(e)}), 500

def create_tables():
    """Create database tables"""
    with app.app_context():
        db.create_all()
        logger.info("Database tables created")

def initialize_services():
    """Initialize services"""
    global file_monitor, file_processor
    from services.file_monitor import FileMonitorService
    from services.file_processor import FileProcessorService
    
    file_monitor = FileMonitorService()
    file_processor = FileProcessorService()
    
    return file_monitor, file_processor

def monitor_files_with_context():
    """Wrapper function to run file monitoring within application context"""
    with app.app_context():
        if file_monitor:
            file_monitor.monitor_files()

if __name__ == '__main__':
    # Create database tables
    create_tables()
    
    # Initialize services
    file_monitor, file_processor = initialize_services()
    
    # Start monitoring automatically
    scheduler.start()
    scheduler.add_job(
        func=monitor_files_with_context,
        trigger=IntervalTrigger(seconds=30),
        id='file_monitor',
        name='File Monitor Job',
        replace_existing=True
    )
    
    logger.info("Exhibit Monitor application started")
    app.run(debug=True, host='0.0.0.0', port=5000)