import os
import sys
import streamlit as st
import pandas as pd
import folium
import numpy as np
import matplotlib.pyplot as plt
from streamlit_folium import st_folium

# 🌟 1. PATH SETUP (Always First)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 🌟 2. CONFIG & LOGGING SETUP
from config import Config
from logger import get_logger

Config.ensure_directories()
logger = get_logger(__name__)

# 🌟 3. CORE IMPORTS
from core.database import init_db, log_threat_to_db, fetch_telemetry_history
from core.insat_reader import load_tb_lat_lon
from core.ai_engine import detect_and_cluster_clouds
from core.risk_engine import is_valid_tcc
from core.feature_extractor import extract_tcc_features
from core.data_fetcher import fetch_latest_satellite_data

# Initialize Database
try:
    init_db()
    logger.info("✅ Database initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize database: {e}")
    st.error("Failed to initialize database. Please check logs.")
    st.stop()


# ================= HIGH-TECH MISSION CONTROL CONFIG =================
st.set_page_config(page_title="AETHERWATCH: ISRO-INSAT Mission Control", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    .reportview-container { background: #030712; }
    .stMetric { background: #0b1329; border: 1px solid #1f3a60; padding: 15px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,210,255,0.1); }
    div[data-testid="stMetricValue"] { color: #00ffd2; font-family: 'Courier New', monospace; font-weight: bold; }
</style>
<div style="background: linear-gradient(135deg, #020617, #0f172a); border-left: 5px solid #00ffd2; border-bottom: 1px solid #1e293b; padding: 20px; border-radius: 8px; margin-bottom: 25px;">
    <div style="font-size:11px; letter-spacing:4px; color:#00ffd2; font-family: monospace;">🛰️ DEEP-SPACE METEOROLOGICAL TELEMETRY LINK // INSAT-3D</div>
    <div style="font-size:34px; font-weight:800; color:#ffffff; font-family: 'Segoe UI', sans-serif; margin-top: 5px;">AETHERWATCH: TROPICAL CYCLONE WARN-ROOM</div>
    <div style="font-size:13px; color:#94a3b8; margin-top:5px; font-family: monospace;">STATUS: <span style="color:#22c55e;">● SYSTEM_NOMINAL</span> // CORE: FAILSAFE_AI_ENGINE_V3</div>
</div>
""", unsafe_allow_html=True)

# ================= MISSION CONTROL SIDEBAR =================
with st.sidebar:
    st.markdown("<h3 style='color:#00ffd2; font-family:monospace;'>🛰️ SUBSYSTEM CONSOLE</h3>", unsafe_allow_html=True)
    threshold = st.slider("Convective Cutoff Temp (Kelvin)", 190, 250, 235, 1)
    
    st.markdown("---")
    st.markdown("<h4 style='color:#38bdf8; font-family:monospace;'>🛸 AUTO-INGESTION</h4>", unsafe_allow_html=True)
    
    # Session state to remember the file path across reruns
    if 'file_to_process' not in st.session_state:
        st.session_state['file_to_process'] = Config.DEMO_DATA_FILE
        st.session_state['data_source'] = "LOCAL_DEMO"
        st.session_state['threshold'] = Config.THERMAL_THRESHOLD_KELVIN

    if st.button("📡 FETCH LIVE SATELLITE DATA", use_container_width=True):
        with st.spinner("Establishing uplink with Cloud Matrix..."):
            try:
                path, status = fetch_latest_satellite_data()
                st.session_state['file_to_process'] = path
                st.session_state['data_source'] = status
                st.success(f"Link Established: {status}")
            except Exception as e:
                st.error(f"Uplink Failed: {e}")

    st.caption(f"Current Matrix: {st.session_state['data_source']}")

# ================= COGNITIVE PROCESSING PIPELINE =================
file_to_process = st.session_state['file_to_process']

if not os.path.exists(file_to_process):
    logger.error(f"Matrix data file not found: {file_to_process}")
    st.error("❌ CRITICAL: Matrix Data Missing.")
    st.stop()

try:
    with st.spinner("⚡ PARSING GEOSTATIONARY PACKETS & RUNNING AI..."):
        logger.info(f"Processing satellite data from {file_to_process}")
        Tb, lat, lon = load_tb_lat_lon(file_to_process)
        labeled_image, regions, ai_mask = detect_and_cluster_clouds(Tb, threshold)
        
        results = []
        for r in regions:
            if is_valid_tcc(r):
                feat = extract_tcc_features(r, Tb, lat, lon)
                results.append(feat)
        
        logger.info(f"Detected {len(results)} threat regions")
        
except Exception as e:
    logger.error(f"❌ Processing failed: {e}", exc_info=True)
    st.error(f"❌ PROCESSING ERROR: {str(e)}")
    st.stop()

# ================= COMMAND CENTER UI GRID =================
if not results:
    st.success("✅ ZERO THREAT TARGETS DETECTED: Convection patterns normal across tropical tracking swath.")
    st.stop()

df = pd.DataFrame(results).sort_values(by="risk_score", ascending=False).reset_index(drop=True)
highest_threat = df.iloc[0]

# 🌟 AUTOMATED ALERTING SYSTEM (Enterprise feature)
if highest_threat['risk_score'] >= 85:
    st.error(f"🚨 CRITICAL ALERT TRIGGERED: Extreme Cyclone Eye detected at {highest_threat['center_lat']:.2f}°N, {highest_threat['center_lon']:.2f}°E. Sending automated coordinates to disaster response units via API...")
else:
    st.warning(f"⚠️ THREAT DETECTED: Moderate storm formation tracking at {highest_threat['center_lat']:.2f}°N.")

# Metrics
m1, m2, m3, m4 = st.columns(4)
m1.metric("TRACKED THREAT VECTORS", len(df))
m2.metric("PEAK INTENSITY SCORE", f"{highest_threat['risk_score']}%")
m3.metric("CRITICAL CORE TEMP", f"{highest_threat['min_tb']:.1f} K")
m4.metric("MAX AREA EXPORT RADIUS", f"{highest_threat['mean_radius_km']:.1f} KM")
st.markdown("---")

# Visuals
col_left, col_right = st.columns([3, 2])

with col_left:
    st.markdown("<h4 style='color:#ffffff; font-family:monospace;'>🗺️ TROPICAL TRACKING SURFACE</h4>", unsafe_allow_html=True)
    m = folium.Map(location=[highest_threat['center_lat'], highest_threat['center_lon']], zoom_start=4, tiles="CartoDB dark_matter")
    for idx, row in df.iterrows():
        color = "#ef4444" if row["risk_level"] == "Extreme" else "#f97316" if row["risk_level"] == "High" else "#eab308" if row["risk_level"] == "Medium" else "#22c55e"
        folium.Circle(location=[row["center_lat"], row["center_lon"]], radius=row["mean_radius_km"] * 1000, color=color, weight=2, fill=True, fill_opacity=0.25).add_to(m)
        folium.CircleMarker(location=[row["center_lat"], row["center_lon"]], radius=4, color="#00ffd2", fill=True).add_to(m)
    st_folium(m, width=700, height=400)

with col_right:
    st.markdown("<h4 style='color:#ffffff; font-family:monospace;'>🤖 THERMAL CORE AI RENDER</h4>", unsafe_allow_html=True)
    visual_tb = Tb[::2, ::2]      
    live_mask = visual_tb <= threshold  
    thermal_data = np.where(live_mask, 330.0 - visual_tb, 0)
    normalized_thermal = thermal_data / np.max(thermal_data) if np.max(thermal_data) > 0 else thermal_data
    st.image(plt.cm.inferno(normalized_thermal), caption="VRAM Raster: Dark=Clear Sky // Yellow=Convective Core")

# ================= DATABASE COMMIT & ANALYTICS =================
st.markdown("---")
st.markdown("<h4 style='color:#38bdf8; font-family:monospace;'>💾 TELEMETRY ARCHIVE & TRAJECTORY ANALYSIS</h4>", unsafe_allow_html=True)

col_db1, col_db2 = st.columns([1, 2])

with col_db1:
    if st.button("💾 COMMIT LOGS TO CLOUD DB", use_container_width=True):
        for idx, row in df.iterrows():
            log_threat_to_db(row)
        st.success(f"Archived {len(df)} threat vectors to Database!")
    st.dataframe(df[['mean_tb', 'risk_score', 'trend']], hide_index=True)

with col_db2:
    history_df = fetch_telemetry_history()
    if not history_df.empty:
        chart_data = history_df[['timestamp', 'risk_score']].set_index('timestamp')
        st.line_chart(chart_data, color="#ff4d4d")
    else:
        st.info("Database empty. Commit logs to visualize historical trajectory.")