#charts.py
# ============================================
# components/charts.py
# ============================================

"""
Chart components using Plotly for interactive visualizations.
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import streamlit as st
from typing import Optional, List


def create_trend_line_chart(
    df: pd.DataFrame,
    metric: str,
    athlete: str = None,
    show_team_overlay: bool = True,
    height: int = 400
) -> go.Figure:
    """
    Create a line chart for a metric over time.
    
    Args:
        df: DataFrame with Date, Athlete, and metric columns
        metric: Name of the metric column to plot
        athlete: Specific athlete to highlight (None for all)
        show_team_overlay: Whether to show team average
        height: Chart height in pixels
        
    Returns:
        Plotly figure object
    """
    fig = go.Figure()
    
    # Filter for valid data
    plot_df = df[df[metric].notna()].copy()
    
    if plot_df.empty:
        fig.add_annotation(
            text="No data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return fig
    
    # Add athlete line
    if athlete:
        athlete_df = plot_df[plot_df['Athlete'] == athlete]
        
        # Get trend data if available
        trend_col = f"{metric}_Trend"
        if trend_col in athlete_df.columns:
            hover_text = [
                f"Date: {row['Date'].strftime('%Y-%m-%d')}<br>"
                f"{metric}: {row[metric]:.1f}<br>"
                f"Trend: {row[trend_col]}"
                for _, row in athlete_df.iterrows()
            ]
        else:
            hover_text = [
                f"Date: {row['Date'].strftime('%Y-%m-%d')}<br>"
                f"{metric}: {row[metric]:.1f}"
                for _, row in athlete_df.iterrows()
            ]
        
        fig.add_trace(go.Scatter(
            x=athlete_df['Date'],
            y=athlete_df[metric],
            mode='lines+markers',
            name=athlete,
            line=dict(color='#667eea', width=3),
            marker=dict(size=8),
            hovertemplate='%{text}',
            text=hover_text
        ))
    
    # Add team average overlay
    if show_team_overlay:
        team_avg = plot_df.groupby('Date')[metric].mean().reset_index()
        
        fig.add_trace(go.Scatter(
            x=team_avg['Date'],
            y=team_avg[metric],
            mode='lines',
            name='Team Average',
            line=dict(color='#ffa500', width=2, dash='dash'),
            opacity=0.7,
            hovertemplate='Date: %{x}<br>Team Avg: %{y:.1f}'
        ))
    
    # Update layout
    fig.update_layout(
        title=f"{metric} Trend",
        xaxis_title="Date",
        yaxis_title=metric,
        height=height,
        hovermode='x unified',
        showlegend=True,
        template='plotly_white',
        margin=dict(l=0, r=0, t=40, b=0)
    )
    
    # Set y-axis range for 1-10 metrics
    if metric in ['Sleep', 'Mood', 'Energy', 'Stress', 'Soreness', 'Fatigue', 'Readiness']:
        fig.update_yaxis(range=[0, 10.5])
    
    return fig


def create_comparison_chart(
    df: pd.DataFrame,
    athletes: List[str],
    metric: str,
    chart_type: str = 'line',
    height: int = 400
) -> go.Figure:
    """
    Create a comparison chart for multiple athletes.
    
    Args:
        df: DataFrame with data
        athletes: List of athlete names to compare
        metric: Metric to compare
        chart_type: 'line' or 'bar'
        height: Chart height
        
    Returns:
        Plotly figure
    """
    fig = go.Figure()
    
    # Filter data
    plot_df = df[df['Athlete'].isin(athletes) & df[metric].notna()]
    
    if plot_df.empty:
        fig.add_annotation(
            text="No data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return fig
    
    # Create traces for each athlete
    colors = px.colors.qualitative.Set2
    
    for idx, athlete in enumerate(athletes):
        athlete_df = plot_df[plot_df['Athlete'] == athlete]
        color = colors[idx % len(colors)]
        
        if chart_type == 'bar':
            fig.add_trace(go.Bar(
                x=athlete_df['Date'],
                y=athlete_df[metric],
                name=athlete,
                marker_color=color
            ))
        else:
            fig.add_trace(go.Scatter(
                x=athlete_df['Date'],
                y=athlete_df[metric],
                mode='lines+markers',
                name=athlete,
                line=dict(color=color, width=2),
                marker=dict(size=6)
            ))
    
    # Update layout
    fig.update_layout(
        title=f"{metric} Comparison",
        xaxis_title="Date",
        yaxis_title=metric,
        height=height,
        hovermode='x unified',
        showlegend=True,
        template='plotly_white',
        barmode='group' if chart_type == 'bar' else None
    )
    
    return fig


def create_heatmap(
    df: pd.DataFrame,
    athlete: str,
    metrics: List[str] = None,
    height: int = 400
) -> go.Figure:
    """
    Create a heatmap of z-scores for an athlete.
    
    Args:
        df: DataFrame with z-score columns
        athlete: Athlete name
        metrics: List of metrics (uses z-score columns)
        height: Chart height
        
    Returns:
        Plotly figure
    """
    # Filter for athlete
    athlete_df = df[df['Athlete'] == athlete].copy()
    
    if metrics is None:
        # Find all z-score columns
        metrics = [col.replace('_ZScore', '') 
                  for col in athlete_df.columns 
                  if col.endswith('_ZScore')]
    
    # Prepare data for heatmap
    zscore_cols = [f"{m}_ZScore" for m in metrics if f"{m}_ZScore" in athlete_df.columns]
    
    if not zscore_cols:
        fig = go.Figure()
        fig.add_annotation(
            text="No z-score data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return fig
    
    # Sort by date
    athlete_df = athlete_df.sort_values('Date')
    
    # Create matrix
    z_data = athlete_df[zscore_cols].T.values
    
    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        z=z_data,
        x=athlete_df['Date'].dt.strftime('%Y-%m-%d'),
        y=[col.replace('_ZScore', '') for col in zscore_cols],
        colorscale='RdYlGn',
        zmid=0,
        text=z_data.round(2),
        texttemplate='%{text}',
        textfont={"size": 10},
        colorbar=dict(title="Z-Score")
    ))
    
    fig.update_layout(
        title=f"Z-Score Heatmap - {athlete}",
        xaxis_title="Date",
        yaxis_title="Metric",
        height=height,
        template='plotly_white'
    )
    
    return fig


def create_radar_chart(
    df: pd.DataFrame,
    athlete: str,
    date: pd.Timestamp = None,
    metrics: List[str] = None
) -> go.Figure:
    """
    Create a radar chart for athlete metrics.
    
    Args:
        df: DataFrame with metrics
        athlete: Athlete name
        date: Specific date (uses latest if None)
        metrics: List of metrics to include
        
    Returns:
        Plotly figure
    """
    # Filter for athlete
    athlete_df = df[df['Athlete'] == athlete].copy()
    
    if athlete_df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return fig
    
    # Use specific date or latest
    if date is None:
        date = athlete_df['Date'].max()
    
    row = athlete_df[athlete_df['Date'] == date]
    
    if row.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No data for selected date",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return fig
    
    row = row.iloc[0]
    
    # Default metrics
    if metrics is None:
        metrics = ['Sleep', 'Mood', 'Energy', 'Stress', 'Readiness']
    
    # Get values
    values = []
    labels = []
    
    for metric in metrics:
        if metric in row.index:
            # Invert stress for better visualization
            if metric == 'Stress':
                values.append(10 - row[metric])
                labels.append('Low Stress')
            else:
                values.append(row[metric])
                labels.append(metric)
    
    if not values:
        fig = go.Figure()
        fig.add_annotation(
            text="No metric data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return fig
    
    # Close the polygon
    values.append(values[0])
    labels.append(labels[0])
    
    # Create radar chart
    fig = go.Figure(data=go.Scatterpolar(
        r=values,
        theta=labels,
        fill='toself',
        name=athlete,
        line=dict(color='#667eea'),
        fillcolor='rgba(102, 126, 234, 0.3)'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 10]
            )
        ),
        showlegend=False,
        title=f"Wellness Profile - {athlete} ({date.strftime('%Y-%m-%d')})",
        template='plotly_white'
    )
    
    return fig
