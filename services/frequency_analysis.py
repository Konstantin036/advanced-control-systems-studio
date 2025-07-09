import numpy as np
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from models.system_model import SystemModel
from models.pid_controller import PIDController

logger = logging.getLogger(__name__)

@dataclass
class FrequencyResponse:
    """Data class for frequency response results."""
    frequencies: np.ndarray
    magnitude: np.ndarray
    phase: np.ndarray
    gain_margin: float
    phase_margin: float
    gain_crossover_freq: float
    phase_crossover_freq: float
    stability_margin: str

@dataclass
class NyquistResponse:
    """Data class for Nyquist plot results."""
    real_part: np.ndarray
    imaginary_part: np.ndarray
    frequencies: np.ndarray
    encirclements: int
    stability: str

class FrequencyAnalysisService:
    """
    Advanced frequency domain analysis service for control systems.
    
    Provides:
    - Bode plot generation
    - Nyquist plot generation
    - Stability analysis
    - Gain and phase margins
    - Robustness analysis
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.info("FrequencyAnalysisService initialized")
    
    def analyze_open_loop_system(self, system: SystemModel, controller: PIDController, 
                                freq_range: Tuple[float, float] = (0.001, 1000),
                                num_points: int = 1000) -> FrequencyResponse:
        """
        Analyze the open-loop frequency response of the system with controller.
        
        Args:
            system: System model (FOPDT)
            controller: PID controller
            freq_range: Frequency range (min, max) in rad/s
            num_points: Number of frequency points
            
        Returns:
            FrequencyResponse object with analysis results
        """
        try:
            # Generate frequency vector (logarithmic spacing)
            frequencies = np.logspace(np.log10(freq_range[0]), np.log10(freq_range[1]), num_points)
            
            # Calculate system transfer function at each frequency
            s = 1j * frequencies
            
            # FOPDT system: G(s) = K * exp(-theta*s) / (T*s + 1)
            system_response = self._calculate_fopdt_response(system, s)
            
            # PID controller: C(s) = Kp + Ki/s + Kd*s
            controller_response = self._calculate_pid_response(controller, s)
            
            # Open-loop transfer function: L(s) = C(s) * G(s)
            open_loop_response = controller_response * system_response
            
            # Calculate magnitude and phase
            magnitude = np.abs(open_loop_response)
            phase = np.angle(open_loop_response, deg=True)
            
            # Calculate stability margins
            gain_margin, phase_margin, gain_crossover_freq, phase_crossover_freq = \
                self._calculate_stability_margins(frequencies, magnitude, phase)
            
            # Determine stability
            stability_margin = self._determine_stability(gain_margin, phase_margin)
            
            return FrequencyResponse(
                frequencies=frequencies,
                magnitude=20 * np.log10(magnitude),  # Convert to dB
                phase=phase,
                gain_margin=gain_margin,
                phase_margin=phase_margin,
                gain_crossover_freq=gain_crossover_freq,
                phase_crossover_freq=phase_crossover_freq,
                stability_margin=stability_margin
            )
            
        except Exception as e:
            self.logger.error(f"Error in open-loop analysis: {str(e)}")
            raise
    
    def analyze_closed_loop_system(self, system: SystemModel, controller: PIDController,
                                 freq_range: Tuple[float, float] = (0.001, 1000),
                                 num_points: int = 1000) -> FrequencyResponse:
        """
        Analyze the closed-loop frequency response.
        
        Args:
            system: System model
            controller: PID controller
            freq_range: Frequency range
            num_points: Number of frequency points
            
        Returns:
            FrequencyResponse object for closed-loop system
        """
        try:
            frequencies = np.logspace(np.log10(freq_range[0]), np.log10(freq_range[1]), num_points)
            s = 1j * frequencies
            
            # Calculate transfer functions
            system_response = self._calculate_fopdt_response(system, s)
            controller_response = self._calculate_pid_response(controller, s)
            
            # Closed-loop transfer function: T(s) = C(s)*G(s) / (1 + C(s)*G(s))
            open_loop = controller_response * system_response
            closed_loop_response = open_loop / (1 + open_loop)
            
            magnitude = np.abs(closed_loop_response)
            phase = np.angle(closed_loop_response, deg=True)
            
            # For closed-loop, we analyze different characteristics
            bandwidth = self._calculate_bandwidth(frequencies, magnitude)
            resonance_peak = np.max(magnitude)
            
            return FrequencyResponse(
                frequencies=frequencies,
                magnitude=20 * np.log10(magnitude),
                phase=phase,
                gain_margin=float('inf'),  # Not applicable for closed-loop
                phase_margin=float('inf'),  # Not applicable for closed-loop
                gain_crossover_freq=bandwidth,
                phase_crossover_freq=0,
                stability_margin=f"Bandwidth: {bandwidth:.2f} rad/s, Peak: {resonance_peak:.2f}"
            )
            
        except Exception as e:
            self.logger.error(f"Error in closed-loop analysis: {str(e)}")
            raise
    
    def generate_nyquist_plot(self, system: SystemModel, controller: PIDController,
                            freq_range: Tuple[float, float] = (0.001, 1000),
                            num_points: int = 1000) -> NyquistResponse:
        """
        Generate Nyquist plot data for stability analysis.
        
        Args:
            system: System model
            controller: PID controller
            freq_range: Frequency range
            num_points: Number of frequency points
            
        Returns:
            NyquistResponse object with plot data and stability analysis
        """
        try:
            # Generate frequency vector including negative frequencies
            freq_pos = np.logspace(np.log10(freq_range[0]), np.log10(freq_range[1]), num_points//2)
            freq_neg = -freq_pos[::-1]
            frequencies = np.concatenate([freq_neg, freq_pos])
            
            s = 1j * frequencies
            
            # Calculate open-loop transfer function
            system_response = self._calculate_fopdt_response(system, s)
            controller_response = self._calculate_pid_response(controller, s)
            open_loop_response = controller_response * system_response
            
            real_part = np.real(open_loop_response)
            imaginary_part = np.imag(open_loop_response)
            
            # Nyquist stability analysis
            encirclements = self._count_encirclements(real_part, imaginary_part)
            stability = self._nyquist_stability_analysis(encirclements)
            
            return NyquistResponse(
                real_part=real_part,
                imaginary_part=imaginary_part,
                frequencies=frequencies,
                encirclements=encirclements,
                stability=stability
            )
            
        except Exception as e:
            self.logger.error(f"Error in Nyquist analysis: {str(e)}")
            raise
    
    def _calculate_fopdt_response(self, system: SystemModel, s: np.ndarray) -> np.ndarray:
        """Calculate FOPDT system response: G(s) = K * e^(-theta*s) / (T*s + 1)"""
        numerator = system.K * np.exp(-system.theta * s)
        denominator = system.T * s + 1
        return numerator / denominator
    
    def _calculate_pid_response(self, controller: PIDController, s: np.ndarray) -> np.ndarray:
        """Calculate PID controller response: C(s) = Kp + Ki/s + Kd*s"""
        # Handle s = 0 case for integral term
        s_safe = np.where(s == 0, 1e-12, s)
        return controller.Kp + controller.Ki / s_safe + controller.Kd * s
    
    def _calculate_stability_margins(self, frequencies: np.ndarray, magnitude: np.ndarray, 
                                   phase: np.ndarray) -> Tuple[float, float, float, float]:
        """Calculate gain and phase margins."""
        try:
            # Find gain crossover frequency (where |L(jω)| = 1, or 0 dB)
            magnitude_db = 20 * np.log10(magnitude)
            gain_crossover_idx = np.argmin(np.abs(magnitude_db))
            gain_crossover_freq = frequencies[gain_crossover_idx]
            
            # Phase margin at gain crossover
            phase_margin = 180 + phase[gain_crossover_idx]
            
            # Find phase crossover frequency (where ∠L(jω) = -180°)
            phase_crossover_indices = np.where(np.abs(phase + 180) < 1.0)[0]
            if len(phase_crossover_indices) > 0:
                phase_crossover_idx = phase_crossover_indices[0]
                phase_crossover_freq = frequencies[phase_crossover_idx]
                gain_margin = -magnitude_db[phase_crossover_idx]
            else:
                phase_crossover_freq = 0
                gain_margin = float('inf')
            
            return gain_margin, phase_margin, gain_crossover_freq, phase_crossover_freq
            
        except Exception as e:
            self.logger.error(f"Error calculating stability margins: {str(e)}")
            return 0, 0, 0, 0
    
    def _determine_stability(self, gain_margin: float, phase_margin: float) -> str:
        """Determine system stability based on margins."""
        if gain_margin > 6 and phase_margin > 30:
            return "Stable with good margins"
        elif gain_margin > 3 and phase_margin > 15:
            return "Marginally stable"
        elif gain_margin > 0 and phase_margin > 0:
            return "Stable with poor margins"
        else:
            return "Unstable"
    
    def _calculate_bandwidth(self, frequencies: np.ndarray, magnitude: np.ndarray) -> float:
        """Calculate system bandwidth (-3dB point)."""
        try:
            # Find -3dB point (magnitude = 0.707 of DC gain)
            dc_gain = magnitude[0]
            target_magnitude = dc_gain * 0.707
            
            # Find closest point to -3dB
            idx = np.argmin(np.abs(magnitude - target_magnitude))
            return frequencies[idx]
            
        except Exception as e:
            self.logger.error(f"Error calculating bandwidth: {str(e)}")
            return 0
    
    def _count_encirclements(self, real: np.ndarray, imag: np.ndarray) -> int:
        """Count encirclements of -1 point for Nyquist stability."""
        try:
            # Simple encirclement counting (could be improved)
            # This is a simplified version - full implementation would be more complex
            encirclements = 0
            
            # Check if the plot encircles the -1 point
            # This is a basic implementation
            center_x, center_y = -1, 0
            
            # Calculate angles relative to the -1 point
            angles = np.arctan2(imag - center_y, real - center_x)
            
            # Count net angle change
            angle_diff = np.diff(angles)
            
            # Handle angle wraparound
            angle_diff = np.where(angle_diff > np.pi, angle_diff - 2*np.pi, angle_diff)
            angle_diff = np.where(angle_diff < -np.pi, angle_diff + 2*np.pi, angle_diff)
            
            total_angle_change = np.sum(angle_diff)
            encirclements = int(total_angle_change / (2 * np.pi))
            
            return encirclements
            
        except Exception as e:
            self.logger.error(f"Error counting encirclements: {str(e)}")
            return 0
    
    def _nyquist_stability_analysis(self, encirclements: int) -> str:
        """Analyze stability using Nyquist criterion."""
        if encirclements == 0:
            return "Stable (no encirclements of -1)"
        elif encirclements > 0:
            return f"Unstable ({encirclements} clockwise encirclements)"
        else:
            return f"Unstable ({abs(encirclements)} counter-clockwise encirclements)"
    
    def generate_analysis_report(self, system: SystemModel, controller: PIDController) -> Dict:
        """
        Generate a comprehensive frequency analysis report.
        
        Returns:
            Dictionary with complete analysis results
        """
        try:
            # Perform all analyses
            open_loop = self.analyze_open_loop_system(system, controller)
            closed_loop = self.analyze_closed_loop_system(system, controller)
            nyquist = self.generate_nyquist_plot(system, controller)
            
            return {
                'open_loop_analysis': {
                    'frequencies': open_loop.frequencies.tolist(),
                    'magnitude_db': open_loop.magnitude.tolist(),
                    'phase_deg': open_loop.phase.tolist(),
                    'gain_margin_db': open_loop.gain_margin,
                    'phase_margin_deg': open_loop.phase_margin,
                    'gain_crossover_freq': open_loop.gain_crossover_freq,
                    'phase_crossover_freq': open_loop.phase_crossover_freq,
                    'stability': open_loop.stability_margin
                },
                'closed_loop_analysis': {
                    'frequencies': closed_loop.frequencies.tolist(),
                    'magnitude_db': closed_loop.magnitude.tolist(),
                    'phase_deg': closed_loop.phase.tolist(),
                    'bandwidth': closed_loop.gain_crossover_freq,
                    'info': closed_loop.stability_margin
                },
                'nyquist_analysis': {
                    'real_part': nyquist.real_part.tolist(),
                    'imaginary_part': nyquist.imaginary_part.tolist(),
                    'frequencies': nyquist.frequencies.tolist(),
                    'encirclements': nyquist.encirclements,
                    'stability': nyquist.stability
                },
                'summary': {
                    'overall_stability': open_loop.stability_margin,
                    'recommended_actions': self._generate_recommendations(open_loop, closed_loop)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error generating analysis report: {str(e)}")
            raise
    
    def _generate_recommendations(self, open_loop: FrequencyResponse, 
                                closed_loop: FrequencyResponse) -> List[str]:
        """Generate tuning recommendations based on frequency analysis."""
        recommendations = []
        
        if open_loop.gain_margin < 6:
            recommendations.append("Consider reducing proportional gain - low gain margin")
        
        if open_loop.phase_margin < 30:
            recommendations.append("Consider reducing derivative gain - low phase margin")
        
        if open_loop.gain_crossover_freq < 0.1:
            recommendations.append("System responds slowly - consider increasing controller gains")
        
        if open_loop.gain_crossover_freq > 10:
            recommendations.append("System may be too aggressive - consider reducing gains")
        
        if not recommendations:
            recommendations.append("System appears well-tuned from frequency domain perspective")
        
        return recommendations