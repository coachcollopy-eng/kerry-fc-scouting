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
        sheets[sheet] = df
    return sheets

data = load_data()

# Navigation View
sheet_options = ["Overall Leaderboard (All Positions)"] + list(data.keys())
selected_tab = st.sidebar.selectbox("Select View", sheet_options)

if selected_tab == "Overall Leaderboard (All Positions)":
    st.header("🏆 Master Recruitment Leaderboard")
    st.markdown("Consolidated ranking across all positional shortlists.")
    
    all_scored_dfs = []
    for pos_name, df in data.items():
        temp_df = df.copy()
        temp_df["Position Tab"] = pos_name
        
        # Simple dynamic composite scoring fallback based on available stats
        numeric_cols = temp_df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            # Normalize numeric columns to 0-100 scale for a composite index
            normalized = temp_df[numeric_cols].apply(lambda x: (x - x.min()) / (x.max() - x.min()) * 100 if x.max() != x.min() else 50)
            temp_df["Composite Score"] = normalized.mean(axis=1).round(2)
        else:
            temp_df["Composite Score"] = 50.0
            
        all_scored_dfs.append(temp_df)
    
    master_df = pd.concat(all_scored_dfs, ignore_index=True)
    master_df = master_df.sort_values(by="Composite Score", ascending=False)
    
    # Reorder columns to show Player, Team, Position, and Score first
    front_cols = [col for col in ['Player', 'Team', 'Position Tab', 'Composite Score', 'Minutes played', 'Age'] if col in master_df.columns]
    other_cols = [col for col in master_df.columns if col not in front_cols]
    master_df = master_df[front_cols + other_cols]
    
    st.dataframe(master_df, use_container_width=True)
    
    st.subheader("Top 15 Club-Wide Targets")
    top_15 = master_df.head(15)
    if "Player" in top_15.columns:
        st.bar_chart(top_15.set_index("Player")["Composite Score"])

else:
    df = data[selected_tab]
    
    mins_col = next((col for col in df.columns if any(k in col.lower() for k in ["minute", "min"])), None)
    if mins_col:
        df[mins_col] = pd.to_numeric(df[mins_col], errors="coerce").fillna(0)
        max_mins = int(df[mins_col].max()) if not df[mins_col].empty and df[mins_col].max() > 0 else 5000
        min_minutes = st.sidebar.slider("Minimum Minutes Played", 0, max_mins, 500)
        filtered_df = df[df[mins_col] >= min_minutes]
    else:
        filtered_df = df

    st.header(f"Shortlist: {selected_tab}")
    st.dataframe(filtered_df, use_container_width=True)
