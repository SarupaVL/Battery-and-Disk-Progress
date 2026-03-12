/**
 * Battery & Disk Neural Core - Main Application
 * Handles UI updates, animations, and data visualization
 * Data source: battery_service.py (writes JSON files)
 */

// Chart instances
let timeSeriesChart = null;
let diskTimeSeriesChart = null;

// Current data
let currentBatteryData = null;
let currentDiskData = null;
let previousBatteryPercent = 0;
let diskHistory = []; // For analytics
let currentUser = null;

/**
 * Initialize the application
 */
function initApp() {
  console.log('🚀 Initializing Battery & Disk Neural Core...');

  // Set up neural network background
  initNeuralNetwork();

  // Initialize charts
  initTimeSeriesChart();
  initDiskTimeSeriesChart();

  // Set up tab switching
  setupTabNavigation();

  // Initialize authentication (which will trigger data fetching if logged in)
  initAuth();

  // Start live clock
  updateClock();
  setInterval(updateClock, 1000);

  console.log('✅ Battery & Disk Neural Core initialized');
}

/**
 * Start data subscriptions
 */
function startDataSubscriptions() {
  console.log('📡 Starting data subscriptions...');
  dataLoader.subscribeBattery(onBatteryDataUpdate);
  dataLoader.subscribeDisk(onDiskDataUpdate);
}

/**
 * Set up tab navigation
 */
function setupTabNavigation() {
  const tabs = [
    { btn: document.getElementById('tabBattery'), view: document.getElementById('batteryView') },
    { btn: document.getElementById('tabDisk'), view: document.getElementById('diskView') },
    { btn: document.getElementById('tabHistory'), view: document.getElementById('historyView') }
  ];

  tabs.forEach(tab => {
    if (tab.btn) {
      tab.btn.addEventListener('click', () => {
        tabs.forEach(t => {
          t.btn.classList.remove('tab-active');
          if (t.view) t.view.classList.remove('active');
        });
        tab.btn.classList.add('tab-active');
        if (tab.view) tab.view.classList.add('active');

        // Auto-load history when switching to the History tab
        if (tab.btn.id === 'tabHistory' && !historyChart) {
          initHistoryChart();
          setupHistoryControls();
          loadHistoryData(1);
        }
      });
    }
  });
}

/**
 * Handle battery data updates
 */
function onBatteryDataUpdate(data) {
  currentBatteryData = data;
  console.log('📊 Battery data updated:', data.current.psutil.percent + '%');

  // Update all battery UI components
  updateBatteryGauge(data);
  updateBatteryStatusDisplay(data);
  updateHealthMetrics(data);
  updateMiniStats(data);
  updatePredictiveAnalytics(data);
  updateExtraAnalytics(data);
  updateTimeSeriesChart(data);
  updateThemeColors(data);
}

/**
 * Handle disk data updates
 */
function onDiskDataUpdate(data) {
  currentDiskData = data;
  console.log('💾 Disk data updated:', data.current.usage.percent + '%');

  // Maintain history for analytics
  diskHistory.push({
    timestamp: new Date(data.current.timestamp),
    usage: data.current.usage.percent,
    usedBytes: data.current.usage.used_bytes
  });

  // Keep last 100 entries
  if (diskHistory.length > 100) {
    diskHistory = diskHistory.slice(-100);
  }

  // Update all disk UI components
  updateDiskGauge(data);
  updateDiskStatus(data);
  updateDiskAnalytics(data);
  updateTopProcesses(data);
  updateDiskTimeSeriesChart(data);
  updateNeuralHealth(data);
  updateStorageEfficiency(data);
  updateHardwareHealth(data);
}

/**
 * Update battery gauge ring with smooth animation
 */
function updateBatteryGauge(data) {
  const percent = data.current.psutil.percent;
  const timeRemaining = data.analytics.estimated_runtime_minutes;

  // Animate gauge value
  animateValue('gaugeValue', previousBatteryPercent, percent, 800, (val) => val.toFixed(1) + '%');
  previousBatteryPercent = percent;

  // Update gauge ring (circumference = 2 * PI * r = 2 * 3.14159 * 85 ≈ 534)
  const circumference = 534;
  const offset = circumference - (percent / 100) * circumference;
  const gaugeProgress = document.getElementById('gaugeProgress');
  if (gaugeProgress) gaugeProgress.style.strokeDashoffset = offset;

  // Update time remaining
  const gaugeTime = document.getElementById('gaugeTime');
  if (gaugeTime) {
    gaugeTime.textContent = timeRemaining > 0 ? `${timeRemaining} min` : 'N/A';
  }

  // Update gauge color
  updateGaugeColor(percent);
}

/**
 * Update gauge color based on battery level
 */
function updateGaugeColor(percent) {
  const stop1 = document.getElementById('gaugeStop1');
  const stop2 = document.getElementById('gaugeStop2');

  if (!stop1 || !stop2) return;

  if (percent >= 70) {
    stop1.setAttribute('stop-color', '#10b981'); // Success Green
    stop2.setAttribute('stop-color', '#4287f5'); // Primary Cobalt
  } else if (percent >= 30) {
    stop1.setAttribute('stop-color', '#4287f5'); // Primary
    stop2.setAttribute('stop-color', '#6366f1'); // Indigo
  } else if (percent >= 15) {
    stop1.setAttribute('stop-color', '#f59e0b'); // Warning Orange
    stop2.setAttribute('stop-color', '#d97706');
  } else {
    stop1.setAttribute('stop-color', '#ef4444'); // Danger Red
    stop2.setAttribute('stop-color', '#dc2626');
  }
}

/**
 * Update disk gauge ring
 */
function updateDiskGauge(data) {
  const percent = data.current.usage.percent;
  const freeGB = (data.current.usage.free_bytes / (1024 ** 3)).toFixed(2);

  // Animate gauge value
  animateValue('diskGaugeValue', 0, percent, 800, (val) => val.toFixed(1) + '%');

  // Update gauge ring
  const circumference = 534;
  const offset = circumference - (percent / 100) * circumference;
  const diskGaugeProgress = document.getElementById('diskGaugeProgress');
  if (diskGaugeProgress) diskGaugeProgress.style.strokeDashoffset = offset;

  // Update free space
  const diskFreeSpace = document.getElementById('diskFreeSpace');
  if (diskFreeSpace) {
    diskFreeSpace.textContent = `${freeGB} GB free`;
  }

  // Update disk gauge color
  updateDiskGaugeColor(percent);
}

/**
 * Update disk gauge color based on usage
 */
function updateDiskGaugeColor(percent) {
  const stop1 = document.getElementById('diskGaugeStop1');
  const stop2 = document.getElementById('diskGaugeStop2');

  if (!stop1 || !stop2) return;

  if (percent >= 90) {
    stop1.setAttribute('stop-color', '#ef4444');
    stop2.setAttribute('stop-color', '#dc2626');
  } else if (percent >= 75) {
    stop1.setAttribute('stop-color', '#f59e0b');
    stop2.setAttribute('stop-color', '#d97706');
  } else if (percent >= 50) {
    stop1.setAttribute('stop-color', '#4287f5');
    stop2.setAttribute('stop-color', '#6366f1');
  } else {
    stop1.setAttribute('stop-color', '#10b981');
    stop2.setAttribute('stop-color', '#059669');
  }
}

/**
 * Update Neural Health Prediction UI
 */
function updateNeuralHealth(data) {
  const prediction = data.current.failure_probability || 0;
  const healthLabel = data.analytics.neural_health_label || 'SAFE';

  const percentElem = document.getElementById('predictionPercent');
  const labelElem = document.getElementById('predictionLabel');
  const barFill = document.getElementById('predictionBarFill');
  const displayCard = document.querySelector('.prediction-display')?.parentElement;

  if (!percentElem || !labelElem || !barFill) return;

  // Calculate Health Score (100% - Failure Probability)
  // We add a tiny bit of jitter if health is perfectly 100% to show it's "alive"
  let healthScore = (1.0 - prediction) * 100;
  if (healthScore > 99.98) {
      healthScore = 99.98 - (Math.random() * 0.05);
  }
  
  const displayScore = healthScore.toFixed(2);
  percentElem.textContent = displayScore + '%';
  labelElem.textContent = healthLabel;
  barFill.style.width = displayScore + '%';

  // Update description based on status
  const descElem = document.getElementById('predictionDesc');
  if (descElem) {
    if (healthLabel === 'SAFE') descElem.textContent = 'OVERALL HEALTH SCORE';
    else if (healthLabel === 'WARNING') descElem.textContent = 'ANOMALY DETECTED';
    else if (healthLabel === 'CRITICAL') descElem.textContent = 'HARDWARE RISK';
  }

  // Update CSS classes for risk levels
  if (displayCard) {
    displayCard.classList.remove('risk-safe', 'risk-warning', 'risk-critical');
    displayCard.classList.add(`risk-${healthLabel.toLowerCase()}`);
  }
}

/**
 * Update disk status display
 */
function updateDiskStatus(data) {
  const totalGB = (data.current.usage.total_bytes / (1024 ** 3)).toFixed(2);
  const usedGB = (data.current.usage.used_bytes / (1024 ** 3)).toFixed(2);
  const freeGB = (data.current.usage.free_bytes / (1024 ** 3)).toFixed(2);

  const totalElem = document.getElementById('diskTotal');
  const usedElem = document.getElementById('diskUsed');
  const freeElem = document.getElementById('diskFree');

  if (totalElem) totalElem.textContent = totalGB + ' GB';
  if (usedElem) usedElem.textContent = usedGB + ' GB';
  if (freeElem) freeElem.textContent = freeGB + ' GB';

  // Update I/O rates
  updateIOStats(data.current.io_rates);
}

/**
 * Update I/O statistics
 */
function updateIOStats(ioRates) {
  const formatBytesPerSec = (bytes) => {
    if (bytes >= 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(1) + ' MB/s';
    if (bytes >= 1024) return (bytes / 1024).toFixed(1) + ' KB/s';
    return bytes.toFixed(0) + ' B/s';
  };

  const readRateElem = document.getElementById('diskReadRate');
  const writeRateElem = document.getElementById('diskWriteRate');
  const readOpsElem = document.getElementById('diskReadOps');
  const writeOpsElem = document.getElementById('diskWriteOps');

  if (readRateElem) readRateElem.textContent = formatBytesPerSec(ioRates.read_bytes_per_sec);
  if (writeRateElem) writeRateElem.textContent = formatBytesPerSec(ioRates.write_bytes_per_sec);
  if (readOpsElem) readOpsElem.textContent = ioRates.read_ops_per_sec.toFixed(1) + ' /s';
  if (writeOpsElem) writeOpsElem.textContent = ioRates.write_ops_per_sec.toFixed(1) + ' /s';
}

/**
 * Update disk details from telemetry
 */
function updateDiskAnalytics(data) {
  const details = data.current.details;
  if (!details) return;

  const modelElem = document.getElementById('diskModel');
  const interfaceElem = document.getElementById('diskInterface');
  const serialElem = document.getElementById('diskSerial');

  if (modelElem) modelElem.textContent = details.model || 'Unknown';
  if (interfaceElem) interfaceElem.textContent = details.interface || 'Unknown';
  if (serialElem) serialElem.textContent = details.serial || 'Unknown';
}

/**
 * Update hardware health metrics (Temp, Power-on, etc)
 */
function updateHardwareHealth(data) {
  const health = data.current.hardware_health;
  if (!health) return;

  const tempElem = document.getElementById('diskTemp');
  const hoursElem = document.getElementById('diskPowerHours');
  const countElem = document.getElementById('diskPowerCount');
  const readsElem = document.getElementById('diskTotalReads');
  const writesElem = document.getElementById('diskTotalWrites');

  if (tempElem && health.temperature_c !== null) {
      tempElem.textContent = health.temperature_c + ' °C';
      tempElem.style.color = health.temperature_c > 60 ? '#ff4d4d' : (health.temperature_c > 50 ? '#ffcc00' : '#00ff88');
  }

  if (hoursElem) {
      if (health.power_on_hours === 0 || health.power_on_hours === null) {
          hoursElem.textContent = 'Admin Required';
          hoursElem.style.fontSize = '10px';
          hoursElem.style.color = 'rgba(255,255,255,0.3)';
      } else {
          hoursElem.textContent = (health.power_on_hours || 0).toLocaleString() + ' h';
          hoursElem.style.fontSize = '';
          hoursElem.style.color = '';
      }
  }

  if (countElem) {
      countElem.textContent = (health.power_on_count || 0).toLocaleString();
      countElem.style.color = health.power_on_count > 0 ? '' : 'rgba(255,255,255,0.3)';
  }
  
  if (readsElem) {
      const val = health.total_host_reads_gb || 0;
      readsElem.textContent = val > 1024 ? (val / 1024).toFixed(2) + ' TB' : val.toFixed(1) + ' GB';
      readsElem.style.color = val > 0 ? '' : 'rgba(255,255,255,0.3)';
  }
  
  if (writesElem) {
      const val = health.total_host_writes_gb || 0;
      writesElem.textContent = val > 1024 ? (val / 1024).toFixed(2) + ' TB' : val.toFixed(1) + ' GB';
      writesElem.style.color = val > 0 ? '' : 'rgba(255,255,255,0.3)';
  }
}

/**
 * Update storage efficiency (Logical vs Physical)
 */
function updateStorageEfficiency(data) {
  const stats = data.analytics.storage_efficiency;
  if (!stats) return;

  const logicalElem = document.getElementById('logicalSize');
  const physicalElem = document.getElementById('physicalSize');
  const efficiencyElem = document.getElementById('storageEfficiency');
  const barFill = document.getElementById('efficiencyBarFill');
  const statusElem = document.getElementById('storageScanStatus');

  if (!logicalElem || !physicalElem || !efficiencyElem || !barFill) return;

  // Format sizes
  logicalElem.textContent = formatBytes(stats.logical_bytes);
  physicalElem.textContent = formatBytes(stats.physical_bytes);

  // Update Status
  if (statusElem) {
      const count = stats.files_scanned.toLocaleString();
      if (stats.status === 'scanning') {
          statusElem.textContent = `Scanning Disk... (${count} files)`;
          statusElem.style.color = 'rgba(0, 243, 255, 0.6)';
      } else if (stats.status === 'complete') {
          statusElem.textContent = `Scan Complete (${count} files)`;
          statusElem.style.color = 'rgba(0, 255, 136, 0.6)';
      }
  }

  // Calculate efficiency percentage (how much of physical is logical)
  if (stats.physical_bytes > 0) {
    const ratio = (stats.logical_bytes / stats.physical_bytes) * 100;
    efficiencyElem.textContent = ratio.toFixed(2) + '%';
    barFill.style.width = Math.min(100, ratio) + '%';
  } else {
    efficiencyElem.textContent = '--%';
    barFill.style.width = '0%';
  }
}

/**
 * Update top disk writing processes
 */
function updateTopProcesses(data) {
  const tbody = document.getElementById('topProcesses');
  if (!tbody) return;

  const processes = data.current.top_processes;

  if (!processes || processes.length === 0) {
    tbody.innerHTML = '<tr><td colspan="3" class="empty-state">No active I/O</td></tr>';
    return;
  }

  const rows = processes.slice(0, 10).map(proc => {
    const bytesFormatted = formatBytes(proc.write_bytes_delta);
    return `
      <tr>
        <td>${proc.name || 'Unknown'}</td>
        <td>${proc.pid}</td>
        <td>${bytesFormatted}</td>
      </tr>
    `;
  }).join('');

  tbody.innerHTML = rows;
}

/**
 * Format bytes to human readable
 */
function formatBytes(bytes) {
  if (bytes >= 1024 * 1024 * 1024) return (bytes / (1024 * 1024 * 1024)).toFixed(2) + ' GB';
  if (bytes >= 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
  if (bytes >= 1024) return (bytes / 1024).toFixed(2) + ' KB';
  return bytes + ' B';
}

/**
 * Update battery status display
 */
function updateBatteryStatusDisplay(data) {
  const percent = data.current.psutil.percent;
  const plugged = data.current.psutil.power_plugged;

  // Update status badge
  let status = 'STANDBY';
  if (plugged) {
    status = percent >= 99 ? 'FULL' : 'CHARGING';
  } else {
    status = percent < 15 ? 'LOW POWER' : 'DISCHARGING';
  }

  const statusBadge = document.getElementById('statusBadgeText');
  if (statusBadge) statusBadge.textContent = status;

  // Update last update time
  const lastUpdate = new Date(data.current.timestamp);
  const timeStr = lastUpdate.toLocaleTimeString();
  const lastUpdateElem = document.getElementById('lastUpdate');
  if (lastUpdateElem) lastUpdateElem.textContent = timeStr;

  // Update data points
  const dataPointsElem = document.getElementById('dataPoints');
  if (dataPointsElem && data.history) {
    dataPointsElem.textContent = data.history.length;
  }
}

/**
 * Update health metrics
 */
function updateHealthMetrics(data) {
  const health = data.analytics.battery_health_percent;

  const healthPercent = document.getElementById('healthPercent');
  if (healthPercent) healthPercent.textContent = health + '%';

  const healthBarFill = document.getElementById('healthBarFill');
  if (healthBarFill) {
    healthBarFill.style.width = health + '%';
    // Color based on health
    if (health >= 80) {
      healthBarFill.style.background = 'linear-gradient(90deg, #00ff88, #00f3ff)';
    } else if (health >= 50) {
      healthBarFill.style.background = 'linear-gradient(90deg, #00f3ff, #0066ff)';
    } else {
      healthBarFill.style.background = 'linear-gradient(90deg, #ff9500, #ff0040)';
    }
  }

  // Update capacity info
  if (data.static) {
    const designCap = document.getElementById('designCapacity');
    const currentCap = document.getElementById('currentCapacity');
    const cycles = document.getElementById('cycleCount');

    if (designCap) designCap.textContent = data.static.design_capacity_mwh + ' mWh';
    if (currentCap) currentCap.textContent = data.static.full_charge_capacity_mwh + ' mWh';
    if (cycles) cycles.textContent = data.static.cycle_count;
  }
}

/**
 * Update mini stats
 */
function updateMiniStats(data) {
  const voltage = document.getElementById('voltage');
  const temperature = document.getElementById('temperature');
  const powerDraw = document.getElementById('powerDraw');
  const sessions = document.getElementById('sessions');

  if (voltage) voltage.textContent = data.current.voltage + ' V';
  if (temperature) temperature.textContent = data.current.temperature + '°C';
  if (powerDraw) powerDraw.textContent = data.current.power_draw + ' W';
  if (sessions) sessions.textContent = data.analytics.total_sessions;
}

/**
 * Update predictive maintenance analytics
 */
function updatePredictiveAnalytics(data) {
  if (!data.predictive_maintenance) return;

  const risk = data.predictive_maintenance.battery_risk_score;
  const level = data.predictive_maintenance.risk_level;
  const drain = data.battery_analytics?.drain_rate_percent_per_hour || 0;
  const safeCharge = 100 - (data.charging_analytics?.percent_time_above_90 || 0);

  // Update Risk Score with animation
  animateValue('riskScore', 0, risk, 1000, (val) => Math.round(val));

  // Update Risk Badge and Card State
  const riskBadge = document.getElementById('riskBadge');
  const riskContainer = document.querySelector('.risk-score-container');

  if (riskBadge) {
    riskBadge.textContent = level;

    // Reset classes
    if (riskContainer) {
      riskContainer.classList.remove('risk-low', 'risk-med', 'risk-high');
      riskContainer.classList.add(`risk-${level.toLowerCase()}`);
    }
  }

  // Update ML Active Badge
  const mlBadge = document.getElementById('mlStatusBadge');
  if (mlBadge) {
    mlBadge.style.display = data.predictive_maintenance.ml_health_predicted ? 'block' : 'none';
  }

  // Update other stats
  const drainRateElem = document.getElementById('drainRate');
  if (drainRateElem) drainRateElem.textContent = drain + '%/hr';

  const chargeSafetyElem = document.getElementById('chargeSafety');
  if (chargeSafetyElem) chargeSafetyElem.textContent = Math.round(safeCharge) + '%';
}

/**
 * Format raw minutes into human-readable 'Xh Ym' string
 */
function formatMinutesToHours(totalMinutes) {
  if (!totalMinutes || totalMinutes === 0) return '0 m';
  const hours = Math.floor(totalMinutes / 60);
  const mins = Math.round(totalMinutes % 60);
  if (hours > 0) {
    return `${hours}h ${mins}m`;
  }
  return `${mins}m`;
}

/**
 * Update the extra charging and usage analytics blocks
 */
function updateExtraAnalytics(data) {
  // Charging Stats
  if (data.charging_analytics) {
    const timeCharging = document.getElementById('timeCharging');
    const timeAbove90 = document.getElementById('timeAbove90');
    const safeChargeTime = document.getElementById('safeChargeTime');

    if (timeCharging) timeCharging.textContent = formatMinutesToHours(data.charging_analytics.time_charging_minutes);
    if (timeAbove90) timeAbove90.textContent = formatMinutesToHours(data.charging_analytics.time_above_90_minutes);
    if (safeChargeTime) safeChargeTime.textContent = (100 - data.charging_analytics.percent_time_above_90).toFixed(1) + ' %';
  }

  // Usage Summary
  if (data.battery_summary && data.battery_summary.daily) {
    const dailyAvgDrain = document.getElementById('dailyAvgDrain');
    const maxDrainSpike = document.getElementById('maxDrainSpike');

    if (dailyAvgDrain) dailyAvgDrain.textContent = (data.battery_summary.daily.average_drain_rate || 0).toFixed(1) + ' %/hr';
    if (maxDrainSpike) maxDrainSpike.textContent = (data.battery_summary.daily.max_drain_spike || 0).toFixed(1) + ' %/hr';
  }

  // Worst Window
  const worstWindow = document.getElementById('worstWindow');
  if (worstWindow && data.battery_analytics?.worst_drain_window) {
    const start = new Date(data.battery_analytics.worst_drain_window.start).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const end = new Date(data.battery_analytics.worst_drain_window.end).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    worstWindow.textContent = `${start} - ${end}`;
  }
}

/**
 * Update theme colors based on battery status
 */
function updateThemeColors(data) {
  const percent = data.current.psutil.percent;
  const plugged = data.current.psutil.power_plugged;

  const topBar = document.querySelector('.top-bar');
  if (!topBar) return;

  topBar.className = 'top-bar glass-card';
  if (plugged) {
    topBar.classList.add('glow-charging');
  } else if (percent < 15) {
    topBar.classList.add('glow-low');
  } else {
    topBar.classList.add('glow-discharging');
  }
}

/**
 * Initialize battery time series chart
 */
function initTimeSeriesChart() {
  const ctx = document.getElementById('timeSeriesChart');
  if (!ctx) return;

  timeSeriesChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: [],
      datasets: [
        {
          label: 'Battery %',
          data: [],
          borderColor: '#4287f5',
          backgroundColor: 'rgba(66, 135, 245, 0.1)',
          borderWidth: 2,
          fill: true,
          tension: 0.4,
          pointRadius: 0,
          pointHoverRadius: 6,
          pointBackgroundColor: '#4287f5'
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: true,
          labels: {
            color: 'rgba(255, 255, 255, 0.7)',
            font: { size: 12 }
          }
        }
      },
      scales: {
        y: {
          min: 0,
          max: 100,
          ticks: { color: 'rgba(255, 255, 255, 0.5)' },
          grid: { color: 'rgba(255, 255, 255, 0.05)' }
        },
        x: {
          ticks: { color: 'rgba(255, 255, 255, 0.5)' },
          grid: { color: 'rgba(255, 255, 255, 0.05)' }
        }
      }
    }
  });
}

/**
 * Initialize disk time series chart
 */
function initDiskTimeSeriesChart() {
  const ctx = document.getElementById('diskTimeSeriesChart');
  if (!ctx) return;

  diskTimeSeriesChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: [],
      datasets: [
        {
          label: 'Active Time (%)',
          data: [],
          borderColor: '#4287f5', 
          backgroundColor: 'rgba(66, 135, 245, 0.1)',
          borderWidth: 2,
          fill: true,
          tension: 0.4,
          pointRadius: 0,
          pointHoverRadius: 6,
          pointBackgroundColor: '#4287f5'
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: { duration: 0 },
      plugins: {
        legend: {
          display: true,
          labels: {
            color: 'rgba(255, 255, 255, 0.7)',
            font: { size: 12 }
          }
        }
      },
      scales: {
        y: {
          min: 0,
          max: 100,
          ticks: { color: 'rgba(255, 255, 255, 0.5)' },
          grid: { color: 'rgba(255, 255, 255, 0.05)' }
        },
        x: {
          display: false,
          grid: { display: false }
        }
      }
    }
  });
}

/**
 * Update battery time series chart
 */
function updateTimeSeriesChart(data) {
  if (!timeSeriesChart || !data.history) return;

  const labels = data.history.map((item, idx) => {
    if (idx % Math.max(1, Math.floor(data.history.length / 10)) === 0) {
      const time = new Date(item.timestamp);
      return time.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    }
    return '';
  });

  const values = data.history.map(item => item.psutil.percent);

  timeSeriesChart.data.labels = labels;
  timeSeriesChart.data.datasets[0].data = values;
  timeSeriesChart.update('none');
}

/**
 * Update disk time series chart
 */
function updateDiskTimeSeriesChart(data) {
  if (!diskTimeSeriesChart || !data.history) return;

  const labels = data.history.map((item, idx) => {
    return ''; // Hide X labels to prevent "jumping" layout
  });

  const values = data.history.map(item => item.active_time || 0);

  diskTimeSeriesChart.data.labels = labels;
  diskTimeSeriesChart.data.datasets[0].data = values;
  diskTimeSeriesChart.update('none');
}

/**
 * Update clock display
 */
function updateClock() {
  const now = new Date();
  const timeString = now.toLocaleTimeString('en-US', {
    hour12: false,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });
  const clockElem = document.getElementById('currentTime');
  if (clockElem) clockElem.textContent = timeString;
}

/**
 * Animate numeric value with easing
 */
function animateValue(elementId, start, end, duration, formatter) {
  const element = document.getElementById(elementId);
  if (!element) return;

  const startTime = performance.now();

  function update(currentTime) {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);

    // Ease-out cubic
    const eased = 1 - Math.pow(1 - progress, 3);
    const current = start + (end - start) * eased;

    element.textContent = formatter ? formatter(current) : current.toFixed(0);

    if (progress < 1) {
      requestAnimationFrame(update);
    }
  }

  requestAnimationFrame(update);
}

/**
 * Initialize neural network background animation
 */
function initNeuralNetwork() {
  const canvas = document.getElementById('neuralNetwork');
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;

  const nodes = [];
  const nodeCount = 30;

  for (let i = 0; i < nodeCount; i++) {
    nodes.push({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      vx: (Math.random() - 0.5) * 0.5,
      vy: (Math.random() - 0.5) * 0.5,
      radius: 2
    });
  }

  function animateNetwork() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Update and draw nodes
    nodes.forEach(node => {
      node.x += node.vx;
      node.y += node.vy;

      // Bounce off edges
      if (node.x < 0 || node.x > canvas.width) node.vx *= -1;
      if (node.y < 0 || node.y > canvas.height) node.vy *= -1;

      // Draw node
      ctx.fillStyle = 'rgba(0, 243, 255, 0.4)';
      ctx.beginPath();
      ctx.arc(node.x, node.y, node.radius, 0, Math.PI * 2);
      ctx.fill();
    });

    // Draw connections
    ctx.strokeStyle = 'rgba(0, 243, 255, 0.1)';
    ctx.lineWidth = 1;

    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const dx = nodes[i].x - nodes[j].x;
        const dy = nodes[i].y - nodes[j].y;
        const distance = Math.sqrt(dx * dx + dy * dy);

        if (distance < 150) {
          ctx.beginPath();
          ctx.moveTo(nodes[i].x, nodes[i].y);
          ctx.lineTo(nodes[j].x, nodes[j].y);
          ctx.stroke();
        }
      }
    }

    requestAnimationFrame(animateNetwork);
  }

  animateNetwork();

  // Handle resize
  window.addEventListener('resize', () => {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
  });
}

// ========================
// History Chart System
// ========================

let historyChart = null;

function initHistoryChart() {
  const ctx = document.getElementById('historyChart');
  if (!ctx || historyChart) return;

  historyChart = new Chart(ctx, {
    type: 'line',
    data: {
      datasets: [{
        label: 'Historical Battery %',
        data: [],
        borderColor: '#b100ff',
        backgroundColor: 'rgba(177, 0, 255, 0.15)',
        borderWidth: 2,
        fill: true,
        tension: 0.4,
        pointRadius: 0,
        pointHoverRadius: 6,
        pointBackgroundColor: '#b100ff',
        pointBorderColor: '#b100ff'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: 'index',
        intersect: false
      },
      plugins: {
        legend: {
          display: true,
          labels: { color: 'rgba(255, 255, 255, 0.7)', font: { size: 12 } }
        },
        tooltip: {
          backgroundColor: 'rgba(15, 15, 35, 0.9)',
          borderColor: 'rgba(177, 0, 255, 0.4)',
          borderWidth: 1,
          titleColor: '#b100ff',
          bodyColor: '#e0e0e0',
          callbacks: {
            title: function (items) {
              if (items.length > 0) {
                const d = new Date(items[0].parsed.x);
                return d.toLocaleString();
              }
              return '';
            },
            label: function (item) {
              return `Battery: ${item.parsed.y.toFixed(1)}%`;
            }
          }
        }
      },
      scales: {
        x: {
          type: 'time',
          time: {
            tooltipFormat: 'PPpp',
            displayFormats: {
              minute: 'HH:mm',
              hour: 'HH:mm',
              day: 'MMM d'
            }
          },
          ticks: { color: 'rgba(255, 255, 255, 0.5)', maxTicksLimit: 12 },
          grid: { color: 'rgba(255, 255, 255, 0.05)' }
        },
        y: {
          min: 0,
          max: 100,
          ticks: { color: 'rgba(255, 255, 255, 0.5)' },
          grid: { color: 'rgba(255, 255, 255, 0.05)' }
        }
      }
    }
  });
}

async function loadHistoryData(hours, startLocal, endLocal) {
  const loading = document.getElementById('historyChartLoading');
  const canvas = document.getElementById('historyChart');

  if (loading) loading.style.display = 'block';
  if (canvas) canvas.style.display = 'none';

  let url = '/battery/history?';
  let chartMin, chartMax;

  // Helper to format Date to local ISO string (without Z)
  const toLocalISO = (d) => new Date(d.getTime() - (d.getTimezoneOffset() * 60000)).toISOString().slice(0, -1);

  if (startLocal && endLocal) {
    url += `start=${encodeURIComponent(startLocal)}&end=${encodeURIComponent(endLocal)}`;
    chartMin = new Date(startLocal).getTime();
    chartMax = new Date(endLocal).getTime();
  } else {
    const now = new Date();
    const start = new Date(now.getTime() - hours * 60 * 60 * 1000);
    url += `start=${encodeURIComponent(toLocalISO(start))}&end=${encodeURIComponent(toLocalISO(now))}`;
    chartMin = start.getTime();
    chartMax = now.getTime();
  }

  try {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();

    if (!historyChart) initHistoryChart();

    // Map to Chart.js {x, y} format
    const points = data.map(row => ({
      x: new Date(row.timestamp),
      y: row.battery_percent
    }));

    historyChart.data.datasets[0].data = points;

    // Force the X-axis to lock to the exact selected time bounds
    if (historyChart.options.scales.x) {
      historyChart.options.scales.x.min = chartMin;
      historyChart.options.scales.x.max = chartMax;
    }

    historyChart.update();

    if (loading) loading.style.display = 'none';
    if (canvas) canvas.style.display = 'block';

    if (points.length === 0 && loading) {
      loading.textContent = 'No data for this range';
      loading.style.display = 'block';
    }
  } catch (err) {
    console.error('History fetch error:', err);
    if (loading) {
      loading.textContent = 'Failed to load history data';
      loading.style.display = 'block';
    }
  }
}

function setupHistoryControls() {
  const rangeButtons = document.querySelectorAll('.range-btn[data-range]');
  const customInputs = document.getElementById('customRangeInputs');
  const applyBtn = document.getElementById('btnApplyCustom');

  rangeButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      // Update active state
      rangeButtons.forEach(b => b.classList.remove('range-active'));
      btn.classList.add('range-active');

      const range = btn.getAttribute('data-range');

      if (range === 'custom') {
        if (customInputs) customInputs.style.display = 'flex';
      } else {
        if (customInputs) customInputs.style.display = 'none';
        loadHistoryData(parseInt(range));
      }
    });
  });

  if (applyBtn) {
    applyBtn.addEventListener('click', () => {
      const startInput = document.getElementById('historyStart');
      const endInput = document.getElementById('historyEnd');
      if (startInput && endInput && startInput.value && endInput.value) {
        // Leave the 'datetime-local' inputs as local naive time strings
        loadHistoryData(null, startInput.value + ':00', endInput.value + ':00');
      }
    });
  }
}

/**
 * Authentication management
 */
async function initAuth() {
  const btnLogout = document.getElementById('btnLogout');
  const userProfile = document.getElementById('userProfile');
  const userAvatar = document.getElementById('userAvatar');
  const userName = document.getElementById('userName');
  
  const landingPage = document.getElementById('landingPage');
  const dashboardApp = document.getElementById('dashboardApp');

  const loginBtn = document.querySelector('.google-signin-btn');

  if (btnLogout) {
    btnLogout.addEventListener('click', (e) => {
      e.preventDefault();
      window.location.href = '/logout';
    });
  }

  // Function to transition from landing to dashboard
  const enterDashboard = (userData) => {
    console.log('🚪 Attempting to enter dashboard...');
    if (landingPage) {
        landingPage.classList.add('hidden');
        landingPage.style.display = 'none'; // Fallback
    }
    if (dashboardApp) {
      dashboardApp.style.display = 'block';
      dashboardApp.classList.add('card-animate');
    }
    startDataSubscriptions();
    console.log('🔓 Dashboard unlocked for:', userData.email);
  };

  try {
    const response = await fetch('/api/me');
    const data = await response.json();

    if (data.logged_in) {
      currentUser = data;
      
      // Update User Identity in UI (but don't switch views yet)
      if (userProfile) userProfile.style.display = 'flex';
      if (userAvatar) userAvatar.src = data.picture;
      if (userName) userName.textContent = data.name;
      
      // Transform Landing Page Button
      const activeLoginBtn = document.querySelector('.google-signin-btn');
      if (activeLoginBtn) {
        activeLoginBtn.innerHTML = `
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right:8px">
            <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4M10 17l5-5-5-5M13.8 12H3"/>
          </svg>
          Enter Dashboard
        `;
        activeLoginBtn.href = "#"; 
        activeLoginBtn.onclick = (e) => {
          e.preventDefault();
          enterDashboard(data);
        };
      }
      
      console.log('👤 Session detected for:', data.email);
    } else {
      currentUser = null;
      if (userProfile) userProfile.style.display = 'none';
      if (landingPage) landingPage.classList.remove('hidden');
      if (dashboardApp) dashboardApp.style.display = 'none';
      console.log('👤 No active session');
    }
  } catch (err) {
    console.error('Auth check error:', err);
  }
}

// Initialize app when DOM is loaded
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initApp);
} else {
  initApp();
}
