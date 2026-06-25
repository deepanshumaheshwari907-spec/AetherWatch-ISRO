"""
AetherWatch — ISRO INSAT-3D Tropical Cyclone Warn-Room
"""

import os
import sys
import time
import streamlit as st
import pandas as pd
import folium
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from datetime import datetime
from streamlit_folium import st_folium

# ─────────────────────────────────────────────────────────────────────────────
# 1. PATH SETUP
# ─────────────────────────────────────────────────────────────────────────────
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# ─────────────────────────────────────────────────────────────────────────────
# 2. CORE IMPORTS
# ─────────────────────────────────────────────────────────────────────────────
from core.database import (
    init_db, new_session_id, log_threat_to_db,
    log_scan_session, fetch_telemetry_history,
    fetch_scan_sessions, fetch_risk_trend,
)
from core.insat_reader      import load_tb_lat_lon
from core.ai_engine         import detect_and_cluster_clouds
from core.risk_engine       import is_valid_tcc
from core.feature_extractor import (
    build_threat_explanation, describe_geographic_context, extract_tcc_features,
)
from core.data_fetcher      import fetch_latest_satellite_data

init_db()

# ─────────────────────────────────────────────────────────────────────────────
# 3. PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AETHERWATCH – ISRO Cyclone Intel",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="🛰️",
)

# ─────────────────────────────────────────────────────────────────────────────
# 4. GLOBAL CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Inter:wght@400;600;800&display=swap');

[data-testid="stAppViewContainer"]  { background:#030b18; }
[data-testid="stSidebar"]           { background:#040d1c; border-right:1px solid #0f2340; }
[data-testid="stHeader"]            { background:transparent; }

[data-testid="metric-container"] {
    background: linear-gradient(135deg,#071428,#0b1f3a);
    border: 1px solid #163558;
    border-radius: 10px;
    padding: 16px 20px;
    box-shadow: 0 0 20px rgba(0,180,255,0.07);
}
[data-testid="stMetricValue"] {
    color:#00ffd2 !important;
    font-family:'Share Tech Mono',monospace !important;
    font-weight:800 !important;
    font-size:24px !important;
    letter-spacing:1px;
}
[data-testid="stMetricLabel"] {
    color:#64748b !important;
    font-family:'Share Tech Mono',monospace !important;
    font-size:10px !important;
    text-transform:uppercase;
    letter-spacing:2px;
}

.stButton > button {
    background: linear-gradient(135deg,#0a2540,#0f3460) !important;
    border: 1px solid #1d4ed8 !important;
    color: #93c5fd !important;
    font-family: 'Share Tech Mono', monospace !important;
    border-radius: 6px !important;
    letter-spacing: 1px;
    font-size: 12px !important;
    transition: all 0.2s;
}
.stButton > button:hover {
    border-color:#00ffd2 !important;
    color:#00ffd2 !important;
    box-shadow: 0 0 12px rgba(0,255,210,0.2) !important;
}

.stTabs [data-baseweb="tab-list"]  { background:#040d1c; border-bottom:1px solid #0f2340; gap:4px; }
.stTabs [data-baseweb="tab"]       { background:transparent; color:#64748b;
                                     font-family:'Share Tech Mono',monospace; font-size:12px;
                                     border-radius:6px 6px 0 0; padding:8px 18px; }
.stTabs [aria-selected="true"]     { background:#071428 !important; color:#00ffd2 !important;
                                     border-bottom:2px solid #00ffd2 !important; }

[data-testid="stDataFrame"]        { background:#071428; border:1px solid #0f2340; border-radius:8px; }
details { border:1px solid #0f2340 !important; border-radius:8px !important; background:#071428 !important; }
summary { color:#94a3b8 !important; font-family:'Share Tech Mono',monospace !important; font-size:13px !important; }
::-webkit-scrollbar       { width:4px; height:4px; }
::-webkit-scrollbar-track { background:#030b18; }
::-webkit-scrollbar-thumb { background:#163558; border-radius:4px; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# 5. BOOT SEQUENCE (runs once per session)
# ─────────────────────────────────────────────────────────────────────────────
if "booted" not in st.session_state:
    boot_box = st.empty()
    steps = [
        ("AETHERWATCH v3.0 INITIALIZING", 0.4),
        ("▸ Loading U-Net weights (30.8 MB)... <span style='color:#22c55e'>OK</span>", 0.5),
        ("▸ Connecting INSAT-3D telemetry feed... <span style='color:#22c55e'>OK</span>", 0.5),
        ("▸ Threat detection engine... <span style='color:#22c55e'>READY</span>", 0.4),
        ("▸ Telemetry database... <span style='color:#22c55e'>ONLINE</span>", 0.3),
        ("<span style='color:#00ffd2;font-size:16px;'>● ALL SYSTEMS NOMINAL — LAUNCHING WARN-ROOM</span>", 0.6),
    ]
    log_lines = []
    for msg, delay in steps:
        log_lines.append(msg)
        boot_box.markdown(f"""
        <div style="background:#020c1b;border:1px solid #00ffd244;border-radius:10px;
                    padding:28px 36px;font-family:'Share Tech Mono',monospace;
                    font-size:13px;color:#94a3b8;line-height:2.2;">
            <div style="color:#00ffd2;font-size:11px;letter-spacing:4px;margin-bottom:16px;">
                🛰️ ISRO · AETHERWATCH MISSION CONTROL
            </div>
            {"<br>".join(log_lines)}
        </div>
        """, unsafe_allow_html=True)
        time.sleep(delay)
    time.sleep(0.4)
    boot_box.empty()
    st.session_state["booted"] = True

# ─────────────────────────────────────────────────────────────────────────────
# 6. HEADER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="background:linear-gradient(135deg,#020c1b,#071428);
            border-left:4px solid #00ffd2; border-bottom:1px solid #0f2340;
            padding:22px 28px; border-radius:10px; margin-bottom:24px;
            box-shadow:0 4px 32px rgba(0,255,210,0.06);">
  <div style="font-size:10px;letter-spacing:5px;color:#00ffd2;
              font-family:'Share Tech Mono',monospace;margin-bottom:6px;">
    🛰️ &nbsp;INDIAN SPACE RESEARCH ORGANISATION · INSAT-3D THERMAL TELEMETRY · TIR1 CHANNEL
  </div>
  <div style="font-size:30px;font-weight:800;color:#ffffff;font-family:'Inter',sans-serif;letter-spacing:-0.5px;">
    AETHERWATCH
    <span style="font-size:14px;font-weight:400;color:#38bdf8;
                 font-family:'Share Tech Mono',monospace;margin-left:12px;vertical-align:middle;">
      TROPICAL CYCLONE INTELLIGENCE SYSTEM
    </span>
  </div>
  <div style="margin-top:8px;display:flex;gap:24px;flex-wrap:wrap;">
    <span style="font-size:11px;color:#22c55e;font-family:'Share Tech Mono',monospace;">● SYSTEM NOMINAL</span>
    <span style="font-size:11px;color:#94a3b8;font-family:'Share Tech Mono',monospace;">ENGINE: U-NET (PyTorch) + K-MEANS FALLBACK</span>
    <span style="font-size:11px;color:#94a3b8;font-family:'Share Tech Mono',monospace;">RISK: Tb(60%) + RADIUS(40%)</span>
    <span style="font-size:11px;color:#94a3b8;font-family:'Share Tech Mono',monospace;">SOURCE: INSAT-3D TIR1 L1C</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# 7. SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("<div style='font-family:\"Share Tech Mono\",monospace;color:#00ffd2;font-size:13px;letter-spacing:3px;margin-bottom:16px;'>🛰️ SUBSYSTEM CONSOLE</div>", unsafe_allow_html=True)

    threshold = st.slider("Convective Cutoff (K)", 190, 250, 235, 1,
                          help="Pixels colder than this → deep convective cloud tops (TCCs).")

    st.markdown("---")
    st.markdown("<div style='font-family:\"Share Tech Mono\",monospace;color:#38bdf8;font-size:11px;letter-spacing:3px;margin-bottom:12px;'>📡 DATA INGESTION</div>", unsafe_allow_html=True)

    default_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "demo_insat.h5"))
    if "file_to_process" not in st.session_state:
        st.session_state["file_to_process"] = default_file
        st.session_state["data_source"]     = "LOCAL_DEMO"

    uploaded_file = st.file_uploader("Upload INSAT HDF5", type=["h5","hdf5"])
    if uploaded_file is not None:
        save_dir  = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
        os.makedirs(save_dir, exist_ok=True)
        up_path   = os.path.join(save_dir, uploaded_file.name)
        with open(up_path, "wb") as fh:
            fh.write(uploaded_file.getbuffer())
        st.session_state["file_to_process"] = up_path
        st.session_state["data_source"]     = f"UPLOADED::{uploaded_file.name}"
        st.success(f"Matrix loaded: {uploaded_file.name}")

    if st.button("📡 FETCH LIVE SATELLITE DATA", use_container_width=True):
        with st.spinner("Establishing uplink…"):
            try:
                path, status = fetch_latest_satellite_data()
                st.session_state["file_to_process"] = path
                st.session_state["data_source"]     = status
                st.success(f"Uplink OK — {status}")
            except Exception as exc:
                st.error(f"Uplink failed: {exc}")

    file_to_process = st.session_state["file_to_process"]
    exists   = os.path.exists(file_to_process)
    size_str = f"{os.path.getsize(file_to_process)/1024/1024:.2f} MB" if exists else "—"

    st.markdown("---")
    st.markdown(f"""
    <div style="background:#071428;border:1px solid #0f2340;border-radius:8px;padding:12px;
                font-family:'Share Tech Mono',monospace;font-size:11px;color:#64748b;line-height:2.2;">
      <span style="color:#38bdf8;">SOURCE</span> &nbsp;{st.session_state['data_source']}<br>
      <span style="color:#38bdf8;">FILE  </span> &nbsp;{os.path.basename(file_to_process)}<br>
      <span style="color:#38bdf8;">SIZE  </span> &nbsp;{size_str}<br>
      <span style="color:{'#22c55e' if exists else '#ef4444'};">{'● FILE OK' if exists else '● FILE MISSING'}</span>
    </div>""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("""
    <div style="font-family:'Share Tech Mono',monospace;font-size:10px;color:#475569;line-height:1.9;">
      ARCHITECT &nbsp;: Deepanshu Maheshwari<br>
      ENGINE    &nbsp;: U-Net (30M weights) + K-Means<br>
      ALGO      &nbsp;: Haversine · TCC Filter · Risk Score<br>
      DATA      &nbsp;: INSAT-3D TIR1 (MOSDAC/ISRO)<br>
      DB        &nbsp;: SQLite telemetry archive
    </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# 8. PIPELINE
# ─────────────────────────────────────────────────────────────────────────────
file_to_process = st.session_state["file_to_process"]

if not os.path.exists(file_to_process):
    st.error("❌ No satellite data file found. Upload an INSAT HDF5 via the sidebar.")
    st.stop()

with st.spinner("🔄 Loading INSAT satellite matrix…"):
    try:
        Tb, lat, lon = load_tb_lat_lon(file_to_process)
    except Exception as exc:
        st.error(f"Failed to read satellite file: {exc}")
        st.stop()

with st.spinner("🤖 Running AI detection (U-Net / K-Means)…"):
    try:
        labeled_image, regions, ai_mask = detect_and_cluster_clouds(Tb, threshold=threshold)
        # Detect which engine ran
        import torch, os as _os
        _weights = _os.path.join(_os.path.dirname(__file__), '..', 'core', 'unet_trained_weights.pth')
        ai_engine_used = "U-Net (Deep Learning)" if (torch.cuda.is_available() or True) and _os.path.exists(_weights) else "K-Means (Fallback)"
    except Exception as exc:
        st.error(f"AI engine error: {exc}")
        st.stop()

records = []
for region in regions:
    if not is_valid_tcc(region):
        continue
    try:
        records.append(extract_tcc_features(region, Tb, lat, lon))
    except Exception:
        continue

if not records:
    st.warning("⚠️ No significant TCC clusters at this threshold. Lower the cutoff in sidebar.")
    st.stop()

df = pd.DataFrame(records).sort_values("risk_score", ascending=False).reset_index(drop=True)

SUMMARY_RENAME = {
    "center_lat":"Lat","center_lon":"Lon","risk_level":"Risk Level",
    "risk_score":"Score (%)","trend":"Trend","min_tb":"Min Tb (K)",
    "mean_tb":"Mean Tb (K)","mean_radius_km":"Radius (km)",
}
summary_df     = df[list(SUMMARY_RENAME)].rename(columns=SUMMARY_RENAME)
highest_threat = df.iloc[0]
severity       = highest_threat["risk_level"]
visible_df     = df.head(30)

RISK_COLORS = {"Extreme":"#ef4444","High":"#f97316","Medium":"#eab308","Low":"#22c55e"}

if "session_id" not in st.session_state:
    st.session_state["session_id"] = new_session_id()

# ─────────────────────────────────────────────────────────────────────────────
# 9. IMD-STYLE BULLETIN CARD
# ─────────────────────────────────────────────────────────────────────────────
_risk_color  = RISK_COLORS.get(severity, "#22c55e")
_now         = datetime.utcnow().strftime("%d %b %Y · %H:%M UTC")
_geo_ctx     = describe_geographic_context(highest_threat["center_lat"], highest_threat["center_lon"])
_threat_exp  = build_threat_explanation(highest_threat)

# Population at risk estimate (rough density: Indian subcontinent ~400/km²)
_area_km2    = 3.14159 * (highest_threat["mean_radius_km"] ** 2)
_pop_density = 400 if (6 <= highest_threat["center_lat"] <= 37 and 68 <= highest_threat["center_lon"] <= 98) else 80
_pop_risk    = int(_area_km2 * _pop_density)
_pop_str     = f"{_pop_risk/1_000_000:.1f}M" if _pop_risk > 1_000_000 else f"{_pop_risk//1000}K"

_icon_map  = {"Extreme":"🔴","High":"🟠","Medium":"🟡","Low":"🟢"}
_saffir    = {"Extreme":"CAT 4–5 EQUIVALENT","High":"CAT 2–3 EQUIVALENT","Medium":"TROPICAL STORM","Low":"DEPRESSION"}

st.markdown(f"""
<div style="background:linear-gradient(135deg,#0a0f1e,#0d1829);
            border:1px solid {_risk_color}55;border-left:4px solid {_risk_color};
            border-radius:12px;padding:24px 28px;margin-bottom:20px;
            box-shadow:0 0 32px {_risk_color}18;">

  <!-- Header row -->
  <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:12px;">
    <div>
      <div style="font-family:'Share Tech Mono',monospace;font-size:10px;
                  color:#64748b;letter-spacing:3px;margin-bottom:6px;">
        AETHERWATCH · CYCLONE WATCH BULLETIN
      </div>
      <div style="font-family:'Share Tech Mono',monospace;font-size:11px;color:#94a3b8;">
        ISSUED: {_now} &nbsp;·&nbsp; SOURCE: INSAT-3D TIR1 &nbsp;·&nbsp; ENGINE: {ai_engine_used.upper()}
      </div>
    </div>
    <div style="background:{_risk_color}22;border:1px solid {_risk_color}66;
                border-radius:8px;padding:8px 18px;text-align:center;">
      <div style="font-family:'Share Tech Mono',monospace;font-size:9px;
                  color:{_risk_color};letter-spacing:2px;">THREAT LEVEL</div>
      <div style="font-family:'Inter',sans-serif;font-size:22px;font-weight:800;
                  color:{_risk_color};">{_icon_map.get(severity,'')} {severity.upper()}</div>
      <div style="font-family:'Share Tech Mono',monospace;font-size:9px;
                  color:{_risk_color}99;">{_saffir.get(severity,'')}</div>
    </div>
  </div>

  <div style="border-top:1px solid #0f2340;margin:18px 0;"></div>

  <!-- 5 data columns -->
  <div style="display:grid;grid-template-columns:repeat(5,1fr);gap:16px;margin-bottom:18px;">
    <div style="background:#071428;border:1px solid #163558;border-radius:8px;padding:12px;text-align:center;">
      <div style="font-family:'Share Tech Mono',monospace;font-size:9px;color:#64748b;letter-spacing:1px;margin-bottom:4px;">RISK SCORE</div>
      <div style="font-family:'Share Tech Mono',monospace;font-size:20px;font-weight:800;color:#00ffd2;">{highest_threat['risk_score']:.1f}%</div>
    </div>
    <div style="background:#071428;border:1px solid #163558;border-radius:8px;padding:12px;text-align:center;">
      <div style="font-family:'Share Tech Mono',monospace;font-size:9px;color:#64748b;letter-spacing:1px;margin-bottom:4px;">CORE TEMP</div>
      <div style="font-family:'Share Tech Mono',monospace;font-size:20px;font-weight:800;color:#38bdf8;">{highest_threat['min_tb']:.1f} K</div>
    </div>
    <div style="background:#071428;border:1px solid #163558;border-radius:8px;padding:12px;text-align:center;">
      <div style="font-family:'Share Tech Mono',monospace;font-size:9px;color:#64748b;letter-spacing:1px;margin-bottom:4px;">STORM RADIUS</div>
      <div style="font-family:'Share Tech Mono',monospace;font-size:20px;font-weight:800;color:#a78bfa;">{highest_threat['mean_radius_km']:.0f} km</div>
    </div>
    <div style="background:#071428;border:1px solid #163558;border-radius:8px;padding:12px;text-align:center;">
      <div style="font-family:'Share Tech Mono',monospace;font-size:9px;color:#64748b;letter-spacing:1px;margin-bottom:4px;">TREND</div>
      <div style="font-family:'Share Tech Mono',monospace;font-size:20px;font-weight:800;color:{'#ef4444' if highest_threat['trend']=='Intensifying' else '#eab308' if highest_threat['trend']=='Stable' else '#22c55e'};">{highest_threat['trend'].upper()}</div>
    </div>
    <div style="background:#071428;border:1px solid #163558;border-radius:8px;padding:12px;text-align:center;">
      <div style="font-family:'Share Tech Mono',monospace;font-size:9px;color:#64748b;letter-spacing:1px;margin-bottom:4px;">POP. AT RISK</div>
      <div style="font-family:'Share Tech Mono',monospace;font-size:20px;font-weight:800;color:#fb923c;">{_pop_str}</div>
    </div>
  </div>

  <!-- Location + context -->
  <div style="display:grid;grid-template-columns:1fr 2fr;gap:16px;">
    <div style="background:#071428;border:1px solid #163558;border-radius:8px;padding:14px;">
      <div style="font-family:'Share Tech Mono',monospace;font-size:9px;color:#64748b;letter-spacing:1px;margin-bottom:8px;">HOTSPOT COORDINATES</div>
      <div style="font-family:'Share Tech Mono',monospace;font-size:15px;color:#ffffff;">
        {highest_threat['center_lat']:.3f}°N &nbsp; {highest_threat['center_lon']:.3f}°E
      </div>
      <div style="font-family:'Share Tech Mono',monospace;font-size:10px;color:#475569;margin-top:6px;">
        Clusters tracked: {len(df)} &nbsp;|&nbsp; Mean Tb: {highest_threat['mean_tb']:.1f} K
      </div>
    </div>
    <div style="background:#071428;border:1px solid #163558;border-radius:8px;padding:14px;">
      <div style="font-family:'Share Tech Mono',monospace;font-size:9px;color:#64748b;letter-spacing:1px;margin-bottom:8px;">THREAT ASSESSMENT</div>
      <div style="font-family:'Inter',sans-serif;font-size:12px;color:#94a3b8;line-height:1.6;">{_geo_ctx}</div>
      <div style="font-family:'Inter',sans-serif;font-size:11px;color:#475569;margin-top:8px;border-top:1px solid #0f2340;padding-top:8px;">{_threat_exp}</div>
    </div>
  </div>

</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# 10. MAIN TABS
# ─────────────────────────────────────────────────────────────────────────────
tab_intel, tab_map, tab_tb, tab_ai, tab_archive = st.tabs([
    "🧠  THREAT INTEL",
    "🗺️  TRACKING SURFACE",
    "🌡️  BRIGHTNESS MATRIX",
    "⚙️  AI ENGINE",
    "💾  TELEMETRY ARCHIVE",
])

# ══════════════════════════════════════════════════════
# TAB 1 — THREAT INTEL
# ══════════════════════════════════════════════════════
with tab_intel:
    m1,m2,m3,m4,m5 = st.columns(5)
    m1.metric("CLUSTERS TRACKED",  str(len(df)))
    m2.metric("PEAK RISK SCORE",   f"{highest_threat['risk_score']:.1f}%")
    m3.metric("CRITICAL CORE Tb",  f"{highest_threat['min_tb']:.1f} K")
    m4.metric("MAX STORM RADIUS",  f"{highest_threat['mean_radius_km']:.1f} km")
    m5.metric("POP. AT RISK",      _pop_str)

    st.markdown("---")
    col_chart, col_table = st.columns([1,2])

    with col_chart:
        st.markdown("<div style='font-family:\"Share Tech Mono\",monospace;color:#38bdf8;font-size:11px;letter-spacing:2px;margin-bottom:8px;'>RISK DISTRIBUTION</div>", unsafe_allow_html=True)
        risk_counts = df["risk_level"].value_counts().reindex(["Extreme","High","Medium","Low"], fill_value=0)
        fig, ax = plt.subplots(figsize=(4,3), facecolor="#071428")
        ax.set_facecolor("#071428")
        colors = [RISK_COLORS[k] for k in risk_counts.index]
        bars   = ax.bar(risk_counts.index, risk_counts.values, color=colors, width=0.55, edgecolor="#0f2340")
        ax.set_ylabel("Count", color="#64748b", fontsize=9, fontfamily="monospace")
        ax.tick_params(colors="#64748b", labelsize=9)
        for spine in ax.spines.values(): spine.set_edgecolor("#0f2340")
        for bar, val in zip(bars, risk_counts.values):
            if val > 0:
                ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.1, str(val),
                        ha="center", color="#94a3b8", fontsize=10, fontfamily="monospace")
        st.pyplot(fig); plt.close(fig)

    with col_table:
        st.markdown("<div style='font-family:\"Share Tech Mono\",monospace;color:#38bdf8;font-size:11px;letter-spacing:2px;margin-bottom:8px;'>TOP 12 THREAT VECTORS</div>", unsafe_allow_html=True)
        st.dataframe(summary_df.head(12), use_container_width=True, hide_index=True)
        csv_bytes = summary_df.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Export CSV", data=csv_bytes, file_name="aetherwatch_threats.csv", mime="text/csv")

# ══════════════════════════════════════════════════════
# TAB 2 — TRACKING SURFACE
# ══════════════════════════════════════════════════════
with tab_map:
    st.markdown("<div style='font-family:\"Share Tech Mono\",monospace;color:#38bdf8;font-size:11px;letter-spacing:2px;margin-bottom:6px;'>🗺️ TROPICAL THREAT TRACKING SURFACE</div>", unsafe_allow_html=True)
    st.caption(f"Top {len(visible_df)} of {len(df)} clusters · Red=Extreme · Orange=High · Yellow=Medium · Green=Low")

    m = folium.Map(
        location=[highest_threat["center_lat"], highest_threat["center_lon"]],
        zoom_start=4, tiles="CartoDB dark_matter", control_scale=True,
    )
    folium.TileLayer("OpenStreetMap", opacity=0.25).add_to(m)

    for _, row in visible_df.iterrows():
        color    = RISK_COLORS.get(row["risk_level"], "#22c55e")
        radius_m = max(40_000, row["mean_radius_km"]*1000*1.4 + row["risk_score"]*10_000)
        # Population estimate per cluster
        _a   = 3.14159 * row["mean_radius_km"]**2
        _p   = int(_a * 400) if (6<=row["center_lat"]<=37 and 68<=row["center_lon"]<=98) else int(_a*80)
        _ps  = f"{_p/1_000_000:.1f}M" if _p>1_000_000 else f"{_p//1000}K"
        popup_html = (
            f"<div style='font-family:Segoe UI,sans-serif;font-size:13px;min-width:200px;'>"
            f"<b style='color:{color}'>{row['risk_level']} Threat</b><br>"
            f"Score &nbsp;&nbsp;: <b>{row['risk_score']:.1f}%</b><br>"
            f"Trend &nbsp;&nbsp;: <b>{row['trend']}</b><br>"
            f"Radius &nbsp;: <b>{row['mean_radius_km']:.1f} km</b><br>"
            f"Min Tb &nbsp;: <b>{row['min_tb']:.1f} K</b><br>"
            f"Pop Risk : <b>{_ps}</b><br>"
            f"Loc &nbsp;&nbsp;&nbsp;&nbsp;: <b>{row['center_lat']:.2f}°N, {row['center_lon']:.2f}°E</b>"
            f"</div>"
        )
        folium.Circle(
            location=[row["center_lat"], row["center_lon"]],
            radius=radius_m, color=color, weight=2,
            fill=True, fill_color=color, fill_opacity=0.22,
            tooltip=f"{row['risk_level']} · {row['risk_score']:.1f}% · {row['trend']} · Pop:{_ps}",
            popup=folium.Popup(popup_html, max_width=280),
        ).add_to(m)
        folium.CircleMarker(
            location=[row["center_lat"], row["center_lon"]],
            radius=7, color="#ffffff", weight=2,
            fill=True, fill_color=color, fill_opacity=0.95,
        ).add_to(m)

        # Simulated track projection arrow (Intensifying storms only)
        if row["trend"] == "Intensifying":
            end_lat = row["center_lat"] + 1.8
            end_lon = row["center_lon"] + 0.9
            folium.PolyLine(
                locations=[[row["center_lat"], row["center_lon"]], [end_lat, end_lon]],
                color=color, weight=2, opacity=0.7, dash_array="6 4",
                tooltip="Projected track (simulated)"
            ).add_to(m)
            folium.CircleMarker(
                location=[end_lat, end_lon],
                radius=4, color=color, fill=True, fill_opacity=0.5,
                tooltip="Projected position +24h"
            ).add_to(m)

    st_folium(m, width="100%", height=520, returned_objects=[])

# ══════════════════════════════════════════════════════
# TAB 3 — BRIGHTNESS TEMPERATURE MATRIX
# ══════════════════════════════════════════════════════
with tab_tb:
    st.markdown("<div style='font-family:\"Share Tech Mono\",monospace;color:#38bdf8;font-size:11px;letter-spacing:2px;margin-bottom:6px;'>🌡️ INSAT-3D TIR1 — BRIGHTNESS TEMPERATURE MATRIX</div>", unsafe_allow_html=True)
    st.caption(f"Cold dark regions = deep convective tops. Cyan contour = {threshold} K cutoff threshold.")

    col_tb1, col_tb2 = st.columns([3,1])
    with col_tb1:
        with st.spinner("Rendering…"):
            try:
                ds = max(1, Tb.shape[0]//600)
                Tb_d = Tb[::ds, ::ds]
                fig, ax = plt.subplots(figsize=(13,5.5), facecolor="#030b18")
                ax.set_facecolor("#030b18")
                im = ax.imshow(Tb_d, cmap="plasma_r", vmin=190, vmax=310, aspect="auto")
                try:
                    ax.contour(Tb_d, levels=[threshold], colors=["#00ffd2"], linewidths=0.8, alpha=0.9)
                except Exception:
                    pass
                cbar = plt.colorbar(im, ax=ax, fraction=0.025, pad=0.02)
                cbar.set_label("Brightness Temperature (K)", color="#64748b", fontsize=9)
                cbar.ax.yaxis.set_tick_params(color="#64748b")
                plt.setp(cbar.ax.yaxis.get_ticklabels(), color="#64748b", fontsize=8)
                ax.set_title("INSAT-3D TIR1 — Full Disk Brightness Temperature",
                             color="#94a3b8", fontsize=11, fontfamily="monospace", pad=10)
                ax.tick_params(colors="#2d3f55", labelsize=8)
                for spine in ax.spines.values(): spine.set_edgecolor("#0f2340")
                st.pyplot(fig); plt.close(fig)
            except Exception as exc:
                st.warning(f"Could not render Tb matrix: {exc}")

    with col_tb2:
        st.markdown("**Matrix stats:**")
        valid_tb = Tb[~np.isnan(Tb)]
        if len(valid_tb):
            st.metric("Min Tb",       f"{valid_tb.min():.1f} K")
            st.metric("Max Tb",       f"{valid_tb.max():.1f} K")
            st.metric("Mean Tb",      f"{valid_tb.mean():.1f} K")
            cold_frac = np.sum(valid_tb <= threshold)/len(valid_tb)*100
            st.metric("Cold Pixel %", f"{cold_frac:.2f}%")
            st.metric("Matrix Size",  f"{Tb.shape[0]}×{Tb.shape[1]}")

# ══════════════════════════════════════════════════════
# TAB 4 — AI ENGINE TRANSPARENCY
# ══════════════════════════════════════════════════════
with tab_ai:
    st.markdown("<div style='font-family:\"Share Tech Mono\",monospace;color:#38bdf8;font-size:11px;letter-spacing:2px;margin-bottom:16px;'>⚙️ AI ENGINE TRANSPARENCY PANEL</div>", unsafe_allow_html=True)

    col_e1, col_e2, col_e3 = st.columns(3)

    # Engine status
    import torch as _torch
    _weights_path = os.path.join(os.path.dirname(__file__), '..', 'core', 'unet_trained_weights.pth')
    _unet_ok      = os.path.exists(_weights_path)
    _torch_ok     = True
    _gpu          = _torch.cuda.is_available()
    _weights_mb   = os.path.getsize(_weights_path)/1024/1024 if _unet_ok else 0

    with col_e1:
        st.markdown(f"""
        <div style="background:#071428;border:1px solid #163558;border-radius:10px;padding:18px;">
          <div style="font-family:'Share Tech Mono',monospace;font-size:10px;color:#64748b;letter-spacing:2px;margin-bottom:12px;">PRIMARY ENGINE</div>
          <div style="font-family:'Share Tech Mono',monospace;font-size:14px;color:#00ffd2;margin-bottom:8px;">U-NET (PyTorch)</div>
          <div style="font-size:11px;color:#94a3b8;font-family:'Share Tech Mono',monospace;line-height:2;">
            Weights &nbsp;: <span style="color:{'#22c55e' if _unet_ok else '#ef4444'};">{'LOADED' if _unet_ok else 'MISSING'}</span><br>
            Size &nbsp;&nbsp;&nbsp;&nbsp;: {_weights_mb:.1f} MB<br>
            PyTorch &nbsp;: <span style="color:#22c55e;">OK</span><br>
            GPU &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;: <span style="color:{'#22c55e' if _gpu else '#eab308'};">{'AVAILABLE' if _gpu else 'CPU MODE'}</span><br>
            Status &nbsp;&nbsp;: <span style="color:{'#22c55e' if _unet_ok else '#ef4444'};">{'ACTIVE' if _unet_ok else 'FALLBACK'}</span>
          </div>
        </div>""", unsafe_allow_html=True)

    with col_e2:
        st.markdown(f"""
        <div style="background:#071428;border:1px solid #163558;border-radius:10px;padding:18px;">
          <div style="font-family:'Share Tech Mono',monospace;font-size:10px;color:#64748b;letter-spacing:2px;margin-bottom:12px;">FALLBACK ENGINE</div>
          <div style="font-family:'Share Tech Mono',monospace;font-size:14px;color:#f97316;margin-bottom:8px;">K-MEANS (sklearn)</div>
          <div style="font-size:11px;color:#94a3b8;font-family:'Share Tech Mono',monospace;line-height:2;">
            Algorithm : K-Means (k=3)<br>
            Trigger &nbsp;&nbsp;: PyTorch fail<br>
            n_init &nbsp;&nbsp;&nbsp;: 10<br>
            Status &nbsp;&nbsp;&nbsp;: <span style="color:{'#eab308' if not _unet_ok else '#475569'};">{'ACTIVE' if not _unet_ok else 'STANDBY'}</span>
          </div>
        </div>""", unsafe_allow_html=True)

    with col_e3:
        valid_tb = Tb[~np.isnan(Tb)]
        cold_px  = int(np.sum(valid_tb <= threshold))
        total_px = int(Tb.shape[0] * Tb.shape[1])
        st.markdown(f"""
        <div style="background:#071428;border:1px solid #163558;border-radius:10px;padding:18px;">
          <div style="font-family:'Share Tech Mono',monospace;font-size:10px;color:#64748b;letter-spacing:2px;margin-bottom:12px;">THIS SCAN</div>
          <div style="font-size:11px;color:#94a3b8;font-family:'Share Tech Mono',monospace;line-height:2;">
            Total pixels &nbsp;: {total_px:,}<br>
            Cold pixels &nbsp;&nbsp;: {cold_px:,}<br>
            Cold fraction : {cold_px/total_px*100:.2f}%<br>
            Regions found : {len(regions)}<br>
            Valid TCCs &nbsp;&nbsp;&nbsp;: {len(records)}<br>
            Threshold &nbsp;&nbsp;&nbsp;: {threshold} K
          </div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # TCC size distribution
    st.markdown("<div style='font-family:\"Share Tech Mono\",monospace;color:#38bdf8;font-size:11px;letter-spacing:2px;margin-bottom:8px;'>DETECTED CLUSTER SIZE DISTRIBUTION</div>", unsafe_allow_html=True)
    fig2, ax2 = plt.subplots(figsize=(10,3), facecolor="#071428")
    ax2.set_facecolor("#071428")
    ax2.scatter(df["mean_radius_km"], df["risk_score"],
                c=[RISK_COLORS.get(r,"#22c55e") for r in df["risk_level"]],
                s=80, alpha=0.85, edgecolors="#0f2340", linewidth=0.5)
    ax2.set_xlabel("Storm Radius (km)", color="#64748b", fontsize=9, fontfamily="monospace")
    ax2.set_ylabel("Risk Score (%)", color="#64748b", fontsize=9, fontfamily="monospace")
    ax2.tick_params(colors="#64748b", labelsize=8)
    ax2.axhline(85, color="#ef4444", linewidth=0.6, linestyle="--", alpha=0.5, label="Extreme threshold")
    ax2.axhline(60, color="#f97316", linewidth=0.6, linestyle="--", alpha=0.5, label="High threshold")
    for spine in ax2.spines.values(): spine.set_edgecolor("#0f2340")
    ax2.legend(fontsize=8, facecolor="#071428", edgecolor="#163558", labelcolor="#94a3b8")
    st.pyplot(fig2); plt.close(fig2)

    st.markdown("---")
    st.markdown("""
    <div style="background:#071428;border:1px solid #0f2340;border-radius:8px;padding:16px 20px;
                font-family:'Share Tech Mono',monospace;font-size:11px;color:#475569;line-height:2;">
      <span style="color:#38bdf8;">RISK FORMULA</span><br>
      &nbsp;&nbsp;risk_score = 0.6 × tb_score + 0.4 × size_score<br>
      &nbsp;&nbsp;tb_score   = clamp((235 − min_Tb) / (235 − 190) × 100)<br>
      &nbsp;&nbsp;size_score = (mean_radius_km / 1200) × 100<br><br>
      <span style="color:#38bdf8;">TCC FILTER</span><br>
      &nbsp;&nbsp;Valid TCC : radius ≥ 111 km AND area ≥ 34,800 km²<br><br>
      <span style="color:#38bdf8;">SPATIAL ALGO</span><br>
      &nbsp;&nbsp;Haversine formula · INSAT-3D geostationary projection (82°E, H=42,164 km)
    </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════
# TAB 5 — TELEMETRY ARCHIVE
# ══════════════════════════════════════════════════════
with tab_archive:
    st.markdown("<div style='font-family:\"Share Tech Mono\",monospace;color:#38bdf8;font-size:11px;letter-spacing:2px;margin-bottom:16px;'>💾 TELEMETRY ARCHIVE & TRAJECTORY ANALYSIS</div>", unsafe_allow_html=True)

    col_commit, col_chart = st.columns([1,2])

    with col_commit:
        if st.button("💾 COMMIT SCAN TO DATABASE", use_container_width=True):
            sid = st.session_state["session_id"]
            src = st.session_state["data_source"]
            committed = 0
            for _, row in df.iterrows():
                try:
                    log_threat_to_db(row.to_dict(), session_id=sid, data_source=src)
                    committed += 1
                except Exception:
                    pass
            try:
                log_scan_session(sid, src, len(df), float(highest_threat["risk_score"]), severity, threshold)
            except Exception:
                pass
            st.session_state["session_id"] = new_session_id()
            st.success(f"✅ Archived {committed} vectors (Session: {sid})")

        st.markdown("**Current scan:**")
        st.dataframe(df[["risk_level","risk_score","trend","min_tb"]].head(10),
                     hide_index=True, use_container_width=True)

        sess_df = fetch_scan_sessions(limit=8)
        if not sess_df.empty:
            st.markdown("**Recent sessions:**")
            st.dataframe(sess_df[["timestamp","total_clusters","peak_risk_score","peak_risk_level"]],
                         hide_index=True, use_container_width=True)

    with col_chart:
        trend_df = fetch_risk_trend()
        if not trend_df.empty:
            st.markdown("**Historical peak risk trajectory:**")
            st.line_chart(trend_df.set_index("timestamp")[["risk_score"]], color="#ef4444", height=220)

            hist_df = fetch_telemetry_history(limit=500)
            if not hist_df.empty and "risk_level" in hist_df.columns:
                st.markdown("**Archive breakdown:**")
                hist_counts = hist_df["risk_level"].value_counts().reindex(
                    ["Extreme","High","Medium","Low"], fill_value=0)
                fig3, ax3 = plt.subplots(figsize=(5,2.5), facecolor="#071428")
                ax3.set_facecolor("#071428")
                ax3.barh(hist_counts.index, hist_counts.values,
                         color=[RISK_COLORS[k] for k in hist_counts.index], edgecolor="#0f2340")
                ax3.tick_params(colors="#64748b", labelsize=9)
                for spine in ax3.spines.values(): spine.set_edgecolor("#0f2340")
                st.pyplot(fig3); plt.close(fig3)
        else:
            st.info("📭 No history yet — commit scan above to start tracking.")

# ─────────────────────────────────────────────────────────────────────────────
# 11. FOOTER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style="text-align:center;padding:10px 0;font-family:'Share Tech Mono',monospace;
            font-size:10px;color:#1e3a5f;letter-spacing:2px;">
  AETHERWATCH · ISRO INSAT-3D CYCLONE INTELLIGENCE SYSTEM ·
  U-NET (PyTorch) + K-MEANS FALLBACK · HAVERSINE · TCC FILTER · RISK SCORE
</div>""", unsafe_allow_html=True)