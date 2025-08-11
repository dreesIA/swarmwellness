#readiness.py
# ============================================
# components/readiness.py
# ============================================

"""
Readiness score calculations converted from DAX measures.
Implements individual and team readiness metrics.
"""

import pandas as pd
import numpy as np
from typing import Optional, Union


def parse_sleep_text(sleep_text: str) -> Optional[float]:
    """
    Convert sleep text format "HH:MM" to minutes.
    
    DAX equivalent:
    SleepMinutes = hrs * 60 + mins
    
    Args:
        sleep_text: String in format "HH:MM" or "H:MM"
        
    Returns:
        Total minutes as float, or None if invalid
    """
    if pd.isna(sleep_text) or not sleep_text:
        return None
    
    try:
        # Handle various formats
        sleep_text = str(sleep_text).strip()
        
        if ':' in sleep_text:
            parts = sleep_text.split(':')
            if len(parts) == 2:
                hours = float(parts[0])
                minutes = float(parts[1])
                return hours * 60 + minutes
    except (ValueError, AttributeError):
        pass
    
    return None


def calculate_readiness_score(
    sleep: float,
    mood: float,
    energy: float,
    stress: float
) -> Optional[float]:
    """
    Calculate individual readiness score.
    
    DAX equivalent:
    Readiness Score = 
        IF(any blank, BLANK(), 
           (Sleep + Mood + Energy + (10 - Stress))/4)
    
    Args:
        sleep: Sleep quality rating (1-10)
        mood: Mood rating (1-10)
        energy: Energy level rating (1-10)
        stress: Stress level rating (1-10)
        
    Returns:
        Readiness score (0-10) or None if any input is missing
    """
    # Check for any missing values
    if any(pd.isna([sleep, mood, energy, stress])):
        return None
    
    # Calculate inverted stress
    inv_stress = 10 - stress
    
    # Return average of four components
    return (sleep + mood + energy + inv_stress) / 4


def add_readiness_column(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add readiness score column to DataFrame.
    
    Args:
        df: DataFrame with Sleep, Mood, Energy, Stress columns
        
    Returns:
        DataFrame with added 'Readiness' column
    """
    df = df.copy()
    
    # Add SleepMinutes if SleepText exists
    if 'SleepText' in df.columns:
        df['SleepMinutes'] = df['SleepText'].apply(parse_sleep_text)
    
    # Calculate readiness for each row
    if all(col in df.columns for col in ['Sleep', 'Mood', 'Energy', 'Stress']):
        df['Readiness'] = df.apply(
            lambda row: calculate_readiness_score(
                row['Sleep'], row['Mood'], row['Energy'], row['Stress']
            ),
            axis=1
        )
    
    return df


def calculate_team_readiness_by_date(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate team readiness average by date.
    
    DAX equivalent uses AVERAGEX over athletes for each date.
    
    Args:
        df: DataFrame with Readiness and Date columns
        
    Returns:
        DataFrame with Date and TeamReadiness columns
    """
    if 'Readiness' not in df.columns or 'Date' not in df.columns:
        return pd.DataFrame()
    
    # Group by date and calculate mean readiness
    team_readiness = df.groupby('Date')['Readiness'].mean().reset_index()
    team_readiness.columns = ['Date', 'TeamReadiness']
    
    return team_readiness


def calculate_overall_team_readiness(
    df: pd.DataFrame,
    respect_filters: bool = True
) -> Optional[float]:
    """
    Calculate overall team readiness across all data or filtered subset.
    
    Args:
        df: DataFrame with Readiness column
        respect_filters: If True, use the provided (filtered) DataFrame
        
    Returns:
        Overall team readiness score or None
    """
    if 'Readiness' not in df.columns:
        return None
    
    # Calculate mean, ignoring NaN values
    return df['Readiness'].mean()


def get_metric_averages(
    df: pd.DataFrame,
    exclude_zeros: bool = False
) -> dict:
    """
    Calculate averages for all wellness metrics.
    
    DAX equivalents:
    Sleep Quality Avg = AVERAGE('Morning Wellness'[How did you sleep?])
    Mood Avg = AVERAGE('Morning Wellness'[How is your mood?])
    etc.
    
    Args:
        df: DataFrame with metric columns
        exclude_zeros: Whether to exclude zero values from averages
        
    Returns:
        Dictionary of metric averages
    """
    metrics = ['Sleep', 'Mood', 'Energy', 'Stress', 'Soreness', 'Fatigue', 'Readiness']
    averages = {}
    
    for metric in metrics:
        if metric in df.columns:
            series = df[metric]
            if exclude_zeros:
                series = series[series != 0]
            averages[f"{metric}_Avg"] = series.mean()
    
    return averages
