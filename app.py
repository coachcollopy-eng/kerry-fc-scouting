import streamlit as st
import pandas as pd

# 1. Page Configuration
st.set_page_config(page_title="Kerry FC Scouting Hub", layout="wide")
st.title("Kerry FC Recruitment Platform")

# 2. Load Position Tabs with Header Row Set to Index 2 (Row 3 in Excel)
@st.cache_data
def load_data():
    xls = pd.ExcelFile("Kerry_FC_Master_Scouting_Database_2026.xlsx")
    # Set header=2 to pick up 'Player', 'Minutes played', etc., correctly
    sheets = {sheet: pd.read_excel(xls, sheet_name=sheet, header=2) for sheet in xls.sheet_names}
    return sheets

data = load_data()

# 3. Position Navigation & Sidebar Filters
position = st.sidebar.selectbox("Select Position", list(data.keys()))

# Get max minutes safely for slider bounds
df = data[position]
max_mins = int(df["Minutes played"].max()) if "Minutes played" in df.columns else 5000

min_minutes = st.sidebar.slider("Minimum Minutes Played", 0, max_mins, 1000)

# 4. Filter & Display
if "Minutes played" in df.columns:
    filtered_df = df[df["Minutes played"] >= min_minutes]
else:
    filtered_df = df

st.header(f"Shortlist: {position}")
st.dataframe(filtered_df, use_container_width=True)

# 5. Visual Score Ranking (if CPI or Score column exists)
score_col = [col for col in filtered_df.columns if "Composite" in col or "Score" in col or "CPI" in col]
if score_col:
    st.subheader("Composite Index Ranking")
    st.bar_chart(filtered_df.set_index("Player")[score_col[0]])
