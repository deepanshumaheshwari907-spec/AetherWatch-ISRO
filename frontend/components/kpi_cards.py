"""
KPI Cards and Metrics Display Components
Professional dashboard metrics for AetherWatch
"""

import streamlit as st
import numpy as np
from datetime import datetime


def render_status_card(status, color):
    """
    Render a status indicator card
    
    Args:
        status: Status string (e.g., 'SYSTEM_NOMINAL', 'WARNING', 'CRITICAL')
        color: Color name (green, yellow, red)
    """
    
    color_map = {
        'green': '#22c55e',
        'yellow': '#eab308',
        'red': '#ef4444',
        'cyan': '#00ffd2'
    }
    
    html = f"""
    <div style="background: linear-gradient(135deg, #020617, #0b1329); 
                border: 2px solid {color_map.get(color, '#00ffd2')}; 
                padding: 20px; 
                border-radius: 8px; 
                text-align: center;
                box-shadow: 0 0 20px rgba(0, 255, 210, 0.2);">
        <div style="font-size: 14px; color: #94a3b8; font-family: monospace; letter-spacing: 2px;">● {status}</div>
    </div>
    """
    
    st.markdown(html, unsafe_allow_html=True)


def render_threat_metrics(critical_count, high_count, medium_count, low_count):
    """
    Render threat level metrics in KPI format
    
    Args:
        critical_count: Number of critical threats
        high_count: Number of high threats
        medium_count: Number of medium threats
        low_count: Number of low threats
    """
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="🔴 CRITICAL",
            value=critical_count,
            delta=None,
            delta_color="off"
        )
        st.markdown("""
        <style>
        [data-testid="metric-container"] {
            background: linear-gradient(135deg, #4c0519, #7f1d1d);
            border: 1px solid #dc2626;
            border-radius: 8px;
            padding: 15px;
        }
        </style>
        """, unsafe_allow_html=True)
    
    with col2:
        st.metric(
            label="🟠 HIGH",
            value=high_count,
            delta=None,
            delta_color="off"
        )
        st.markdown("""
        <style>
        [data-testid="metric-container"] {
            background: linear-gradient(135deg, #78350f, #b45309);
            border: 1px solid #f97316;
            border-radius: 8px;
            padding: 15px;
        }
        </style>
        """, unsafe_allow_html=True)
    
    with col3:
        st.metric(
            label="🟡 MEDIUM",
            value=medium_count,
            delta=None,
            delta_color="off"
        )
        st.markdown("""
        <style>
        [data-testid="metric-container"] {
            background: linear-gradient(135deg, #713f12, #b45309);
            border: 1px solid #eab308;
            border-radius: 8px;
            padding: 15px;
        }
        </style>
        """, unsafe_allow_html=True)
    
    with col4:
        st.metric(
            label="🟢 LOW",
            value=low_count,
            delta=None,
            delta_color="off"
        )
        st.markdown("""
        <style>
        [data-testid="metric-container"] {
            background: linear-gradient(135deg, #15803d, #22c55e);
            border: 1px solid #22c55e;
            border-radius: 8px;
            padding: 15px;
        }
        </style>
        """, unsafe_allow_html=True)


def render_system_metrics(api_status, database_status, model_status, data_freshness):
    """
    Render system health metrics
    
    Args:
        api_status: bool - API operational
        database_status: bool - Database operational
        model_status: bool - AI Model operational
        data_freshness: str - "Fresh", "Stale", "Unavailable"
    """
    
    col1, col2, col3, col4 = st.columns(4)
    
    status_indicator = lambda x: "✅" if x else "❌"
    
    with col1:
        st.metric(
            label="API Server",
            value=status_indicator(api_status)
        )
    
    with col2:
        st.metric(
            label="Database",
            value=status_indicator(database_status)
        )
    
    with col3:
        st.metric(
            label="AI Model",
            value=status_indicator(model_status)
        )
    
    with col4:
        st.metric(
            label="Data Status",
            value=data_freshness
        )


def render_satellite_info(timestamp, source, region, resolution):
    """
    Render satellite data information card
    
    Args:
        timestamp: When data was captured
        source: Data source (e.g., "MOSDAC INSAT-3D")
        region: Geographic region
        resolution: Spatial resolution
    """
    
    html = f"""
    <div style="background: linear-gradient(135deg, #020617, #0b1329); 
                border-left: 4px solid #00ffd2; 
                padding: 15px; 
                border-radius: 6px;
                margin: 10px 0;">
        <div style="color: #00ffd2; font-family: monospace; font-size: 12px; letter-spacing: 1px;">
            🛰️ SATELLITE DATA INFO
        </div>
        <div style="color: #e2e8f0; font-family: monospace; font-size: 11px; margin-top: 8px;">
            <div>⏰ Captured: {timestamp}</div>
            <div>📡 Source: {source}</div>
            <div>🌍 Region: {region}</div>
            <div>📏 Resolution: {resolution}</div>
        </div>
    </div>
    """
    
    st.markdown(html, unsafe_allow_html=True)


def render_risk_gauge(risk_score):
    """
    Render a risk level gauge
    
    Args:
        risk_score: Float between 0.0 and 1.0
    """
    
    # Determine color based on risk
    if risk_score > 0.8:
        color = '#ff0000'
        level = 'CRITICAL'
    elif risk_score > 0.6:
        color = '#ff6b00'
        level = 'HIGH'
    elif risk_score > 0.4:
        color = '#ffd700'
        level = 'MEDIUM'
    else:
        color = '#00ff00'
        level = 'LOW'
    
    html = f"""
    <div style="margin: 20px 0;">
        <div style="font-size: 14px; color: #00ffd2; font-family: monospace; margin-bottom: 10px;">
            Overall Risk Index: <span style="color: {color}; font-weight: bold;">{level}</span>
        </div>
        <div style="width: 100%; height: 30px; background: #0b1329; border: 1px solid #1e293b; border-radius: 4px; overflow: hidden;">
            <div style="width: {risk_score * 100}%; height: 100%; background: linear-gradient(90deg, #00ff00, #ffd700, #ff6b00, #ff0000); 
                        box-shadow: 0 0 10px {color};">
            </div>
        </div>
        <div style="margin-top: 8px; color: #94a3b8; font-family: monospace; font-size: 11px;">
            {risk_score:.1%} of maximum risk threshold
        </div>
    </div>
    """
    
    st.markdown(html, unsafe_allow_html=True)


def render_data_quality_metrics(thermal_coverage, accuracy, last_updated):
    """
    Render data quality metrics
    
    Args:
        thermal_coverage: Percentage of area with valid data
        accuracy: Detection accuracy percentage
        last_updated: When data was last updated
    """
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="📊 Thermal Coverage",
            value=f"{thermal_coverage:.1f}%"
        )
    
    with col2:
        st.metric(
            label="🎯 Detection Accuracy",
            value=f"{accuracy:.1f}%"
        )
    
    with col3:
        st.metric(
            label="🕐 Last Updated",
            value=last_updated
        )


def render_threat_summary(total_threats, detection_rate, avg_confidence):
    """
    Render threat detection summary
    
    Args:
        total_threats: Total threats detected
        detection_rate: Detection rate percentage
        avg_confidence: Average AI confidence
    """
    
    html = f"""
    <div style="background: linear-gradient(135deg, #020617, #0b1329); 
                border-left: 4px solid #00ffd2; 
                padding: 20px; 
                border-radius: 6px;
                margin: 15px 0;">
        <div style="color: #00ffd2; font-family: monospace; font-size: 12px; letter-spacing: 1px; margin-bottom: 15px;">
            🎯 THREAT DETECTION SUMMARY
        </div>
        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px;">
            <div style="text-align: center;">
                <div style="font-size: 28px; color: #ff6b00; font-weight: bold;">{total_threats}</div>
                <div style="color: #94a3b8; font-size: 11px; margin-top: 5px;">Total Threats</div>
            </div>
            <div style="text-align: center;">
                <div style="font-size: 28px; color: #00ffd2; font-weight: bold;">{detection_rate:.1f}%</div>
                <div style="color: #94a3b8; font-size: 11px; margin-top: 5px;">Detection Rate</div>
            </div>
            <div style="text-align: center;">
                <div style="font-size: 28px; color: #22c55e; font-weight: bold;">{avg_confidence:.1f}%</div>
                <div style="color: #94a3b8; font-size: 11px; margin-top: 5px;">Avg Confidence</div>
            </div>
        </div>
    </div>
    """
    
    st.markdown(html, unsafe_allow_html=True)
