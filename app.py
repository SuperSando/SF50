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
        # Use a token stored in Streamlit Secrets
        g = Github(st.secrets["github_token"])
        # Format: "Username/RepositoryName"
        repo = g.get_repo(st.secrets["repo_path"]) 
        return repo
    except Exception as e:
        st.error(f"GitHub Connection Error: {e}")
        return None

repo = get_github_repo()

# --- 2. MAIN APP ---
if check_password() and repo:
    st.set_page_config(layout="wide", page_title="Vision Jet Analytics", page_icon="✈️")

    with st.sidebar:
        st.title("🚀 SF50 Fleet Control")
        
        # Aircraft Selection (Scans folders in the 'data/' directory of your repo)
        st.subheader("📁 Aircraft Profile")
        try:
            contents = repo.get_contents("data")
            profile_names = [c.name for c in contents if c.type == "dir"]
        except:
            profile_names = []

        selected_profile = st.selectbox("Select Aircraft", ["New Profile..."] + sorted(profile_names))
        
        if selected_profile == "New Profile...":
            tail_number = st.text_input("Tail Number (New)", placeholder="N123SF").upper().strip()
        else:
            tail_number = selected_profile

        aircraft_sn = st.text_input("Aircraft S/N", placeholder="e.g. 1234")
        st.divider()

        # History Selection
        if tail_number:
            try:
                history_files = repo.get_contents(f"data/{tail_number}")
                history_list = [f.name for f in history_files if f.name.endswith(".csv")]
                selected_history = st.selectbox("📜 Flight History", ["-- Load Previous --"] + sorted(history_list, reverse=True))
            except:
                selected_history = "-- Load Previous --"
        else:
            selected_history = "-- Load Previous --"

        st.divider()
        uploaded_file = st.file_uploader("Upload New Log", type="csv")
        flight_dt = st.date_input("Flight Date", value=datetime.now())
        flight_tm = st.time_input("Flight Time", value=datetime.now().time())

    # --- 3. DATA LOGIC ---
    df = None
    active_source = ""

    if uploaded_file:
        with st.spinner("Pushing Data to GitHub..."):
            df = cleaner.clean_data(uploaded_file)
            active_source = uploaded_file.name
            save_name = f"{flight_dt.strftime('%Y%m%d')}_{flight_tm.strftime('%H%M')}_{active_source}"
            file_path = f"data/{tail_number}/{save_name}"
            
            # Commit to GitHub
            csv_content = df.to_csv(index=False)
            try:
                repo.create_file(file_path, f"Upload flight data: {save_name}", csv_content)
                st.sidebar.success(f"Pushed to GitHub: {save_name}")
            except Exception as e:
                st.error(f"GitHub Write Error: {e}")

    elif selected_history != "-- Load Previous --":
        file_content = repo.get_contents(f"data/{tail_number}/{selected_history}")
        df = pd.read_csv(io.StringIO(file_content.decoded_content.decode()))
        active_source = selected_history

    # --- 4. DASHBOARD ---
    if df is not None:
        st.title(f"✈️ {tail_number} Analysis")
        st.caption(f"S/N: {aircraft_sn} | Source: {active_source}")
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Max GS", f"{df['Groundspeed'].max():.0f} kts")
        m2.metric("Peak ITT", f"{df['ITT (F)'].max():.0f} °F")
        m3.metric("Max N1", f"{df['N1 %'].max():.1f}%")
        m4.metric("Duration", f"{(len(df) / 60):.1f} min")

        st.plotly_chart(visualizer.generate_dashboard(df), use_container_width=True)
    else:
        st.info("Log in and select an aircraft profile to view telemetry.")
