import os
import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Kerry FC Scouting Hub", layout="wide")
st.title("Kerry FC Recruitment Platform")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXCEL_PATH = os.path.join(BASE_DIR, "Kerry_FC_Master_Scouting_Database_2026.xlsx")

# Define position-specific weights matching your professional criteria (must sum to 1.0)
POSITION_WEIGHTS = {
    "Center Backs": {
        'Defensive duels won, %': 0.25,
        'Aerial duels won, %': 0.25,
        'Accurate passes, %': 0.20,
        'Successful defensive actions per 90': 0.15,
        'Progressive passes per 90': 0.15
    },
    "Left Backs": {
        'Defensive duels won, %': 0.25,
        'Aerial duels won, %': 0.20,
        'Accurate passes, %': 0.20,
        'xA per 90': 0.20,
        'Progressive runs per 90': 0.15
    },
    "Right Backs": {
        'Defensive duels won, %': 0.25,
        'Aerial duels won, %': 0.20,
        'Accurate passes, %': 0.20,
        'xA per 90': 0.20,
        'Progressive runs per 90': 0.15
    },
    "Central Midfielders": {
        'Defensive duels won, %': 0.25,
        'Accurate passes, %': 0.25,
        'xA per 90': 0.20,
        'Progressive passes per 90': 0.15,
        'Goals': 0.15
    },
    "Wingers": {
        'Successful dribbles, %': 0.25,
        'xG per 90': 0.25,
        'xA per 90': 0.20,
        'Shots on target, %': 0.15,
        'Goals': 0.15
    },
    "Center Forwards": {
        'Goal conversion, %': 0.30,
        'xG per 90': 0.25,
        'Aerial duels won, %': 0.20,
        'Goals': 0.15,
        'Touches in box per 90': 0.10
    },
    "Goalkeepers": {
        'Save rate, %': 0.40,
        'Accurate long passes, %': 0.30,
        'Prevented goals per 90': 0.20,
        'Clean sheets': 0.10
    }
}

@st.cache_data(ttl=60)
def load_and_rank_data():
    if not os.path.exists(EXCEL_PATH):
        st.error(f"Database file not found at: {EXCEL_PATH}")
        st.stop()
    
    xls = pd.ExcelFile(EXCEL_PATH)
    sheets = {}
    
    for sheet in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet, header=2)
        df.columns = df.columns.astype(str).str.strip()
        
        # Clean numeric columns
        for col in df.columns:
            if col not in ['Player', 'Team', 'Position', 'Contract expires', 'id']:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        weights = POSITION_WEIGHTS.get(sheet, {})
        if weights:
            norm_df = df.copy()
            composite = np.zeros(len(df))
            
            for col, weight in weights.items():
                if col in df.columns:
                    min_val = df[col].min()
                    max_val = df[col].max()
                    if max_val == min_val:
                        scaled = 50.0
                    else:
                        scaled = (df[col] - min_val) / (max_val - min_val) * 100
                    composite += scaled * weight
                
            df["Composite Score"] = np.round(composite, 2)
        else:
            df["Composite Score"] = 50.0
            
        # Sort by Composite Score descending and add Rank
        df = df.sort_values(by="Composite Score", ascending=False).reset_index(drop=True)
        df.insert(0, "Rank", range(1, len(df) + 1))
        
        # Bring Rank, Player, Team, Composite Score to front
        front_cols = [c for c in ['Rank', 'Player', 'Team', 'Composite Score'] if c in df.columns]
        other_cols = [c for c in df.columns if c not in front_cols]
        sheets[sheet] = df[front_cols + other_cols]
        
    return sheets

data = load_and_rank_data()

# Sidebar Navigation
view_options = ["🏆 Master Leaderboard (All Positions)"] + [f"📍 Position: {pos}" for pos in data.keys()]
selected_view = st.sidebar.selectbox("Select Scouting View", view_options)

if selected_view.startswith("🏆"):
    st.header("🏆 Master Recruitment Leaderboard")
    st.markdown("Consolidated club-wide ranking across all position shortlists.")
    
    all_dfs = []
    for pos_name, df in data.items():
        temp_df = df.copy()
        temp_df["Position Tab"] = pos_name
        all_dfs.append(temp_df)
    
    master_df = pd.concat(all_dfs, ignore_index=True)
    if "Composite Score" in master_df.columns:
        master_df = master_df.sort_values(by="Composite Score", ascending=False).reset_index(drop=True)
        master_df["Club Rank"] = range(1, len(master_df) + 1)
        front_cols = ['Club Rank', 'Player', 'Team', 'Position Tab', 'Composite Score', 'Minutes played', 'Age']
        other_cols = [col for col in master_df.columns if col not in front_cols]
        master_df = master_df[[c for c in front_cols if c in master_df.columns] + other_cols]
    
    st.dataframe(master_df, use_container_width=True)
    
    if "Composite Score" in master_df.columns and "Player" in master_df.columns:
        st.subheader("Top 15 Targets Club-Wide")
        top_15 = master_df.head(15)
        st.bar_chart(top_15.set_index("Player")["Composite Score"])

else:
    position = selected_view.replace("📍 Position: ", "")
    df = data[position]
    
    st.header(f"Shortlist: {position}")
    
    mins_col = next((col for col in df.columns if any(k in col.lower() for k in ["minute", "min"])), None)
    if mins_col:
        df[mins_col] = pd.to_numeric(df[mins_col], errors="coerce").fillna(0)
        max_mins = int(df[mins_col].max()) if not df[mins_col].empty and df[mins_col].max() > 0 else 5000
        min_minutes = st.sidebar.slider("Minimum Minutes Played", 0, max_mins, 0)
        filtered_df = df[df[mins_col] >= min_minutes]
    else:
        filtered_df = df

    st.dataframe(filtered_df, use_container_width=True)
    
    if "Composite Score" in filtered_df.columns and "Player" in filtered_df.columns:
        st.subheader(f"{position} Composite Performance Ranking")
        chart_data = filtered_df.set_index("Player")["Composite Score"].dropna()
        st.bar_chart(chart_data)
