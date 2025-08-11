"""
AI-powered insights module using OpenAI's GPT models.
Analyzes wellness data and provides personalized recommendations.
"""

import openai
import streamlit as st
import pandas as pd
import numpy as np
import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
def init_openai_client():
    """Initialize OpenAI client with API key from environment or Streamlit secrets."""
    api_key = None
    
    # Try environment variable first
    api_key = os.getenv("OPENAI_API_KEY")
    
    # Try Streamlit secrets if available
    if not api_key:
        try:
            api_key = st.secrets["OPENAI_API_KEY"]
        except:
            pass
    
    if api_key:
        return openai.OpenAI(api_key=api_key)
    else:
        return None


class WellnessAIAnalyst:
    """AI analyst for wellness data insights and recommendations."""
    
    def __init__(self, model: str = "gpt-4-turbo-preview"):
        """
        Initialize the AI analyst.
        
        Args:
            model: OpenAI model to use for analysis
        """
        self.client = init_openai_client()
        self.model = model
        self.system_prompt = """You are an expert sports performance analyst and wellness coach 
        specializing in athlete readiness and recovery. Your role is to analyze wellness data 
        and provide actionable insights to optimize performance and prevent injury.
        
        When analyzing data:
        1. Look for patterns and trends in the metrics
        2. Identify potential concerns or risk factors
        3. Recognize positive developments and improvements
        4. Consider the relationships between different metrics
        5. Provide specific, actionable recommendations
        6. Use sports science best practices
        7. Be encouraging but honest about areas needing attention
        
        Keep insights concise, practical, and athlete-focused."""
    
    def prepare_data_summary(
        self, 
        df: pd.DataFrame, 
        athlete: str = None,
        days: int = 14
    ) -> Dict[str, Any]:
        """
        Prepare a summary of wellness data for AI analysis.
        
        Args:
            df: DataFrame with wellness data
            athlete: Specific athlete to analyze (None for team)
            days: Number of recent days to include
            
        Returns:
            Dictionary with formatted data summary
        """
        # Filter data
        if athlete:
            data = df[df['Athlete'] == athlete].copy()
        else:
            data = df.copy()
        
        # Get recent data
        if 'Date' in data.columns:
            cutoff_date = data['Date'].max() - timedelta(days=days)
            data = data[data['Date'] >= cutoff_date]
        
        # Calculate summary statistics
        summary = {
            'context': {
                'athlete': athlete if athlete else 'Team',
                'period_days': days,
                'data_points': len(data),
                'date_range': {
                    'start': data['Date'].min().strftime('%Y-%m-%d') if 'Date' in data.columns else None,
                    'end': data['Date'].max().strftime('%Y-%m-%d') if 'Date' in data.columns else None
                }
            },
            'current_status': {},
            'averages': {},
            'trends': {},
            'patterns': {},
            'correlations': {}
        }
        
        # Current status (most recent values)
        if not data.empty:
            latest = data.iloc[-1]
            metrics = ['Sleep', 'Mood', 'Energy', 'Stress', 'Soreness', 'Fatigue', 'Readiness']
            
            for metric in metrics:
                if metric in latest.index:
                    value = latest[metric]
                    if not pd.isna(value):
                        summary['current_status'][metric] = round(float(value), 2)
                
                # Add trend if available
                trend_col = f"{metric}_Trend"
                if trend_col in latest.index:
                    summary['trends'][metric] = latest[trend_col]
        
        # Calculate averages and standard deviations
        for metric in ['Sleep', 'Mood', 'Energy', 'Stress', 'Soreness', 'Fatigue', 'Readiness']:
            if metric in data.columns:
                summary['averages'][metric] = {
                    'mean': round(data[metric].mean(), 2) if not data[metric].isna().all() else None,
                    'std': round(data[metric].std(), 2) if not data[metric].isna().all() else None,
                    'min': round(data[metric].min(), 2) if not data[metric].isna().all() else None,
                    'max': round(data[metric].max(), 2) if not data[metric].isna().all() else None
                }
        
        # Sleep patterns
        if 'SleepMinutes' in data.columns:
            sleep_data = data['SleepMinutes'].dropna()
            if not sleep_data.empty:
                summary['patterns']['sleep'] = {
                    'avg_duration_hours': round(sleep_data.mean() / 60, 1),
                    'consistency_std_minutes': round(sleep_data.std(), 0),
                    'shortest_hours': round(sleep_data.min() / 60, 1),
                    'longest_hours': round(sleep_data.max() / 60, 1)
                }
        
        # Weekly patterns
        if 'Date' in data.columns:
            data['DayOfWeek'] = pd.to_datetime(data['Date']).dt.day_name()
            
            # Average readiness by day of week
            if 'Readiness' in data.columns:
                dow_readiness = data.groupby('DayOfWeek')['Readiness'].mean()
                if not dow_readiness.empty:
                    summary['patterns']['weekly_readiness'] = {
                        day: round(float(val), 2) 
                        for day, val in dow_readiness.items()
                    }
        
        # Calculate simple correlations
        if athlete and len(data) > 3:
            metrics_for_corr = ['Sleep', 'Mood', 'Energy', 'Stress', 'Readiness']
            available_metrics = [m for m in metrics_for_corr if m in data.columns]
            
            if len(available_metrics) > 1:
                corr_data = data[available_metrics].dropna()
                if len(corr_data) > 3:
                    correlations = corr_data.corr()
                    
                    # Find notable correlations with Readiness
                    if 'Readiness' in correlations.columns:
                        for metric in available_metrics:
                            if metric != 'Readiness':
                                corr_value = correlations.loc[metric, 'Readiness']
                                if abs(corr_value) > 0.3:  # Only notable correlations
                                    summary['correlations'][f"{metric}_to_Readiness"] = round(corr_value, 2)
        
        # Add z-scores if available
        z_scores = {}
        for col in data.columns:
            if col.endswith('_ZScore'):
                metric = col.replace('_ZScore', '')
                if not data[col].isna().all():
                    latest_z = data[col].iloc[-1] if not data.empty else None
                    if latest_z is not None and not pd.isna(latest_z):
                        z_scores[metric] = round(float(latest_z), 2)
        
        if z_scores:
            summary['z_scores'] = z_scores
        
        return summary
    
    def generate_athlete_insights(
        self,
        data_summary: Dict[str, Any],
        focus_areas: List[str] = None
    ) -> str:
        """
        Generate AI insights for an individual athlete.
        
        Args:
            data_summary: Prepared data summary
            focus_areas: Specific areas to focus on
            
        Returns:
            AI-generated insights text
        """
        if not self.client:
            return "⚠️ OpenAI API key not configured. Add OPENAI_API_KEY to your environment variables or Streamlit secrets."
        
        # Build the prompt
        prompt = f"""Analyze this athlete's wellness data and provide insights:

Data Summary:
{json.dumps(data_summary, indent=2)}

Focus Areas: {', '.join(focus_areas) if focus_areas else 'General wellness and performance'}

Please provide:
1. **Current Status Assessment** (2-3 sentences on overall wellness state)
2. **Key Observations** (2-3 bullet points on notable patterns or concerns)
3. **Actionable Recommendations** (2-3 specific actions to improve performance/recovery)
4. **Risk Factors** (Any warning signs or areas needing immediate attention)

Keep the response concise, practical, and encouraging. Use metrics to support observations."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error generating insights: {str(e)}"
    
    def generate_team_insights(
        self,
        df: pd.DataFrame,
        days: int = 14
    ) -> str:
        """
        Generate insights for the entire team.
        
        Args:
            df: DataFrame with all athletes' data
            days: Number of recent days to analyze
            
        Returns:
            Team-level insights
        """
        if not self.client:
            return "⚠️ OpenAI API key not configured. Add OPENAI_API_KEY to your environment variables or Streamlit secrets."
        
        # Prepare team summary
        team_summary = {
            'num_athletes': df['Athlete'].nunique() if 'Athlete' in df.columns else 0,
            'athletes': [],
            'team_averages': {},
            'team_trends': {},
            'outliers': {}
        }
        
        # Get recent data
        if 'Date' in df.columns:
            cutoff_date = df['Date'].max() - timedelta(days=days)
            recent_df = df[df['Date'] >= cutoff_date]
        else:
            recent_df = df
        
        # Calculate team averages
        for metric in ['Sleep', 'Mood', 'Energy', 'Stress', 'Readiness']:
            if metric in recent_df.columns:
                team_summary['team_averages'][metric] = round(recent_df[metric].mean(), 2)
        
        # Get individual athlete summaries
        if 'Athlete' in df.columns:
            for athlete in df['Athlete'].unique():
                athlete_data = self.prepare_data_summary(df, athlete, days)
                team_summary['athletes'].append({
                    'name': athlete,
                    'readiness': athlete_data['current_status'].get('Readiness'),
                    'trend': athlete_data['trends'].get('Readiness')
                })
        
        # Identify outliers (athletes significantly below team average)
        if 'Readiness' in recent_df.columns and 'Athlete' in recent_df.columns:
            team_avg_readiness = recent_df['Readiness'].mean()
            athlete_readiness = recent_df.groupby('Athlete')['Readiness'].mean()
            
            for athlete, readiness in athlete_readiness.items():
                if readiness < team_avg_readiness - 1.5:  # 1.5 points below average
                    team_summary['outliers'][athlete] = round(readiness, 2)
        
        prompt = f"""Analyze this team's wellness data and provide insights:

Team Summary:
{json.dumps(team_summary, indent=2)}

Please provide:
1. **Team Performance Overview** (2-3 sentences on overall team wellness)
2. **Athletes Needing Support** (Identify any athletes who may need extra attention)
3. **Team Patterns** (Common trends or issues across the team)
4. **Team Recommendations** (2-3 actions for coaches/staff to improve team readiness)

Focus on actionable insights that coaches can implement immediately."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error generating team insights: {str(e)}"
    
    def generate_comparative_analysis(
        self,
        df: pd.DataFrame,
        athlete1: str,
        athlete2: str,
        days: int = 14
    ) -> str:
        """
        Generate comparative analysis between two athletes.
        
        Args:
            df: DataFrame with wellness data
            athlete1: First athlete name
            athlete2: Second athlete name
            days: Number of days to analyze
            
        Returns:
            Comparative insights
        """
        if not self.client:
            return "⚠️ OpenAI API key not configured."
        
        # Prepare data for both athletes
        summary1 = self.prepare_data_summary(df, athlete1, days)
        summary2 = self.prepare_data_summary(df, athlete2, days)
        
        comparison = {
            'athlete1': {'name': athlete1, 'data': summary1},
            'athlete2': {'name': athlete2, 'data': summary2}
        }
        
        prompt = f"""Compare these two athletes' wellness data:

{json.dumps(comparison, indent=2)}

Provide:
1. **Key Differences** (Main areas where athletes differ)
2. **Strengths** (What each athlete is doing well)
3. **Learning Opportunities** (What each could learn from the other)
4. **Personalized Recommendations** (Specific advice for each athlete)

Keep it constructive and focused on improvement."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=600
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error generating comparison: {str(e)}"
    
    def predict_performance_risk(
        self,
        df: pd.DataFrame,
        athlete: str,
        threshold_readiness: float = 5.0
    ) -> Dict[str, Any]:
        """
        Predict performance risk based on recent trends.
        
        Args:
            df: DataFrame with wellness data
            athlete: Athlete name
            threshold_readiness: Readiness threshold for risk
            
        Returns:
            Risk assessment dictionary
        """
        athlete_df = df[df['Athlete'] == athlete].copy()
        
        if athlete_df.empty:
            return {'risk_level': 'unknown', 'factors': []}
        
        # Sort by date
        athlete_df = athlete_df.sort_values('Date')
        recent = athlete_df.tail(7)  # Last week
        
        risk_factors = []
        risk_score = 0
        
        # Check readiness trend
        if 'Readiness' in recent.columns:
            avg_readiness = recent['Readiness'].mean()
            if avg_readiness < threshold_readiness:
                risk_factors.append(f"Low average readiness ({avg_readiness:.1f})")
                risk_score += 2
            
            # Check if declining
            if len(recent) > 1:
                readiness_trend = recent['Readiness'].iloc[-1] - recent['Readiness'].iloc[0]
                if readiness_trend < -1:
                    risk_factors.append("Declining readiness trend")
                    risk_score += 1
        
        # Check stress levels
        if 'Stress' in recent.columns:
            avg_stress = recent['Stress'].mean()
            if avg_stress > 7:
                risk_factors.append(f"High stress levels ({avg_stress:.1f})")
                risk_score += 2
        
        # Check sleep consistency
        if 'SleepMinutes' in recent.columns:
            sleep_std = recent['SleepMinutes'].std()
            if sleep_std > 90:  # More than 1.5 hours variation
                risk_factors.append("Inconsistent sleep patterns")
                risk_score += 1
        
        # Check fatigue
        if 'Fatigue' in recent.columns:
            avg_fatigue = recent['Fatigue'].mean()
            if avg_fatigue > 7:
                risk_factors.append(f"High fatigue ({avg_fatigue:.1f})")
                risk_score += 2
        
        # Determine risk level
        if risk_score >= 5:
            risk_level = "high"
        elif risk_score >= 3:
            risk_level = "moderate"
        elif risk_score >= 1:
            risk_level = "low"
        else:
            risk_level = "minimal"
        
        return {
            'risk_level': risk_level,
            'risk_score': risk_score,
            'factors': risk_factors,
            'recommendation': self._get_risk_recommendation(risk_level, risk_factors)
        }
    
    def _get_risk_recommendation(self, risk_level: str, factors: List[str]) -> str:
        """Generate recommendation based on risk level."""
        recommendations = {
            'high': "⚠️ Consider modified training or additional recovery day. Monitor closely.",
            'moderate': "📊 Adjust training intensity. Focus on recovery protocols.",
            'low': "✅ Monitor trends. Maintain current recovery practices.",
            'minimal': "💪 Athlete is in good condition for normal training."
        }
        return recommendations.get(risk_level, "Continue monitoring wellness metrics.")


@st.cache_data(ttl=3600)
def get_cached_insights(
    df: pd.DataFrame,
    athlete: str,
    insight_type: str = "individual",
    **kwargs
) -> str:
    """
    Get cached AI insights to reduce API calls.
    
    Args:
        df: DataFrame with wellness data
        athlete: Athlete name
        insight_type: Type of insight to generate
        **kwargs: Additional parameters
        
    Returns:
        Cached or newly generated insights
    """
    analyst = WellnessAIAnalyst()
    
    if insight_type == "individual":
        summary = analyst.prepare_data_summary(df, athlete)
        return analyst.generate_athlete_insights(summary)
    elif insight_type == "team":
        return analyst.generate_team_insights(df)
    elif insight_type == "comparison" and 'athlete2' in kwargs:
        return analyst.generate_comparative_analysis(df, athlete, kwargs['athlete2'])
    
    return "Invalid insight type requested."