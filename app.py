#app.py
"""
Main Streamlit application for the Wellness Dashboard with AI insights.
Orchestrates data loading, processing, visualization, and AI analysis.
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

# Import utility modules
from utils.data_loader import (
    load_google_sheet, 
    refresh_data, 
    get_latest_date,
    get_athletes
)

# Import component modules
from components.readiness import (
    add_readiness_column,
    calculate_team_readiness_by_date,
    calculate_overall_team_readiness,
    get_metric_averages
)
from components.zscores import add_all_zscores
from components.trends import add_all_trends
from components.metric_cards import (
    render_metric_row,
    create_athlete_metrics_display,
    render_team_summary_card
)
from components.charts import (
    create_trend_line_chart,
    create_comparison_chart,
    create_heatmap,
    create_radar_chart
)
from components.profile import (
    render_athlete_profile,
    render_historical_table,
    render_insights
)

# Import AI components (conditional based on API key availability)
try:
    from components.ai_insights_ui import (
        render_ai_insights_panel,
        render_team_ai_insights,
        render_athlete_comparison,
        render_ai_chat_interface
    )
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

# Check if OpenAI API key is configured
def check_openai_configured():
    """Check if OpenAI API key is available."""
    # Check environment variable
    if os.getenv("OPENAI_API_KEY"):
        return True
    # Check Streamlit secrets
    try:
        if st.secrets.get("OPENAI_API_KEY"):
            return True
    except:
        pass
    return False

# Configuration
SHEET_TITLE = "Wellness Dashboard Data"  # Change to your sheet name
WORKSHEET_NAME = "Form Responses 1"  # Default for Google Forms
USE_FALLBACK = True  # Use CSV if Google Sheets fails

# Page configuration
st.set_page_config(
    page_title="Wellness Dashboard",
    page_icon="💪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main > div {
        padding-top: 2rem;
    }
    .stButton>button {
        width: 100%;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .ai-insights {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 0.5rem;
        color: white;
    }
</style>
""", unsafe_allow_html=True)


def main():
    """Main application logic."""
    
    # Check AI availability
    ai_enabled = AI_AVAILABLE and check_openai_configured()
    
    # Title and header
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.title("🏃‍♂️ Wellness Dashboard")
        st.markdown("Track athlete readiness and wellness metrics")
    with col2:
        if ai_enabled:
            st.success("🤖 AI Insights Enabled")
        else:
            with st.expander("Enable AI Insights"):
                st.info("""
                To enable AI-powered insights:
                1. Install OpenAI: `pip install openai`
                2. Add your API key to `.env` file:
                   `OPENAI_API_KEY=your-key-here`
                3. Or add to Streamlit secrets
                """)
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Controls")
        
        # Refresh button
        if st.button("🔄 Refresh Data"):
            refresh_data()
            st.rerun()
        
        st.divider()
    
    # Load data
    try:
        with st.spinner("Loading data..."):
            df = load_google_sheet(
                sheet_title=SHEET_TITLE,
                worksheet_name=WORKSHEET_NAME,
                use_fallback=USE_FALLBACK
            )
            
            if df.empty:
                st.error("No data available. Please check your data source.")
                return
            
            # Process data - add calculated columns
            df = add_readiness_column(df)
            df = add_all_trends(df)
            df = add_all_zscores(df)
            
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return
    
    # Get available athletes
    athletes = get_athletes(df)
    
    if not athletes:
        st.warning("No athletes found in the data")
        return
    
    # Sidebar athlete selector
    with st.sidebar:
        selected_athlete = st.selectbox(
            "Select Athlete",
            options=athletes,
            index=0
        )
        
        st.divider()
        
        # Date filter
        st.subheader("📅 Date Range")
        
        min_date = df['Date'].min().date() if 'Date' in df.columns else datetime.now().date()
        max_date = df['Date'].max().date() if 'Date' in df.columns else datetime.now().date()
        
        date_range = st.date_input(
            "Select dates",
            value=(max_date - timedelta(days=30), max_date),
            min_value=min_date,
            max_value=max_date
        )
        
        # Apply date filter
        if len(date_range) == 2:
            mask = (df['Date'].dt.date >= date_range[0]) & (df['Date'].dt.date <= date_range[1])
            df = df[mask]
        
        st.divider()
        
        # AI Settings (if enabled)
        if ai_enabled:
            st.subheader("🤖 AI Settings")
            
            analysis_mode = st.radio(
                "Analysis Mode",
                ["Individual", "Team", "Comparison"],
                index=0
            )
            
            if st.button("💬 Open AI Coach"):
                st.session_state['show_chat'] = True
    
    # Main content area
    # Team Summary
    render_team_summary_card(df)
    
    # AI Team Insights (if enabled and in team mode)
    if ai_enabled and 'analysis_mode' in locals() and analysis_mode == "Team":
        render_team_ai_insights(df)
    
    # Athlete Profile
    st.header(f"Athlete: {selected_athlete}")
    render_athlete_profile(df, selected_athlete)
    
    # Metric Cards
    st.subheader("Current Metrics")
    metrics = create_athlete_metrics_display(df, selected_athlete)
    
    if metrics:
        render_metric_row(metrics, columns=5)
    else:
        st.info("No current metrics available")
    
    # AI Insights Panel (if enabled and in individual mode)
    if ai_enabled and 'analysis_mode' in locals() and analysis_mode == "Individual":
        render_ai_insights_panel(df, selected_athlete)
    
    # AI Comparison (if enabled and in comparison mode)
    if ai_enabled and 'analysis_mode' in locals() and analysis_mode == "Comparison":
        render_athlete_comparison(df, athletes)
    
    # Charts Section
    st.subheader("Trends Analysis")
    
    # Create tabs for different visualizations
    tab_names = ["📈 Trends", "🎯 Radar", "🔥 Heatmap", "📊 Comparison"]
    if ai_enabled:
        tab_names.append("🤖 AI Analysis")
    
    tabs = st.tabs(tab_names)
    
    with tabs[0]:
        # Trend charts for key metrics
        col1, col2 = st.columns(2)
        
        with col1:
            st.plotly_chart(
                create_trend_line_chart(df, 'Readiness', selected_athlete),
                use_container_width=True
            )
            st.plotly_chart(
                create_trend_line_chart(df, 'Sleep', selected_athlete),
                use_container_width=True
            )
        
        with col2:
            st.plotly_chart(
                create_trend_line_chart(df, 'Energy', selected_athlete),
                use_container_width=True
            )
            st.plotly_chart(
                create_trend_line_chart(df, 'Stress', selected_athlete),
                use_container_width=True
            )
    
    with tabs[1]:
        # Radar chart
        st.plotly_chart(
            create_radar_chart(df, selected_athlete),
            use_container_width=True
        )
    
    with tabs[2]:
        # Z-score heatmap
        st.plotly_chart(
            create_heatmap(df, selected_athlete),
            use_container_width=True
        )
    
    with tabs[3]:
        # Multi-athlete comparison
        st.subheader("Compare Athletes")
        
        compare_athletes = st.multiselect(
            "Select athletes to compare",
            options=athletes,
            default=[selected_athlete] + (athletes[:2] if len(athletes) > 1 else [])
        )
        
        if len(compare_athletes) > 1:
            metric_to_compare = st.selectbox(
                "Select metric",
                options=['Readiness', 'Sleep', 'Mood', 'Energy', 'Stress']
            )
            
            st.plotly_chart(
                create_comparison_chart(df, compare_athletes, metric_to_compare),
                use_container_width=True
            )
        else:
            st.info("Select at least 2 athletes to compare")
    
    # AI Analysis tab (if enabled)
    if ai_enabled and len(tabs) > 4:
        with tabs[4]:
            st.subheader("🧠 Deep AI Analysis")
            
            analysis_type = st.selectbox(
                "Choose Analysis Type",
                ["Performance Prediction", "Recovery Recommendations", 
                 "Training Load Optimization", "Injury Risk Assessment"]
            )
            
            if st.button("Generate Analysis"):
                with st.spinner("Running AI analysis..."):
                    from utils.ai_insights import WellnessAIAnalyst
                    
                    analyst = WellnessAIAnalyst()
                    summary = analyst.prepare_data_summary(df, selected_athlete)
                    
                    # Focus areas based on analysis type
                    focus_map = {
                        "Performance Prediction": ["readiness trends", "energy levels", "recovery status"],
                        "Recovery Recommendations": ["sleep quality", "stress management", "fatigue levels"],
                        "Training Load Optimization": ["readiness score", "fatigue", "soreness"],
                        "Injury Risk Assessment": ["soreness trends", "fatigue accumulation", "recovery patterns"]
                    }
                    
                    insights = analyst.generate_athlete_insights(
                        summary,
                        focus_areas=focus_map.get(analysis_type, [])
                    )
                    
                    st.markdown(insights)
    
    # Historical Data Table
    st.subheader("Historical Data")
    render_historical_table(df, selected_athlete, num_days=14)
    
    # Basic Insights (non-AI)
    render_insights(df, selected_athlete)
    
    # AI Chat Interface (if enabled and requested)
    if ai_enabled and st.session_state.get('show_chat', False):
        with st.expander("💬 AI Coach Chat", expanded=True):
            render_ai_chat_interface(df, selected_athlete)
            if st.button("Close Chat"):
                st.session_state['show_chat'] = False
                st.rerun()
    
    # Footer
    st.divider()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        latest_date = get_latest_date(df)
        if latest_date:
            st.caption(f"Last updated: {latest_date.strftime('%Y-%m-%d %H:%M')}")
    
    with col2:
        st.caption(f"Total athletes: {len(athletes)}")
    
    with col3:
        if ai_enabled:
            st.caption("🤖 AI-Powered Analytics Active")
        else:
            st.caption("📊 Standard Analytics Mode")


if __name__ == "__main__":
    main()