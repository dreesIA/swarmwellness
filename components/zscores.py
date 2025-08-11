#zscores.py
# ============================================
# components/zscores.py
# ============================================

"""
Z-score calculations for normalizing metrics by date cohort.
Converts DAX ALLEXCEPT patterns to pandas group operations.
"""

import pandas as pd
import numpy as np
from typing import Optional, List


def calculate_zscore_by_date(
    df: pd.DataFrame,
    metric_col: str,
    by: List[str] = None,
    zscore_col_suffix: str = "_ZScore"
) -> pd.DataFrame:
    """
    Calculate z-scores for a metric grouped by date.
    
    DAX equivalent pattern:
    [Metric] Z Score = 
        VAR x = SELECTEDVALUE([MetricColumn])
        VAR mean = CALCULATE(AVERAGE([MetricColumn]), 
                           ALLEXCEPT(Table, Date))
        VAR sd = CALCULATE(STDEV.P([MetricColumn]), 
                         ALLEXCEPT(Table, Date))
        RETURN IF(sd = 0, BLANK(), (x - mean) / sd)
    
    Args:
        df: DataFrame with metric and grouping columns
        metric_col: Name of the metric column to z-score
        by: Grouping columns (default: ['Date'])
        zscore_col_suffix: Suffix for z-score column name
        
    Returns:
        DataFrame with added z-score column
    """
    if by is None:
        by = ['Date']
    
    df = df.copy()
    zscore_col = f"{metric_col}{zscore_col_suffix}"
    
    # Check if required columns exist
    if metric_col not in df.columns:
        df[zscore_col] = np.nan
        return df
    
    for col in by:
        if col not in df.columns:
            df[zscore_col] = np.nan
            return df
    
    # Calculate group statistics
    group_stats = df.groupby(by)[metric_col].agg(['mean', 'std']).reset_index()
    
    # Merge back with original data
    df = df.merge(group_stats, on=by, how='left', suffixes=('', '_group'))
    
    # Calculate z-score
    # Use population std (ddof=0) to match DAX STDEV.P
    df[zscore_col] = np.where(
        df['std'] > 0,
        (df[metric_col] - df['mean']) / df['std'],
        np.nan
    )
    
    # Clean up temporary columns
    df = df.drop(['mean', 'std'], axis=1)
    
    return df


def add_all_zscores(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add z-score columns for all standard metrics.
    
    Args:
        df: DataFrame with metric columns
        
    Returns:
        DataFrame with added z-score columns
    """
    df = df.copy()
    
    # List of metrics to calculate z-scores for
    metrics = ['Sleep', 'Mood', 'Energy', 'Stress', 'Soreness', 
               'Fatigue', 'Readiness', 'SleepMinutes']
    
    for metric in metrics:
        if metric in df.columns:
            df = calculate_zscore_by_date(df, metric)
    
    return df


def calculate_readiness_zscore_special(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate readiness z-score using the special pattern from DAX.
    
    Note: DAX version uses AVERAGEX/STDEVX.P pattern.
    This ensures readiness is calculated per athlete-date first,
    then z-scored against the date cohort.
    
    Args:
        df: DataFrame with Readiness column
        
    Returns:
        DataFrame with Readiness_ZScore column
    """
    # Readiness should already be calculated per athlete-date
    # Now calculate z-score by date cohort
    return calculate_zscore_by_date(df, 'Readiness')


def get_athlete_zscore_summary(
    df: pd.DataFrame,
    athlete: str,
    date: pd.Timestamp = None
) -> dict:
    """
    Get z-score summary for a specific athlete.
    
    Args:
        df: DataFrame with z-score columns
        athlete: Athlete name
        date: Optional specific date (uses latest if None)
        
    Returns:
        Dictionary of z-scores for the athlete
    """
    # Filter for athlete
    athlete_df = df[df['Athlete'] == athlete].copy()
    
    if athlete_df.empty:
        return {}
    
    # Use specific date or latest
    if date is None:
        date = athlete_df['Date'].max()
    
    athlete_df = athlete_df[athlete_df['Date'] == date]
    
    if athlete_df.empty:
        return {}
    
    # Extract z-scores
    zscore_cols = [col for col in athlete_df.columns if col.endswith('_ZScore')]
    result = {}
    
    for col in zscore_cols:
        value = athlete_df[col].iloc[0] if not athlete_df.empty else np.nan
        result[col] = value
    
    return result
