import numpy as np
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class PIDController:
    """
    PID Controller with anti-windup and derivative filtering.
    
    Implements the standard PID control algorithm:
    u(t) = Kp*e(t) + Ki*∫e(t)dt + Kd*de(t)/dt
    
    Features:
    - Anti-windup protection
    - Derivative kick prevention
    - Configurable output limits
    - Reset functionality
    """
    
    def __init__(self, Kp: float, Ki: float, Kd: float, Ts: float,
                 output_limits: Tuple[float, float] = (-100, 100),
                 derivative_on_measurement: bool = False):
        """
        Initialize PID controller.
        
        Args:
            Kp (float): Proportional gain
            Ki (float): Integral gain
            Kd (float): Derivative gain
            Ts (float): Sample time (seconds)
            output_limits (Tuple[float, float]): Min and max output limits
            derivative_on_measurement (bool): Use derivative on measurement instead of error
        """
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.Ts = Ts
        self.output_limits = output_limits
        self.derivative_on_measurement = derivative_on_measurement
        
        # Internal state
        self.reset()
        
        # Validation
        self._validate_parameters()
        
        logger.info(f"PIDController initialized: Kp={Kp}, Ki={Ki}, Kd={Kd}")
    
    def _validate_parameters(self):
        """Validate PID parameters."""
        if self.Ts <= 0:
            raise ValueError("Sample time Ts must be positive")
        if self.output_limits[0] >= self.output_limits[1]:
            raise ValueError("Invalid output limits: min must be less than max")
    
    def reset(self):
        """Reset controller internal state."""
        self.integral = 0.0
        self.previous_error = 0.0
        self.previous_measurement = 0.0
        self.previous_output = 0.0
        self._first_run = True
    
    def calculate(self, setpoint: float, measurement: float) -> float:
        """
        Calculate PID output.
        
        Args:
            setpoint (float): Desired value
            measurement (float): Current process value
            
        Returns:
            float: Control output
        """
        error = setpoint - measurement
        
        # Proportional term
        P = self.Kp * error
        
        # Integral term with anti-windup
        self.integral += error * self.Ts
        I = self.Ki * self.integral
        
        # Derivative term
        if self._first_run:
            derivative = 0.0
            self._first_run = False
        else:
            if self.derivative_on_measurement:
                # Derivative on measurement (prevents derivative kick)
                derivative = -(measurement - self.previous_measurement) / self.Ts
            else:
                # Derivative on error
                derivative = (error - self.previous_error) / self.Ts
        
        D = self.Kd * derivative
        
        # Calculate output
        output = P + I + D
        
        # Apply output limits and anti-windup
        if output > self.output_limits[1]:
            output = self.output_limits[1]
            # Anti-windup: back-calculate integral
            self.integral = (output - P - D) / self.Ki if self.Ki != 0 else 0
        elif output < self.output_limits[0]:
            output = self.output_limits[0]
            # Anti-windup: back-calculate integral
            self.integral = (output - P - D) / self.Ki if self.Ki != 0 else 0
        
        # Store values for next iteration
        self.previous_error = error
        self.previous_measurement = measurement
        self.previous_output = output
        
        return output
    
    def get_components(self, setpoint: float, measurement: float) -> dict:
        """
        Get individual PID components for debugging/monitoring.
        
        Args:
            setpoint (float): Desired value
            measurement (float): Current process value
            
        Returns:
            dict: Dictionary with P, I, D components and total output
        """
        error = setpoint - measurement
        
        P = self.Kp * error
        I = self.Ki * self.integral
        
        if self._first_run:
            derivative = 0.0
        else:
            if self.derivative_on_measurement:
                derivative = -(measurement - self.previous_measurement) / self.Ts
            else:
                derivative = (error - self.previous_error) / self.Ts
        
        D = self.Kd * derivative
        
        return {
            'P': P,
            'I': I,
            'D': D,
            'output': P + I + D,
            'error': error
        }
    
    def set_tuning(self, Kp: float, Ki: float, Kd: float):
        """Update PID tuning parameters."""
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        logger.info(f"PID tuning updated: Kp={Kp}, Ki={Ki}, Kd={Kd}")
    
    def set_output_limits(self, min_output: float, max_output: float):
        """Update output limits."""
        if min_output >= max_output:
            raise ValueError("Invalid output limits: min must be less than max")
        self.output_limits = (min_output, max_output)
    
    def __str__(self) -> str:
        return f"PIDController(Kp={self.Kp}, Ki={self.Ki}, Kd={self.Kd})"