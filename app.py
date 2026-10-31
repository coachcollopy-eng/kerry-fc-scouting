import os
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Kerry FC Scouting Hub", layout="wide")
st.title("Kerry FC Recruitment Platform")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXCEL_PATH = os.path.join(BASE_DIR, "Kerry_FC_Master_Scouting_Database_2026.xlsx")

@st.cache_data(ttl=60)
def load_data():
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
        
        # Position-Specific Weighted Composite Scoring
        if sheet == "Center Backs":
            df["Composite Score"] = (
                df.get("Defensive duels won, %", 0) * 0.25 +
                df.get("Aerial duels won, %", 0) * 0.25 +
                df.get("Accurate passes, %", 0) * 0.20 +
                df.get("Successful defensive actions per 90", 0) * 1.5 +
                df.get("Progressive passes per 90", 0) * 1.5
            ).round(2)
        elif sheet == "Left Backs":
            df["Composite Score"] = (
                df.get("Defensive duels won, %", 0) * 0.25 +
                df.get("Aerial duels won, %", 0) * 0.20 +
                df.get("Accurate passes, %", 0) * 0.20 +
                df.get("xA per 90", 0) * 10 +
                df.get("Progressive runs per 90", 0) * 2
            ).round(2)
        elif sheet == "Central Midfielders":
            df["Composite Score"] = (
                df.get("Defensive duels won, %", 0) * 0.25 +
                df.get("Accurate passes, %", 0) * 0.25 +
                df.get("xA per 90", 0) * 10 +
                df.get("Progressive passes per 90", 0) * 1.5 +
                df.get("Goals", 0) * 3
            ).round(2)
        elif sheet == "Wingers":
            df["Composite Score"] = (
                df.get("Successful dribbles, %", 0) * 0.25 +
                df.get("xG per 90", 0) * 12 +
                df.get("xA per 90", 0) * 12 +
                df.get("Shots on target, %", 0) * 0.20 +
                df.get("Goals", 0) * 2
            ).round(2)
        elif sheet == "Center Forwards":
            df["Composite Score"] = (
                df.get("Goal conversion, %", 0) * 0.30 +
                df.get("xG per 90", 0) * 15 +
                df.get("Aerial duels won, %", 0) * 0.20 +
                df.get("Goals", 0) * 3 +
                df.get("Touches in box per 90", 0) * 1.5
            ).round(2)
        elif sheet == "Goalkeepers":
            df["Composite Score"] = (
                df.get("Save rate, %", 0) * 0.40 +
                df.get("Accurate long passes, %", 0) * 0.30 +
                df.get("Prevented goals per 90", 0) * 15 +
                df.get("Clean sheets", 0) * 2
            ).round(2)
        else:
            df["Composite Score"] = 50.0

        # Sort sheet by Composite Score descending
        df = df.sort_values(by="Composite Score", ascending=False).reset_index(drop=True)
        
        # Safely reorder columns
        front_cols = [c for c in ['Player', 'Team', 'Composite Score'] if c in df.columns]
        other_cols = [c for c in df.columns if c not in front_cols]
        sheets[sheet] = df[front_cols + other_cols]
        
    return sheets

data = load_data()

# Sidebar Navigation
view_options = ["🏆 Master Leaderboard (All Positions)"] + [f"📍 Position: {pos}" for pos in data.keys()]
selected_view = st.sidebar.selectbox("Select Scouting View", view_options)

if selected_view.startswith("🏆"):
    st.header("🏆 Master Recruitment Leaderboard")
    st.markdown("Consolidated club-wide ranking based on weighted position performance metrics.")
    
    all_dfs = []
    for pos_name, df in data.items():
        temp_df = df.copy()
        temp_df["Position Tab"] = pos_name
        all_dfs.append(temp_df)
    
    master_df = pd.concat(all_dfs, ignore_index=True)
    master_df = master_df.sort_values(by="Composite Score", ascending=False).reset_index(drop=True)
    
    front_cols = [c for c in ['Player', 'Team', 'Position Tab', 'Composite Score', 'Minutes played', 'Age'] if c in master_df.columns]
    other_cols = [col for col in master_df.columns if col not in front_cols]
    master_df = master_df[front_cols + other_cols]
    
    st.dataframe(master_df, use_container_width=True)
    
    st.subheader("Top 15 Club-Wide Targets")
    top_15 = master_df.head(15)
    if "Player" in top_15.columns:
        st.bar_chart(top_15.set_index("Player")["Composite Score"])

else:
    position = selected_view.replace("📍 Position: ", "")
    df = data[position]
    
    st.header(f"Shortlist: {position}")
    
    mins_col = next((col for col in df.columns if any(k in col.lower() for k in ["minute", "min"])), None)
    if mins_col:
        max_mins = int(df[mins_col].max()) if not df[mins_col].empty and df[mins_col].max() > 0 else 5000
        min_minutes = st.sidebar.slider("Minimum Minutes Played", 0, max_mins, 500)
        filtered_df = df[df[mins_col] >= min_minutes]
    else:
        filtered_df = df

    st.dataframe(filtered_df, use_container_width=True)
    
    if "Player" in filtered_df.columns and "Composite Score" in filtered_df.columns:
        st.subheader(f"{position} Composite Performance Ranking")
        chart_data = filtered_df.set_index("Player")["Composite Score"].dropna()
        st.bar_chart(chart_data)
