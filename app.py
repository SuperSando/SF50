import streamlit as st
import pandas as pd
import clean_flight_data as cleaner
import graph_flight_interactive as visualizer
from datetime import datetime
import io
from github import Github

# --- 1. AUTHENTICATION ---
def check_password():
    if "password_correct" not in st.session_state:
        st.title("🔒 SF50 Data Access")
        st.text_input("Enter Dashboard Password", type="password", key="password_input")
        if st.button("Log In"):
            if st.session_state["password_input"] == st.secrets["password"]["password"]:
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("😕 Password incorrect")
        return False
    return True

# --- GITHUB CONNECTION ---
@st.cache_resource
def get_github_repo():
    try:
        # Shorthand fix: explicitly pulling the string value from the secret dict
        token_str = st.secrets["github_token"]["github_token"]
        repo_path_str = st.secrets["repo_path"]["repo_path"]
        
        g = Github(token_str)
        repo = g.get_repo(repo_path_str) 
        return repo
    except Exception as e:
        st.error(f"GitHub Connection Error: {e}")
        return None

repo = get_github_repo()

# --- 2. MAIN APP ---
if check_password() and repo:
    st.set_page_config(layout="wide", page_title="Vision Jet Analytics", page_icon="✈️")

    # Sidebar: Branding and Controls
    with st.sidebar:
        st.title("🚀 SF50 Fleet Control")
        
        # Aircraft Profile Logic
        st.subheader("📁 Aircraft Profile")
        try:
            # Scans the 'data/' directory in your GitHub repo for folders
            contents = repo.get_contents("data")
            profile_names = [c.name for c in contents if c.type == "dir"]
        except:
            profile_names = []

        selected_profile = st.selectbox("Select Aircraft", ["New Profile..."] + sorted(profile_names))
        
        if selected_profile == "New Profile...":
            tail_number = st.text_input("Tail Number (New)", placeholder="N123SF").upper().strip()
        else:
            tail_number = selected_profile

        # Aircraft Serial Number
        aircraft_sn = st.text_input("Aircraft S/N", placeholder="e.g. 1234")
        st.divider()

        # Flight History Logic
        if tail_number:
            try:
                # Scans the specific tail number folder
                history_files = repo.get_contents(f"data/{tail_number}")
                history_list = [f.name for f in history_files if f.name.endswith(".csv")]
                selected_history = st.selectbox("📜 Flight History", ["-- Load Previous --"] + sorted(history_list, reverse=True))
            except:
                selected_history = "-- Load Previous --"
        else:
            selected_history = "-- Load Previous --"

        st.divider()
        uploaded_file = st.file_uploader("Upload New G3000 Log", type="csv")
        flight_dt = st.date_input("Flight Date", value=datetime.now())
        flight_tm = st.time_input("Flight Time", value=datetime.now().time())

    # --- 3. DATA PROCESSING ---
    df = None
    active_source = ""

    # Option A: Handle New Uploads
    if uploaded_file:
        with st.spinner("Processing & Pushing to GitHub..."):
            try:
                uploaded_file.seek(0)
                df = cleaner.clean_data(uploaded_file)
                active_source = uploaded_file.name
                
                # Filename logic: YYYYMMDD_HHMM_FileName.csv
                dt_stamp = f"{flight_dt.strftime('%Y%m%d')}_{flight_tm.strftime('%H%M')}"
                save_name = f"{dt_stamp}_{active_source}"
                file_path = f"data/{tail_number}/{save_name}"
                
                # Push the cleaned CSV to GitHub
                csv_content = df.to_csv(index=False)
                repo.create_file(file_path, f"Upload flight data: {save_name}", csv_content)
                st.sidebar.success(f"Pushed to GitHub: {save_name}")
            except Exception as e:
                st.error(f"Upload Error: {e}")

    # Option B: Load From History
    elif selected_history != "-- Load Previous --":
        try:
            file_content = repo.get_contents(f"data/{tail_number}/{selected_history}")
            df = pd.read_csv(io.StringIO(file_content.decoded_content.decode()))
            active_source = selected_history
        except Exception as e:
            st.error(f"Error loading history: {e}")

    # --- 4. DASHBOARD DISPLAY ---
    if df is not None:
        st.title(f"✈️ {tail_number} | Performance Dashboard")
        st.caption(f"Aircraft S/N: {aircraft_sn} | Source: {active_source}")
        
        # Performance Metrics Row
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Max Groundspeed", f"{df['Groundspeed'].max():.0f} kts")
        m2.metric("Peak ITT", f"{df['ITT (F)'].max():.0f} °F")
        m3.metric("Max N1", f"{df['N1 %'].max():.1f}%")
        m4.metric("Flight Duration", f"{(len(df) / 60):.1f} min")

        st.divider()
        
        # Analytics Tabs
        tab_viz, tab_raw = st.tabs(["📊 Interactive Analytics", "📋 Raw Telemetry"])
        
        with tab_viz:
            fig = visualizer.generate_dashboard(df)
            st.plotly_chart(fig, use_container_width=True)
            
        with tab_raw:
            st.dataframe(df, use_container_width=True)
            
            # Export with Metadata
            header = f"# Tail: {tail_number} | S/N: {aircraft_sn}\n# Log: {active_source}\n"
            csv_data = header + df.to_csv(index=False)
            st.download_button("💾 Download Local CSV", csv_data, f"CLEANED_{active_source}", "text/csv")
    else:
        st.title("SF50 Fleet Data Analysis")
        st.info("Log in and select an aircraft profile or upload a G3000 log in the sidebar to begin.")
