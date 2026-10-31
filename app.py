import os
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Kerry FC Scouting Hub", layout="wide")
st.title("Kerry FC Recruitment Platform")

# 1. Load database with robust header and path handling
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
        # Strip trailing/leading spaces from all column names
        df.columns = df.columns.astype(str).str.strip()
        sheets[sheet] = df
    return sheets

data = load_data()

# 2. Position Navigation Sidebar
position = st.sidebar.selectbox("Select Position", list(data.keys()))
df = data[position]

# 3. Flexible Minutes Column Finder (Matches "Minutes played", "Minutes", "Mins", etc.)
mins_col = next((col for col in df.columns if any(k in col.lower() for k in ["minute", "min"])), None)

if mins_col:
    df[mins_col] = pd.to_numeric(df[mins_col], errors="coerce").fillna(0)
    max_mins = int(df[mins_col].max()) if not df[mins_col].empty and df[mins_col].max() > 0 else 5000
    min_minutes = st.sidebar.slider("Minimum Minutes Played", 0, max_mins, 500)
    filtered_df = df[df[mins_col] >= min_minutes]
else:
    st.sidebar.warning(f"No minutes column found. Showing all players.")
    filtered_df = df

# 4. Display Table
st.header(f"Shortlist: {position}")
st.dataframe(filtered_df, use_container_width=True)

# 5. Visual Ranking Chart
score_col = next((col for col in filtered_df.columns if any(k in col.lower() for k in ["composite", "score", "cpi"])), None)
if score_col and "Player" in filtered_df.columns:
    st.subheader("Composite Performance Index Ranking")
    chart_data = filtered_df.set_index("Player")[score_col].dropna()
    st.bar_chart(chart_data)
