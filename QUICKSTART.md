# Quick Start - Windows Only

## 🚀 One-Click Start

**Double-click:** `run_dashboard.bat`

That's it! Your dashboard will automatically:
1. Start the battery service (writes to `battery_data.json`)
2. Start the web server (serves dashboard on localhost:3000)
3. Open your browser

---

## Manual Start (If Needed)

### Terminal 1 - Start Battery Service
```
python battery_service.py
```

### Terminal 2 - Start Web Server
```
python server.py 3000
```

Then open: **http://localhost:3000**

---

## How It Works

- **`battery_service.py`** - Runs in background, collects Windows battery data, writes to `battery_data.json` every 2 seconds
- **`server.py`** - Simple web server that serves the dashboard HTML/CSS/JS
- **`data_loader.js`** - JavaScript that reads `battery_data.json` and updates the UI
- **`battery_data.json`** - Real-time battery data file (auto-generated)

---

## All Features Working

✅ Real battery percentage  
✅ Charging status  
✅ Battery health  
✅ Voltage, temperature, power draw  
✅ Historical data (30+ points)  
✅ Live updates every 2 seconds  

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Python not found" | Install from https://www.python.org/ |
| Dashboard shows "--" | Wait 3 seconds, or check browser console |
| Port 3000 in use | Run: `python server.py 8080` |
| Data not updating | Make sure `battery_service.py` is running |

---

**Windows only - no Mac/Linux support**
