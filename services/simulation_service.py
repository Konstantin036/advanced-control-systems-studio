import time
import numpy as np
from typing import Dict, Any, Optional
import logging
from threading import Thread, Event
from datetime import datetime
from flask_socketio import SocketIO, emit

from models.system_model import SystemModel
from models.pid_controller import PIDController
from services.auto_tuner import AutoTuner
from config import Config

logger = logging.getLogger(__name__)

class SimulationService:
    """
    Service for managing PID controller simulations and auto-tuning.
    Handles real-time communication with frontend via SocketIO.
    """
    
    def __init__(self, socketio: SocketIO):
        self.socketio = socketio
        self.config = Config()
        
        # Simulation state
        self.is_running = False
        self.stop_event = Event()
        self.current_thread: Optional[Thread] = None
        
        # Performance metrics
        self.simulation_start_time = None
        self.data_points_sent = 0
        
        logger.info("SimulationService initialized")
    
    def get_timestamp(self) -> str:
        """Get current timestamp for logging."""
        return datetime.now().strftime("%H:%M:%S")
    
    def stop_simulation(self):
        """Stop any running simulation."""
        if self.is_running:
            self.stop_event.set()
            self.is_running = False
            if self.current_thread and self.current_thread.is_alive():
                self.current_thread.join(timeout=2.0)
            logger.info("Simulation stopped")
    
    def start_tuning_simulation(self, params: Dict[str, Any]):
        """Start auto-tuning simulation in background thread."""
        logger.info(f"Received start_tuning_simulation request with params: {params}")
        
        if self.is_running:
            logger.info("Stopping existing simulation before starting new one")
            self.stop_simulation()
        
        try:
            # Validate parameters first
            system_params = self._validate_system_parameters(params)
            tuning_params = self._validate_tuning_parameters(params)
            logger.info(f"Parameters validated successfully: system={system_params}, tuning={tuning_params}")
        except Exception as e:
            logger.error(f"Parameter validation failed: {str(e)}")
            self.socketio.emit('error', {
                'msg': f'Parameter validation failed: {str(e)}',
                'timestamp': self.get_timestamp()
            })
            return
        
        self.stop_event.clear()
        self.current_thread = Thread(target=self._run_tuning_simulation, args=(params,))
        self.current_thread.daemon = True  # Make thread daemon so it doesn't prevent app shutdown
        logger.info("Starting tuning simulation thread")
        self.current_thread.start()
    
    def start_pid_simulation(self, params: Dict[str, Any]):
        """Start PID simulation in background thread."""
        logger.info(f"Received start_pid_simulation request with params: {params}")
        
        if self.is_running:
            logger.info("Stopping existing simulation before starting new one")
            self.stop_simulation()
        
        try:
            # Validate parameters first
            system_params = self._validate_system_parameters(params)
            pid_params = self._validate_pid_parameters(params)
            logger.info(f"Parameters validated successfully: system={system_params}, pid={pid_params}")
        except Exception as e:
            logger.error(f"Parameter validation failed: {str(e)}")
            self.socketio.emit('error', {
                'msg': f'Parameter validation failed: {str(e)}',
                'timestamp': self.get_timestamp()
            })
            return
        
        self.stop_event.clear()
        self.current_thread = Thread(target=self._run_pid_simulation, args=(params,))
        self.current_thread.daemon = True  # Make thread daemon so it doesn't prevent app shutdown
        logger.info("Starting PID simulation thread")
        self.current_thread.start()
    
    def _run_tuning_simulation(self, params: Dict[str, Any]):
        """Execute auto-tuning simulation."""
        try:
            self.is_running = True
            self.simulation_start_time = time.time()
            self.data_points_sent = 0
            
            # Validate and extract parameters
            system_params = self._validate_system_parameters(params)
            tuning_params = self._validate_tuning_parameters(params)
            
            # Create system model
            system = SystemModel(
                K=system_params['K'],
                T=system_params['T'],
                theta=system_params['theta'],
                dt=self.config.DEFAULT_SIMULATION_DT
            )
            
            # Create auto-tuner
            auto_tuner = AutoTuner(
                system=system,
                relay_amplitude=tuning_params['relay_amplitude'],
                setpoint=tuning_params['setpoint'],
                tuning_method=tuning_params.get('method', 'ziegler_nichols')
            )
            
            self.socketio.emit('log_message', {
                'msg': 'Starting relay feedback auto-tuning...',
                'type': 'info',
                'timestamp': self.get_timestamp()
            })
            
            # Run relay test with real-time updates
            self._run_relay_test_with_updates(auto_tuner, tuning_params)
            
            if not self.stop_event.is_set():
                # Get tuning results
                results = auto_tuner.tuned_parameters
                quality_metrics = auto_tuner.get_tuning_quality_metrics()
                
                self.socketio.emit('tuning_result', {
                    'parameters': results,
                    'quality_metrics': quality_metrics,
                    'timestamp': self.get_timestamp()
                })
                
                self.socketio.emit('log_message', {
                    'msg': f'Auto-tuning completed successfully! Kp={results["Kp"]}, Ki={results["Ki"]}, Kd={results["Kd"]}',
                    'type': 'success',
                    'timestamp': self.get_timestamp()
                })
        
        except Exception as e:
            logger.error(f"Error in tuning simulation: {str(e)}")
            self.socketio.emit('error', {
                'msg': f'Tuning simulation error: {str(e)}',
                'timestamp': self.get_timestamp()
            })
        
        finally:
            self.is_running = False
            self._log_simulation_stats()
    
    def _run_pid_simulation(self, params: Dict[str, Any]):
        """Execute PID control simulation."""
        try:
            self.is_running = True
            self.simulation_start_time = time.time()
            self.data_points_sent = 0
            
            # Validate parameters
            system_params = self._validate_system_parameters(params)
            pid_params = self._validate_pid_parameters(params)
            
            # Create system and controller
            system = SystemModel(
                K=system_params['K'],
                T=system_params['T'],
                theta=system_params['theta'],
                dt=self.config.DEFAULT_SIMULATION_DT
            )
            
            pid = PIDController(
                Kp=pid_params['Kp'],
                Ki=pid_params['Ki'],
                Kd=pid_params['Kd'],
                Ts=self.config.DEFAULT_SIMULATION_DT,
                output_limits=(self.config.MIN_CONTROL_OUTPUT, self.config.MAX_CONTROL_OUTPUT)
            )
            
            setpoint = float(params.get('setpoint', 10.0))
            duration = float(params.get('duration', self.config.PID_DURATION))
            
            self.socketio.emit('log_message', {
                'msg': f'Starting PID simulation for {duration}s...',
                'type': 'info',
                'timestamp': self.get_timestamp()
            })
            
            # Run PID simulation
            self._run_pid_loop(system, pid, setpoint, duration)
            
            if not self.stop_event.is_set():
                self.socketio.emit('log_message', {
                    'msg': 'PID simulation completed successfully!',
                    'type': 'success',
                    'timestamp': self.get_timestamp()
                })
        
        except Exception as e:
            logger.error(f"Error in PID simulation: {str(e)}")
            self.socketio.emit('error', {
                'msg': f'PID simulation error: {str(e)}',
                'timestamp': self.get_timestamp()
            })
        
        finally:
            self.is_running = False
            self._log_simulation_stats()
    
    def _run_relay_test_with_updates(self, auto_tuner: AutoTuner, params: Dict):
        """Run relay test with real-time frontend updates."""
        dt = self.config.DEFAULT_SIMULATION_DT
        duration = float(params.get('duration', self.config.TUNING_DURATION))
        setpoint = float(params.get('setpoint', 0.0))
        
        control_signal = auto_tuner.relay_amplitude
        update_interval = 0.05  # Send updates every 50ms for smooth visualization
        last_update_time = 0
        
        for t in np.arange(0, duration, dt):
            if self.stop_event.is_set():
                break
            
            # Update system
            system_output = auto_tuner.system.update(control_signal)
            
            # Store data in auto_tuner
            auto_tuner.time_data.append(t)
            auto_tuner.output_data.append(system_output)
            auto_tuner.control_data.append(control_signal)
            
            # Relay logic
            if system_output > setpoint:
                control_signal = -auto_tuner.relay_amplitude
            else:
                control_signal = auto_tuner.relay_amplitude
            
            # Send real-time updates
            current_time = time.time()
            if current_time - last_update_time >= update_interval:
                self.socketio.emit('tuning_update', {
                    'time': round(t, 2),
                    'output': round(system_output, 3),
                    'control': round(control_signal, 3),
                    'setpoint': setpoint
                })
                self.data_points_sent += 1
                last_update_time = current_time
            
            # Small delay for real-time effect
            time.sleep(dt / 10)  # Speed up simulation
        
        # Analyze results
        if not self.stop_event.is_set():
            auto_tuner._analyze_oscillations()
            auto_tuner._calculate_pid_parameters()
    
    def _run_pid_loop(self, system: SystemModel, pid: PIDController, setpoint: float, duration: float):
        """Run PID control loop with real-time updates."""
        dt = self.config.DEFAULT_SIMULATION_DT
        update_interval = 0.05
        last_update_time = 0
        
        # Performance tracking
        iae = 0  # Integral Absolute Error
        ise = 0  # Integral Square Error
        
        for t in np.arange(0, duration, dt):
            if self.stop_event.is_set():
                break
            
            # PID control step
            current_output = system.output
            error = setpoint - current_output
            control_signal = pid.calculate(setpoint, current_output)
            system.update(control_signal)
            
            # Calculate performance metrics
            iae += abs(error) * dt
            ise += error**2 * dt
            
            # Send real-time updates
            current_time = time.time()
            if current_time - last_update_time >= update_interval:
                pid_components = pid.get_components(setpoint, current_output)
                
                self.socketio.emit('pid_update', {
                    'time': round(t, 2),
                    'output': round(current_output, 3),
                    'control': round(control_signal, 3),
                    'setpoint': setpoint,
                    'error': round(error, 3),
                    'components': {
                        'P': round(pid_components['P'], 3),
                        'I': round(pid_components['I'], 3),
                        'D': round(pid_components['D'], 3)
                    },
                    'performance': {
                        'iae': round(iae, 2),
                        'ise': round(ise, 2)
                    }
                })
                self.data_points_sent += 1
                last_update_time = current_time
            
            # Small delay for real-time effect
            time.sleep(dt / 20)  # Speed up simulation
    
    def _validate_system_parameters(self, params: Dict) -> Dict:
        """Validate and extract system parameters."""
        try:
            return {
                'K': float(params['K']),
                'T': float(params['T']),
                'theta': float(params['theta'])
            }
        except (KeyError, ValueError, TypeError) as e:
            raise ValueError(f"Invalid system parameters: {str(e)}")
    
    def _validate_tuning_parameters(self, params: Dict) -> Dict:
        """Validate and extract tuning parameters."""
        try:
            return {
                'setpoint': float(params.get('setpoint', 0.0)),
                'relay_amplitude': float(params.get('relay_amplitude', 10.0)),
                'duration': float(params.get('duration', self.config.TUNING_DURATION)),
                'method': params.get('method', 'ziegler_nichols')
            }
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid tuning parameters: {str(e)}")
    
    def _validate_pid_parameters(self, params: Dict) -> Dict:
        """Validate and extract PID parameters."""
        try:
            tuned_params = params.get('tunedParams', {})
            return {
                'Kp': float(tuned_params['Kp']),
                'Ki': float(tuned_params['Ki']),
                'Kd': float(tuned_params['Kd'])
            }
        except (KeyError, ValueError, TypeError) as e:
            raise ValueError(f"Invalid PID parameters: {str(e)}")
    
    def _log_simulation_stats(self):
        """Log simulation performance statistics."""
        if self.simulation_start_time:
            duration = time.time() - self.simulation_start_time
            logger.info(f"Simulation completed: {duration:.2f}s, {self.data_points_sent} data points sent")