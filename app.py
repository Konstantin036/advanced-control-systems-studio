from flask import Flask, render_template, request, jsonify, send_file
from flask_socketio import SocketIO, emit
import logging
import os
import json
import numpy as np
from datetime import datetime
from config import Config
from models.system_model import SystemModel
from models.pid_controller import PIDController
from services.auto_tuner import AutoTuner
from services.simulation_service import SimulationService

# Configure logging with better formatting
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Enhanced security headers
@app.after_request
def set_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

# Initialize SocketIO with enhanced configuration
socketio = SocketIO(
    app, 
    async_mode='threading',
    cors_allowed_origins="*",
    logger=True,
    engineio_logger=True,
    ping_timeout=app.config['SOCKETIO_PING_TIMEOUT'],
    ping_interval=app.config['SOCKETIO_PING_INTERVAL']
)

# Initialize services
simulation_service = SimulationService(socketio)

@app.route('/')
def index():
    """Main page route."""
    return render_template('index.html')

@app.route('/api/health')
def health_check():
    """Enhanced health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'PID Controller Simulator',
        'version': '2.1',
        'timestamp': datetime.now().isoformat(),
        'features': {
            'frequency_analysis': app.config['ENABLE_FREQUENCY_ANALYSIS'],
            'root_locus': app.config['ENABLE_ROOT_LOCUS'],
            'robustness_analysis': app.config['ENABLE_ROBUSTNESS_ANALYSIS'],
            'adaptive_control': app.config['ENABLE_ADAPTIVE_CONTROL']
        }
    })

@app.route('/api/presets')
def get_presets():
    """Get all available system presets."""
    return jsonify(app.config['INDUSTRIAL_PRESETS'])

@app.route('/api/controller-types')
def get_controller_types():
    """Get available controller types."""
    return jsonify(app.config['CONTROLLER_TYPES'])

@app.route('/api/tuning-methods')
def get_tuning_methods():
    """Get available tuning methods."""
    return jsonify(app.config['TUNING_METHODS'])

@app.route('/api/export/data', methods=['POST'])
def export_data():
    """Export simulation data in various formats."""
    try:
        data = request.json
        format_type = data.get('format', 'csv')
        
        if format_type not in app.config['EXPORT_FORMATS']:
            return jsonify({'error': 'Unsupported format'}), 400
        
        # Implementation would go here for different formats
        # For now, return JSON format
        return jsonify(data)
    
    except Exception as e:
        logger.error(f"Export error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/analysis/frequency', methods=['POST'])
def frequency_analysis():
    """Perform frequency domain analysis."""
    try:
        if not app.config['ENABLE_FREQUENCY_ANALYSIS']:
            return jsonify({'error': 'Frequency analysis disabled'}), 403
        
        data = request.json
        # Implementation for frequency analysis would go here
        return jsonify({
            'bode_plot': [],
            'nyquist_plot': [],
            'margins': {'gain_margin': 0, 'phase_margin': 0}
        })
    
    except Exception as e:
        logger.error(f"Frequency analysis error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/analysis/root-locus', methods=['POST'])
def root_locus_analysis():
    """Perform root locus analysis."""
    try:
        if not app.config['ENABLE_ROOT_LOCUS']:
            return jsonify({'error': 'Root locus analysis disabled'}), 403
        
        data = request.json
        # Implementation for root locus analysis would go here
        return jsonify({
            'root_locus_plot': [],
            'stability_margins': {}
        })
    
    except Exception as e:
        logger.error(f"Root locus analysis error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    """Custom 404 error handler."""
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Custom 500 error handler."""
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({'error': 'Internal server error'}), 500

@socketio.on('connect')
def handle_connect():
    """Handle client connection with enhanced logging."""
    client_info = {
        'sid': request.sid,
        'remote_addr': request.remote_addr,
        'user_agent': request.headers.get('User-Agent', 'Unknown')
    }
    logger.info(f'Client connected: {client_info}')
    
    emit('log_message', {
        'msg': 'Successfully connected to PID Controller Simulator',
        'type': 'success',
        'timestamp': simulation_service.get_timestamp()
    })
    
    # Send initial configuration
    emit('config_update', {
        'presets': app.config['INDUSTRIAL_PRESETS'],
        'controller_types': app.config['CONTROLLER_TYPES'],
        'tuning_methods': app.config['TUNING_METHODS'],
        'features': {
            'frequency_analysis': app.config['ENABLE_FREQUENCY_ANALYSIS'],
            'root_locus': app.config['ENABLE_ROOT_LOCUS'],
            'robustness_analysis': app.config['ENABLE_ROBUSTNESS_ANALYSIS'],
            'adaptive_control': app.config['ENABLE_ADAPTIVE_CONTROL']
        }
    })

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection with enhanced logging."""
    logger.info(f'Client disconnected: {request.sid}')
    simulation_service.stop_simulation()

@socketio.on('start_tuning')
def handle_start_tuning(data):
    """Start auto-tuning simulation with enhanced error handling."""
    try:
        logger.info(f"Received start_tuning event with data: {data}")
        
        # Enhanced validation
        if not data:
            raise ValueError("No data received for start_tuning")
        
        # Validate required fields
        required_fields = ['K', 'T', 'theta']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")
        
        # Rate limiting check
        if hasattr(simulation_service, 'last_tuning_start'):
            time_since_last = datetime.now() - simulation_service.last_tuning_start
            if time_since_last.total_seconds() < 1.0:  # 1 second cooldown
                raise ValueError("Rate limit exceeded. Please wait before starting new tuning.")
        
        simulation_service.last_tuning_start = datetime.now()
        simulation_service.start_tuning_simulation(data)
        
    except Exception as e:
        logger.error(f"Error in handle_start_tuning: {str(e)}", exc_info=True)
        emit('error', {
            'msg': f'Error starting tuning: {str(e)}',
            'timestamp': simulation_service.get_timestamp(),
            'error_type': 'tuning_error'
        })

@socketio.on('start_pid')
def handle_start_pid(data):
    """Start PID simulation with enhanced error handling."""
    try:
        logger.info(f"Received start_pid event with data: {data}")
        
        if not data:
            raise ValueError("No data received for start_pid")
        
        # Enhanced validation
        required_fields = ['K', 'T', 'theta', 'tunedParams']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")
        
        # Rate limiting check
        if hasattr(simulation_service, 'last_pid_start'):
            time_since_last = datetime.now() - simulation_service.last_pid_start
            if time_since_last.total_seconds() < 1.0:  # 1 second cooldown
                raise ValueError("Rate limit exceeded. Please wait before starting new simulation.")
        
        simulation_service.last_pid_start = datetime.now()
        simulation_service.start_pid_simulation(data)
        
    except Exception as e:
        logger.error(f"Error in handle_start_pid: {str(e)}", exc_info=True)
        emit('error', {
            'msg': f'Error starting PID simulation: {str(e)}',
            'timestamp': simulation_service.get_timestamp(),
            'error_type': 'pid_error'
        })

@socketio.on('stop_simulation')
def handle_stop_simulation():
    """Stop any running simulation."""
    logger.info("Stopping simulation")
    simulation_service.stop_simulation()
    emit('log_message', {
        'msg': 'Simulation stopped',
        'type': 'info',
        'timestamp': simulation_service.get_timestamp()
    })

@socketio.on('get_preset_parameters')
def handle_get_presets():
    """Get predefined system parameters with enhanced presets."""
    emit('preset_parameters', app.config['INDUSTRIAL_PRESETS'])

@socketio.on('request_frequency_analysis')
def handle_frequency_analysis(data):
    """Handle frequency analysis request."""
    try:
        if not app.config['ENABLE_FREQUENCY_ANALYSIS']:
            emit('error', {
                'msg': 'Frequency analysis is disabled',
                'timestamp': simulation_service.get_timestamp()
            })
            return
        
        # Implementation for frequency analysis would go here
        emit('frequency_analysis_result', {
            'bode_magnitude': [],
            'bode_phase': [],
            'nyquist_real': [],
            'nyquist_imag': [],
            'gain_margin': 0,
            'phase_margin': 0
        })
        
    except Exception as e:
        logger.error(f"Frequency analysis error: {str(e)}")
        emit('error', {
            'msg': f'Frequency analysis error: {str(e)}',
            'timestamp': simulation_service.get_timestamp()
        })

@socketio.on('request_performance_metrics')
def handle_performance_metrics():
    """Send current performance metrics."""
    metrics = simulation_service.get_performance_metrics()
    emit('performance_metrics', metrics)

# Enhanced error handling for SocketIO
@socketio.on_error_default
def default_error_handler(e):
    """Default error handler for SocketIO events."""
    logger.error(f"SocketIO error: {str(e)}")
    emit('error', {
        'msg': f'Server error: {str(e)}',
        'timestamp': datetime.now().strftime("%H:%M:%S")
    })

if __name__ == '__main__':
    # Enhanced startup logging
    logger.info("=" * 50)
    logger.info("Starting PID Controller Simulator")
    logger.info("=" * 50)
    logger.info(f"Debug mode: {app.config['DEBUG']}")
    logger.info(f"Features enabled:")
    logger.info(f"  - Frequency Analysis: {app.config['ENABLE_FREQUENCY_ANALYSIS']}")
    logger.info(f"  - Root Locus: {app.config['ENABLE_ROOT_LOCUS']}")
    logger.info(f"  - Robustness Analysis: {app.config['ENABLE_ROBUSTNESS_ANALYSIS']}")
    logger.info(f"  - Adaptive Control: {app.config['ENABLE_ADAPTIVE_CONTROL']}")
    logger.info("Server starting on http://127.0.0.1:5000")
    logger.info("=" * 50)
    
    # Fixed: Use configuration values for debug mode
    socketio.run(
        app, 
        debug=app.config['DEBUG'], 
        host='127.0.0.1', 
        port=5000,
        log_output=True
    )