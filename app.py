import os
import streamlit as st
import pandas as pd
import numpy as np

# Set Streamlit Page Configuration
st.set_page_config(
    page_title="Kerry FC Scouting Hub", 
    page_icon="⚽",
    layout="wide"
)

# ==============================================================================
# KERRY FC CUSTOM CSS STYLING (Green & Gold Theme)
# ==============================================================================
st.markdown("""
<style>
    /* Main App Background */
    .stApp {
        background-color: #F8F9FA;
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #0B3B2C !important; /* Deep Kerry Green */
        color: #FFFFFF;
    }
    
    section[data-testid="stSidebar"] .stMarkdown h1, 
    section[data-testid="stSidebar"] .stMarkdown h2, 
    section[data-testid="stSidebar"] .stMarkdown h3,
    section[data-testid="stSidebar"] label {
        color: #FFD700 !important; /* Gold Text */
    }
    
    section[data-testid="stSidebar"] .stSelectbox label, 
    section[data-testid="stSidebar"] .stSlider label {
        color: #FFFFFF !important;
    }

    /* Headers Styling */
    h1, h2, h3 {
        color: #0B3B2C !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Title Custom Banner Styling */
    .main-title {
        background: linear-gradient(90deg, #0B3B2C 0%, #145A43 100%);
        padding: 20px 30px;
        border-radius: 10px;
        color: white;
        margin-bottom: 25px;
        border-left: 6px solid #C5A059; /* Gold Accent Border */
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .main-title h1 {
        color: #FFFFFF !important;
        margin: 0;
        font-size: 2.2rem;
    }
    .main-title p {
        color: #E2E8F0;
        margin: 5px 0 0 0;
        font-size: 1.05rem;
    }

    /* DataFrame container styling */
    div[data-testid="stDataFrame"] {
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        background-color: #FFFFFF;
        padding: 5px;
    }
</style>
""", unsafe_allow_html=True)

# Path to Master Database
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXCEL_PATH = os.path.join(BASE_DIR, "Kerry_FC_Master_Scouting_Database_2026.xlsx")

# ==============================================================================
# 1. LOCKED POSITION-SPECIFIC WEIGHT DICTIONARIES (Must Sum to 1.00)
# ==============================================================================
POSITION_PROFILES = {
    "Center Backs": {
        "weights": {
            'Defensive duels won, %': 0.20,
            'Aerial duels won, %': 0.20,
            'Total duels per 90': 0.10,
            'PAdj Interceptions': 0.10,
            'Fouls per 90': 0.05,
            'Successful defensive actions per 90': 0.10,
            'Accurate passes, %': 0.10,
            'Accurate forward passes, %': 0.05,
            'Forward passes per 90': 0.05,
            'Accurate long passes, %': 0.05
        },
        "inverse_metrics": ['Fouls per 90']
    },
    "Left Backs": {
        "weights": {
            'Defensive duels won, %': 0.20,
            'Aerial duels won, %': 0.10,
            'PAdj Interceptions': 0.10,
            'Fouls per 90': 0.05,
            'Crosses per 90': 0.05,
            'Accurate crosses, %': 0.10,
            'xA per 90': 0.10,
            'Successful dribbles, %': 0.05,
            'Accurate passes, %': 0.10,
            'Accurate forward passes, %': 0.05,
            'Forward passes per 90': 0.05,
            'Accurate progressive passes, %': 0.05
        },
        "inverse_metrics": ['Fouls per 90']
    },
    "Right Backs": {
        "weights": {
            'Defensive duels won, %': 0.20,
            'Aerial duels won, %': 0.10,
            'PAdj Interceptions': 0.10,
            'Fouls per 90': 0.05,
            'Crosses per 90': 0.05,
            'Accurate crosses, %': 0.10,
            'xA per 90': 0.10,
            'Successful dribbles, %': 0.05,
            'Accurate passes, %': 0.10,
            'Accurate forward passes, %': 0.05,
            'Forward passes per 90': 0.05,
            'Accurate progressive passes, %': 0.05
        },
        "inverse_metrics": ['Fouls per 90']
    },
    "Central Midfielders": {
        "weights": {
            'Accurate passes, %': 0.15,
            'Accurate forward passes, %': 0.125,
            'Forward passes per 90': 0.10,
            'Passes to final third per 90': 0.10,
            'Progressive passes per 90': 0.10,
            'Offensive duels won, %': 0.05,
            'Successful dribbles, %': 0.075,
            'Progressive runs per 90': 0.05,
            'Defensive duels won, %': 0.10,
            'PAdj Interceptions': 0.10,
            'xA per 90': 0.05
        },
        "inverse_metrics": []
    },
    "Attacking Midfielders": {
        "weights": {
            'xA per 90': 0.15,
            'Key passes per 90': 0.15,
            'Progressive passes per 90': 0.15,
            'Accurate passes, %': 0.10,
            'Passes to final third per 90': 0.10,
            'xG per 90': 0.10,
            'Successful dribbles, %': 0.125,
            'Progressive runs per 90': 0.125
        },
        "inverse_metrics": []
    },
    "Wingers": {
        "weights": {
            'Successful dribbles, %': 0.125,
            'xG per 90': 0.075,
            'xA per 90': 0.075,
            'Accurate passes to final third, %': 0.075,
            'Crosses per 90': 0.075,
            'Dribbles per 90': 0.075,
            'Shots on target, %': 0.10,
            'Shots per 90': 0.05,
            'Progressive runs per 90': 0.10,
            'Touches in box per 90': 0.10,
            'Accurate crosses, %': 0.10,
            'Accurate progressive passes, %': 0.05
        },
        "inverse_metrics": []
    },
    "Center Forwards": {
        "weights": {
            'xG per 90': 0.15,
            'Goals per 90': 0.15,
            'Goal conversion, %': 0.15,
            'Shots on target, %': 0.125,
            'Aerial duels won, %': 0.10,
            'Offensive duels won, %': 0.10,
            'Shots per 90': 0.075,
            'Touches in box per 90': 0.05,
            'Progressive runs per 90': 0.05,
            'Received long passes per 90': 0.025,
            'xA per 90': 0.025
        },
        "inverse_metrics": []
    },
    "Goalkeepers": {
        "weights": {
            'Save rate, %': 0.25,
            'Prevented goals per 90': 0.25,
            'Conceded goals per 90': 0.20,       # Inverse metric (lower is better)
            'Accurate long passes, %': 0.15,
            'Aerial duels won, %': 0.15
        },
        "inverse_metrics": ['Conceded goals per 90']
    }
}

# ==============================================================================
# 2. ZERO-DISCREPANCY RANKING ENGINE FUNCTION
# ==============================================================================
def calculate_absolute_ranking(df: pd.DataFrame, weights: dict, inverse_metrics: list = None) -> pd.DataFrame:
    if inverse_metrics is None:
        inverse_metrics = []
        
    df_clean = df.copy()
    
    total_weight = sum(weights.values())
    if not np.isclose(total_weight, 1.0, atol=1e-5):
        st.warning(f"Warning: Position weights sum to {total_weight:.3f} instead of 1.00")

    composite_series = pd.Series(0.0, index=df_clean.index)
    
    for metric, weight in weights.items():
        if metric in df_clean.columns:
            s = pd.to_numeric(df_clean[metric], errors='coerce').fillna(0)
            min_val = s.min()
            max_val = s.max()
            
            if max_val == min_val:
                scaled = pd.Series(50.0, index=df_clean.index)
            else:
                scaled = (s - min_val) / (max_val - min_val) * 100.0
                
            if metric in inverse_metrics:
                scaled = 100.0 - scaled
                
            composite_series += scaled * weight
        else:
            st.error(f"Missing required metric column: '{metric}'")

    df_clean['Composite Score'] = composite_series.round(2)
    df_clean = df_clean.sort_values(by='Composite Score', ascending=False).reset_index(drop=True)
    df_clean['Rank'] = range(1, len(df_clean) + 1)
    
    return df_clean

# ==============================================================================
# 3. DATA LOADING AND PROCESSING PIPELINE
# ==============================================================================
@st.cache_data(ttl=60)
def load_and_process_database():
    if not os.path.exists(EXCEL_PATH):
        st.error(f"Database file not found at: {EXCEL_PATH}")
        st.stop()
    
    xls = pd.ExcelFile(EXCEL_PATH)
    sheets_dict = {}
    
    for sheet_name in xls.sheet_names:
        # Check header row depending on sheet format
        header_row = 0 if sheet_name == "Attacking Midfielders" else 2
        df_raw = pd.read_excel(xls, sheet_name=sheet_name, header=header_row)
        df_raw.columns = df_raw.columns.astype(str).str.strip()
        
        # Foolproof Team Column Matching
        for col in df_raw.columns:
            if 'team' in col.lower() or 'club' in col.lower():
                df_raw = df_raw.rename(columns={col: 'Team'})
                break
        if 'Team' not in df_raw.columns:
            df_raw['Team'] = "Unknown"
        else:
            df_raw['Team'] = df_raw['Team'].fillna("Unknown")

        if 'id' in df_raw.columns:
            df_raw = df_raw.drop(columns=['id'])
            
        # DYNAMICALLY CREATE COMBINED METRIC FOR CENTER BACKS
        if sheet_name == "Center Backs":
            if 'Defensive duels per 90' in df_raw.columns and 'Aerial duels per 90' in df_raw.columns:
                df_raw['Total duels per 90'] = (
                    pd.to_numeric(df_raw['Defensive duels per 90'], errors='coerce').fillna(0) + 
                    pd.to_numeric(df_raw['Aerial duels per 90'], errors='coerce').fillna(0)
                )

        profile = POSITION_PROFILES.get(sheet_name)
        if profile:
            df_ranked = calculate_absolute_ranking(
                df_raw, 
                weights=profile['weights'], 
                inverse_metrics=profile['inverse_metrics']
            )
        else:
            df_ranked = df_raw.copy()
            df_ranked['Composite Score'] = 50.0
            df_ranked['Rank'] = range(1, len(df_ranked) + 1)
            
        front_cols = [c for c in ['Rank', 'Player', 'Team', 'Composite Score', 'Minutes played', 'Age'] if c in df_ranked.columns]
        other_cols = [c for c in df_ranked.columns if c not in front_cols]
        sheets_dict[sheet_name] = df_ranked[front_cols + other_cols]
        
    return sheets_dict

# Load Data
data = load_and_process_database()

import base64

def render_svg(svg_file, width=120):
    """Renders an SVG file cleanly in Streamlit via base64 encoding."""
    if not os.path.exists(svg_file):
        return False
    try:
        with open(svg_file, "r", encoding="utf-8") as f:
            svg_content = f.read()
        b64 = base64.b64encode(svg_content.encode("utf-8")).decode("utf-8")
        html = f'<img src="data:image/svg+xml;base64,{b64}" width="{width}" />'
        st.sidebar.markdown(html, unsafe_allow_html=True)
        return True
    except Exception:
        return False

# ==============================================================================
# 4. USER INTERFACE & NAVIGATION
# ==============================================================================

# Attempt to render the SVG logo in the sidebar
logo_rendered = render_svg("kerry_logo.svg", width=110) # Replace with your exact SVG filename

if not logo_rendered:
    st.sidebar.markdown("⚽ **Kerry FC Scouting**")

st.sidebar.title("Navigation")
view_options = ["🏆 Master Leaderboard (All Positions)"] + [f"📍 Position: {pos}" for pos in data.keys()]
selected_view = st.sidebar.selectbox("Select View", view_options)
# Styled Branded Header Banner
st.markdown("""
<div class="main-title">
    <h1>Kerry FC Recruitment Platform</h1>
    <p>Deterministic tactical scouting engine evaluated using Min-Max normalization & custom positional weightings.</p>
</div>
""", unsafe_allow_html=True)

if selected_view.startswith("🏆"):
    st.header("🏆 Master Recruitment Leaderboard (Top 1 Per Position)")
    st.markdown("Consolidated club-wide view featuring the top-ranked target for each tactical position.")
    
    # Define your exact desired position display order
    position_order = [
        "Goalkeepers",
        "Center Backs",
        "Left Backs",
        "Right Backs",
        "Central Midfielder", # Matches your exact sheet name (or update to match your exact sheet title)
        "Attacking Midfielders",
        "Wingers",
        "Center Forwards"
    ]
    
    all_dfs = []
    
    # Loop through in your strict order
    for pos_name in position_order:
        # Match position name flexibly to your loaded sheets dict keys
        actual_sheet_key = next((k for k in data.keys() if pos_name.lower() in k.lower()), None)
        
        if actual_sheet_key and actual_sheet_key in data:
            df_pos = data[actual_sheet_key].copy()
            df_pos["Position Tab"] = actual_sheet_key
            
            # Ensure team column is uniform
            if 'Team' not in df_pos.columns:
                for col in df_pos.columns:
                    if 'team' in col.lower() or 'club' in col.lower():
                        df_pos = df_pos.rename(columns={col: 'Team'})
                        break
                if 'Team' not in df_pos.columns:
                    df_pos['Team'] = "Unknown"
            else:
                df_pos['Team'] = df_pos['Team'].fillna("Unknown")
            
            # Grab strictly the #1 top player for this position tab
            top_1_pos = df_pos.sort_values(by="Composite Score", ascending=False).head(1)
            all_dfs.append(top_1_pos)
    
    if all_dfs:
        master_df = pd.concat(all_dfs, ignore_index=True)
        # Note: We do NOT re-sort by composite score here, preserving your requested position order!
        master_df["Club Rank"] = range(1, len(master_df) + 1)
        
        # --- SELECT ONLY ESSENTIAL COLUMNS ---
        desired_columns = ['Club Rank', 'Player', 'Team', 'Position Tab', 'Composite Score', 'Minutes played', 'Age']
        display_columns = [col for col in desired_columns if col in master_df.columns]
        master_clean = master_df[display_columns]
        
        st.dataframe(master_clean, use_container_width=True, hide_index=True)
        
        st.subheader("Top Tier Targets by Position")
        if "Player" in master_clean.columns and "Composite Score" in master_clean.columns:
            st.bar_chart(master_clean.set_index("Player")["Composite Score"])
    else:
        st.warning("No position data available to build the master leaderboard.")

else:
    position_name = selected_view.replace("📍 Position: ", "")
    df_pos = data[position_name]
    
    st.header(f"Shortlist: {position_name}")
    
    # Minutes Played Slider Filter in Sidebar
    mins_col = next((col for col in df_pos.columns if any(k in col.lower() for k in ["minute", "min"])), None)
    if mins_col:
        df_pos[mins_col] = pd.to_numeric(df_pos[mins_col], errors="coerce").fillna(0)
        max_mins = int(df_pos[mins_col].max()) if not df_pos[mins_col].empty and df_pos[mins_col].max() > 0 else 5000
        st.sidebar.markdown("---")
        st.sidebar.subheader("Filters")
        min_minutes = st.sidebar.slider("Minimum Minutes Played", 0, max_mins, 0)
        filtered_df = df_pos[df_pos[mins_col] >= min_minutes]
    else:
        filtered_df = df_pos

    st.dataframe(filtered_df, use_container_width=True)
    
    if "Composite Score" in filtered_df.columns and "Player" in filtered_df.columns:
        st.subheader(f"{position_name} Composite Performance Ranking")
        chart_data = filtered_df.set_index("Player")["Composite Score"].dropna()
        st.bar_chart(chart_data)
