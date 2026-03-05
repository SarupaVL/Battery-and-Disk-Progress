# Battery Neural Core & Predictive Analytics - Windows Edition

A complete, end-to-end Windows battery telemetry pipeline. It silently tracks your battery health in the background and uses a Machine Learning model (Random Forest Regressor trained on NASA Datasets) to predict your battery's risk of failure and degradation rate.

## ⚡ Quick Start (Manual)
**Double-click:** `run_dashboard.bat`
The telemetry logger will start and open your dashboard at `http://localhost:3000`.

## 🔋 Persistent Telemetry (Automatic)
To build historical data and predict long-term degradation, the logger needs to run constantly. 
**Double-click:** `install_service.bat`
This will automatically register the python `battery_service.py` script to boot silently every time you turn on your Windows laptop. You never have to think about it again. Just open `http://localhost:3000` whenever you want to check your battery health!

## 📁 Key Files

| File | Purpose |
|------|---------|
| `run_dashboard.bat` | Starts the logger and server manually |
| `install_service.bat` | Installs the logger as an invisible Windows Startup task |
| `battery_service.py` | Core telemetry engine - collects psutil battery data every 2s |
| `battery_analytics.py` | Feeds live telemetry into the Random Forest `.joblib` ML model |
| `server.py` | Web API Server (Handles History range queries & CSV exports) |
| `index.html` & `app.js`| Real-time Glassmorphism Dashboard UI |

## 🧠 Machine Learning Integration
The backend utilizes the `battery_rf_model.joblib` to calculate a live **Predictive Risk Score**.
- **Inputs:** Current voltage, temperature proxy, capacity loss, and drain speed.
- **Output:** A dynamically calculating 0-100 Risk Index predicting short-term failure or high-temperature degradation limits. 
- *Note: Machine Learning Models are excluded from Github!* To train your own model from scratch, run `local_train_rf.py` or use the Colab notebook version.

## 📊 Features

✅ **Live Time Series:** Sub-second glowing chart tracking current voltage and drain.
✅ **Historical Data Querying:** Explore past days of battery drain performance with custom time bounds.
✅ **Predictive Maintenance:** Live ML Risk Score.
✅ **Charging Analytics:** Tracks exactly how long your laptop has been plugged in at >90% (which accelerates chemical degradation).
✅ **Auto-Startup Persistence:** Set-It-And-Forget-It Windows `.vbs` launcher.
✅ **Dark Mode Neural Net UX.**

---

**Windows only** - No dependencies except `Python`, `psutil`, `scikit-learn`, and `joblib`.
