import streamlit as st
import pandas as pd

# 1. Page Configuration
st.set_page_config(page_title="Kerry FC Scouting Hub", layout="wide")
st.title("Kerry FC Recruitment Platform")

# 2. Load Position Tabs from Master File
@st.cache_data
def load_data():
    xls = pd.ExcelFile("Kerry_FC_Master_Scouting_Database_2026.xlsx")
    sheets = {sheet: pd.read_excel(xls, sheet) for sheet in xls.sheet_names}
    return sheets

data = load_data()

# 3. Position Navigation & Sidebar Filters
position = st.sidebar.selectbox("Select Position", list(data.keys()))
min_minutes = st.sidebar.slider("Minimum Minutes Played", 0, 5000, 1000)

# 4. Filter & Display
df = data[position]
filtered_df = df[df["Minutes played"] >= min_minutes]

st.header(f"Shortlist: {position}")
st.dataframe(filtered_df, use_container_width=True)

# 5. Visual Ranking Chart
st.subheader("Composite Index Ranking")
st.bar_chart(filtered_df.set_index("Player")["Composite_Score"])
