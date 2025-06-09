// PID Controller Simulator - Frontend Application
class PIDSimulatorApp {
    constructor() {
        this.socket = null;
        this.charts = {};
        this.currentSimulation = null;
        this.presetParameters = {};
        this.tunedParameters = null;
        
        this.init();
    }

    init() {
        this.initializeSocketIO();
        this.initializeCharts();
        this.bindEventHandlers();
        this.loadPresetParameters();
        
        console.log('PID Simulator App initialized');
    }

    // ========== Socket.IO Communication ==========
    initializeSocketIO() {
        this.socket = io();
        
        this.socket.on('connect', () => {
            this.updateConnectionStatus(true);
            this.addLogMessage('Connected to server', 'success');
        });

        this.socket.on('disconnect', () => {
            this.updateConnectionStatus(false);
            this.addLogMessage('Disconnected from server', 'error');
        });

        this.socket.on('log_message', (data) => {
            this.addLogMessage(data.msg, data.type, data.timestamp);
        });

        this.socket.on('error', (data) => {
            this.addLogMessage(data.msg, 'error', data.timestamp);
            this.stopLoadingStates();
        });

        this.socket.on('tuning_update', (data) => {
            this.updateTuningChart(data);
        });

        this.socket.on('tuning_result', (data) => {
            this.handleTuningResults(data);
            this.stopLoadingStates();
        });

        this.socket.on('pid_update', (data) => {
            this.updatePIDChart(data);
            this.updatePerformanceMetrics(data.performance);
        });

        this.socket.on('preset_parameters', (data) => {
            this.presetParameters = data;
        });
    }

    updateConnectionStatus(connected) {
        const statusElement = document.getElementById('connectionStatus');
        if (connected) {
            statusElement.textContent = 'Connected';
            statusElement.className = 'badge bg-success me-2 connected';
        } else {
            statusElement.textContent = 'Disconnected';
            statusElement.className = 'badge bg-danger me-2 disconnected';
        }
    }

    // ========== Chart Management ==========
    initializeCharts() {
        // Register the zoom plugin
        Chart.register(ChartZoom);
        
        // Main system response chart
        const mainCtx = document.getElementById('mainChart').getContext('2d');
        this.charts.main = new Chart(mainCtx, {
            type: 'line',
            data: {
                datasets: [
                    {
                        label: 'System Output',
                        data: [],
                        borderColor: '#007bff',
                        backgroundColor: 'rgba(0, 123, 255, 0.1)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.1
                    },
                    {
                        label: 'Setpoint',
                        data: [],
                        borderColor: '#28a745',
                        backgroundColor: 'rgba(40, 167, 69, 0.1)',
                        borderWidth: 2,
                        borderDash: [5, 5],
                        fill: false
                    },
                    {
                        label: 'Control Signal',
                        data: [],
                        borderColor: '#ffc107',
                        backgroundColor: 'rgba(255, 193, 7, 0.1)',
                        borderWidth: 2,
                        fill: false,
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: {
                    duration: 0 // Disable animation for real-time updates
                },
                scales: {
                    x: {
                        type: 'linear',
                        title: {
                            display: true,
                            text: 'Time (s)'
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'System Output'
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: {
                            display: true,
                            text: 'Control Signal'
                        },
                        grid: {
                            drawOnChartArea: false
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    },
                    zoom: {
                        zoom: {
                            wheel: {
                                enabled: true,
                                speed: 0.1
                            },
                            pinch: {
                                enabled: true
                            },
                            mode: 'xy',
                            drag: {
                                enabled: true,
                                borderColor: 'rgb(54, 162, 235)',
                                borderWidth: 1,
                                backgroundColor: 'rgba(54, 162, 235, 0.3)'
                            }
                        },
                        pan: {
                            enabled: true,
                            mode: 'xy'
                        }
                    }
                },
                interaction: {
                    mode: 'nearest',
                    axis: 'x',
                    intersect: false
                }
            }
        });

        // PID components chart
        const pidCtx = document.getElementById('pidChart').getContext('2d');
        this.charts.pid = new Chart(pidCtx, {
            type: 'line',
            data: {
                datasets: [
                    {
                        label: 'Proportional (P)',
                        data: [],
                        borderColor: '#dc3545',
                        backgroundColor: 'rgba(220, 53, 69, 0.1)',
                        borderWidth: 2,
                        fill: false
                    },
                    {
                        label: 'Integral (I)',
                        data: [],
                        borderColor: '#fd7e14',
                        backgroundColor: 'rgba(253, 126, 20, 0.1)',
                        borderWidth: 2,
                        fill: false
                    },
                    {
                        label: 'Derivative (D)',
                        data: [],
                        borderColor: '#6610f2',
                        backgroundColor: 'rgba(102, 16, 242, 0.1)',
                        borderWidth: 2,
                        fill: false
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: {
                    duration: 0
                },
                scales: {
                    x: {
                        type: 'linear',
                        title: {
                            display: true,
                            text: 'Time (s)'
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Component Value'
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    },
                    zoom: {
                        zoom: {
                            wheel: {
                                enabled: true,
                                speed: 0.1
                            },
                            pinch: {
                                enabled: true
                            },
                            mode: 'xy',
                            drag: {
                                enabled: true,
                                borderColor: 'rgb(54, 162, 235)',
                                borderWidth: 1,
                                backgroundColor: 'rgba(54, 162, 235, 0.3)'
                            }
                        },
                        pan: {
                            enabled: true,
                            mode: 'xy'
                        }
                    }
                }
            }
        });

        // Add zoom control buttons to chart containers
        this.addZoomControls();
    }

    updateTuningChart(data) {
        const chart = this.charts.main;
        
        // Add data points
        chart.data.datasets[0].data.push({x: data.time, y: data.output});
        chart.data.datasets[1].data.push({x: data.time, y: data.setpoint});
        chart.data.datasets[2].data.push({x: data.time, y: data.control});
        
        // Limit data points for performance (keep last 1000 points)
        chart.data.datasets.forEach(dataset => {
            if (dataset.data.length > 1000) {
                dataset.data.shift();
            }
        });
        
        chart.update('none'); // Update without animation
    }

    updatePIDChart(data) {
        const mainChart = this.charts.main;
        const pidChart = this.charts.pid;
        
        // Update main chart
        mainChart.data.datasets[0].data.push({x: data.time, y: data.output});
        mainChart.data.datasets[1].data.push({x: data.time, y: data.setpoint});
        mainChart.data.datasets[2].data.push({x: data.time, y: data.control});
        
        // Update PID components chart
        if (data.components) {
            pidChart.data.datasets[0].data.push({x: data.time, y: data.components.P});
            pidChart.data.datasets[1].data.push({x: data.time, y: data.components.I});
            pidChart.data.datasets[2].data.push({x: data.time, y: data.components.D});
        }
        
        // Limit data points
        [mainChart, pidChart].forEach(chart => {
            chart.data.datasets.forEach(dataset => {
                if (dataset.data.length > 1000) {
                    dataset.data.shift();
                }
            });
        });
        
        mainChart.update('none');
        pidChart.update('none');
        
        // Show PID components chart if hidden
        document.getElementById('pidComponentsCard').style.display = 'block';
    }

    clearCharts() {
        Object.values(this.charts).forEach(chart => {
            chart.data.datasets.forEach(dataset => {
                dataset.data = [];
            });
            chart.update();
        });
        
        // Hide PID components chart
        document.getElementById('pidComponentsCard').style.display = 'none';
        
        // Reset performance metrics
        this.updatePerformanceMetrics({iae: '-', ise: '-'});
    }

    // ========== Event Handlers ==========
    bindEventHandlers() {
        // System preset buttons
        document.querySelectorAll('.preset-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.loadPreset(e.target.dataset.preset);
                this.setActivePresetButton(e.target);
            });
        });

        // Auto-tuning
        document.getElementById('startTuning').addEventListener('click', () => {
            this.startAutoTuning();
        });

        // PID simulation
        document.getElementById('startPID').addEventListener('click', () => {
            this.startPIDSimulation();
        });

        // Stop simulation
        document.getElementById('stopSimulation').addEventListener('click', () => {
            this.stopSimulation();
        });

        // Chart controls
        document.getElementById('clearChart').addEventListener('click', () => {
            this.clearCharts();
        });

        document.getElementById('exportData').addEventListener('click', () => {
            this.exportChartData();
        });

        // Log controls
        document.getElementById('clearLog').addEventListener('click', () => {
            this.clearLog();
        });

        // Tuning results modal
        document.getElementById('applyTunedParams').addEventListener('click', () => {
            this.applyTunedParameters();
        });

        // Input validation
        this.addInputValidation();
    }

    addInputValidation() {
        const numericInputs = document.querySelectorAll('input[type="number"]');
        numericInputs.forEach(input => {
            input.addEventListener('input', (e) => {
                this.validateNumericInput(e.target);
            });
        });
    }

    validateNumericInput(input) {
        const value = parseFloat(input.value);
        const min = parseFloat(input.min) || -Infinity;
        const max = parseFloat(input.max) || Infinity;
        
        if (isNaN(value) || value < min || value > max) {
            input.classList.add('is-invalid');
            input.classList.remove('is-valid');
        } else {
            input.classList.add('is-valid');
            input.classList.remove('is-invalid');
        }
    }

    // ========== Simulation Control ==========
    startAutoTuning() {
        if (!this.validateSystemParameters()) {
            this.addLogMessage('Invalid system parameters', 'error');
            return;
        }

        const params = {
            K: parseFloat(document.getElementById('processGain').value),
            T: parseFloat(document.getElementById('timeConstant').value),
            theta: parseFloat(document.getElementById('deadTime').value),
            setpoint: parseFloat(document.getElementById('setpoint').value),
            relay_amplitude: parseFloat(document.getElementById('relayAmplitude').value),
            method: document.getElementById('tuningMethod').value
        };

        this.clearCharts();
        this.setLoadingState('startTuning', true);
        this.currentSimulation = 'tuning';
        
        this.socket.emit('start_tuning', params);
        this.addLogMessage('Starting auto-tuning simulation...', 'info');
    }

    startPIDSimulation() {
        if (!this.validateSystemParameters() || !this.validatePIDParameters()) {
            this.addLogMessage('Invalid parameters', 'error');
            return;
        }

        const params = {
            K: parseFloat(document.getElementById('processGain').value),
            T: parseFloat(document.getElementById('timeConstant').value),
            theta: parseFloat(document.getElementById('deadTime').value),
            setpoint: parseFloat(document.getElementById('setpoint').value),
            tunedParams: {
                Kp: parseFloat(document.getElementById('Kp').value),
                Ki: parseFloat(document.getElementById('Ki').value),
                Kd: parseFloat(document.getElementById('Kd').value)
            }
        };

        this.clearCharts();
        this.setLoadingState('startPID', true);
        this.currentSimulation = 'pid';
        
        this.socket.emit('start_pid', params);
        this.addLogMessage('Starting PID simulation...', 'info');
    }

    stopSimulation() {
        this.socket.emit('stop_simulation');
        this.stopLoadingStates();
        this.currentSimulation = null;
    }

    // ========== Parameter Management ==========
    loadPresetParameters() {
        this.socket.emit('get_preset_parameters');
    }

    loadPreset(presetName) {
        const preset = this.presetParameters[presetName];
        if (preset) {
            document.getElementById('processGain').value = preset.K;
            document.getElementById('timeConstant').value = preset.T;
            document.getElementById('deadTime').value = preset.theta;
            
            this.addLogMessage(`Loaded preset: ${presetName}`, 'info');
        }
    }

    setActivePresetButton(activeBtn) {
        document.querySelectorAll('.preset-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        activeBtn.classList.add('active');
    }

    // ========== Apply Tuned Parameters ==========
    applyTunedParameters() {
        if (this.tunedParameters) {
            document.getElementById('Kp').value = this.tunedParameters.Kp;
            document.getElementById('Ki').value = this.tunedParameters.Ki;
            document.getElementById('Kd').value = this.tunedParameters.Kd;
            
            // Close the modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('tuningResultsModal'));
            modal.hide();
            
            this.addLogMessage('Tuned parameters applied successfully!', 'success');
        }
    }

    // ========== Chart Zoom Controls ==========
    addZoomControls() {
        // Add zoom controls to main chart
        const mainChartContainer = document.getElementById('mainChart').parentElement;
        mainChartContainer.classList.add('chart-container');
        
        const mainControls = document.createElement('div');
        mainControls.className = 'chart-controls';
        mainControls.innerHTML = `
            <button type="button" class="btn btn-outline-primary btn-sm" onclick="pidApp.resetZoom('main')" title="Reset Zoom">
                <i class="fas fa-search-minus"></i>
            </button>
            <button type="button" class="btn btn-outline-secondary btn-sm" onclick="pidApp.togglePan('main')" title="Toggle Pan" id="panToggleMain">
                <i class="fas fa-hand-paper"></i>
            </button>
        `;
        
        const mainHint = document.createElement('div');
        mainHint.className = 'zoom-hint';
        mainHint.textContent = 'Mouse wheel: zoom | Drag: pan | Ctrl+drag: zoom area';
        
        mainChartContainer.appendChild(mainControls);
        mainChartContainer.appendChild(mainHint);
        
        // Add zoom controls to PID chart
        const pidChartContainer = document.getElementById('pidChart').parentElement;
        pidChartContainer.classList.add('chart-container');
        
        const pidControls = document.createElement('div');
        pidControls.className = 'chart-controls';
        pidControls.innerHTML = `
            <button type="button" class="btn btn-outline-primary btn-sm" onclick="pidApp.resetZoom('pid')" title="Reset Zoom">
                <i class="fas fa-search-minus"></i>
            </button>
            <button type="button" class="btn btn-outline-secondary btn-sm" onclick="pidApp.togglePan('pid')" title="Toggle Pan" id="panTogglePid">
                <i class="fas fa-hand-paper"></i>
            </button>
        `;
        
        const pidHint = document.createElement('div');
        pidHint.className = 'zoom-hint';
        pidHint.textContent = 'Mouse wheel: zoom | Drag: pan | Ctrl+drag: zoom area';
        
        pidChartContainer.appendChild(pidControls);
        pidChartContainer.appendChild(pidHint);
    }
    
    resetZoom(chartType) {
        if (this.charts[chartType]) {
            this.charts[chartType].resetZoom();
            this.addLogMessage(`${chartType.toUpperCase()} chart zoom reset`, 'info');
        }
    }
    
    togglePan(chartType) {
        if (this.charts[chartType]) {
            const chart = this.charts[chartType];
            const panEnabled = chart.options.plugins.zoom.pan.enabled;
            chart.options.plugins.zoom.pan.enabled = !panEnabled;
            chart.update();
            
            const button = document.getElementById(`panToggle${chartType.charAt(0).toUpperCase() + chartType.slice(1)}`);
            if (!panEnabled) {
                button.classList.remove('btn-outline-secondary');
                button.classList.add('btn-secondary');
                this.addLogMessage(`${chartType.toUpperCase()} chart pan enabled`, 'info');
            } else {
                button.classList.remove('btn-secondary');
                button.classList.add('btn-outline-secondary');
                this.addLogMessage(`${chartType.toUpperCase()} chart pan disabled`, 'info');
            }
        }
    }

    // ========== Enhanced Tuning Results ==========
    handleTuningResults(data) {
        this.tunedParameters = data.parameters;
        
        // Update parameter values with animations
        this.animateParameterUpdate('tunedKp', data.parameters.Kp);
        this.animateParameterUpdate('tunedKi', data.parameters.Ki);
        this.animateParameterUpdate('tunedKd', data.parameters.Kd);
        
        // Update analysis data
        document.getElementById('ultimateGain').textContent = data.parameters.Ku;
        document.getElementById('ultimatePeriod').textContent = data.parameters.Tu;
        document.getElementById('tunedMethod').textContent = this.formatMethodName(data.parameters.method);
        
        // Calculate and display quality score
        const qualityScore = this.calculateQualityScore(data.quality_metrics, data.parameters);
        this.updateQualityScore(qualityScore);
        
        // Update detailed analysis
        this.updateDetailedAnalysis(data.quality_metrics);
        
        // Update recommendations
        this.updateRecommendations(data.quality_metrics);
        
        // Update transfer function
        this.updateTransferFunction(data.parameters);
        
        // Set timestamp
        document.getElementById('tuningTimestamp').textContent = new Date().toLocaleTimeString();
        
        // Show modal with animation
        const modal = new bootstrap.Modal(document.getElementById('tuningResultsModal'));
        modal.show();
        
        this.addLogMessage('Auto-tuning analysis complete!', 'success');
    }
    
    animateParameterUpdate(elementId, value) {
        const element = document.getElementById(elementId);
        element.style.transform = 'scale(1.2)';
        element.style.transition = 'transform 0.3s ease';
        
        setTimeout(() => {
            element.textContent = value;
            element.style.transform = 'scale(1)';
        }, 150);
    }
    
    formatMethodName(method) {
        const methodNames = {
            'ziegler_nichols': 'Ziegler-Nichols',
            'tyreus_luyben': 'Tyreus-Luyben',
            'cohen_coon': 'Cohen-Coon'
        };
        return methodNames[method] || method;
    }
    
    calculateQualityScore(metrics, parameters) {
        // Simple quality scoring algorithm (0-100)
        let score = 70; // Base score
        
        if (metrics && metrics.oscillation_amplitude !== undefined) {
            // Lower oscillation amplitude is better
            if (metrics.oscillation_amplitude < 1.0) score += 15;
            else if (metrics.oscillation_amplitude < 2.0) score += 10;
            else if (metrics.oscillation_amplitude > 5.0) score -= 10;
        }
        
        // Check parameter reasonableness
        if (parameters.Kp > 0 && parameters.Ki > 0 && parameters.Kd >= 0) {
            score += 10;
        }
        
        // Ensure score is within bounds
        return Math.max(0, Math.min(100, score));
    }
    
    updateQualityScore(score) {
        const scoreElement = document.getElementById('qualityScore');
        const statusElement = document.getElementById('qualityStatus');
        
        // Animate score circle
        const degrees = (score / 100) * 360;
        scoreElement.style.setProperty('--score-deg', `${degrees}deg`);
        
        // Update score value with counting animation
        this.animateCountUp(scoreElement.querySelector('.score-value'), score);
        
        // Update status text and color
        let status, color;
        if (score >= 80) {
            status = 'Excellent';
            color = '#28a745';
        } else if (score >= 60) {
            status = 'Good';
            color = '#ffc107';
        } else if (score >= 40) {
            status = 'Fair';
            color = '#fd7e14';
        } else {
            status = 'Poor';
            color = '#dc3545';
        }
        
        statusElement.textContent = status;
        statusElement.style.color = color;
        scoreElement.querySelector('.score-value').style.color = color;
    }
    
    animateCountUp(element, targetValue) {
        let currentValue = 0;
        const increment = targetValue / 30; // 30 steps animation
        const timer = setInterval(() => {
            currentValue += increment;
            if (currentValue >= targetValue) {
                currentValue = targetValue;
                clearInterval(timer);
            }
            element.textContent = Math.round(currentValue);
        }, 50);
    }
    
    updateDetailedAnalysis(metrics) {
        const analysisElement = document.getElementById('qualityMetrics');
        
        let analysisHtml = '<div class="analysis-grid">';
        
        if (metrics) {
            if (metrics.settling_characteristics) {
                analysisHtml += `
                    <div class="analysis-item">
                        <div class="analysis-icon">
                            <i class="fas fa-chart-line text-primary"></i>
                        </div>
                        <div class="analysis-content">
                            <strong>Settling Behavior:</strong><br>
                            ${metrics.settling_characteristics}
                        </div>
                    </div>
                `;
            }
            
            if (metrics.oscillation_amplitude !== undefined) {
                const oscillationLevel = metrics.oscillation_amplitude < 1.0 ? 'Low' : 
                                       metrics.oscillation_amplitude < 3.0 ? 'Moderate' : 'High';
                const oscillationIcon = oscillationLevel === 'Low' ? 'check-circle text-success' :
                                      oscillationLevel === 'Moderate' ? 'exclamation-triangle text-warning' :
                                      'times-circle text-danger';
                
                analysisHtml += `
                    <div class="analysis-item">
                        <div class="analysis-icon">
                            <i class="fas fa-${oscillationIcon}"></i>
                        </div>
                        <div class="analysis-content">
                            <strong>Oscillation Level:</strong><br>
                            ${oscillationLevel} (${metrics.oscillation_amplitude.toFixed(2)})
                        </div>
                    </div>
                `;
            }
        }
        
        analysisHtml += '</div>';
        analysisElement.innerHTML = analysisHtml;
    }
    
    updateRecommendations(metrics) {
        const recommendationsElement = document.getElementById('tuningRecommendations');
        
        let recommendations = [];
        
        if (metrics && metrics.recommended_adjustments) {
            recommendations = metrics.recommended_adjustments;
        }
        
        // Add some general recommendations
        recommendations.push('Monitor system response during initial testing');
        recommendations.push('Fine-tune parameters based on actual performance');
        
        let recommendationsHtml = '';
        recommendations.forEach((rec, index) => {
            const icon = index < 2 ? 'lightbulb text-warning' : 'info-circle text-info';
            recommendationsHtml += `
                <div class="recommendation-item fade-in" style="animation-delay: ${index * 0.1}s">
                    <i class="fas fa-${icon} me-2"></i>
                    ${rec}
                </div>
            `;
        });
        
        recommendationsElement.innerHTML = recommendationsHtml;
    }
    
    updateTransferFunction(parameters) {
        const transferElement = document.getElementById('transferFunction');
        const { Kp, Ki, Kd } = parameters;
        
        let transferFunction = `C(s) = ${Kp}`;
        if (Ki > 0) transferFunction += ` + ${Ki}/s`;
        if (Kd > 0) transferFunction += ` + ${Kd}·s`;
        
        transferElement.textContent = transferFunction;
        
        // Add animation
        transferElement.style.transform = 'scale(0.9)';
        transferElement.style.transition = 'transform 0.3s ease';
        setTimeout(() => {
            transferElement.style.transform = 'scale(1)';
        }, 100);
    }

    // ========== Validation ==========
    validateSystemParameters() {
        const K = parseFloat(document.getElementById('processGain').value);
        const T = parseFloat(document.getElementById('timeConstant').value);
        const theta = parseFloat(document.getElementById('deadTime').value);
        
        return !isNaN(K) && !isNaN(T) && !isNaN(theta) && 
               K !== 0 && T > 0 && theta >= 0;
    }

    validatePIDParameters() {
        const Kp = parseFloat(document.getElementById('Kp').value);
        const Ki = parseFloat(document.getElementById('Ki').value);
        const Kd = parseFloat(document.getElementById('Kd').value);
        
        return !isNaN(Kp) && !isNaN(Ki) && !isNaN(Kd);
    }

    // ========== UI Updates ==========
    setLoadingState(buttonId, loading) {
        const button = document.getElementById(buttonId);
        if (loading) {
            button.classList.add('loading');
            button.disabled = true;
        } else {
            button.classList.remove('loading');
            button.disabled = false;
        }
    }

    stopLoadingStates() {
        ['startTuning', 'startPID'].forEach(id => {
            this.setLoadingState(id, false);
        });
    }

    updatePerformanceMetrics(metrics) {
        if (metrics) {
            document.getElementById('iaeValue').textContent = 
                typeof metrics.iae === 'number' ? metrics.iae.toFixed(2) : metrics.iae;
            document.getElementById('iseValue').textContent = 
                typeof metrics.ise === 'number' ? metrics.ise.toFixed(2) : metrics.ise;
        }
    }

    // ========== Logging ==========
    addLogMessage(message, type = 'info', timestamp = null) {
        const logContainer = document.getElementById('logMessages');
        const messageDiv = document.createElement('div');
        
        const time = timestamp || new Date().toLocaleTimeString();
        
        messageDiv.className = `log-message ${type} fade-in`;
        messageDiv.innerHTML = `
            <span class="log-timestamp">${time}</span>
            ${message}
        `;
        
        logContainer.appendChild(messageDiv);
        logContainer.scrollTop = logContainer.scrollHeight;
        
        // Limit log messages (keep last 100)
        while (logContainer.children.length > 100) {
            logContainer.removeChild(logContainer.firstChild);
        }
    }

    clearLog() {
        document.getElementById('logMessages').innerHTML = '';
    }

    // ========== Data Export ==========
    exportChartData() {
        const data = {
            timestamp: new Date().toISOString(),
            systemParameters: {
                K: parseFloat(document.getElementById('processGain').value),
                T: parseFloat(document.getElementById('timeConstant').value),
                theta: parseFloat(document.getElementById('deadTime').value)
            },
            pidParameters: {
                Kp: parseFloat(document.getElementById('Kp').value),
                Ki: parseFloat(document.getElementById('Ki').value),
                Kd: parseFloat(document.getElementById('Kd').value)
            },
            chartData: {
                main: this.charts.main.data.datasets,
                pid: this.charts.pid.data.datasets
            }
        };
        
        const blob = new Blob([JSON.stringify(data, null, 2)], {
            type: 'application/json'
        });
        
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `pid_simulation_${new Date().toISOString().slice(0, 19)}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        this.addLogMessage('Data exported successfully', 'success');
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.pidApp = new PIDSimulatorApp();
});