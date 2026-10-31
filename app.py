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

# Add an "Overall Master Leaderboard" option to your position selector
sheet_options = ["Overall Leaderboard (All Positions)"] + list(data.keys())
selected_tab = st.sidebar.selectbox("Select View", sheet_options)

if selected_tab == "Overall Leaderboard (All Positions)":
    st.header("🏆 Master Recruitment Leaderboard")
    st.markdown("Consolidated ranking across all positional shortlists based on Composite Performance Index.")
    
    # Combine all position dataframes into one master table
    all_dfs = []
    for pos_name, df in data.items():
        temp_df = df.copy()
        temp_df["Position Tab"] = pos_name
        all_dfs.append(temp_df)
    
    master_df = pd.concat(all_dfs, ignore_index=True)
    
    # Find the composite score column dynamically
    score_col = next((col for col in master_df.columns if any(k in col.lower() for k in ["composite", "score", "cpi"])), None)
    
    if score_col:
        master_df[score_col] = pd.to_numeric(master_df[score_col], errors="coerce")
        master_df = master_df.dropna(subset=[score_col]).sort_values(by=score_col, ascending=False)
        
        # Display top targets table
        st.dataframe(master_df[['Player', 'Team', 'Position Tab', score_col, 'Minutes played'] if 'Minutes played' in master_df.columns else master_df.columns], use_container_width=True)
        
        # Visual top 15 overall chart
        st.subheader("Top 15 Targets Across All Positions")
        top_15 = master_df.head(15)
        if "Player" in top_15.columns:
            st.bar_chart(top_15.set_index("Player")[score_col])
    else:
        st.warning("Could not locate a composite score column across sheets to generate master ranking.")

else:
    # Standard Positional View
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

    score_col = next((col for col in filtered_df.columns if any(k in col.lower() for k in ["composite", "score", "cpi"])), None)
    if score_col and "Player" in filtered_df.columns:
        st.subheader("Composite Performance Index Ranking")
        chart_data = filtered_df.set_index("Player")[score_col].dropna()
        st.bar_chart(chart_data)
