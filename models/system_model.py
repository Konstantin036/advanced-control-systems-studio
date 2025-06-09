import numpy as np
from collections import deque
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class SystemModel:
    """
    First-order plus dead time (FOPDT) system model.
    
    Transfer function: G(s) = K * e^(-theta*s) / (T*s + 1)
    
    Parameters:
        K (float): Process gain
        T (float): Time constant (seconds)
        theta (float): Dead time delay (seconds)
        initial_output (float): Initial system output
        dt (float): Simulation time step (seconds)
    """
    
    def __init__(self, K: float, T: float, theta: float, 
                 initial_output: float = 0.0, dt: float = 0.1):
        self.K = K
        self.T = T
        self.theta = theta
        self.dt = dt
        self.output = initial_output
        
        # Initialize delay buffer
        self._setup_delay_buffer()
        
        # Validation
        self._validate_parameters()
        
        logger.info(f"SystemModel initialized: K={K}, T={T}, theta={theta}")
    
    def _setup_delay_buffer(self):
        """Setup the delay buffer for dead time simulation."""
        delay_steps = max(1, int(self.theta / self.dt))
        self.delay_buffer = deque([0.0] * delay_steps, maxlen=delay_steps)
        self.delay_steps = delay_steps
    
    def _validate_parameters(self):
        """Validate system parameters."""
        if self.K == 0:
            raise ValueError("Process gain K cannot be zero")
        if self.T <= 0:
            raise ValueError("Time constant T must be positive")
        if self.theta < 0:
            raise ValueError("Dead time theta cannot be negative")
        if self.dt <= 0:
            raise ValueError("Time step dt must be positive")
    
    def update(self, control_input: float) -> float:
        """
        Update the system state with a new control input.
        
        Args:
            control_input (float): Control signal input
            
        Returns:
            float: Current system output
        """
        # Add current input to delay buffer
        self.delay_buffer.append(control_input)
        
        # Get delayed input
        delayed_input = self.delay_buffer[0]
        
        # First-order system differential equation: T*dy/dt + y = K*u
        # Discretized: y[k+1] = y[k] + dt/T * (K*u[k] - y[k])
        d_output = (self.K * delayed_input - self.output) / self.T
        self.output += d_output * self.dt
        
        return self.output
    
    def reset(self, initial_output: float = 0.0):
        """Reset the system to initial conditions."""
        self.output = initial_output
        self.delay_buffer.clear()
        self.delay_buffer.extend([0.0] * self.delay_steps)
        
    def get_steady_state_output(self, control_input: float) -> float:
        """Calculate steady-state output for a given constant input."""
        return self.K * control_input
    
    def get_time_constant(self) -> float:
        """Get the system time constant."""
        return self.T
    
    def get_dead_time(self) -> float:
        """Get the system dead time."""
        return self.theta
    
    def get_process_gain(self) -> float:
        """Get the system process gain."""
        return self.K
    
    def __str__(self) -> str:
        return f"SystemModel(K={self.K}, T={self.T}, theta={self.theta})"