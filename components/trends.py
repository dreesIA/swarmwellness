#trends.py
# ============================================
# components/trends.py
# ============================================

"""
Trend calculations comparing current values to previous dates.
Implements DAX trend patterns with UP/DOWN/FLAT indicators.
"""

import pandas as pd
import numpy as np
from typing import Optional, Tuple


# Color codes for trends
TREND_COLORS = {
    'UP': '#a1d99b',      # Light green
    'DOWN': '#fcae91',    # Light red  
    'FLAT': '#fdd0a2',    # Light orange
    'default': '#ffffff'  # White
}

# Arrow symbols for trends
TREND_ARROWS = {
    'UP': '▲',
    'DOWN': '▼',
    'FLAT': '▬',
    'default': ''
}


def compute_trend(
    df: pd.DataFrame,
    metric_col: str,
    trend_col_suffix: str = "_Trend"
) -> pd.DataFrame:
    """
    Calculate trend by comparing to previous date for each athlete.
    
    DAX pattern:
    [Metric] Trend = 
        IF(ISBLANK(prevVal), BLANK(),
           IF(curr > prev, "UP",
              IF(curr < prev, "DOWN", "FLAT")))
    
    Args:
        df: DataFrame with Athlete, Date, and metric columns
        metric_col: Name of the metric column
        trend_col_suffix: Suffix for trend column name
        
    Returns:
        DataFrame with added trend column
    """
    df = df.copy()
    trend_col = f"{metric_col}{trend_col_suffix}"
    
    # Check required columns
    if not all(col in df.columns for col in ['Athlete', 'Date', metric_col]):
        df[trend_col] = np.nan
        return df
    
    # Sort by athlete and date
    df = df.sort_values(['Athlete', 'Date'])
    
    # Calculate difference from previous value per athlete
    df['_prev'] = df.groupby('Athlete')[metric_col].shift(1)
    df['_diff'] = df[metric_col] - df['_prev']
    
    # Map to trend categories
    conditions = [
        pd.isna(df['_diff']),
        df['_diff'] > 0,
        df['_diff'] < 0,
        df['_diff'] == 0
    ]
    
    choices = [np.nan, 'UP', 'DOWN', 'FLAT']
    
    df[trend_col] = np.select(conditions, choices, default=np.nan)
    
    # Clean up temporary columns
    df = df.drop(['_prev', '_diff'], axis=1)
    
    return df


def add_all_trends(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add trend columns for all standard metrics.
    
    Args:
        df: DataFrame with metric columns
        
    Returns:
        DataFrame with added trend columns
    """
    df = df.copy()
    
    # List of metrics to calculate trends for
    metrics = ['Sleep', 'Mood', 'Energy', 'Stress', 'Soreness', 
               'Fatigue', 'Readiness', 'SleepMinutes']
    
    for metric in metrics:
        if metric in df.columns:
            df = compute_trend(df, metric)
    
    return df


def format_display_value(
    value: float,
    trend: str,
    decimals: int = 1
) -> str:
    """
    Format value with trend arrow for display.
    
    Pattern: "[value] [arrow]"
    
    Args:
        value: Numeric value to display
        trend: Trend category (UP/DOWN/FLAT)
        decimals: Number of decimal places
        
    Returns:
        Formatted string with value and arrow
    """
    if pd.isna(value):
        return ""
    
    # Format value
    if decimals == 0:
        value_str = f"{int(value)}"
    else:
        value_str = f"{value:.{decimals}f}"
    
    # Get arrow
    arrow = TREND_ARROWS.get(trend, TREND_ARROWS['default'])
    
    # Combine
    if arrow:
        return f"{value_str} {arrow}"
    return value_str


def get_trend_color(trend: str) -> str:
    """
    Get hex color code for a trend.
    
    Args:
        trend: Trend category (UP/DOWN/FLAT)
        
    Returns:
        Hex color code
    """
    return TREND_COLORS.get(trend, TREND_COLORS['default'])


def get_latest_trends(
    df: pd.DataFrame,
    athlete: str
) -> dict:
    """
    Get the latest trends for a specific athlete.
    
    Args:
        df: DataFrame with trend columns
        athlete: Athlete name
        
    Returns:
        Dictionary of latest trends
    """
    # Filter for athlete
    athlete_df = df[df['Athlete'] == athlete].copy()
    
    if athlete_df.empty:
        return {}
    
    # Get latest date
    latest_date = athlete_df['Date'].max()
    latest_row = athlete_df[athlete_df['Date'] == latest_date]
    
    if latest_row.empty:
        return {}
    
    # Extract trends
    trend_cols = [col for col in latest_row.columns if col.endswith('_Trend')]
    result = {}
    
    for col in trend_cols:
        value = latest_row[col].iloc[0] if not latest_row.empty else None
        result[col] = value
    
    return result


def create_trend_summary(
    df: pd.DataFrame,
    athlete: str,
    metrics: list = None
) -> pd.DataFrame:
    """
    Create a summary table of trends for an athlete.
    
    Args:
        df: DataFrame with metrics and trends
        athlete: Athlete name
        metrics: List of metrics to include (default: all)
        
    Returns:
        DataFrame with metric, value, trend, and display columns
    """
    if metrics is None:
        metrics = ['Sleep', 'Mood', 'Energy', 'Stress', 'Readiness']
    
    # Filter for athlete
    athlete_df = df[df['Athlete'] == athlete].copy()
    
    if athlete_df.empty:
        return pd.DataFrame()
    
    # Get latest date
    latest_date = athlete_df['Date'].max()
    latest_row = athlete_df[athlete_df['Date'] == latest_date].iloc[0]
    
    # Build summary
    summary_data = []
    
    for metric in metrics:
        if metric in df.columns:
            value = latest_row.get(metric, np.nan)
            trend = latest_row.get(f"{metric}_Trend", None)
            display = format_display_value(value, trend)
            color = get_trend_color(trend)
            
            summary_data.append({
                'Metric': metric,
                'Value': value,
                'Trend': trend,
                'Display': display,
                'Color': color
            })
    
    return pd.DataFrame(summary_data)

