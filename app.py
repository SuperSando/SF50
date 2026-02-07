import streamlit as st
import pandas as pd
import clean_flight_data as cleaner
import graph_flight_interactive as visualizer
from datetime import datetime
import gcsfs
from google.oauth2 import service_account

# --- 1. AUTHENTICATION & CLOUD CONNECTION ---
def check_password():
    """Simple password protection layer."""
    if "password_correct" not in st.session_state:
        st.title("🔒 SF50 Data Access")
        st.text_input("Enter Dashboard Password", type="password", key="password_input")
        if st.button("Log In"):
            # Check against the [password] section in your secrets
            try:
                if st.session_state["password_input"] == st.secrets["password"]["password"]:
                    st.session_state["password_correct"] = True
                    st.rerun()
                else:
                    st.error("😕 Password incorrect")
            except:
                st.error("Secrets not configured correctly. Check [password] block.")
        return False
    return True

# Initialize GCS/Google Drive Connection
try:
    # Convert the secrets to a dict
    creds_dict = dict(st.secrets["gdrive_service_account"])
    
    # Create formal credentials
    # This specifically addresses the 401 error by ensuring the key is parsed correctly
    credentials = service_account.Credentials.from_service_account_info(creds_dict)
    
    # Initialize the filesystem
    fs = gcsfs.GCSFileSystem(project=creds_dict.get('project_id'), token=credentials)
    
    # Root Folder Name
    ROOT_FOLDER = "sf50-fleet-data" 
    
    # Pre-flight check: Can we see the folder?
    if not fs.exists(ROOT_FOLDER):
        fs.mkdir(ROOT_FOLDER)
        
except Exception as e:
    st.error(f"Cloud Connection Error (401/Auth): {e}")
    st.info("Check: 1. Is Google Drive API enabled? 2. Is the folder shared with the Service Account email?")
    st.stop()

# --- 2. MAIN APP ---
if check_password():
    st.set_page_config(layout="wide", page_title="Vision Jet Analytics", page_icon="✈️")

    # Custom CSS for UI branding
    st.markdown("""
        <style>
        [data-testid="stMetricValue"] { font-size: 1.8rem; color: #d33612; }
        .stTabs [data-baseweb="tab-list"] { gap: 24px; }
        .stTabs [data-baseweb="tab"] { height: 50px; font-weight: bold; }
        </style>
        """, unsafe_allow_html=True)

    # --- SIDEBAR: PROFILES & UPLOADS ---
    with st.sidebar:
        st.title("🚀 SF50 Fleet Control")
        
        st.subheader("📁 Aircraft Profile")
        try:
            # List folders in Google Drive
            existing_profiles = [f.split('/')[-1] for f in fs.ls(ROOT_FOLDER) if fs.isdir(f)]
        except:
            existing_profiles = []
            
        selected_profile = st.selectbox("Select Aircraft", ["New Profile..."] + existing_profiles)
        
        if selected_profile == "New Profile...":
            tail_number = st.text_input("Tail Number (New)", placeholder="N123SF").upper().strip()
        else:
            tail_number = selected_profile

        # Metadata: Aircraft S/N
        aircraft_sn = st.text_input("Aircraft S/N", placeholder="e.g. 1234")
        
        st.divider()
        
        # Load History
        if tail_number:
            profile_path = f"{ROOT_FOLDER}/{tail_number}"
            if not fs.exists(profile_path):
                fs.mkdir(profile_path)
            
            history = sorted([f.split('/')[-1] for f in fs.ls(profile_path)], reverse=True)
            selected_history = st.selectbox("📜 Flight History", ["-- Load Previous --"] + history)
        else:
            selected_history = "-- Load Previous --"

        st.divider()
        uploaded_file = st.file_uploader("Upload New Log", type="csv")
        
        st.subheader("📝 Flight Details")
        flight_dt = st.date_input("Flight Date", value=datetime.now())
        flight_tm = st.time_input("Flight Time", value=datetime.now().time())
        flight_notes = st.text_area("Flight Notes")

    # --- 3. DATA LOGIC ---
    df = None
    active_source = ""

    # New Upload Logic
    if uploaded_file:
        try:
            with st.spinner("Saving to Cloud..."):
                uploaded_file.seek(0)
                df = cleaner.clean_data(uploaded_file)
                active_source = uploaded_file.name
                
                dt_stamp = f"{flight_dt.strftime('%Y%m%d')}_{flight_tm.strftime('%H%M')}"
                save_name = f"{dt_stamp}_{active_source}"
                save_path = f"{ROOT_FOLDER}/{tail_number}/{save_name}"
                
                with fs.open(save_path, "w") as f:
                    df.to_csv(f, index=False)
                st.sidebar.success(f"Log Saved to {tail_number}")
        except Exception as e:
            st.error(f"Upload Error: {e}")

    # History Selection Logic
    elif selected_history != "-- Load Previous --":
        try:
            load_path = f"{ROOT_FOLDER}/{tail_number}/{selected_history}"
            with fs.open(load_path, "r") as f:
                df = pd.read_csv(f)
            active_source = selected_history
        except Exception as e:
            st.error(f"Load Error: {e}")

    # --- 4. DASHBOARD DISPLAY ---
    if df is not None:
        st.title(f"✈️ {tail_number} | Flight Analysis")
        st.caption(f"S/N: {aircraft_sn} | Source: {active_source}")

        # Metrics Row
        m1, m2, m3, m4 = st.columns(4)
        with m1: st.metric("Max GS", f"{df['Groundspeed'].max():.0f} kts")
        with m2: st.metric("Peak ITT", f"{df['ITT (F)'].max():.0f} °F")
        with m3: st.metric("Max N1", f"{df['N1 %'].max():.1f}%")
        with m4: st.metric("Duration", f"{(len(df) / 60):.1f} min")

        st.divider()

        tab_graph, tab_data = st.tabs(["📊 Interactive Analytics", "📋 Raw Telemetry"])

        with tab_graph:
            fig = visualizer.generate_dashboard(df)
            st.plotly_chart(fig, use_container_width=True)

        with tab_data:
            st.dataframe(df, use_container_width=True)
            
            # Export with Metadata
            header = (
                f"# Tail Number: {tail_number}\n"
                f"# Aircraft S/N: {aircraft_sn}\n"
                f"# Flight Time: {flight_dt} {flight_tm}\n"
                f"# Notes: {flight_notes.replace(chr(10), ' ')}\n"
            )
            csv_data = header + df.to_csv(index=False)
            st.download_button("💾 Export Local CSV", csv_data, f"CLEANED_{active_source}", "text/csv")
    else:
        st.title("SF50 Fleet Analytics")
        st.info("Select a profile or upload a new G3000 log in the sidebar.")
