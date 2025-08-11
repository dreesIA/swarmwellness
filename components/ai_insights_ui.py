# ============================================
# components/ai_insights_ui.py
# ============================================

"""
UI components for AI-powered insights display.
"""

import streamlit as st
import pandas as pd
from typing import Optional, List
from utils.ai_insights import (
    WellnessAIAnalyst,
    get_cached_insights
)


def render_ai_insights_panel(
    df: pd.DataFrame,
    athlete: str,
    show_risk: bool = True
):
    """
    Render the AI insights panel for an athlete.
    
    Args:
        df: DataFrame with wellness data
        athlete: Athlete name
        show_risk: Whether to show risk assessment
    """
    st.subheader("🤖 AI-Powered Insights")
    
    # Create tabs for different insight types
    tabs = st.tabs(["Individual Analysis", "Risk Assessment", "Recommendations"])
    
    with tabs[0]:
        with st.spinner("Analyzing wellness data..."):
            insights = get_cached_insights(df, athlete, "individual")
            
            # Display insights in a nice format
            st.markdown("""
            <div style="
                background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                padding: 1.5rem;
                border-radius: 0.5rem;
                border-left: 4px solid #667eea;
            ">
            """, unsafe_allow_html=True)
            
            st.markdown(insights)
            
            st.markdown("</div>", unsafe_allow_html=True)
    
    with tabs[1]:
        if show_risk:
            analyst = WellnessAIAnalyst()
            risk_assessment = analyst.predict_performance_risk(df, athlete)
            
            # Color code based on risk level
            risk_colors = {
                'high': '#ff4444',
                'moderate': '#ff9900',
                'low': '#ffcc00',
                'minimal': '#00cc44'
            }
            
            color = risk_colors.get(risk_assessment['risk_level'], '#666666')
            
            st.markdown(f"""
            <div style="
                background: white;
                padding: 1rem;
                border-radius: 0.5rem;
                border-left: 4px solid {color};
                margin-bottom: 1rem;
            ">
                <h4 style="color: {color}; margin: 0;">
                    Risk Level: {risk_assessment['risk_level'].upper()}
                </h4>
                <p style="margin: 0.5rem 0;">
                    {risk_assessment['recommendation']}
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            if risk_assessment['factors']:
                st.markdown("**Risk Factors Identified:**")
                for factor in risk_assessment['factors']:
                    st.markdown(f"• {factor}")
    
    with tabs[2]:
        # Quick action buttons for common analyses
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📈 Generate Weekly Report"):
                with st.spinner("Generating report..."):
                    analyst = WellnessAIAnalyst()
                    summary = analyst.prepare_data_summary(df, athlete, days=7)
                    report = analyst.generate_athlete_insights(
                        summary, 
                        focus_areas=["recovery", "training readiness", "sleep quality"]
                    )
                    st.markdown(report)
        
        with col2:
            if st.button("💡 Get Recovery Tips"):
                with st.spinner("Generating tips..."):
                    analyst = WellnessAIAnalyst()
                    summary = analyst.prepare_data_summary(df, athlete, days=3)
                    tips = analyst.generate_athlete_insights(
                        summary,
                        focus_areas=["recovery strategies", "sleep optimization", "stress management"]
                    )
                    st.markdown(tips)


def render_team_ai_insights(df: pd.DataFrame):
    """
    Render team-level AI insights.
    
    Args:
        df: DataFrame with all athletes' data
    """
    st.subheader("🏆 Team Intelligence Report")
    
    with st.spinner("Analyzing team performance..."):
        insights = get_cached_insights(df, None, "team")
        
        # Display in an attractive card
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            border-radius: 0.5rem;
            margin-bottom: 2rem;
        ">
            <h3 style="color: white; margin-top: 0;">Team Wellness Analysis</h3>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(insights)
        
        # Add export button
        if st.button("📄 Export Team Report"):
            report_date = pd.Timestamp.now().strftime("%Y-%m-%d")
            filename = f"team_wellness_report_{report_date}.txt"
            st.download_button(
                label="Download Report",
                data=insights,
                file_name=filename,
                mime="text/plain"
            )


def render_athlete_comparison(
    df: pd.DataFrame,
    athletes: List[str]
):
    """
    Render AI-powered athlete comparison.
    
    Args:
        df: DataFrame with wellness data
        athletes: List of athlete names
    """
    if len(athletes) < 2:
        st.info("Select at least 2 athletes for comparison")
        return
    
    st.subheader("🔄 Athlete Comparison Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        athlete1 = st.selectbox("First Athlete", athletes, index=0)
    
    with col2:
        athlete2 = st.selectbox(
            "Second Athlete", 
            [a for a in athletes if a != athlete1],
            index=0
        )
    
    if st.button("Generate Comparison"):
        with st.spinner("Comparing athletes..."):
            comparison = get_cached_insights(
                df, 
                athlete1, 
                "comparison",
                athlete2=athlete2
            )
            
            # Display comparison in columns
            st.markdown(comparison)


def render_ai_chat_interface(
    df: pd.DataFrame,
    athlete: str = None
):
    """
    Render a chat interface for asking questions about the data.
    
    Args:
        df: DataFrame with wellness data
        athlete: Optional athlete focus
    """
    st.subheader("💬 Ask the AI Coach")
    
    # Initialize chat history in session state
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # Chat input
    user_question = st.text_input(
        "Ask a question about wellness data...",
        placeholder="e.g., 'What should John focus on this week?' or 'How is the team's sleep quality?'"
    )
    
    if user_question:
        analyst = WellnessAIAnalyst()
        
        # Prepare context
        if athlete:
            context = analyst.prepare_data_summary(df, athlete)
            context_str = f"Analyzing data for {athlete}"
        else:
            context = analyst.prepare_data_summary(df)
            context_str = "Analyzing team data"
        
        # Generate response
        with st.spinner("Thinking..."):
            try:
                response = analyst.client.chat.completions.create(
                    model=analyst.model,
                    messages=[
                        {"role": "system", "content": analyst.system_prompt},
                        {"role": "user", "content": f"""
                        Context: {context_str}
                        Data: {context}
                        
                        Question: {user_question}
                        
                        Provide a helpful, specific answer based on the data.
                        """}
                    ],
                    temperature=0.7,
                    max_tokens=300
                )
                
                answer = response.choices[0].message.content
                
                # Add to chat history
                st.session_state.chat_history.append({
                    'question': user_question,
                    'answer': answer
                })
                
                # Display chat history
                for chat in st.session_state.chat_history[-3:]:  # Show last 3 exchanges
                    st.markdown(f"**You:** {chat['question']}")
                    st.markdown(f"**AI Coach:** {chat['answer']}")
                    st.divider()
                    
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    # Clear chat button
    if st.button("Clear Chat"):
        st.session_state.chat_history = []
        st.rerun()