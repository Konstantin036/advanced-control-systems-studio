from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import logging
from config import Config
from models.system_model import SystemModel
from models.pid_controller import PIDController
from services.auto_tuner import AutoTuner
from services.simulation_service import SimulationService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize SocketIO with CORS support
socketio = SocketIO(
    app, 
    async_mode='threading',  # Changed from 'eventlet' to 'threading'
    cors_allowed_origins="*",
    logger=True,
    engineio_logger=True
)

# Initialize services
simulation_service = SimulationService(socketio)

@app.route('/')
def index():
    """Main page route."""
    return render_template('index.html')

@app.route('/api/health')
def health_check():
    """Health check endpoint."""
    return {'status': 'healthy', 'service': 'PID Controller Simulator'}

@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    logger.info('Client connected')
    emit('log_message', {
        'msg': 'Successfully connected to PID Controller Simulator',
        'type': 'success',
        'timestamp': simulation_service.get_timestamp()
    })

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    logger.info('Client disconnected')
    simulation_service.stop_simulation()

@socketio.on('start_tuning')
def handle_start_tuning(data):
    """Start auto-tuning simulation."""
    try:
        logger.info(f"Received start_tuning event with data: {data}")
        if not data:
            raise ValueError("No data received for start_tuning")
        simulation_service.start_tuning_simulation(data)
    except Exception as e:
        logger.error(f"Error in handle_start_tuning: {str(e)}", exc_info=True)
        emit('error', {
            'msg': f'Error starting tuning: {str(e)}',
            'timestamp': simulation_service.get_timestamp()
        })

@socketio.on('start_pid')
def handle_start_pid(data):
    """Start PID simulation."""
    try:
        logger.info(f"Received start_pid event with data: {data}")
        if not data:
            raise ValueError("No data received for start_pid")
        simulation_service.start_pid_simulation(data)
    except Exception as e:
        logger.error(f"Error in handle_start_pid: {str(e)}", exc_info=True)
        emit('error', {
            'msg': f'Error starting PID simulation: {str(e)}',
            'timestamp': simulation_service.get_timestamp()
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
    """Get predefined system parameters."""
    presets = {
        'fast_system': {'K': 2.0, 'T': 5.0, 'theta': 1.0},
        'slow_system': {'K': 1.5, 'T': 20.0, 'theta': 3.0},
        'oscillatory': {'K': 3.0, 'T': 8.0, 'theta': 2.5},
        'sluggish': {'K': 0.8, 'T': 30.0, 'theta': 5.0}
    }
    emit('preset_parameters', presets)

if __name__ == '__main__':
    logger.info("Starting PID Controller Simulator on http://127.0.0.1:5000")
    socketio.run(app, debug=True, host='127.0.0.1', port=5000)