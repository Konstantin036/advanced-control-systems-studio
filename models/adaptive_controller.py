import logging
import math
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from collections import deque
from .pid_controller import PIDController

logger = logging.getLogger(__name__)

@dataclass
class AdaptiveSettings:
    """Settings for adaptive controller behavior."""
    adaptation_rate: float = 0.1
    min_adaptation_interval: float = 5.0  # seconds
    performance_window: int = 100  # number of samples
    stability_threshold: float = 0.1
    aggressive_tuning: bool = False
    enable_gain_scheduling: bool = True
    enable_self_tuning: bool = True

@dataclass
class PerformanceMetrics:
    """Performance metrics for adaptation decisions."""
    iae: float = 0.0
    ise: float = 0.0
    itae: float = 0.0
    overshoot: float = 0.0
    settling_time: float = 0.0
    rise_time: float = 0.0
    steady_state_error: float = 0.0
    oscillation_count: int = 0
    stability_index: float = 0.0

class AdaptiveController:
    """
    Adaptive PID Controller with self-tuning capabilities.
    
    Features:
    - Automatic parameter adaptation based on performance
    - Gain scheduling for different operating points
    - Self-tuning using pattern recognition
    - Disturbance rejection adaptation
    - Load change compensation
    """
    
    def __init__(self, base_controller: PIDController, settings: Optional[AdaptiveSettings] = None):
        self.base_controller = base_controller
        self.settings = settings if settings is not None else AdaptiveSettings()
        
        # Adaptation state
        self.adaptation_enabled = True
        self.last_adaptation_time = 0.0
        self.adaptation_count = 0
        
        # Performance tracking
        self.error_history = deque(maxlen=self.settings.performance_window)
        self.output_history = deque(maxlen=self.settings.performance_window)
        self.setpoint_history = deque(maxlen=self.settings.performance_window)
        self.time_history = deque(maxlen=self.settings.performance_window)
        
        # Adaptation parameters
        self.original_params = {'Kp': base_controller.Kp, 'Ki': base_controller.Ki, 'Kd': base_controller.Kd}
        self.adaptation_history = []
        
        # Pattern recognition
        self.oscillation_detector = OscillationDetector()
        self.load_change_detector = LoadChangeDetector()
        
        # Gain scheduling
        self.gain_schedule = GainScheduler()
        
        logger.info("AdaptiveController initialized")
    
    def calculate(self, setpoint: float, measurement: float, current_time: float) -> float:
        """
        Calculate control output with adaptive behavior.
        
        Args:
            setpoint: Desired value
            measurement: Current process value
            current_time: Current time
            
        Returns:
            Control output
        """
        # Calculate base PID output
        control_output = self.base_controller.calculate(setpoint, measurement)
        
        # Store data for adaptation
        error = setpoint - measurement
        self._store_performance_data(setpoint, measurement, error, current_time)
        
        # Perform adaptation if enabled and conditions are met
        if self.adaptation_enabled and self._should_adapt(current_time):
            self._adapt_parameters(current_time)
        
        return control_output
    
    def _store_performance_data(self, setpoint: float, measurement: float, 
                              error: float, current_time: float):
        """Store data for performance analysis."""
        self.setpoint_history.append(setpoint)
        self.output_history.append(measurement)
        self.error_history.append(error)
        self.time_history.append(current_time)
        
        # Update pattern detectors
        self.oscillation_detector.update(error, current_time)
        self.load_change_detector.update(setpoint, measurement, current_time)
    
    def _should_adapt(self, current_time: float) -> bool:
        """Determine if adaptation should occur."""
        # Check minimum time interval
        if current_time - self.last_adaptation_time < self.settings.min_adaptation_interval:
            return False
        
        # Check if we have enough data
        if len(self.error_history) < self.settings.performance_window // 2:
            return False
        
        # Check if system is stable enough for adaptation
        recent_errors = list(self.error_history)[-20:]  # Last 20 samples
        if not recent_errors:
            return False
        
        error_variance = sum((e - sum(recent_errors)/len(recent_errors))**2 for e in recent_errors) / len(recent_errors)
        
        return error_variance > self.settings.stability_threshold
    
    def _adapt_parameters(self, current_time: float):
        """Adapt PID parameters based on performance analysis."""
        try:
            # Calculate current performance metrics
            metrics = self._calculate_performance_metrics()
            
            # Detect system behavior patterns
            adaptation_needed = self._analyze_system_behavior(metrics)
            
            if adaptation_needed:
                # Calculate parameter adjustments
                new_params = self._calculate_parameter_adjustments(metrics)
                
                # Apply parameter changes
                self._apply_parameter_changes(new_params)
                
                # Update adaptation history
                self.adaptation_history.append({
                    'time': current_time,
                    'old_params': self.original_params.copy(),
                    'new_params': new_params,
                    'metrics': metrics,
                    'reason': adaptation_needed
                })
                
                self.last_adaptation_time = current_time
                self.adaptation_count += 1
                
                logger.info(f"Adaptation #{self.adaptation_count}: {adaptation_needed}")
                logger.info(f"New parameters: Kp={new_params['Kp']:.3f}, Ki={new_params['Ki']:.3f}, Kd={new_params['Kd']:.3f}")
        
        except Exception as e:
            logger.error(f"Error in parameter adaptation: {str(e)}")
    
    def _calculate_performance_metrics(self) -> PerformanceMetrics:
        """Calculate current performance metrics."""
        if len(self.error_history) < 10:
            return PerformanceMetrics()
        
        errors = list(self.error_history)
        outputs = list(self.output_history)
        setpoints = list(self.setpoint_history)
        times = list(self.time_history)
        
        # Calculate integral metrics
        dt = times[1] - times[0] if len(times) > 1 else 0.1
        iae = sum(abs(e) for e in errors) * dt
        ise = sum(e**2 for e in errors) * dt
        itae = sum(abs(e) * t for e, t in zip(errors, times)) * dt
        
        # Calculate overshoot
        if setpoints:
            target = setpoints[-1]
            max_output = max(outputs) if outputs else 0
            overshoot = max(0, (max_output - target) / target * 100) if target != 0 else 0
        else:
            overshoot = 0
        
        # Calculate settling time (simplified)
        settling_time = self._calculate_settling_time(outputs, setpoints)
        
        # Calculate rise time (simplified)
        rise_time = self._calculate_rise_time(outputs, setpoints)
        
        # Calculate steady-state error
        steady_state_error = abs(errors[-1]) if errors else 0
        
        # Count oscillations
        oscillation_count = self.oscillation_detector.get_oscillation_count()
        
        # Calculate stability index
        stability_index = self._calculate_stability_index(errors)
        
        return PerformanceMetrics(
            iae=iae,
            ise=ise,
            itae=itae,
            overshoot=overshoot,
            settling_time=settling_time,
            rise_time=rise_time,
            steady_state_error=steady_state_error,
            oscillation_count=oscillation_count,
            stability_index=stability_index
        )
    
    def _calculate_settling_time(self, outputs: List[float], setpoints: List[float]) -> float:
        """Calculate settling time (simplified approach)."""
        if not outputs or not setpoints:
            return 0.0
        
        target = setpoints[-1]
        tolerance = 0.02 * abs(target) if target != 0 else 0.02
        
        # Find last time when output was outside tolerance
        for i in range(len(outputs) - 1, -1, -1):
            if abs(outputs[i] - target) > tolerance:
                return len(outputs) - i  # Return in samples, not actual time
        
        return 0.0
    
    def _calculate_rise_time(self, outputs: List[float], setpoints: List[float]) -> float:
        """Calculate rise time (simplified approach)."""
        if not outputs or not setpoints:
            return 0.0
        
        target = setpoints[-1]
        start_value = outputs[0]
        
        # Find time to reach 90% of target
        target_90 = start_value + 0.9 * (target - start_value)
        
        for i, output in enumerate(outputs):
            if output >= target_90:
                return i  # Return in samples
        
        return len(outputs)
    
    def _calculate_stability_index(self, errors: List[float]) -> float:
        """Calculate stability index based on error variance."""
        if len(errors) < 10:
            return 0.0
        
        recent_errors = errors[-20:]  # Last 20 samples
        mean_error = sum(recent_errors) / len(recent_errors)
        variance = sum((e - mean_error)**2 for e in recent_errors) / len(recent_errors)
        
        return 1.0 / (1.0 + variance)  # Higher is more stable
    
    def _analyze_system_behavior(self, metrics: PerformanceMetrics) -> Optional[str]:
        """Analyze system behavior and determine if adaptation is needed."""
        # Check for excessive oscillations
        if metrics.oscillation_count > 5:
            return "excessive_oscillations"
        
        # Check for poor settling
        if metrics.settling_time > 50:  # samples
            return "poor_settling"
        
        # Check for high steady-state error
        if metrics.steady_state_error > 0.1:
            return "high_steady_state_error"
        
        # Check for excessive overshoot
        if metrics.overshoot > 20:
            return "excessive_overshoot"
        
        # Check for load change
        if self.load_change_detector.is_load_change_detected():
            return "load_change_detected"
        
        # Check for poor stability
        if metrics.stability_index < 0.3:
            return "poor_stability"
        
        return None
    
    def _calculate_parameter_adjustments(self, metrics: PerformanceMetrics) -> Dict[str, float]:
        """Calculate new PID parameters based on performance."""
        current_kp = self.base_controller.Kp
        current_ki = self.base_controller.Ki
        current_kd = self.base_controller.Kd
        
        # Base adjustments
        new_kp = current_kp
        new_ki = current_ki
        new_kd = current_kd
        
        # Adaptation based on performance issues
        if metrics.oscillation_count > 5:
            # Reduce gains to reduce oscillations
            new_kp *= 0.8
            new_kd *= 0.7
        
        if metrics.overshoot > 20:
            # Reduce proportional gain
            new_kp *= 0.9
        
        if metrics.steady_state_error > 0.1:
            # Increase integral gain
            new_ki *= 1.1
        
        if metrics.settling_time > 50:
            # Increase proportional gain slightly
            new_kp *= 1.05
        
        if metrics.stability_index < 0.3:
            # Reduce derivative gain for stability
            new_kd *= 0.8
        
        # Apply gain scheduling if enabled
        if self.settings.enable_gain_scheduling:
            scheduling_factors = self.gain_schedule.get_scheduling_factors(
                self.setpoint_history, self.output_history
            )
            new_kp *= scheduling_factors['kp_factor']
            new_ki *= scheduling_factors['ki_factor']
            new_kd *= scheduling_factors['kd_factor']
        
        # Ensure reasonable bounds
        new_kp = max(0.1, min(10.0, new_kp))
        new_ki = max(0.0, min(5.0, new_ki))
        new_kd = max(0.0, min(2.0, new_kd))
        
        return {'Kp': new_kp, 'Ki': new_ki, 'Kd': new_kd}
    
    def _apply_parameter_changes(self, new_params: Dict[str, float]):
        """Apply new parameters to the controller."""
        self.base_controller.set_tuning(
            new_params['Kp'], 
            new_params['Ki'], 
            new_params['Kd']
        )
    
    def get_adaptation_status(self) -> Dict:
        """Get current adaptation status."""
        return {
            'adaptation_enabled': self.adaptation_enabled,
            'adaptation_count': self.adaptation_count,
            'last_adaptation_time': self.last_adaptation_time,
            'current_params': {
                'Kp': self.base_controller.Kp,
                'Ki': self.base_controller.Ki,
                'Kd': self.base_controller.Kd
            },
            'original_params': self.original_params,
            'oscillation_count': self.oscillation_detector.get_oscillation_count(),
            'load_changes': self.load_change_detector.get_change_count()
        }
    
    def enable_adaptation(self, enabled: bool = True):
        """Enable or disable adaptation."""
        self.adaptation_enabled = enabled
        logger.info(f"Adaptation {'enabled' if enabled else 'disabled'}")
    
    def reset_adaptation(self):
        """Reset adaptation to original parameters."""
        self.base_controller.set_tuning(
            self.original_params['Kp'],
            self.original_params['Ki'],
            self.original_params['Kd']
        )
        self.adaptation_count = 0
        self.adaptation_history.clear()
        logger.info("Adaptation reset to original parameters")

class OscillationDetector:
    """Detects oscillations in the system response."""
    
    def __init__(self, window_size: int = 50):
        self.window_size = window_size
        self.error_history = deque(maxlen=window_size)
        self.time_history = deque(maxlen=window_size)
        self.oscillation_count = 0
    
    def update(self, error: float, time: float):
        """Update with new error value."""
        self.error_history.append(error)
        self.time_history.append(time)
        
        if len(self.error_history) >= self.window_size:
            self._detect_oscillations()
    
    def _detect_oscillations(self):
        """Detect oscillations in the error signal."""
        if len(self.error_history) < 20:
            return
        
        errors = list(self.error_history)
        
        # Simple oscillation detection: count zero crossings
        zero_crossings = 0
        for i in range(1, len(errors)):
            if errors[i] * errors[i-1] < 0:  # Sign change
                zero_crossings += 1
        
        # If too many zero crossings, it's oscillating
        if zero_crossings > 6:  # Threshold for oscillation
            self.oscillation_count += 1
    
    def get_oscillation_count(self) -> int:
        """Get current oscillation count."""
        return self.oscillation_count

class LoadChangeDetector:
    """Detects load changes in the system."""
    
    def __init__(self, sensitivity: float = 0.1):
        self.sensitivity = sensitivity
        self.setpoint_history = deque(maxlen=100)
        self.output_history = deque(maxlen=100)
        self.change_count = 0
        self.last_check_time = 0
    
    def update(self, setpoint: float, output: float, time: float):
        """Update with new values."""
        self.setpoint_history.append(setpoint)
        self.output_history.append(output)
        
        # Check for load changes periodically
        if time - self.last_check_time > 10:  # Check every 10 seconds
            self._detect_load_change()
            self.last_check_time = time
    
    def _detect_load_change(self):
        """Detect sudden load changes."""
        if len(self.output_history) < 20:
            return
        
        outputs = list(self.output_history)
        
        # Check for sudden changes in output
        recent_mean = sum(outputs[-10:]) / 10
        older_mean = sum(outputs[-20:-10]) / 10
        
        if abs(recent_mean - older_mean) > self.sensitivity:
            self.change_count += 1
    
    def is_load_change_detected(self) -> bool:
        """Check if load change was recently detected."""
        return self.change_count > 0
    
    def get_change_count(self) -> int:
        """Get load change count."""
        return self.change_count

class GainScheduler:
    """Implements gain scheduling for different operating points."""
    
    def __init__(self):
        self.operating_points = {
            'low': {'range': (0, 33), 'kp_factor': 1.2, 'ki_factor': 0.8, 'kd_factor': 1.0},
            'medium': {'range': (33, 67), 'kp_factor': 1.0, 'ki_factor': 1.0, 'kd_factor': 1.0},
            'high': {'range': (67, 100), 'kp_factor': 0.8, 'ki_factor': 1.2, 'kd_factor': 0.9}
        }
    
    def get_scheduling_factors(self, setpoint_history: deque, output_history: deque) -> Dict[str, float]:
        """Get gain scheduling factors based on operating point."""
        if not setpoint_history or not output_history:
            return {'kp_factor': 1.0, 'ki_factor': 1.0, 'kd_factor': 1.0}
        
        # Determine current operating point
        current_output = output_history[-1]
        
        for point_name, point_data in self.operating_points.items():
            if point_data['range'][0] <= current_output <= point_data['range'][1]:
                return {
                    'kp_factor': point_data['kp_factor'],
                    'ki_factor': point_data['ki_factor'],
                    'kd_factor': point_data['kd_factor']
                }
        
        # Default if no range matches
        return {'kp_factor': 1.0, 'ki_factor': 1.0, 'kd_factor': 1.0}