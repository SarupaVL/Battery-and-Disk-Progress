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

  // Subscribe to data updates
  dataLoader.subscribeBattery(onBatteryDataUpdate);
  dataLoader.subscribeDisk(onDiskDataUpdate);

  // Start live clock
  updateClock();
  setInterval(updateClock, 1000);

  console.log('✅ Battery & Disk Neural Core initialized');
}

/**
 * Set up tab navigation
 */
function setupTabNavigation() {
  const tabBattery = document.getElementById('tabBattery');
  const tabDisk = document.getElementById('tabDisk');
  const batteryView = document.getElementById('batteryView');
  const diskView = document.getElementById('diskView');

  if (tabBattery) {
    tabBattery.addEventListener('click', () => {
      tabBattery.classList.add('tab-active');
      tabDisk.classList.remove('tab-active');
      batteryView.classList.add('active');
      diskView.classList.remove('active');
    });
  }

  if (tabDisk) {
    tabDisk.addEventListener('click', () => {
      tabDisk.classList.add('tab-active');
      tabBattery.classList.remove('tab-active');
      diskView.classList.add('active');
      batteryView.classList.remove('active');
    });
  }
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
    stop1.setAttribute('stop-color', '#00ff88');
    stop2.setAttribute('stop-color', '#00f3ff');
  } else if (percent >= 30) {
    stop1.setAttribute('stop-color', '#00f3ff');
    stop2.setAttribute('stop-color', '#0066ff');
  } else if (percent >= 15) {
    stop1.setAttribute('stop-color', '#ff9500');
    stop2.setAttribute('stop-color', '#ff6b00');
  } else {
    stop1.setAttribute('stop-color', '#ff0040');
    stop2.setAttribute('stop-color', '#ff006e');
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
    stop1.setAttribute('stop-color', '#ff0040');
    stop2.setAttribute('stop-color', '#ff006e');
  } else if (percent >= 75) {
    stop1.setAttribute('stop-color', '#ff6b00');
    stop2.setAttribute('stop-color', '#ff0080');
  } else if (percent >= 50) {
    stop1.setAttribute('stop-color', '#ff9500');
    stop2.setAttribute('stop-color', '#ff6b00');
  } else {
    stop1.setAttribute('stop-color', '#00f3ff');
    stop2.setAttribute('stop-color', '#00ff88');
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
 * Calculate and update disk analytics
 */
function updateDiskAnalytics(data) {
  if (diskHistory.length < 2) {
    const dailyGrowthElem = document.getElementById('dailyGrowth');
    const timeToFullElem = document.getElementById('timeToFull');
    if (dailyGrowthElem) dailyGrowthElem.textContent = '-- GB/day';
    if (timeToFullElem) timeToFullElem.textContent = '-- days';
    return;
  }

  // Calculate daily growth rate
  const oldest = diskHistory[0];
  const newest = diskHistory[diskHistory.length - 1];
  const timeDiffMs = newest.timestamp - oldest.timestamp;
  const timeDiffHours = timeDiffMs / (1000 * 60 * 60);

  const bytesDelta = newest.usedBytes - oldest.usedBytes;
  const bytesPerHour = bytesDelta / Math.max(timeDiffHours, 0.016);
  const bytesPerDay = bytesPerHour * 24;
  const gbPerDay = bytesPerDay / (1024 ** 3);

  // Calculate time to full
  const totalBytes = data.current.usage.total_bytes;
  const usedBytes = data.current.usage.used_bytes;
  const freeBytes = totalBytes - usedBytes;

  let daysToFull = 999;
  if (bytesPerDay > 0) {
    daysToFull = (freeBytes / (1024 ** 3)) / gbPerDay;
  }

  // Update UI
  const dailyGrowthElem = document.getElementById('dailyGrowth');
  const timeToFullElem = document.getElementById('timeToFull');

  if (dailyGrowthElem) {
    if (gbPerDay > 0) {
      dailyGrowthElem.textContent = gbPerDay.toFixed(2) + ' GB/day';
    } else {
      dailyGrowthElem.textContent = 'Minimal';
    }
  }

  if (timeToFullElem) {
    if (daysToFull < 999) {
      timeToFullElem.textContent = daysToFull.toFixed(1) + ' days';
    } else {
      timeToFullElem.textContent = '> 1 year';
    }
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
        <td>${proc.process_name || 'Unknown'}</td>
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
          borderColor: '#00f3ff',
          backgroundColor: 'rgba(0, 243, 255, 0.1)',
          borderWidth: 2,
          fill: true,
          tension: 0.4,
          pointRadius: 0,
          pointHoverRadius: 6,
          pointBackgroundColor: '#00f3ff'
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
          label: 'Disk Usage %',
          data: [],
          borderColor: '#ff6b00',
          backgroundColor: 'rgba(255, 107, 0, 0.1)',
          borderWidth: 2,
          fill: true,
          tension: 0.4,
          pointRadius: 0,
          pointHoverRadius: 6,
          pointBackgroundColor: '#ff6b00'
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
    if (idx % Math.max(1, Math.floor(data.history.length / 10)) === 0) {
      const time = new Date(item.timestamp);
      return time.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    }
    return '';
  });

  const values = data.history.map(item => item.usage.percent);

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

// Initialize app when DOM is loaded
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initApp);
} else {
  initApp();
}
