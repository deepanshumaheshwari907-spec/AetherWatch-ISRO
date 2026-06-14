# 🛰️ AetherWatch-ISRO: Tropical Cyclone Detection System

A production-ready AI-powered satellite data analysis system for detecting and tracking tropical cyclones using INSAT-3D thermal infrared data.

## 📋 Table of Contents
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [API Documentation](#api-documentation)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)

## ✨ Features

- **🤖 AI-Powered Detection**: U-Net deep learning model with K-Means fallback for cloud detection
- **🗺️ Interactive Maps**: Real-time Folium-based map visualization with threat zones
- **📊 Risk Scoring**: Advanced risk calculation based on temperature and cloud radius
- **💾 Persistent Logging**: SQLite database for threat history and analytics
- **🔌 REST API**: FastAPI backend for programmatic access
- **📱 Streamlit Dashboard**: Interactive web UI for monitoring
- **🐳 Docker Ready**: Complete containerization for cloud deployment
- **🔧 Configuration-Driven**: Environment-based configuration for all deployments

## 🔧 Prerequisites

- Python 3.9 or higher
- pip package manager
- 2GB+ RAM (for satellite data processing)
- CUDA-capable GPU (optional, for faster AI inference)

## 📦 Installation

### 1. Clone/Setup Project
```bash
cd d:\baadal detection
```

### 2. Create Virtual Environment (Optional but Recommended)
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

This will install:
- **streamlit**: Web UI framework
- **fastapi + uvicorn**: REST API backend
- **torch**: Deep learning framework
- **h5py**: HDF5 file support
- **scikit-image, scikit-learn**: Image processing and ML
- **folium**: Map visualization
- **python-dotenv**: Environment configuration
- And all other dependencies

### 4. Verify Installation
```bash
python -c "import torch, streamlit, fastapi; print('✅ All imports successful!')"
```

## ⚙️ Configuration

### 1. Create .env File
```bash
# Copy the example config
copy .env.example .env

# Edit .env with your settings (optional)
# Most settings have sensible defaults
```

### 2. Key Configuration Options
```env
# API Server
API_PORT=8000

# Streamlit Dashboard
STREAMLIT_PORT=8501

# AI Model
USE_GPU=true                    # Set to false if GPU not available

# Risk Detection
THERMAL_THRESHOLD_KELVIN=235

# Database
DATABASE_AUTO_INIT=true

# Feature Flags
ENABLE_ALERTS=true
ENABLE_DATABASE_LOGGING=true
```

## 🚀 Running the Application

### Option 1: Run Both Services (Recommended)

#### Windows
```bash
# Terminal 1: Start API
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Start Dashboard
python -m streamlit run frontend/app.py --server.port 8501
```

#### macOS/Linux
```bash
# Terminal 1: Start API
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Start Dashboard
streamlit run frontend/app.py --server.port 8501
```

### Option 2: Quick Start Script
```bash
# Create a run script (Windows)
@echo off
start python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
start streamlit run frontend/app.py --server.port 8501
```

### Option 3: Docker (Production)
```bash
# Build image
docker build -f backend/Dockerfile -t aetherwatch:latest .

# Run container
docker run -p 8000:8000 -p 8501:8501 aetherwatch:latest
```

## 🌐 Accessing the Application

After startup, access:

1. **Streamlit Dashboard**: http://localhost:8501
   - Interactive map visualization
   - Threat detection and risk scoring
   - Database logging interface
   - Real-time metrics

2. **REST API**: http://localhost:8000
   - API Documentation: http://localhost:8000/api/docs
   - Live Threats: http://localhost:8000/api/v1/threats/live
   - Health Check: http://localhost:8000/health

## 📡 API Documentation

### Health Check
```
GET /health
```
Returns system health status.

### Get Live Threats
```
GET /api/v1/threats/live
```
Returns simulated real-time threat data with AI confidence scores.

### System Configuration
```
GET /api/v1/system/config
```
Returns current system configuration.

**Full interactive API docs available at**: http://localhost:8000/api/docs

## 🐳 Docker Deployment

### Build Docker Image
```bash
docker build -f backend/Dockerfile -t aetherwatch:latest .
```

### Run Docker Container
```bash
docker run -p 8000:8000 -p 8501:8501 aetherwatch:latest
```

### Push to Docker Registry
```bash
docker tag aetherwatch:latest your-registry/aetherwatch:latest
docker push your-registry/aetherwatch:latest
```

## 🆘 Troubleshooting

### Issue: Module Import Errors
```bash
# Reinstall dependencies
pip install --upgrade --force-reinstall -r requirements.txt
```

### Issue: GPU Not Detected
```bash
# Edit .env
USE_GPU=false

# The system will automatically fall back to CPU
```

### Issue: Port Already in Use
```bash
# Change port in .env or command line
streamlit run frontend/app.py --server.port 8502
```

### Issue: Database Errors
```bash
# Reset database
rm data/aetherwatch_telemetry.db

# Re-run app (will auto-initialize)
```

### Issue: Large Memory Usage
- Reduce batch size in config
- Use `USE_GPU=false` to free up VRAM
- Close other applications

## 📊 Project Structure

```
aetherwatch/
├── frontend/              # Streamlit web UI
│   └── app.py
├── backend/               # FastAPI REST server
│   ├── main.py
│   └── Dockerfile
├── core/                  # Core ML/AI modules
│   ├── ai_engine.py       # U-Net & K-Means
│   ├── database.py        # SQLite management
│   ├── risk_engine.py     # Risk calculation
│   ├── insat_reader.py    # Satellite data parsing
│   └── unet_model.py      # Model architecture
├── data/                  # Sample satellite data
│   └── demo_insat.h5
├── config.py              # Configuration manager
├── logger.py              # Logging system
├── requirements.txt       # Python dependencies
├── .env.example           # Config template
└── README.md              # This file
```

## 🔐 Security Notes

- Change `SECRET_KEY` in .env for production
- Enable `ENABLE_AUTH=true` before public deployment
- Use HTTPS/SSL in production
- Regularly update dependencies: `pip list --outdated`

## 📝 Logging

Logs are stored in `logs/aetherwatch.log` with configurable formats:
- JSON format for structured logging
- Console output for real-time monitoring
- Configurable log levels (INFO, DEBUG, ERROR)

## 🤝 Support & Contributions

For issues or improvements, please check:
1. Logs in `logs/aetherwatch.log`
2. Database integrity in `data/aetherwatch_telemetry.db`
3. Configuration in `.env` file

## 📄 License

This project is part of AetherWatch-ISRO initiative.

---

**Status**: ✅ Production Ready
**Last Updated**: 2026-06-11
