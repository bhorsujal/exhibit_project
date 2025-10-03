# Exhibit Monitor - Text File Processing System

A Flask-based backend application for monitoring, validating, and processing text files according to configurable format specifications.

## Features

- **File Monitoring**: Automatically monitors input directory every 30 seconds for new files
- **File Validation**: Validates file names, arrival times, and checks for duplicates
- **Format-based Processing**: Processes files according to XML-defined format specifications
- **Error Handling**: Captures and logs validation errors with detailed information
- **Database Integration**: Tracks processed files and error records
- **REST API**: Provides endpoints for monitoring status and retrieving processing results

## Project Structure

```
zensar/
├── app.py                 # Main Flask application
├── models.py              # Database models
├── config.py              # Configuration settings
├── requirements.txt       # Python dependencies
├── sample_format.xml      # Sample format configuration
├── services/
│   ├── __init__.py
│   ├── file_monitor.py    # File monitoring service
│   └── file_processor.py  # File processing service
├── sample_data/           # Sample input files
│   ├── A.txt
│   ├── B.txt
│   └── C.txt
├── input_files/           # Directory for incoming files (created automatically)
├── output_files/          # Directory for processed output (created automatically)
└── error_files/           # Directory for error logs (created automatically)
```

## Installation

1. **Clone or download the project**
2. **Install dependencies**:
   
   **For SQLite (default, recommended for development):**
   ```bash
   pip install -r requirements.txt
   ```
   
   **For PostgreSQL (production):**
   ```bash
   # First install PostgreSQL development libraries
   sudo apt-get install libpq-dev  # Ubuntu/Debian
   # or
   sudo yum install postgresql-devel  # CentOS/RHEL
   
   # Then install Python dependencies
   pip install -r requirements-postgresql.txt
   ```

3. **Set up environment variables** (optional):
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

4. **Initialize the database**:
   ```bash
   python app.py
   ```

## Configuration

### Environment Variables

- `INPUT_DIR`: Directory to monitor for incoming files (default: `input_files`)
- `OUTPUT_DIR`: Directory for processed output files (default: `output_files`)
- `ERROR_DIR`: Directory for error log files (default: `error_files`)
- `MONITOR_INTERVAL`: Monitoring interval in seconds (default: `30`)
- `DATABASE_URL`: Database connection string (default: SQLite)

### Format Configuration

The application uses XML files to define file formats. See `sample_format.xml` for examples:

```xml
<file name="A.txt" timeToArrive="12:30" outfileName="a.out.txt">
    <format>
        <field name="customername" maxlength="80"/>
        <field name="address" maxlength="120"/>
        <field name="ordervalue" maxlength="10"/>
    </format>
</file>
```

## Usage

### Starting the Application

```bash
python app.py
```

The application will:
1. Create necessary directories
2. Initialize the database
3. Start file monitoring
4. Run the Flask server on `http://localhost:5000`

### API Endpoints

- `GET /` - Health check
- `GET /api/status` - Application status and statistics
- `GET /api/processed-files` - List of processed files
- `GET /api/error-records` - List of error records
- `POST /api/start-monitoring` - Start file monitoring
- `POST /api/stop-monitoring` - Stop file monitoring

### File Processing Workflow

1. **File Detection**: Monitor scans input directory every 30 seconds
2. **Validation**: Each file undergoes three checks:
   - Valid filename
   - Arrival time (before specified time)
   - Duplicate check
3. **Processing**: Valid files are processed line by line
4. **Output**: Valid records go to output files, errors to error files
5. **Database**: Processing results are recorded in the database

## Sample Data

The `sample_data/` directory contains example files that match the format specifications in `sample_format.xml`:

- `A.txt`: Customer data (name, address, order value)
- `B.txt`: Product data (ID, name, price, quantity)
- `C.txt`: Customer contact data (ID, email, phone, city, country)

## Error Handling

- Files failing validation are automatically deleted
- Processing errors are logged to both files and database
- Error records include filename, line number, error message, and data

## Database Models

- **ProcessedFile**: Tracks processed files with status and statistics
- **ErrorRecord**: Stores detailed error information
- **FileFormat**: Stores format configuration for different file types

## Development

### Adding New File Formats

1. Update `sample_format.xml` with new file specifications
2. Restart the application to load new configurations
3. Place sample files in the input directory for testing

### Extending Validation

The validation logic can be extended in `services/file_processor.py` to include:
- Data type validation
- Format pattern matching
- Custom business rules

## Production Deployment

For production deployment:

1. Set `FLASK_ENV=production`
2. Use a production database (PostgreSQL recommended)
3. Configure proper logging
4. Set up process monitoring
5. Use a production WSGI server (e.g., Gunicorn)

## License

This project is created for demonstration purposes.