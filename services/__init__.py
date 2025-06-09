# Services package for PID Controller Simulator
"""
This package contains service classes for the PID Controller Simulator:

- AutoTuner: Implements relay feedback auto-tuning using various methods
- SimulationService: Handles real-time simulation execution and frontend communication
"""

__version__ = "1.0.0"
__author__ = "PID Controller Simulator"

from .auto_tuner import AutoTuner
from .simulation_service import SimulationService

__all__ = ['AutoTuner', 'SimulationService']