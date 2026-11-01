import os
import streamlit as st
import pandas as pd
import numpy as np

# Set Streamlit Page Configuration
st.set_page_config(page_title="Kerry FC Scouting Hub", layout="wide")
st.title("Kerry FC Recruitment Platform")

# Path to Master Database
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXCEL_PATH = os.path.join(BASE_DIR, "Kerry_FC_Master_Scouting_Database_2026.xlsx")

# ==============================================================================
# 1. LOCKED POSITION-SPECIFIC WEIGHT DICTIONARIES (Must Sum to 1.00)
# ==============================================================================
POSITION_PROFILES = {
    "Center Backs": {
        "weights": {
            'Defensive duels won, %': 0.20,
            'Aerial duels won, %': 0.20,
            'Total duels per 90': 0.10,
            'PAdj Interceptions': 0.10,
            'Fouls per 90': 0.05,
            'Successful defensive actions per 90': 0.10,
            'Accurate passes, %': 0.10,
            'Accurate forward passes, %': 0.05,
            'Forward passes per 90': 0.05,
            'Accurate long passes, %': 0.05
        },
        "inverse_metrics": ['Fouls per 90']
    },
    "Left Backs": {
        "weights": {
            'Defensive duels won, %': 0.20,
            'Aerial duels won, %': 0.10,
            'PAdj Interceptions': 0.10,
            'Fouls per 90': 0.05,
            'Crosses per 90': 0.05,
            'Accurate crosses, %': 0.10,
            'xA per 90': 0.10,
            'Successful dribbles, %': 0.05,
            'Accurate passes, %': 0.10,
            'Accurate forward passes, %': 0.05,
            'Forward passes per 90': 0.05,
            'Accurate progressive passes, %': 0.05
        },
        "inverse_metrics": ['Fouls per 90']
    },
    "Right Backs": {
        "weights": {
            'Defensive duels won, %': 0.20,
            'Aerial duels won, %': 0.10,
            'PAdj Interceptions': 0.10,
            'Fouls per 90': 0.05,
            'Crosses per 90': 0.05,
            'Accurate crosses, %': 0.10,
            'xA per 90': 0.10,
            'Successful dribbles, %': 0.05,
            'Accurate passes, %': 0.10,
            'Accurate forward passes, %': 0.05,
            'Forward passes per 90': 0.05,
            'Accurate progressive passes, %': 0.05
        },
        "inverse_metrics": ['Fouls per 90']
    },
    "Central Midfielders": {
        "weights": {
            'Accurate passes, %': 0.15,
            'Accurate forward passes, %': 0.125,
            'Forward passes per 90': 0.10,
            'Passes to final third per 90': 0.10,
            'Progressive passes per 90': 0.10,
            'Offensive duels won, %': 0.05,
            'Successful dribbles, %': 0.075,
            'Progressive runs per 90': 0.05,
            'Defensive duels won, %': 0.10,
            'PAdj Interceptions': 0.10,
            'xA per 90': 0.05
        },
        "inverse_metrics": []
    },
    "Wingers": {
        "weights": {
            'Successful dribbles, %': 0.125,
            'xG per 90': 0.075,
            'xA per 90': 0.075,
            'Accurate passes to final third, %': 0.075,
            'Crosses per 90': 0.075,
            'Dribbles per 90': 0.075,
            'Shots on target, %': 0.10,
            'Shots per 90': 0.05,
            'Progressive runs per 90': 0.10,
            'Touches in box per 90': 0.10,
            'Accurate crosses, %': 0.10,
            'Accurate progressive passes, %': 0.05
        },
        "inverse_metrics": []
    },
    "Center Forwards": {
        "weights": {
            'xG per 90': 0.15,
            'Goals per 90': 0.15,
            'Goal conversion, %': 0.15,
            'Shots on target, %': 0.125,
            'Aerial duels won, %': 0.10,
            'Offensive duels won, %': 0.10,
            'Shots per 90': 0.075,
            'Touches in box per 90': 0.05,
            'Progressive runs per 90': 0.05,
            'Received long passes per 90': 0.025,
            'xA per 90': 0.025
        },
        "inverse_metrics": []
    },
    "Goalkeepers": {
        "weights": {
            'Save rate, %': 0.25,
            'Prevented goals per 90': 0.25,
            'Conceded goals per 90': 0.20,       # Inverse metric (lower is better)
            'Accurate long passes, %': 0.15,
            'Aerial duels won, %': 0.15
        },
        "inverse_metrics": ['Conceded goals per 90']
    }
}

# ==============================================================================
# 2. ZERO-DISCREPANCY RANKING ENGINE FUNCTION
# ==============================================================================
def calculate_absolute_ranking(df: pd.DataFrame, weights: dict, inverse_metrics: list = None) -> pd.DataFrame:
    """
    Performs deterministic Min-Max normalization and weighted composite index 
    calculation matching rank_players.py logic exactly.
    """
    if inverse_metrics is None:
        inverse_metrics = []
        
    df_clean = df.copy()
    
    # Check weight sum integrity
    total_weight = sum(weights.values())
    if not np.isclose(total_weight, 1.0, atol=1e-5):
        st.warning(f"Warning: Position weights sum to {total_weight:.3f} instead of 1.00")

    # Perform Min-Max Normalization
    composite_series = pd.Series(0.0, index=df_clean.index)
    
    for metric, weight in weights.items():
        if metric in df_clean.columns:
            # Convert metric column to numeric
            s = pd.to_numeric(df_clean[metric], errors='coerce').fillna(0)
            min_val = s.min()
            max_val = s.max()
            
            if max_val == min_val:
                scaled = pd.Series(50.0, index=df_clean.index)
            else:
                scaled = (s - min_val) / (max_val - min_val) * 100.0
                
            if metric in inverse_metrics:
                scaled = 100.0 - scaled
                
            composite_series += scaled * weight
        else:
            st.error(f"Missing required metric column: '{metric}'")

    df_clean['Composite Score'] = composite_series.round(2)
    
    # Sort strictly descending by Composite Score
    df_clean = df_clean.sort_values(by='Composite Score', ascending=False).reset_index(drop=True)
    df_clean['Rank'] = range(1, len(df_clean) + 1)
    
    return df_clean

# ==============================================================================
# 3. DATA LOADING AND PROCESSING PIPELINE
# ==============================================================================
@st.cache_data(ttl=60)
def load_and_process_database():
    if not os.path.exists(EXCEL_PATH):
        st.error(f"Database file not found at: {EXCEL_PATH}")
        st.stop()
    
    xls = pd.ExcelFile(EXCEL_PATH)
    sheets_dict = {}
    
    for sheet_name in xls.sheet_names:
        df_raw = pd.read_excel(xls, sheet_name=sheet_name, header=2)
        df_raw.columns = df_raw.columns.astype(str).str.strip()
        
        # Remove internal ID columns if present
        if 'id' in df_raw.columns:
            df_raw = df_raw.drop(columns=['id'])
            
        # DYNAMICALLY CREATE COMBINED METRIC FOR CENTER BACKS
        if sheet_name == "Center Backs":
            if 'Defensive duels per 90' in df_raw.columns and 'Aerial duels per 90' in df_raw.columns:
                df_raw['Total duels per 90'] = (
                    pd.to_numeric(df_raw['Defensive duels per 90'], errors='coerce').fillna(0) + 
                    pd.to_numeric(df_raw['Aerial duels per 90'], errors='coerce').fillna(0)
                )

        profile = POSITION_PROFILES.get(sheet_name)
        if profile:
            df_ranked = calculate_absolute_ranking(
                df_raw, 
                weights=profile['weights'], 
                inverse_metrics=profile['inverse_metrics']
            )
        else:
            df_ranked = df_raw.copy()
            df_ranked['Composite Score'] = 50.0
            df_ranked['Rank'] = range(1, len(df_ranked) + 1)
            
        # Reorder columns for maximum readability
        front_cols = [c for c in ['Rank', 'Player', 'Team', 'Composite Score', 'Minutes played', 'Age'] if c in df_ranked.columns]
        other_cols = [c for c in df_ranked.columns if c not in front_cols]
        sheets_dict[sheet_name] = df_ranked[front_cols + other_cols]
        
    return sheets_dict

# Load Data
data = load_and_process_database()

# ==============================================================================
# 4. USER INTERFACE & NAVIGATION
# ==============================================================================
st.sidebar.title(" Kerry FC Scouting")
view_options = ["🏆 Master Leaderboard (All Positions)"] + [f"📍 Position: {pos}" for pos in data.keys()]
selected_view = st.sidebar.selectbox("Select View", view_options)

if selected_view.startswith("🏆"):
    st.header("🏆 Master Recruitment Leaderboard")
    st.markdown("Consolidated club-wide rankings evaluated using deterministic Min-Max normalization.")
    
    all_dfs = []
    for pos_name, df_pos in data.items():
        temp_df = df_pos.copy()
        temp_df["Position Tab"] = pos_name
        all_dfs.append(temp_df)
    
    master_df = pd.concat(all_dfs, ignore_index=True)
    master_df = master_df.sort_values(by="Composite Score", ascending=False).reset_index(drop=True)
    master_df["Club Rank"] = range(1, len(master_df) + 1)
    
    # Front-load master columns
    front_cols = ['Club Rank', 'Player', 'Team', 'Position Tab', 'Composite Score', 'Minutes played', 'Age']
    other_cols = [c for c in master_df.columns if c not in front_cols]
    master_df = master_df[[c for c in front_cols if c in master_df.columns] + other_cols]
    
    st.dataframe(master_df, use_container_width=True)
    
    st.subheader("Top 15 Targets Club-Wide")
    top_15 = master_df.head(15)
    if "Player" in top_15.columns and "Composite Score" in top_15.columns:
        st.bar_chart(top_15.set_index("Player")["Composite Score"])

else:
    position_name = selected_view.replace("📍 Position: ", "")
    df_pos = data[position_name]
    
    st.header(f"Shortlist: {position_name}")
    
    # Minutes Played Slider Filter
    mins_col = next((col for col in df_pos.columns if any(k in col.lower() for k in ["minute", "min"])), None)
    if mins_col:
        df_pos[mins_col] = pd.to_numeric(df_pos[mins_col], errors="coerce").fillna(0)
        max_mins = int(df_pos[mins_col].max()) if not df_pos[mins_col].empty and df_pos[mins_col].max() > 0 else 5000
        min_minutes = st.sidebar.slider("Minimum Minutes Played", 0, max_mins, 0)
        filtered_df = df_pos[df_pos[mins_col] >= min_minutes]
    else:
        filtered_df = df_pos

    st.dataframe(filtered_df, use_container_width=True)
    
    if "Composite Score" in filtered_df.columns and "Player" in filtered_df.columns:
        st.subheader(f"{position_name} Composite Performance Ranking")
        chart_data = filtered_df.set_index("Player")["Composite Score"].dropna()
        st.bar_chart(chart_data)
