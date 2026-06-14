# 🚀 AetherWatch Quick Start Guide

**Status**: ✅ All systems operational and ready for launch!

---

## 🎯 What You Have

You now have a **production-ready tropical cyclone detection system** that:
- ✅ Detects & tracks storm formations using satellite data
- ✅ Uses AI (U-Net + K-Means) for intelligent cloud analysis
- ✅ Provides real-time risk scoring and alerts
- ✅ Has a beautiful interactive dashboard
- ✅ Includes a professional REST API
- ✅ Stores threat history in a database
- ✅ Is fully containerized for deployment

---

## 🏃 FASTEST WAY TO LAUNCH (Windows)

### 1. Double-Click to Start Everything
```
Double-click: START_AETHERWATCH.bat
```

That's it! This will:
- Open a new window for the **API Server** (port 8000)
- Open a new window for the **Dashboard** (port 8501)
- Wait for both services to be ready

### 2. Access Your System
Once running, automatically open:
- **Dashboard**: http://localhost:8501
- **API Docs**: http://localhost:8000/api/docs

---

## 🐧 Quick Start (macOS/Linux)

```bash
chmod +x start_aetherwatch.sh
./start_aetherwatch.sh
```

Then visit:
- **Dashboard**: http://localhost:8501
- **API Docs**: http://localhost:8000/api/docs

---

## 📖 Manual Start (If Script Doesn't Work)

### Terminal 1: Start API Backend
```bash
cd d:\baadal detection
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

Expected output:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

### Terminal 2: Start Dashboard
```bash
cd d:\baadal detection
python -m streamlit run frontend/app.py --server.port 8501
```

Expected output:
```
You can now view your Streamlit app in your browser.
Local URL: http://localhost:8501
```

---

## 🎮 Using the Dashboard

Once you see the dashboard at http://localhost:8501:

1. **Adjust Thermal Threshold** (sidebar)
   - Slider to control cloud detection sensitivity
   - Default: 235K (good for cyclones)

2. **Click "FETCH LIVE SATELLITE DATA"** (sidebar)
   - Loads latest satellite imagery
   - Shows status (LIVE_STREAM or FALLBACK_DEMO)

3. **View Threat Map**
   - Interactive map showing detected storm zones
   - Red = Extreme, Orange = High, Yellow = Medium, Green = Low

4. **Monitor Metrics**
   - Number of threats tracked
   - Peak intensity score
   - Temperature readings
   - Storm size estimates

5. **Save to Database**
   - Click "COMMIT LOGS TO CLOUD DB"
   - Historical data persists for analysis

---

## 🔌 Using the REST API

### Check System Health
```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-06-11T10:32:14.612619",
  "message": "AetherWatch system is operational"
}
```

### Get Live Threats
```bash
curl http://localhost:8000/api/v1/threats/live
```

Response:
```json
{
  "timestamp": "2026-06-11T10:32:14.612619",
  "sensor": "INSAT-3D IMG_TIR1",
  "ai_confidence_score": 95.3,
  "active_anomalies": 1,
  "critical_metrics": {
    "min_temperature_kelvin": 205.34,
    "estimated_radius_km": 87.5,
    "risk_level": "SEVERE"
  },
  "recommended_action": "Dispatch automated alerts to coastal authorities."
}
```

### Interactive API Documentation
Open: http://localhost:8000/api/docs
- Try out all endpoints
- See request/response examples
- Auto-generated OpenAPI spec

---

## 📊 Project Structure Recap

```
aetherwatch/
│
├── 📁 frontend/              ← Streamlit Dashboard
│   └── app.py               (Interactive web UI)
│
├── 📁 backend/              ← FastAPI Server
│   ├── main.py              (REST API endpoints)
│   └── Dockerfile           (Container config)
│
├── 📁 core/                 ← AI & Processing
│   ├── ai_engine.py         (U-Net + K-Means)
│   ├── risk_engine.py       (Threat scoring)
│   ├── insat_reader.py      (Satellite data)
│   ├── database.py          (Data persistence)
│   └── unet_model.py        (Deep learning model)
│
├── 📁 data/                 ← Sample Satellite Data
│   └── demo_insat.h5        (Test file)
│
├── 📁 logs/                 ← Application Logs
│   └── aetherwatch.log      (Auto-created)
│
├── config.py                (Environment settings)
├── logger.py                (Logging system)
├── .env                     (Configuration file)
├── requirements.txt         (Python dependencies)
├── START_AETHERWATCH.bat    (Windows launcher)
└── start_aetherwatch.sh     (Linux/Mac launcher)
```

---

## 🆘 Quick Troubleshooting

### Problem: "Port 8501 already in use"
**Solution**: 
```bash
# Use different port
streamlit run frontend/app.py --server.port 8502
```

### Problem: "Module not found" errors
**Solution**:
```bash
# Reinstall all dependencies
pip install --upgrade -r requirements.txt
```

### Problem: GPU memory errors
**Solution**: Edit `.env` file:
```env
USE_GPU=false
```
System will use CPU automatically.

### Problem: "Matrix data file not found"
**Solution**: 
```bash
# Check file exists in data folder
ls data/demo_insat.h5
# If missing, extract from backup or use online fetch
```

---

## 🚀 Deployment Options

### 🐳 Option 1: Docker (Production Recommended)
```bash
# Build container
docker build -f backend/Dockerfile -t aetherwatch:latest .

# Run container
docker run -p 8000:8000 -p 8501:8501 aetherwatch:latest
```

### ☁️ Option 2: Cloud Deployment (AWS/Azure/GCP)
All services containerized and ready for:
- Kubernetes (AKS, EKS, GKE)
- Container Services (Fargate, Cloud Run, etc.)
- App Services (with Docker support)

### 🖥️ Option 3: Systemd Service (Linux Production)
Create `/etc/systemd/system/aetherwatch.service`:
```ini
[Unit]
Description=AetherWatch Satellite Detection System
After=network.target

[Service]
Type=simple
User=aetherwatch
WorkingDirectory=/opt/aetherwatch
ExecStart=/usr/bin/python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl start aetherwatch
sudo systemctl enable aetherwatch
```

---

## ✅ System Verification Checklist

Before deployment, verify:

- [ ] Dashboard loads at http://localhost:8501
- [ ] API responds at http://localhost:8000/health
- [ ] Database initialized in `data/` folder
- [ ] Model weights loaded from `core/unet_trained_weights.pth`
- [ ] Logs appearing in `logs/aetherwatch.log`
- [ ] Map visualization working
- [ ] Risk scores calculated correctly
- [ ] Database logging functional

---

## 📚 Key Features Explanation

### 1. **AI Cloud Detection**
- Primary: U-Net deep learning model
- Fallback: K-Means clustering (if GPU fails)
- Automatically switches if model loading fails

### 2. **Risk Scoring Algorithm**
```
Risk Score = (60% × Temperature Score) + (40% × Size Score)

Temperature Score: Based on thermal IR brightness
Size Score: Based on cloud area coverage
```

### 3. **Risk Levels**
- 🔴 **Extreme** (≥85): Potential cyclone
- 🟠 **High** (60-85): Strong storm
- 🟡 **Medium** (30-60): Moderate threat
- 🟢 **Low** (<30): Normal conditions

### 4. **Database Logging**
- Automatic threat tracking
- Historical analytics
- Trend analysis (Intensifying/Stable/Weakening)

---

## 📞 Support Resources

1. **Check Logs**:
   ```bash
   tail -f logs/aetherwatch.log
   ```

2. **API Documentation**:
   - http://localhost:8000/api/docs (Swagger UI)
   - http://localhost:8000/api/redoc (ReDoc)

3. **Configuration**:
   - Edit `.env` file for all settings
   - Changes take effect on next restart

4. **Data Issues**:
   - Sample data: `data/demo_insat.h5`
   - Database: `data/aetherwatch_telemetry.db`

---

## 🎉 You're Ready!

Your AetherWatch system is fully configured and ready to:
- ✅ Launch immediately
- ✅ Process satellite data
- ✅ Detect cyclones
- ✅ Track threats
- ✅ Serve REST API
- ✅ Store history
- ✅ Deploy to production

**Happy monitoring! 🛰️**

---

**Last Updated**: 2026-06-11  
**Status**: Production Ready ✅  
**Version**: 1.0.0
