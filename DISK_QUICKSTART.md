# Quick Start - Battery & Disk Neural Core

## 🚀 Start the Dashboard

Double-click this file:
```
run_dashboard.bat
```

That's it! The dashboard will:
- ✅ Start collecting battery data
- ✅ Start collecting disk data  
- ✅ Open http://localhost:3000 in your browser

---

## 🎯 What You'll See

### ⚡ Battery View (Default)
- Large gauge showing battery percentage
- System status (CHARGING, DISCHARGING, FULL, LOW POWER)
- Battery health score with capacity info
- Voltage, temperature, power draw, total sessions
- Time-series chart of battery history

Click the **💾 DISK** button to switch to disk monitoring.

### 💾 Disk View
- Large gauge showing disk usage percentage
- Space metrics (total, used, free in GB)
- Disk growth forecast (GB/day and days-to-full)
- I/O rates (read/write speed and operations)
- **Top disk writers** - shows which apps are writing to disk most
- Time-series chart of disk usage history

Click the **⚡ BATTERY** button to go back to battery view.

---

## 📊 Understanding the Metrics

### Battery Metrics
| Metric | Meaning |
|--------|---------|
| **CHARGE** | Current battery percentage (0-100%) |
| **Health Score** | Overall battery condition (design capacity vs current) |
| **Runtime** | Estimated minutes until empty |
| **Voltage** | Current battery voltage in volts |
| **Temperature** | Battery temperature in Celsius |
| **Power Draw** | Current power consumption in watts |

### Disk Metrics
| Metric | Meaning |
|--------|---------|
| **USED %** | Percentage of disk currently in use |
| **Free Space** | GB available before disk is full |
| **Daily Growth** | How much disk usage grows per day |
| **Time to Full** | Days until disk is full at current growth rate |
| **Read Rate** | Speed of reading from disk |
| **Write Rate** | Speed of writing to disk |
| **Read Ops** | Number of read operations per second |
| **Write Ops** | Number of write operations per second |
| **Top Writers** | Which processes are writing most to disk |

---

## 🔄 Auto-Update

Everything updates **automatically every 2 seconds**:
- ✅ Battery percentage
- ✅ Disk usage
- ✅ I/O rates
- ✅ Process activity
- ✅ Charts and history

No manual refresh needed!

---

## 📁 Files

```
c:\projects\SOFTWARE proj progress\
├── battery_service.py          ← Collects battery + disk data
├── server.py                   ← HTTP web server
├── data_loader.js              ← Loads JSON files
├── app.js                       ← Dashboard logic
├── index.html                  ← Dashboard UI
├── style.css                   ← Styling
├── battery_data.json           ← Live battery data (auto-generated)
├── disk_data.json              ← Live disk data (auto-generated)
├── run_dashboard.bat           ← Start everything
└── DISK_EXPANSION_SUMMARY.md   ← Technical details
```

---

## 🛠 Troubleshooting

### Dashboard won't load?
1. Check if both terminal windows are open (Battery Service + Web Server)
2. Open http://localhost:3000 manually in your browser
3. Check the terminal for error messages

### No data showing?
1. Wait 3-5 seconds for initial data collection
2. Check if `battery_data.json` and `disk_data.json` exist in the project folder
3. Refresh the browser (F5 or Cmd+R)

### Data not updating?
1. Check if the Battery Service terminal is still running
2. Check for errors in the terminal window
3. Restart by closing all windows and running `run_dashboard.bat` again

### Python not found?
Install Python from: https://www.python.org/downloads/
- Make sure to check "Add Python to PATH" during installation
- Restart your computer after installing

---

## 💡 Tips

- **Hover over charts** to see exact values
- **Tab switching** is instant (no lag)
- **Process names** in the disk table are the executable names
- **PID** is the process ID (useful for task manager)
- **Growth forecasts** are based on recent history (more accurate with longer tracking)

---

## 📞 Questions?

Everything is documented in:
- `DISK_EXPANSION_SUMMARY.md` - Full technical details
- `README.md` - General information
- `QUICKSTART.md` - Original quick start guide

---

**Enjoy monitoring your system! 🚀**
