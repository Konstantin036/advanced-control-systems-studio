# Advanced Control Systems Design Studio

A professional-grade PID controller simulator and control systems analysis tool designed for automation and control theory engineers.

## 🚀 Features

### Core Capabilities
- **Real-time PID Control Simulation** with interactive visualization
- **Advanced Auto-Tuning Algorithms** (Ziegler-Nichols, Tyreus-Luyben, Cohen-Coon, and more)
- **Multiple System Models** (FOPDT, SOPDT, Transfer Functions, State Space)
- **Professional Chart Analysis** with zoom, pan, and export functionality
- **Performance Metrics** (IAE, ISE, ITAE, Rise Time, Settling Time, Overshoot)

### Advanced Engineering Features
- **Frequency Domain Analysis** (Bode, Nyquist, Nichols plots)
- **Root Locus Analysis** for stability assessment
- **Robustness Analysis** with stability margins
- **Industrial System Presets** (Temperature, Flow, Level, Pressure control)
- **Real-time Parameter Adjustment** with validation
- **Data Export** for further analysis

### Professional Tools
- **Quality Scoring System** for tuning assessment
- **Detailed Recommendations** based on system analysis
- **Transfer Function Display** with mathematical notation
- **Engineering Console** with comprehensive logging
- **Project Save/Load** functionality

## 🛠️ Installation

### Prerequisites
- Python 3.8 or higher
- Modern web browser (Chrome, Firefox, Safari, Edge)

### Quick Setup
1. Clone the repository:
```bash
git clone https://github.com/Konstantin036/advanced-control-systems-studio.git
cd advanced-control-systems-studio
```

2. Create and activate virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
python app.py
```

5. Open your browser and navigate to `http://127.0.0.1:5000`

## 📊 Usage

### Quick Start
1. **Select System Model**: Choose from FOPDT, SOPDT, or custom transfer functions
2. **Configure Parameters**: Set system parameters or use industrial presets
3. **Auto-Tune Controller**: Use advanced tuning algorithms to find optimal PID parameters
4. **Simulate Control**: Run real-time simulation with professional analysis
5. **Analyze Performance**: View comprehensive metrics and stability analysis

### System Models Supported
- **First Order Plus Dead Time (FOPDT)**: `K*e^(-θs)/(Ts+1)`
- **Second Order Plus Dead Time (SOPDT)**: `K*e^(-θs)/(s²/ωn² + 2ζs/ωn + 1)`
- **Custom Transfer Functions**: User-defined numerator/denominator
- **State Space Models**: A, B, C, D matrix representation
- **Discrete Time Models**: Z-domain analysis
- **MIMO Systems**: Multi-input, multi-output support

### Controller Types
- Standard PID (Position and Velocity forms)
- PI/PD Controllers
- Advanced Controllers (MPC, LQR, H∞, Adaptive)
- Anti-windup and derivative filtering
- Configurable output limits

## 🔧 Technical Architecture

### Backend (Python/Flask)
- **Flask-SocketIO**: Real-time communication
- **NumPy/SciPy**: Mathematical computations
- **Control Theory Models**: Professional-grade implementations
- **Auto-tuning Algorithms**: Industry-standard methods

### Frontend (JavaScript/Bootstrap)
- **Chart.js**: Interactive plotting with zoom/pan
- **Bootstrap 5**: Responsive professional UI
- **Socket.IO**: Real-time data streaming
- **MathJax**: Mathematical notation rendering

## 📈 Performance Metrics

The tool calculates comprehensive performance indicators:

### Time Domain Metrics
- **Rise Time**: Time to reach 90% of setpoint
- **Settling Time**: Time to stay within 2% of setpoint
- **Overshoot**: Maximum percentage overshoot
- **Steady-State Error**: Final tracking error

### Integral Performance Criteria
- **IAE**: Integral of Absolute Error
- **ISE**: Integral of Square Error
- **ITAE**: Integral of Time-weighted Absolute Error

### Frequency Domain Analysis
- **Gain Margin**: Stability margin in magnitude
- **Phase Margin**: Stability margin in phase
- **Bandwidth**: Closed-loop bandwidth
- **Sensitivity Function**: Disturbance rejection analysis

## 🏭 Industrial Applications

Pre-configured system models for common industrial processes:
- **Temperature Control**: Thermal systems with typical dynamics
- **Flow Control**: Fluid systems with transportation delays
- **Level Control**: Integrating processes
- **Pressure Control**: Fast dynamics with nonlinearities
- **Motor Speed Control**: Electromechanical systems
- **Chemical Reactors**: Complex multi-variable processes

## 🔬 Academic Features

Perfect for control systems education and research:
- **Interactive Learning**: Real-time parameter effects visualization
- **Comparative Analysis**: Multiple controller comparison
- **Export Functionality**: Data export for reports/publications
- **Professional Documentation**: Comprehensive logging and analysis

## 🤝 Contributing

We welcome contributions from the control systems community! Please read our contributing guidelines and submit pull requests for:
- New controller algorithms
- Additional system models
- Enhanced analysis tools
- Bug fixes and improvements

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For technical support, feature requests, or bug reports:
- **Issues**: Use GitHub Issues for bug reports
- **Discussions**: Join GitHub Discussions for questions
- **Documentation**: Check the wiki for detailed guides

## 🏆 Acknowledgments

- Control systems theory foundations from academic literature
- Industrial control practices and standards
- Open-source scientific computing libraries
- Control engineering community feedback

---

**Built for Control Engineers, by Control Engineers** 🎛️

*Version 2.1 Professional - June 2025*
