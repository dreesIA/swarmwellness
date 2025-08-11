#data_loader.py
"""
Data loader module for fetching data from Google Sheets or fallback CSV.
Handles authentication, caching, and data normalization.
"""

import json
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import streamlit as st
from typing import Optional, Dict, Any
import os
from datetime import datetime, timedelta

scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]

if "GSPREAD_CREDENTIALS" in st.secrets:
    creds_dict = json.loads(st.secrets["GSPREAD_CREDENTIALS"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
else:
    creds = Credentials.from_service_account_file("gspread_credentials.json", scopes=scope)

client = gspread.authorize(creds)
sheet = client.open("Morning Wellness Tracker").worksheet("Form Responses 1")
data = sheet.get_all_records()

@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_google_sheet(
    sheet_title: str,
    worksheet_name: str = "Form Responses 1",
    credentials_file: str = "gspread_credentials.json",
    use_fallback: bool = True
) -> pd.DataFrame:
    """
    Load data from Google Sheets with fallback to local CSV.
    
    Args:
        sheet_title: Name of the Google Sheet
        worksheet_name: Name of the worksheet tab (default for Forms)
        credentials_file: Path to service account JSON
        use_fallback: Whether to use CSV fallback on error
        
    Returns:
        DataFrame with normalized column names and processed dates
    """
    
    try:
        # Authenticate with Google Sheets
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        
        if not os.path.exists(credentials_file):
            raise FileNotFoundError(f"Credentials file not found: {credentials_file}")
        
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            credentials_file, scope
        )
        client = gspread.authorize(creds)
        
        # Open the sheet and get data
        sheet = client.open(sheet_title)
        worksheet = sheet.worksheet(worksheet_name)
        
        # Get all values and convert to DataFrame
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)
        
        if df.empty:
            raise ValueError("No data found in sheet")
            
    except Exception as e:
        st.warning(f"Error loading from Google Sheets: {str(e)}")
        
        if use_fallback:
            st.info("Loading from local example data...")
            df = pd.read_csv("data/example_export.csv")
        else:
            raise e
    
    # Normalize and process the DataFrame
    df = normalize_dataframe(df)
    
    return df


def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize column names and process data types.
    
    Args:
        df: Raw DataFrame from Google Sheets or CSV
        
    Returns:
        Processed DataFrame with standardized columns
    """
    
    # Rename columns to match expected names (handle variations)
    column_mapping = {
        'Timestamp': 'Timestamp',
        'timestamp': 'Timestamp',
        'Date': 'Timestamp',
        'Athlete': 'Athlete',
        'Name': 'Athlete',
        'SleepText': 'SleepText',
        'Sleep Text': 'SleepText',
        'Sleep Duration': 'SleepText',
        'How did you sleep?': 'Sleep',
        'Sleep Quality': 'Sleep',
        'How is your mood?': 'Mood',
        'Mood': 'Mood',
        'What is your overall energy level?': 'Energy',
        'Energy Level': 'Energy',
        'Energy': 'Energy',
        'What is your overall stress level?': 'Stress',
        'Stress Level': 'Stress',
        'Stress': 'Stress',
        'What is your general soreness?': 'Soreness',
        'Soreness': 'Soreness',
        'What is your overall fatigue?': 'Fatigue',
        'Fatigue': 'Fatigue'
    }
    
    # Apply column mapping
    df = df.rename(columns=column_mapping)
    
    # Convert Timestamp to datetime and extract Date
    if 'Timestamp' in df.columns:
        df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')
        df['Date'] = df['Timestamp'].dt.date
        df['Date'] = pd.to_datetime(df['Date'])
    
    # Convert numeric columns
    numeric_columns = ['Sleep', 'Mood', 'Energy', 'Stress', 'Soreness', 'Fatigue']
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Sort by Date and Athlete
    if 'Date' in df.columns and 'Athlete' in df.columns:
        df = df.sort_values(['Date', 'Athlete'])
    
    return df


def refresh_data():
    """Clear the cache to force data refresh."""
    st.cache_data.clear()
    st.success("Data refreshed successfully!")


def get_latest_date(df: pd.DataFrame) -> Optional[datetime]:
    """Get the most recent date in the dataset."""
    if 'Date' in df.columns and not df['Date'].isna().all():
        return df['Date'].max()
    return None


def get_athletes(df: pd.DataFrame) -> list:
    """Get unique list of athletes."""
    if 'Athlete' in df.columns:
        return sorted(df['Athlete'].dropna().unique().tolist())
    return []
