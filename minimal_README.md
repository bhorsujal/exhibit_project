# Minimal Exhibit Monitor

A simplified Flask-based text file processing system that monitors, validates, and processes files according to XML format specifications.

## Features

- **File Monitoring**: Monitors `input_files/` directory every 30 seconds
- **File Validation**: Validates filename, arrival time, and format configuration
- **Format Processing**: Processes files according to XML-defined field specifications
- **Error Handling**: Captures validation errors and writes to error files
- **Database Tracking**: Stores processing results in SQLite database
- **REST API**: Provides status and data retrieval endpoints

## Quick Start

1. **Install dependencies**:
   ```bash
   pip install -r minimal_requirements.txt
   ```

2. **Run the application**:
   ```bash
   python minimal_app.py
   ```

3. **Test with sample files**:
   ```bash
   cp sample_data/*.txt input_files/
   ```

## API Endpoints

- `GET /` - Health check
- `GET /api/status` - Application status and statistics
- `GET /api/processed-files` - List of processed files
- `GET /api/error-records` - List of error records

## File Processing Workflow

1. **File Detection**: Scans `input_files/` every 30 seconds
2. **Validation**: Checks filename, arrival time, and format configuration
3. **Processing**: Validates each line against field definitions
4. **Output**: Valid records → `output_files/`, errors → `error_files/`
5. **Database**: Records processing results and errors
6. **Cleanup**: Deletes processed files from input directory

## Configuration

The `sample_format.xml` file defines file formats:

```xml
<file name="A.txt" timeToArrive="23:59" outfileName="a.out.txt">
    <format>
        <field name="customername" maxlength="80"/>
        <field name="address" maxlength="120"/>
        <field name="ordervalue" maxlength="10"/>
    </format>
</file>
```

## Key Simplifications

- **Single File**: All code in one `minimal_app.py` file (~200 lines)
- **Minimal Dependencies**: Only 4 required packages
- **Simplified Structure**: No separate service classes or complex imports
- **Direct Processing**: Inline file processing without abstraction layers
- **Basic Error Handling**: Simple try-catch blocks
- **Essential Features Only**: Core functionality without extras

## File Structure

```
zensar/
├── minimal_app.py              # Complete application (single file)
├── minimal_requirements.txt    # Minimal dependencies
├── sample_format.xml           # Format configuration
├── sample_data/                # Sample input files
├── input_files/                # Directory for incoming files
├── output_files/               # Directory for processed output
├── error_files/                # Directory for error logs
└── exhibit_monitor.db          # SQLite database
```

This minimal version maintains all core functionality while being much simpler to understand and maintain.