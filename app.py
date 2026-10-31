import os
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Kerry FC Scouting Hub", layout="wide")
st.title("Kerry FC Recruitment Platform")

# 1. Load database securely
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
        
        # Calculate a dynamic Composite Score for ranking if not already present
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0 and "Composite Score" not in df.columns:
            normalized = df[numeric_cols].apply(lambda x: (x - x.min()) / (x.max() - x.min()) * 100 if x.max() != x.min() else 50)
            df["Composite Score"] = normalized.mean(axis=1).round(2)
        elif "Composite Score" not in df.columns:
            df["Composite Score"] = 50.0
            
        sheets[sheet] = df.sort_values(by="Composite Score", ascending=False)
    return sheets

data = load_data()

# 2. Sidebar Navigation: Master Leaderboard vs Position Tabs
view_options = ["🏆 Master Leaderboard (All Positions)"] + [f"📍 Position: {pos}" for pos in data.keys()]
selected_view = st.sidebar.selectbox("Select Scouting View", view_options)

if selected_view.startswith("🏆"):
    st.header("🏆 Master Recruitment Leaderboard")
    st.markdown("Consolidated ranking across all positional shortlists based on performance metrics.")
    
    all_dfs = []
    for pos_name, df in data.items():
        temp_df = df.copy()
        temp_df["Position Tab"] = pos_name
        all_dfs.append(temp_df)
    
    master_df = pd.concat(all_dfs, ignore_index=True)
    master_df = master_df.sort_values(by="Composite Score", ascending=False)
    
    # Prioritize key identifying columns at the front
    front_cols = [col for col in ['Player', 'Team', 'Position Tab', 'Composite Score', 'Minutes played', 'Age'] if col in master_df.columns]
    other_cols = [col for col in master_df.columns if col not in front_cols]
    master_df = master_df[front_cols + other_cols]
    
    st.dataframe(master_df, use_container_width=True)
    
    st.subheader("Top 15 Club-Wide Targets")
    top_15 = master_df.head(15)
    if "Player" in top_15.columns:
        st.bar_chart(top_15.set_index("Player")["Composite Score"])

else:
    # Extract clean position name
    position = selected_view.replace("📍 Position: ", "")
    df = data[position]
    
    st.header(f"Shortlist: {position}")
    
    # Sidebar filter for minutes played
    mins_col = next((col for col in df.columns if any(k in col.lower() for k in ["minute", "min"])), None)
    if mins_col:
        df[mins_col] = pd.to_numeric(df[mins_col], errors="coerce").fillna(0)
        max_mins = int(df[mins_col].max()) if not df[mins_col].empty and df[mins_col].max() > 0 else 5000
        min_minutes = st.sidebar.slider("Minimum Minutes Played", 0, max_mins, 500)
        filtered_df = df[df[mins_col] >= min_minutes]
    else:
        filtered_df = df

    st.dataframe(filtered_df, use_container_width=True)
    
    # Positional Ranking Chart
    if "Player" in filtered_df.columns and "Composite Score" in filtered_df.columns:
        st.subheader(f"{position} Composite Performance Ranking")
        chart_data = filtered_df.set_index("Player")["Composite Score"].dropna()
        st.bar_chart(chart_data)
