import numpy as np
from typing import Tuple, List, Dict, Optional
import logging
from scipy.signal import find_peaks
from models.system_model import SystemModel

logger = logging.getLogger(__name__)

class AutoTuner:
    """
    Automatic PID tuning using relay feedback method.
    
    Implements multiple tuning rules:
    - Ziegler-Nichols
    - Tyreus-Luyben
    - Cohen-Coon
    """
    
    def __init__(self, system: SystemModel, relay_amplitude: float = 10.0,
                 setpoint: float = 0.0, tuning_method: str = 'ziegler_nichols'):
        self.system = system
        self.relay_amplitude = relay_amplitude
        self.setpoint = setpoint
        self.tuning_method = tuning_method
        
        # Data storage
        self.time_data = []
        self.output_data = []
        self.control_data = []
        
        # Analysis results
        self.ultimate_gain = None
        self.ultimate_period = None
        self.tuned_parameters = None
        
        logger.info(f"AutoTuner initialized with method: {tuning_method}")
    
    def run_relay_test(self, duration: float = 150.0, dt: float = 0.1) -> Dict:
        """
        Run relay feedback test to determine ultimate gain and period.
        
        Args:
            duration (float): Test duration in seconds
            dt (float): Time step in seconds
            
        Returns:
            Dict: Results containing time series data and analysis
        """
        self.system.reset()
        self.time_data.clear()
        self.output_data.clear()
        self.control_data.clear()
        
        control_signal = self.relay_amplitude
        
        logger.info(f"Starting relay test for {duration} seconds")
        
        for t in np.arange(0, duration, dt):
            # Get current system output
            system_output = self.system.update(control_signal)
            
            # Store data
            self.time_data.append(t)
            self.output_data.append(system_output)
            self.control_data.append(control_signal)
            
            # Relay logic
            if system_output > self.setpoint:
                control_signal = -self.relay_amplitude
            else:
                control_signal = self.relay_amplitude
        
        # Analyze the oscillations
        self._analyze_oscillations()
        
        # Calculate PID parameters
        self._calculate_pid_parameters()
        
        return {
            'time': self.time_data,
            'output': self.output_data,
            'control': self.control_data,
            'ultimate_gain': self.ultimate_gain,
            'ultimate_period': self.ultimate_period,
            'tuned_parameters': self.tuned_parameters
        }
    
    def _analyze_oscillations(self):
        """Analyze the relay test data to extract ultimate gain and period."""
        if len(self.output_data) < 100:
            raise ValueError("Insufficient data for analysis")
        
        # Remove initial transient (first 30% of data)
        start_idx = int(0.3 * len(self.output_data))
        stable_output = np.array(self.output_data[start_idx:])
        stable_time = np.array(self.time_data[start_idx:])
        
        # Find peaks and valleys
        peaks, _ = find_peaks(stable_output, distance=10)
        valleys, _ = find_peaks(-stable_output, distance=10)
        
        if len(peaks) < 2 or len(valleys) < 2:
            logger.warning("Insufficient oscillations detected")
            self.ultimate_gain = 4.0  # Default fallback
            self.ultimate_period = 10.0
            return
        
        # Calculate amplitude of oscillations
        peak_values = stable_output[peaks]
        valley_values = stable_output[valleys]
        
        amplitude = np.mean(peak_values) - np.mean(valley_values)
        
        # Calculate ultimate gain (Ku)
        # Ku = 4 * relay_amplitude / (π * amplitude)
        self.ultimate_gain = (4 * self.relay_amplitude) / (np.pi * amplitude)
        
        # Calculate ultimate period (Tu)
        if len(peaks) >= 2:
            peak_times = stable_time[peaks]
            periods = np.diff(peak_times) * 2  # Full period
            self.ultimate_period = np.mean(periods)
        else:
            self.ultimate_period = 10.0  # Default fallback
        
        logger.info(f"Analysis complete: Ku={self.ultimate_gain:.3f}, Tu={self.ultimate_period:.3f}")
    
    def _calculate_pid_parameters(self):
        """Calculate PID parameters using the selected tuning method."""
        if self.ultimate_gain is None or self.ultimate_period is None:
            raise ValueError("Must run relay test first")
        
        Ku = self.ultimate_gain
        Tu = self.ultimate_period
        
        if self.tuning_method == 'ziegler_nichols':
            Kp = 0.6 * Ku
            Ki = 2 * Kp / Tu
            Kd = Kp * Tu / 8
        
        elif self.tuning_method == 'tyreus_luyben':
            Kp = 0.454 * Ku
            Ki = 2.2 * Kp / Tu
            Kd = Kp * Tu / 6.3
        
        elif self.tuning_method == 'cohen_coon':
            # Simplified Cohen-Coon (requires step response data)
            Kp = 0.9 * Ku
            Ki = 3.3 * Kp / Tu
            Kd = Kp * Tu / 9
        
        else:
            # Default to Ziegler-Nichols
            Kp = 0.6 * Ku
            Ki = 2 * Kp / Tu
            Kd = Kp * Tu / 8
        
        self.tuned_parameters = {
            'Kp': round(Kp, 3),
            'Ki': round(Ki, 3),
            'Kd': round(Kd, 3),
            'method': self.tuning_method,
            'Ku': round(Ku, 3),
            'Tu': round(Tu, 3)
        }
        
        logger.info(f"PID parameters calculated: {self.tuned_parameters}")
    
    def get_tuning_quality_metrics(self) -> Dict:
        """Calculate quality metrics for the tuning."""
        if not self.tuned_parameters:
            return {}
        
        # Simple quality metrics based on oscillation characteristics
        if len(self.output_data) < 100:
            return {}
        
        stable_output = np.array(self.output_data[int(0.5 * len(self.output_data)):])
        
        return {
            'oscillation_amplitude': np.std(stable_output),
            'settling_characteristics': 'good' if np.std(stable_output) < 2.0 else 'needs_adjustment',
            'recommended_adjustments': self._get_tuning_recommendations()
        }
    
    def _get_tuning_recommendations(self) -> List[str]:
        """Provide recommendations for tuning adjustments."""
        recommendations = []
        
        if self.ultimate_period and self.ultimate_period < 5:
            recommendations.append("System responds quickly - consider reducing derivative gain")
        elif self.ultimate_period and self.ultimate_period > 20:
            recommendations.append("System responds slowly - consider increasing proportional gain")
        
        if self.ultimate_gain and self.ultimate_gain < 2:
            recommendations.append("Low ultimate gain - system may be difficult to control")
        
        return recommendations