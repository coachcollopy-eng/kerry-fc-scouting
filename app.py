import streamlit as st
import pandas as pd

st.set_page_config(page_title="Kerry FC Scouting Hub", layout="wide")
st.title("Kerry FC Recruitment Platform")

# 1. Clear cache on update & load sheets cleanly
@st.cache_data(ttl=60)  # Caches for 60 seconds max so updates register automatically
def load_data():
    xls = pd.ExcelFile("Kerry_FC_Master_Scouting_Database_2026.xlsx")
    sheets = {}
    for sheet in xls.sheet_names:
        # Read with header=2 (Row 3 in Excel)
        df = pd.read_excel(xls, sheet_name=sheet, header=2)
        # Strip trailing/leading spaces from column headers
        df.columns = df.columns.astype(str).str.strip()
        sheets[sheet] = df
    return sheets

data = load_data()

# 2. Position Navigation
position = st.sidebar.selectbox("Select Position", list(data.keys()))
df = data[position]

# 3. Dynamic Column Lookup (Handles potential variations like "Minutes", "Minutes Played")
mins_col = next((col for col in df.columns if "minute" in col.lower()), None)

if mins_col:
    # Convert minutes column to clean integers
    df[mins_col] = pd.to_numeric(df[mins_col], errors="coerce").fillna(0)
    max_mins = int(df[mins_col].max()) if not df[mins_col].empty and df[mins_col].max() > 0 else 5000
    
    min_minutes = st.sidebar.slider("Minimum Minutes Played", 0, max_mins, 1000)
    filtered_df = df[df[mins_col] >= min_minutes]
else:
    st.sidebar.warning("Minutes column not detected for this sheet.")
    filtered_df = df

# 4. Display Shortlist Table
st.header(f"Shortlist: {position}")
st.dataframe(filtered_df, use_container_width=True)

# 5. Visual Ranking Chart
score_col = next((col for col in filtered_df.columns if any(k in col.lower() for k in ["composite", "score", "cpi"])), None)
if score_col and "Player" in filtered_df.columns:
    st.subheader("Composite Performance Index Ranking")
    chart_data = filtered_df.set_index("Player")[score_col]
    st.bar_chart(chart_data)
