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
        
        score_col = next((c for c in df.columns if "composite" in c.lower() or "score" in c.lower()), None)
        
        if score_col:
            df[score_col] = pd.to_numeric(df[score_col], errors='coerce').fillna(0)
            df = df.sort_values(by=score_col, ascending=False).reset_index(drop=True)
            front_cols = [c for c in ['Player', 'Team', score_col] if c in df.columns]
            other_cols = [c for c in df.columns if c not in front_cols]
            sheets[sheet] = df[front_cols + other_cols]
        else:
            sheets[sheet] = df

    return sheets

data = load_data()

# Navigation Sidebar
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
    score_col = next((c for c in master_df.columns if "composite" in c.lower() or "score" in c.lower()), None)
    
    if score_col:
        master_df = master_df.sort_values(by=score_col, ascending=False).reset_index(drop=True)
        front_cols = [c for c in ['Player', 'Team', 'Position Tab', score_col, 'Minutes played', 'Age'] if c in master_df.columns]
        other_cols = [col for col in master_df.columns if col not in front_cols]
        master_df = master_df[front_cols + other_cols]
    
    st.dataframe(master_df, use_container_width=True)
    
    if score_col and "Player" in master_df.columns:
        st.subheader("Top 15 Targets Club-Wide")
        top_15 = master_df.head(15)
        st.bar_chart(top_15.set_index("Player")[score_col])

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
    
    score_col = next((c for c in filtered_df.columns if "composite" in c.lower() or "score" in c.lower()), None)
    if score_col and "Player" in filtered_df.columns:
        st.subheader(f"{position} Composite Performance Ranking")
        chart_data = filtered_df.set_index("Player")[score_col].dropna()
        st.bar_chart(chart_data)
