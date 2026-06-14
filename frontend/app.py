import os
import sys

import folium
import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st
from streamlit_folium import st_folium

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import Config
from logger import get_logger

logger = get_logger(__name__)
API_URL = Config.API_BASE_URL

st.set_page_config(
    page_title="AetherWatch",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .stApp { background: #020617; color: #e2e8f0; }
    [data-testid="stMetric"] {
        background: #0f172a;
        border: 1px solid #1e3a5f;
        border-radius: 8px;
        padding: 12px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(ttl=60)
def fetch_json(path):
    response = requests.get(f"{API_URL}{path}", timeout=30)
    response.raise_for_status()
    return response.json()


def risk_color(level):
    return {
        "CRITICAL": "red",
        "HIGH": "orange",
        "MEDIUM": "cadetblue",
        "LOW": "green",
    }.get(level, "blue")


st.title("AetherWatch")
st.caption(
    "INSAT cold-cloud candidate monitoring. This prototype does not issue "
    "official cyclone forecasts or emergency alerts."
)

try:
    health = fetch_json("/health")
    analysis = fetch_json("/api/v1/analyses/latest")
except requests.RequestException as exc:
    st.error(f"AetherWatch API is unavailable at {API_URL}: {exc}")
    logger.error("Dashboard API request failed: %s", exc)
    st.stop()

freshness = analysis["freshness"]
source_mode = analysis["source_mode"]
status_color = "green" if freshness["is_fresh"] else "orange"
st.markdown(
    f"**System:** `{health['status']}` &nbsp; "
    f"**Data mode:** :{status_color}[{source_mode}] &nbsp; "
    f"**Freshness:** :{status_color}[{freshness['state']}]"
)

if not freshness["is_fresh"]:
    st.warning(
        "The active scene is historical or stale. Results are suitable for "
        "system demonstration and analysis, not real-time operational decisions."
    )

with st.sidebar:
    st.header("Data Status")
    st.write(f"Source: {analysis['source_name']}")
    st.write(f"Product: {analysis.get('product_name') or 'Unknown'}")
    st.write(f"Acquired: {analysis.get('acquisition_time') or 'Unknown'}")
    st.write(f"Processed: {analysis['processed_at']}")
    st.write(f"Detector: {analysis['detector']}")
    st.write(f"Threshold: {analysis['threshold_kelvin']:.1f} K")
    if st.button("Refresh"):
        st.cache_data.clear()
        st.rerun()

threats = analysis.get("threats", [])
counts = {
    level: sum(item["risk_level"] == level for item in threats)
    for level in ("CRITICAL", "HIGH", "MEDIUM", "LOW")
}
metric_columns = st.columns(5)
metric_columns[0].metric("Candidates", analysis["threat_count"])
metric_columns[1].metric("Critical", counts["CRITICAL"])
metric_columns[2].metric("High", counts["HIGH"])
metric_columns[3].metric("Medium", counts["MEDIUM"])
metric_columns[4].metric("Low", counts["LOW"])

map_tab, thermal_tab, risk_tab, table_tab = st.tabs(
    ["Candidate Map", "Thermal Preview", "Risk Analysis", "Candidate Table"]
)

with map_tab:
    if threats:
        center_lat = sum(item["latitude"] for item in threats) / len(threats)
        center_lon = sum(item["longitude"] for item in threats) / len(threats)
    else:
        center_lat, center_lon = 15.0, 82.0
    map_view = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=4,
        tiles="CartoDB positron",
    )
    for item in threats:
        folium.Circle(
            location=[item["latitude"], item["longitude"]],
            radius=max(5000, item["mean_radius_km"] * 1000),
            color=risk_color(item["risk_level"]),
            fill=True,
            fill_opacity=0.2,
            popup=(
                f"Risk: {item['risk_level']} ({item['risk_score']:.1f}/100)"
                f"<br>Minimum temperature: "
                f"{item['min_temperature_kelvin']:.1f} K"
                f"<br>Estimated area: {item['area_km2']:.0f} km2"
            ),
        ).add_to(map_view)
    st_folium(map_view, use_container_width=True, height=600)

with thermal_tab:
    try:
        preview = fetch_json("/api/v1/analyses/latest/preview?max_size=180")
        figure = go.Figure(
            data=go.Heatmap(
                z=preview["thermal"],
                colorscale="RdYlBu_r",
                colorbar={"title": "Kelvin"},
                hovertemplate="Temperature: %{z:.1f} K<extra></extra>",
            )
        )
        figure.update_layout(
            title="Downsampled thermal image",
            xaxis_title="Scan column",
            yaxis_title="Scan row",
            template="plotly_dark",
            height=650,
        )
        st.plotly_chart(figure, use_container_width=True)
        st.caption("Preview is downsampled; candidate calculations use full resolution.")
    except requests.RequestException as exc:
        st.warning(f"Thermal preview is unavailable: {exc}")

with risk_tab:
    scores = [item["risk_score"] for item in threats]
    labels = [f"Candidate {index + 1}" for index in range(len(threats))]
    bar = go.Figure(
        go.Bar(
            x=labels,
            y=scores,
            marker_color=[risk_color(item["risk_level"]) for item in threats],
            hovertemplate="%{x}<br>Risk: %{y:.1f}/100<extra></extra>",
        )
    )
    bar.update_layout(
        title="Candidate risk scores",
        yaxis={"title": "Risk score", "range": [0, 100]},
        template="plotly_dark",
        height=450,
    )
    st.plotly_chart(bar, use_container_width=True)
    st.info(
        "Risk score is a prototype heuristic based on cloud-top temperature "
        "and candidate size. It is not a forecast probability."
    )

with table_tab:
    if threats:
        frame = pd.DataFrame(threats)
        display_columns = [
            "latitude",
            "longitude",
            "risk_level",
            "risk_score",
            "min_temperature_kelvin",
            "mean_temperature_kelvin",
            "area_km2",
            "mean_radius_km",
            "trend",
        ]
        st.dataframe(
            frame[display_columns],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No candidates crossed the configured size threshold.")

st.divider()
st.caption(
    "AetherWatch v2.0 | Public read-only dashboard | "
    "Method: deterministic cold-cloud threshold and connected components"
)
