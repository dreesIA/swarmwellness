#metric_cards.py
# ============================================
# components/metric_cards.py
# ============================================

"""
Streamlit metric card components for displaying KPIs with trends.
"""

import streamlit as st
import pandas as pd
from components.trends import format_display_value, get_trend_color


def render_metric_card(
    title: str,
    value: float,
    trend: str = None,
    show_arrow: bool = True,
    custom_color: str = None,
    width: str = "100%"
):
    """
    Render a styled metric card in Streamlit.
    
    Args:
        title: Card title
        value: Metric value
        trend: Trend indicator (UP/DOWN/FLAT)
        show_arrow: Whether to show trend arrow
        custom_color: Override background color
        width: CSS width property
    """
    # Get display value with arrow
    if show_arrow and trend:
        display_value = format_display_value(value, trend, decimals=1)
    else:
        display_value = f"{value:.1f}" if not pd.isna(value) else "N/A"
    
    # Get background color
    if custom_color:
        bg_color = custom_color
    elif trend:
        bg_color = get_trend_color(trend)
    else:
        bg_color = "#ffffff"
    
    # Create card HTML
    card_html = f"""
    <div style="
        background-color: {bg_color};
        padding: 1.5rem;
        border-radius: 0.5rem;
        text-align: center;
        width: {width};
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    ">
        <h4 style="
            margin: 0;
            color: #666;
            font-size: 0.9rem;
            font-weight: 500;
            margin-bottom: 0.5rem;
        ">{title}</h4>
        <p style="
            margin: 0;
            color: #333;
            font-size: 1.8rem;
            font-weight: bold;
        ">{display_value}</p>
    </div>
    """
    
    st.markdown(card_html, unsafe_allow_html=True)


def render_metric_row(
    metrics: dict,
    columns: int = 5
):
    """
    Render a row of metric cards.
    
    Args:
        metrics: Dictionary with metric data
                 {name: {'value': x, 'trend': 'UP', 'title': 'Label'}}
        columns: Number of columns in the row
    """
    cols = st.columns(columns)
    
    for idx, (metric_name, metric_data) in enumerate(metrics.items()):
        col_idx = idx % columns
        with cols[col_idx]:
            render_metric_card(
                title=metric_data.get('title', metric_name),
                value=metric_data.get('value', 0),
                trend=metric_data.get('trend', None),
                show_arrow=metric_data.get('show_arrow', True)
            )


def create_athlete_metrics_display(
    df: pd.DataFrame,
    athlete: str,
    date: pd.Timestamp = None
) -> dict:
    """
    Prepare metrics data for display cards.
    
    Args:
        df: DataFrame with metrics and trends
        athlete: Athlete name
        date: Specific date (uses latest if None)
        
    Returns:
        Dictionary of metrics ready for display
    """
    # Filter for athlete
    athlete_df = df[df['Athlete'] == athlete].copy()
    
    if athlete_df.empty:
        return {}
    
    # Use specific date or latest
    if date is None:
        date = athlete_df['Date'].max()
    
    row = athlete_df[athlete_df['Date'] == date]
    
    if row.empty:
        return {}
    
    row = row.iloc[0]
    
    # Build metrics dictionary
    metrics = {
        'sleep': {
            'title': 'Sleep Quality',
            'value': row.get('Sleep', 0),
            'trend': row.get('Sleep_Trend', None)
        },
        'mood': {
            'title': 'Mood',
            'value': row.get('Mood', 0),
            'trend': row.get('Mood_Trend', None)
        },
        'energy': {
            'title': 'Energy',
            'value': row.get('Energy', 0),
            'trend': row.get('Energy_Trend', None)
        },
        'stress': {
            'title': 'Stress',
            'value': row.get('Stress', 0),
            'trend': row.get('Stress_Trend', None)
        },
        'readiness': {
            'title': 'Readiness',
            'value': row.get('Readiness', 0),
            'trend': row.get('Readiness_Trend', None)
        }
    }
    
    return metrics


def render_team_summary_card(
    df: pd.DataFrame,
    date: pd.Timestamp = None
):
    """
    Render team readiness summary card.
    
    Args:
        df: DataFrame with readiness data
        date: Specific date (uses latest if None)
    """
    if date is None and 'Date' in df.columns:
        date = df['Date'].max()
    
    if date is not None:
        day_df = df[df['Date'] == date]
        team_readiness = day_df['Readiness'].mean() if 'Readiness' in day_df.columns else None
        num_athletes = day_df['Athlete'].nunique() if 'Athlete' in day_df.columns else 0
    else:
        team_readiness = None
        num_athletes = 0
    
    # Create summary card
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 0.5rem;
        color: white;
        margin-bottom: 2rem;
    ">
        <h2 style="margin: 0; margin-bottom: 1rem;">Team Overview</h2>
        <div style="display: flex; justify-content: space-around;">
            <div>
                <h3 style="margin: 0; opacity: 0.9;">Team Readiness</h3>
                <p style="font-size: 2.5rem; margin: 0; font-weight: bold;">
                    {:.1f}
                </p>
            </div>
            <div>
                <h3 style="margin: 0; opacity: 0.9;">Athletes</h3>
                <p style="font-size: 2.5rem; margin: 0; font-weight: bold;">
                    {}
                </p>
            </div>
        </div>
    </div>
    """.format(
        team_readiness if team_readiness else 0.0,
        num_athletes
    ), unsafe_allow_html=True)

