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

# 🌟 2. CORE IMPORTS
from core.database import init_db, log_threat_to_db, fetch_telemetry_history
from core.insat_reader import load_tb_lat_lon
from core.ai_engine import detect_and_cluster_clouds
from core.risk_engine import is_valid_tcc
from core.feature_extractor import build_threat_explanation, describe_geographic_context, extract_tcc_features
from core.data_fetcher import fetch_latest_satellite_data

# Initialize Database
init_db()

# ================= HIGH-TECH MISSION CONTROL CONFIG =================
st.set_page_config(page_title="AETHERWATCH: ISRO-INSAT Mission Control", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    .reportview-container { background: #030712; }
    .stMetric { background: #0b1329; border: 1px solid #1f3a60; padding: 15px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,210,255,0.1); }
    div[data-testid="stMetricValue"] { color: #00ffd2; font-family: 'Courier New', monospace; font-weight: 800; font-size: 28px; line-height: 1.1; }
    div[data-testid="stMetricLabel"] { color: #cbd5e1; font-size: 13px; text-transform: uppercase; letter-spacing: 1px; }
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
    default_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'demo_insat.h5'))
    if 'file_to_process' not in st.session_state:
        st.session_state['file_to_process'] = default_file
        st.session_state['data_source'] = "LOCAL_DEMO"

    file_to_process = st.session_state['file_to_process']

    uploaded_file = st.file_uploader("📂 Upload INSAT HDF5 file", type=["h5", "hdf5"], help="Use a real INSAT-style HDF5 matrix for operational analysis.")
    if uploaded_file is not None:
        uploaded_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', uploaded_file.name))
        os.makedirs(os.path.dirname(uploaded_path), exist_ok=True)
        with open(uploaded_path, "wb") as handle:
            handle.write(uploaded_file.getbuffer())
        st.session_state['file_to_process'] = uploaded_path
        st.session_state['data_source'] = f"UPLOADED::{uploaded_file.name}"
        file_to_process = uploaded_path
        st.success(f"Loaded uploaded matrix: {uploaded_file.name}")

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
    st.caption(f"Loaded INSAT File: {os.path.basename(file_to_process)}")
    st.caption(f"Full Path: {file_to_process}")
    if os.path.exists(file_to_process):
        st.caption(f"File Size: {os.path.getsize(file_to_process) / 1024 / 1024:.2f} MB")

# ================= COGNITIVE PROCESSING PIPELINE =================
file_to_process = st.session_state['file_to_process']

if not os.path.exists(file_to_process):
    st.error("❌ CRITICAL: Matrix Data Missing.")
    st.stop()

with st.spinner("⚡ PARSING GEOSTATIONARY PACKETS & RUNNING AI..."):
    Tb, lat, lon = load_tb_lat_lon(file_to_process)
    labeled_image, regions, ai_mask = detect_and_cluster_clouds(Tb, threshold)
    
    results = []
    for r in regions:
        if is_valid_tcc(r):
            feat = extract_tcc_features(r, Tb, lat, lon)
            results.append(feat)

# ================= COMMAND CENTER UI GRID =================
if not results:
    st.success("✅ ZERO THREAT TARGETS DETECTED: Convection patterns normal across tropical tracking swath.")
    st.stop()

df = pd.DataFrame(results).sort_values(by="risk_score", ascending=False).reset_index(drop=True)
visible_df = df.head(12).copy()
summary_df = df[['risk_level', 'risk_score', 'mean_radius_km', 'center_lat', 'center_lon', 'trend']].copy()
summary_df['center_lat'] = summary_df['center_lat'].round(2)
summary_df['center_lon'] = summary_df['center_lon'].round(2)
summary_df['mean_radius_km'] = summary_df['mean_radius_km'].round(1)
summary_df['risk_score'] = summary_df['risk_score'].round(1)
highest_threat = df.iloc[0]

# 🌟 AUTOMATED ALERTING SYSTEM (Enterprise feature)
severity = highest_threat['risk_level']
if severity == "Extreme":
    alert_color = "error"
    alert_text = "🚨 CRITICAL ALERT: Extreme convective core detected. Immediate monitoring and response coordination are recommended."
elif severity == "High":
    alert_color = "warning"
    alert_text = "⚠️ HIGH THREAT: Large storm-forming cluster active. Continue monitoring and validate the latest satellite feed."
else:
    alert_color = "info"
    alert_text = "ℹ️ WATCH STATUS: Moderate thermal anomaly detected. The system is tracking the current convective pattern."

geo_context = describe_geographic_context(highest_threat['center_lat'], highest_threat['center_lon'])
threat_explanation = build_threat_explanation(highest_threat)

getattr(st, alert_color)(
    f"{alert_text}\n\n"
    f"INSAT hotspot coordinates: {highest_threat['center_lat']:.2f}°N, {highest_threat['center_lon']:.2f}°E | "
    f"Risk score: {highest_threat['risk_score']:.1f}% | "
    f"Trend: {highest_threat['trend']} | "
    f"Estimated core radius: {highest_threat['mean_radius_km']:.1f} km"
)

with st.expander("🧭 Threat briefing", expanded=True):
    st.write(
        "This panel summarizes the most significant cyclone-like thermal anomaly currently detected. "
        "The score combines core temperature and storm area to help prioritize monitoring attention."
    )
    st.caption(
        f"Top threat vector from the current INSAT matrix: {severity} ({highest_threat['risk_score']:.1f}%) | "
        f"Mean brightness temperature: {highest_threat['mean_tb']:.1f} K | "
        f"Minimum core temperature: {highest_threat['min_tb']:.1f} K"
    )
    st.info(geo_context)
    st.caption(threat_explanation)
    st.caption("Actual hotspot location is derived from the loaded INSAT file and shown in the map and summary cards.")
    st.dataframe(summary_df.head(8), use_container_width=True, hide_index=True)

    csv_bytes = summary_df.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Export threat summary CSV", data=csv_bytes, file_name="threat_summary.csv", mime="text/csv")

# Metrics
m1, m2, m3, m4 = st.columns(4)
m1.metric("TRACKED THREAT VECTORS", len(df))
st.caption(f"Showing top {len(visible_df)} of {len(df)} hotspot clusters on the live map for faster rendering.")
m2.metric("PEAK INTENSITY SCORE", f"{highest_threat['risk_score']}%")
m3.metric("CRITICAL CORE TEMP", f"{highest_threat['min_tb']:.1f} K")
m4.metric("MAX AREA EXPORT RADIUS", f"{highest_threat['mean_radius_km']:.1f} KM")
st.markdown("---")

# Visuals
col_left, col_right = st.columns([3, 2])

with col_left:
    st.markdown("<h4 style='color:#ffffff; font-family:monospace;'>🗺️ TROPICAL TRACKING SURFACE</h4>", unsafe_allow_html=True)
    st.caption("Legend: red = Extreme, orange = High, yellow = Medium, green = Low/normal convection. Hotspot size now reflects intensity and area.")
    m = folium.Map(location=[highest_threat['center_lat'], highest_threat['center_lon']], zoom_start=4, tiles="CartoDB dark_matter", control_scale=True)
    folium.TileLayer('OpenStreetMap', opacity=0.35).add_to(m)
    for _, row in visible_df.iterrows():
        color = "#ef4444" if row["risk_level"] == "Extreme" else "#f97316" if row["risk_level"] == "High" else "#eab308" if row["risk_level"] == "Medium" else "#22c55e"
        radius_km = max(40.0, row["mean_radius_km"] * 1.4 + row["risk_score"] * 10.0)
        popup_html = f"""
        <div style='font-family:Segoe UI, sans-serif; color:#0f172a; line-height:1.3;'>
          <b>{row['risk_level']} Threat</b><br>
          Intensity Score: <b>{row['risk_score']:.1f}%</b><br>
          Trend: <b>{row['trend']}</b><br>
          Radius: <b>{row['mean_radius_km']:.1f} km</b><br>
          Location: <b>{row['center_lat']:.2f}°N, {row['center_lon']:.2f}°E</b>
        </div>
        """
        folium.Circle(
            location=[row["center_lat"], row["center_lon"]],
            radius=radius_km * 1000,
            color=color,
            weight=3,
            fill=True,
            fill_color=color,
            fill_opacity=0.28,
            tooltip=f"{row['risk_level']} • {row['risk_score']:.1f}% • {row['trend']}",
            popup=folium.Popup(popup_html, max_width=260),
        ).add_to(m)
        folium.CircleMarker(location=[row["center_lat"], row["center_lon"]], radius=8, color="#ffffff", fill=True, fill_color=color, fill_opacity=0.95, weight=2).add_to(m)
    st_folium(m, width='100%', height=460, returned_objects=[])

with col_right:
    st.markdown("<h4 style='color:#ffffff; font-family:monospace;'>� THREAT SUMMARY</h4>", unsafe_allow_html=True)
    st.info("This panel shows the strongest hotspot summary only. The map renders the top clusters for faster live performance.")
    st.metric("Highest intensity", f"{highest_threat['risk_score']:.1f}%")
    st.metric("Dominant trend", highest_threat['trend'])
    st.metric("Current severity", severity)
    st.metric("Main location", f"{highest_threat['center_lat']:.2f}°N, {highest_threat['center_lon']:.2f}°E")

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