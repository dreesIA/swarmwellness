#profile.py
# ============================================
# components/profile.py
# ============================================

"""
Athlete profile components for displaying individual summaries.
"""

import streamlit as st
import pandas as pd
from typing import Optional


def render_athlete_profile(
    df: pd.DataFrame,
    athlete: str
):
    """
    Render athlete profile section with key stats.
    
    Args:
        df: DataFrame with athlete data
        athlete: Athlete name
    """
    # Filter for athlete
    athlete_df = df[df['Athlete'] == athlete].copy()
    
    if athlete_df.empty:
        st.warning(f"No data found for {athlete}")
        return
    
    # Calculate profile stats
    latest_date = athlete_df['Date'].max()
    total_days = athlete_df['Date'].nunique()
    
    # Get averages
    avg_readiness = athlete_df['Readiness'].mean() if 'Readiness' in athlete_df.columns else None
    avg_sleep = athlete_df['Sleep'].mean() if 'Sleep' in athlete_df.columns else None
    avg_mood = athlete_df['Mood'].mean() if 'Mood' in athlete_df.columns else None
    
    # Create profile card
    st.markdown(f"""
    <div style="
        background: white;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-left: 4px solid #667eea;
        margin-bottom: 2rem;
    ">
        <h3 style="margin: 0; color: #333;">{athlete}</h3>
        <p style="color: #666; margin: 0.5rem 0;">
            Last Entry: {latest_date.strftime('%Y-%m-%d')} | 
            Total Days: {total_days}
        </p>
        <div style="display: flex; gap: 2rem; margin-top: 1rem;">
            <div>
                <strong>Avg Readiness:</strong> {avg_readiness:.1f if avg_readiness else 'N/A'}
            </div>
            <div>
                <strong>Avg Sleep:</strong> {avg_sleep:.1f if avg_sleep else 'N/A'}
            </div>
            <div>
                <strong>Avg Mood:</strong> {avg_mood:.1f if avg_mood else 'N/A'}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_historical_table(
    df: pd.DataFrame,
    athlete: str,
    num_days: int = 7
):
    """
    Render historical data table for an athlete.
    
    Args:
        df: DataFrame with athlete data
        athlete: Athlete name
        num_days: Number of recent days to show
    """
    # Filter and sort
    athlete_df = df[df['Athlete'] == athlete].copy()
    athlete_df = athlete_df.sort_values('Date', ascending=False).head(num_days)
    
    if athlete_df.empty:
        st.info("No historical data available")
        return
    
    # Select columns to display
    display_cols = ['Date', 'Sleep', 'Mood', 'Energy', 'Stress', 
                   'Soreness', 'Fatigue', 'Readiness']
    
    # Filter to existing columns
    display_cols = [col for col in display_cols if col in athlete_df.columns]
    
    # Format data
    display_df = athlete_df[display_cols].copy()
    
    # Format date
    if 'Date' in display_df.columns:
        display_df['Date'] = display_df['Date'].dt.strftime('%Y-%m-%d')
    
    # Round numeric columns
    numeric_cols = display_df.select_dtypes(include=['float64', 'int64']).columns
    for col in numeric_cols:
        display_df[col] = display_df[col].round(1)
    
    # Display table
    st.subheader(f"Recent History ({num_days} days)")
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )


def render_insights(
    df: pd.DataFrame,
    athlete: str
):
    """
    Generate and display insights for an athlete.
    
    Args:
        df: DataFrame with athlete data
        athlete: Athlete name
    """
    athlete_df = df[df['Athlete'] == athlete].copy()
    
    if athlete_df.empty or len(athlete_df) < 2:
        return
    
    insights = []
    
    # Check readiness trend
    if 'Readiness_Trend' in athlete_df.columns:
        latest_trend = athlete_df.iloc[-1]['Readiness_Trend']
        if latest_trend == 'UP':
            insights.append("✅ Readiness is improving")
        elif latest_trend == 'DOWN':
            insights.append("⚠️ Readiness has decreased")
    
    # Check stress levels
    if 'Stress' in athlete_df.columns:
        recent_stress = athlete_df.tail(3)['Stress'].mean()
        if recent_stress > 7:
            insights.append("⚠️ High stress levels detected")
        elif recent_stress < 3:
            insights.append("✅ Stress levels are well managed")
    
    # Check sleep consistency
    if 'SleepMinutes' in athlete_df.columns:
        sleep_std = athlete_df['SleepMinutes'].std()
        if sleep_std > 60:  # More than 1 hour variation
            insights.append("💡 Sleep duration varies significantly")
    
    # Display insights
    if insights:
        st.subheader("Insights")
        for insight in insights:
            st.markdown(insight)
