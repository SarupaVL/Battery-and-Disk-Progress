# Battery Neural Core - Windows Edition

A real-time battery analytics dashboard that shows actual Windows battery data.

## ⚡ Quick Start

**Double-click:** `run_dashboard.bat`

That's it! The dashboard opens at `http://localhost:3000` with real battery data.

## 📁 Files

| File | Purpose |
|------|---------|
| `run_dashboard.bat` | Start everything (launcher) |
| `battery_service.py` | Background service - collects battery data |
| `server.py` | Web server - serves the dashboard |
| `battery_data.json` | Real-time battery data (auto-updated) |
| `index.html` | Dashboard UI |
| `app.js` | Dashboard logic & animations |
| `data_loader.js` | Loads data from JSON file |
| `style.css` | Dashboard styling |

## 🎯 How It Works

1. **`battery_service.py`** runs in background
   - Reads Windows battery info via psutil
   - Updates `battery_data.json` every 2 seconds

2. **`server.py`** serves the web dashboard
   - Opens on `http://localhost:3000`

3. **Browser** loads and displays
   - Reads `battery_data.json` continuously
   - Shows real battery data with animations

## 🛑 Stop

Close the two command windows to stop.

## ⚙️ Manual Start (if needed)

```powershell
# Terminal 1
python battery_service.py

# Terminal 2 (in same folder)
python server.py 3000

# Then open browser
http://localhost:3000
```

## 📊 Features

✅ Real Windows battery percentage  
✅ Charging/discharging status  
✅ Battery health score  
✅ Voltage, temperature, power draw  
✅ 30+ point historical chart  
✅ Live updates every 2 seconds  
✅ Animated neural network background  

---

**Windows only** - No dependencies except Python + psutil

Enjoy! ⚡
