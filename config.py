import os
from datetime import time

class Config:
    """Base configuration class"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # File processing settings
    INPUT_DIR = os.environ.get('INPUT_DIR', 'input_files')
    OUTPUT_DIR = os.environ.get('OUTPUT_DIR', 'output_files')
    ERROR_DIR = os.environ.get('ERROR_DIR', 'error_files')
    
    # Monitoring settings
    MONITOR_INTERVAL = int(os.environ.get('MONITOR_INTERVAL', 30))  # seconds
    
    # File validation settings
    MAX_FILE_SIZE = int(os.environ.get('MAX_FILE_SIZE', 1024 * 1024 * 1024))  # 1GB default
    STABLE_FILE_CHECK_INTERVAL = float(os.environ.get('STABLE_FILE_CHECK_INTERVAL', 2.0))  # seconds
    
    # Database settings
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///exhibit_monitor.db'
    
    # Logging settings
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', 'exhibit_monitor.log')

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or 'sqlite:///exhibit_monitor_dev.db'

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql://user:password@localhost/exhibit_monitor'

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}