import os
from datetime import timedelta

class Config:
    """Application configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # SocketIO Configuration
    SOCKETIO_ASYNC_MODE = 'eventlet'
    SOCKETIO_CORS_ALLOWED_ORIGINS = "*"
    
    # Simulation Configuration
    DEFAULT_SIMULATION_DT = 0.1
    MAX_SIMULATION_DURATION = 300  # seconds
    TUNING_DURATION = 150  # seconds
    PID_DURATION = 200  # seconds
    
    # System Limits
    MAX_CONTROL_OUTPUT = 100
    MIN_CONTROL_OUTPUT = -100
    
    # Auto-tuning Parameters
    DEFAULT_RELAY_AMPLITUDE = 10.0
    MIN_OSCILLATION_CYCLES = 3
    CONVERGENCE_THRESHOLD = 0.01
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL') or 'INFO'
    
class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    
class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
    # Only raise error if explicitly in production mode
    if os.environ.get('FLASK_ENV') == 'production' and not SECRET_KEY:
        raise ValueError("No SECRET_KEY set for production environment")

# Use development config by default
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}