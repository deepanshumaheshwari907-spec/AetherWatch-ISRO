"""
Advanced Chart Components for AetherWatch Dashboard
Uses Plotly for interactive, professional visualizations
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from typing import List, Dict, Tuple

def create_temperature_trend_chart(thermal_array, timestamps=None):
    """
    Create temperature trend over time visualization
    
    Args:
        thermal_array: Numpy array of thermal data
        timestamps: List of timestamps for x-axis
    
    Returns:
        Plotly figure
    """
    
    # Calculate time-series stats
    if len(thermal_array.shape) == 3:
        # Multiple time steps
        temps_over_time = np.array([np.mean(arr) for arr in thermal_array])
    else:
        temps_over_time = np.array([np.mean(thermal_array)])
    
    if timestamps is None:
        timestamps = [datetime.now() - timedelta(hours=i) for i in range(len(temps_over_time)-1, -1, -1)]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=timestamps,
        y=temps_over_time,
        mode='lines+markers',
        name='Average Temperature',
        line=dict(color='#00ffd2', width=3),
        fill='tozeroy',
        fillcolor='rgba(0, 255, 210, 0.2)',
        marker=dict(size=8, color='#00ffd2')
    ))
    
    fig.update_layout(
        title='Temperature Trend Over Time',
        xaxis_title='Time',
        yaxis_title='Temperature (Kelvin)',
        hovermode='x unified',
        template='plotly_dark',
        plot_bgcolor='#0f172a',
        paper_bgcolor='#020617',
        font=dict(color='#00ffd2', family='monospace', size=11),
        height=400
    )
    
    return fig


def create_temperature_heatmap(thermal_array, latitude, longitude):
    """
    Create interactive heatmap of thermal data
    
    Args:
        thermal_array: 2D numpy array of thermal data
        latitude: Latitude coordinates
        longitude: Longitude coordinates
    
    Returns:
        Plotly figure
    """
    
    fig = go.Figure(data=go.Heatmap(
        z=thermal_array,
        x=longitude,
        y=latitude,
        colorscale='RdYlBu_r',  # Red-Yellow-Blue reversed
        colorbar=dict(title='Temperature (K)', thickness=20, len=0.7),
        hovertemplate='Lat: %{y:.2f}<br>Lon: %{x:.2f}<br>Temp: %{z:.1f}K<extra></extra>'
    ))
    
    fig.update_layout(
        title='Thermal Infrared Satellite Imagery',
        xaxis_title='Longitude',
        yaxis_title='Latitude',
        template='plotly_dark',
        plot_bgcolor='#0f172a',
        paper_bgcolor='#020617',
        font=dict(color='#ffffff', family='monospace', size=11),
        height=500
    )
    
    return fig


def create_risk_distribution_chart(threats_data):
    """
    Create risk level distribution pie chart
    
    Args:
        threats_data: List of threat dictionaries with 'risk_level'
    
    Returns:
        Plotly figure
    """
    
    risk_counts = {
        'CRITICAL': 0,
        'HIGH': 0,
        'MEDIUM': 0,
        'LOW': 0
    }
    
    for threat in threats_data:
        risk_level = threat.get('risk_level', 'MEDIUM')
        if risk_level in risk_counts:
            risk_counts[risk_level] += 1
    
    colors_map = {
        'CRITICAL': '#ff0000',
        'HIGH': '#ff6b00',
        'MEDIUM': '#ffd700',
        'LOW': '#00ff00'
    }
    
    fig = go.Figure(data=[go.Pie(
        labels=list(risk_counts.keys()),
        values=list(risk_counts.values()),
        marker=dict(colors=[colors_map[level] for level in risk_counts.keys()]),
        hole=0.3,  # Donut chart
        hovertemplate='<b>%{label}</b><br>Count: %{value}<br>%{percentInitial}<extra></extra>'
    )])
    
    fig.update_layout(
        title='Risk Level Distribution',
        template='plotly_dark',
        plot_bgcolor='#0f172a',
        paper_bgcolor='#020617',
        font=dict(color='#ffffff', family='monospace', size=11),
        height=400,
        showlegend=True
    )
    
    return fig


def create_intensity_comparison_chart(threats_data):
    """
    Create bar chart comparing threat intensities
    
    Args:
        threats_data: List of threat dictionaries with 'name' and 'risk_score'
    
    Returns:
        Plotly figure
    """
    
    threat_names = [f"Threat #{i+1}" for i in range(min(10, len(threats_data)))]
    risk_scores = [t.get('risk_score', 0) for t in threats_data[:10]]
    
    # Color code by intensity
    colors = ['#ff0000' if score > 0.8 else '#ff6b00' if score > 0.6 else '#ffd700' if score > 0.4 else '#00ff00' 
              for score in risk_scores]
    
    fig = go.Figure(data=[go.Bar(
        x=threat_names,
        y=risk_scores,
        marker=dict(color=colors),
        text=[f'{score:.2f}' for score in risk_scores],
        textposition='auto',
        hovertemplate='<b>%{x}</b><br>Risk Score: %{y:.2%}<extra></extra>'
    )])
    
    fig.update_layout(
        title='Threat Intensity Comparison (Top 10)',
        xaxis_title='Threat ID',
        yaxis_title='Risk Score',
        yaxis=dict(range=[0, 1.0]),
        template='plotly_dark',
        plot_bgcolor='#0f172a',
        paper_bgcolor='#020617',
        font=dict(color='#ffffff', family='monospace', size=10),
        height=400,
        xaxis_tickangle=-45
    )
    
    return fig


def create_time_series_animation(thermal_arrays, timestamps, latitude, longitude):
    """
    Create animated time-series visualization
    
    Args:
        thermal_arrays: List of 2D thermal arrays
        timestamps: List of timestamps
        latitude: Latitude coordinates
        longitude: Longitude coordinates
    
    Returns:
        Plotly figure
    """
    
    frames = []
    for i, (thermal, ts) in enumerate(zip(thermal_arrays, timestamps)):
        frames.append(go.Frame(
            data=[go.Heatmap(z=thermal, x=longitude, y=latitude, colorscale='RdYlBu_r')],
            name=str(ts)
        ))
    
    fig = go.Figure(
        data=[go.Heatmap(z=thermal_arrays[0], x=longitude, y=latitude, colorscale='RdYlBu_r')],
        frames=frames
    )
    
    fig.update_layout(
        title='Thermal Data Evolution Over Time',
        xaxis_title='Longitude',
        yaxis_title='Latitude',
        updatemenus=[dict(
            type='buttons',
            showactive=False,
            buttons=[
                dict(label='▶ Play', method='animate', args=[None, {'frame': {'duration': 500}}]),
                dict(label='⏸ Pause', method='animate', args=[[None], {'frame': {'duration': 0}, 'mode': 'immediate'}])
            ]
        )],
        template='plotly_dark',
        plot_bgcolor='#0f172a',
        paper_bgcolor='#020617',
        font=dict(color='#ffffff', family='monospace', size=11),
        height=500
    )
    
    return fig


def create_geographic_comparison_chart(threats_data):
    """
    Create scatter plot of threats by geographic location
    
    Args:
        threats_data: List of threat dictionaries with 'latitude', 'longitude', 'risk_score'
    
    Returns:
        Plotly figure
    """
    
    lats = [t.get('latitude', 0) for t in threats_data]
    lons = [t.get('longitude', 0) for t in threats_data]
    risks = [t.get('risk_score', 0) for t in threats_data]
    names = [f"Threat #{i+1}" for i in range(len(threats_data))]
    
    fig = go.Figure(data=[go.Scattergeo(
        lon=lons,
        lat=lats,
        mode='markers+text',
        text=names,
        textposition='top center',
        marker=dict(
            size=[score*50 + 10 for score in risks],  # Size proportional to risk
            color=risks,
            colorscale='RdYlGn_r',
            showscale=True,
            colorbar=dict(title='Risk Score', thickness=20),
            line=dict(width=2, color='white')
        ),
        hovertemplate='<b>%{text}</b><br>Lat: %{lat:.2f}<br>Lon: %{lon:.2f}<br>Risk: %{marker.color:.2%}<extra></extra>'
    )])
    
    fig.update_geos(
        projection_type='mercator',
        showland=True,
        landcolor='#1a2741',
        showocean=True,
        oceancolor='#0f172a',
        coastcolor='#00ffd2',
        coastwidth=2
    )
    
    fig.update_layout(
        title='Geographic Distribution of Threats',
        template='plotly_dark',
        paper_bgcolor='#020617',
        font=dict(color='#ffffff', family='monospace', size=11),
        height=600,
        geo=dict(bgcolor='#0f172a')
    )
    
    return fig


def create_multi_cyclone_comparison(cyclone_list):
    """
    Create side-by-side comparison of multiple cyclones
    
    Args:
        cyclone_list: List of cyclone data dictionaries
    
    Returns:
        Plotly figure
    """
    
    metrics = ['max_wind', 'pressure', 'diameter', 'movement_speed']
    
    fig = go.Figure()
    
    for i, cyclone in enumerate(cyclone_list[:5]):  # Top 5 cyclones
        values = [
            cyclone.get('max_wind', 0),
            cyclone.get('pressure', 900),
            cyclone.get('diameter', 0),
            cyclone.get('movement_speed', 0)
        ]
        
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=metrics,
            fill='toself',
            name=f"Cyclone {i+1}",
            line=dict(color=['#ff0000', '#ff6b00', '#ffd700', '#00ff00'][i % 4])
        ))
    
    fig.update_layout(
        polar=dict(
            bgcolor='#0f172a',
            radialaxis=dict(visible=True, range=[0, 100], color='#00ffd2')
        ),
        template='plotly_dark',
        paper_bgcolor='#020617',
        font=dict(color='#ffffff', family='monospace', size=11),
        height=500,
        title='Multi-Cyclone Intensity Radar Comparison'
    )
    
    return fig
