import os
from datetime import timedelta

class Config:
    """Application configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # SocketIO Configuration
    SOCKETIO_ASYNC_MODE = 'threading'  # Fixed: was 'eventlet', now matches app.py
    SOCKETIO_CORS_ALLOWED_ORIGINS = "*"
    SOCKETIO_PING_TIMEOUT = 60
    SOCKETIO_PING_INTERVAL = 25
    
    # Simulation Configuration
    DEFAULT_SIMULATION_DT = 0.1
    MAX_SIMULATION_DURATION = 300  # seconds
    TUNING_DURATION = 150  # seconds
    PID_DURATION = 200  # seconds
    
    # Rate limiting for real-time updates
    UPDATE_RATE_LIMIT = 0.02  # minimum time between updates (50Hz max)
    MAX_DATA_POINTS = 2000    # maximum data points to keep in memory
    
    # System Limits
    MAX_CONTROL_OUTPUT = 100
    MIN_CONTROL_OUTPUT = -100
    
    # Auto-tuning Parameters
    DEFAULT_RELAY_AMPLITUDE = 10.0
    MIN_OSCILLATION_CYCLES = 3
    CONVERGENCE_THRESHOLD = 0.01
    
    # New Advanced Features Configuration
    ENABLE_FREQUENCY_ANALYSIS = True
    ENABLE_ROOT_LOCUS = True
    ENABLE_ROBUSTNESS_ANALYSIS = True
    ENABLE_ADAPTIVE_CONTROL = True
    
    # Performance Monitoring
    ENABLE_PERFORMANCE_MONITORING = True
    PERFORMANCE_METRICS_INTERVAL = 5.0  # seconds
    
    # Data Export Configuration
    EXPORT_FORMATS = ['csv', 'json', 'matlab', 'excel']
    MAX_EXPORT_SIZE = 100000  # maximum number of data points to export
    
    # Industrial Presets
    INDUSTRIAL_PRESETS = {
        'temperature_control': {'K': 0.8, 'T': 120.0, 'theta': 15.0, 'description': 'Typical temperature control system'},
        'flow_control': {'K': 1.5, 'T': 8.0, 'theta': 2.0, 'description': 'Flow control with fast dynamics'},
        'level_control': {'K': 2.0, 'T': 45.0, 'theta': 5.0, 'description': 'Level control (integrating process)'},
        'pressure_control': {'K': 3.0, 'T': 5.0, 'theta': 1.0, 'description': 'Pressure control system'},
        'motor_speed': {'K': 1.2, 'T': 3.0, 'theta': 0.5, 'description': 'Motor speed control'},
        'ph_control': {'K': 0.5, 'T': 25.0, 'theta': 8.0, 'description': 'pH control system'},
        'fast_system': {'K': 2.0, 'T': 5.0, 'theta': 1.0, 'description': 'Fast responding system'},
        'slow_system': {'K': 1.5, 'T': 20.0, 'theta': 3.0, 'description': 'Slow responding system'},
        'oscillatory': {'K': 3.0, 'T': 8.0, 'theta': 2.5, 'description': 'Oscillatory system'},
        'sluggish': {'K': 0.8, 'T': 30.0, 'theta': 5.0, 'description': 'Sluggish system'},
    }
    
    # Advanced Controller Types
    CONTROLLER_TYPES = {
        'pid': 'Standard PID Controller',
        'pi': 'PI Controller',
        'pd': 'PD Controller',
        'fuzzy_pid': 'Fuzzy PID Controller',
        'adaptive_pid': 'Adaptive PID Controller',
        'mpc': 'Model Predictive Controller',
        'lqr': 'Linear Quadratic Regulator',
        'sliding_mode': 'Sliding Mode Controller'
    }
    
    # Tuning Methods
    TUNING_METHODS = {
        'ziegler_nichols': 'Ziegler-Nichols',
        'tyreus_luyben': 'Tyreus-Luyben',
        'cohen_coon': 'Cohen-Coon',
        'imc': 'Internal Model Control',
        'lambda_tuning': 'Lambda Tuning',
        'gain_phase_margin': 'Gain/Phase Margin',
        'genetic_algorithm': 'Genetic Algorithm',
        'particle_swarm': 'Particle Swarm Optimization'
    }
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL') or 'INFO'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Security
    ENABLE_CSRF_PROTECTION = True
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    
class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = False  # Fixed: was True, now False for security
    TESTING = False
    
class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
    # Enhanced security for production
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    PERMANENT_SESSION_LIFETIME = timedelta(hours=1)
    
    # Only raise error if explicitly in production mode
    if os.environ.get('FLASK_ENV') == 'production' and not SECRET_KEY:
        raise ValueError("No SECRET_KEY set for production environment")

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DEBUG = False
    SECRET_KEY = 'test-secret-key'
    
    # Faster simulation for testing
    DEFAULT_SIMULATION_DT = 0.01
    TUNING_DURATION = 10
    PID_DURATION = 15

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}