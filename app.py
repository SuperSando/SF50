import streamlit as st
import pandas as pd
import clean_flight_data as cleaner
import graph_flight_interactive as visualizer
from datetime import datetime
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from google.oauth2 import service_account
import io

# --- 1. AUTHENTICATION & DRIVE CONNECTION ---
def check_password():
    if "password_correct" not in st.session_state:
        st.title("🔒 SF50 Data Access")
        st.text_input("Enter Dashboard Password", type="password", key="password_input")
        if st.button("Log In"):
            try:
                if st.session_state["password_input"] == st.secrets["password"]["password"]:
                    st.session_state["password_correct"] = True
                    st.rerun()
                else:
                    st.error("😕 Password incorrect")
            except Exception:
                st.error("Secrets not configured correctly. Check the [password] block.")
        return False
    return True

@st.cache_resource
def get_drive_connection():
    try:
        creds_dict = dict(st.secrets["gdrive_service_account"])
        
        # FINAL RSA KEY CLEANER: Handles Python 3.13 decoder requirements
        if "private_key" in creds_dict:
            pk = creds_dict["private_key"]
            # 1. Replace escaped newlines if they exist
            pk = pk.replace("\\n", "\n")
            # 2. Ensure the string is clean of accidental wrapping quotes or spaces
            pk = pk.strip().strip("'").strip('"')
            creds_dict["private_key"] = pk
            
        SCOPES = ['https://www.googleapis.com/auth/drive']
        creds = service_account.Credentials.from_service_account_info(
            creds_dict, 
            scopes=SCOPES
        )
        
        gauth = GoogleAuth()
        gauth.credentials = creds
        return GoogleDrive(gauth)
    except Exception as e:
        st.error(f"Drive Connection Error: {e}")
        st.info("Check: Is the private_key pasted correctly between triple quotes in Secrets?")
        return None

drive = get_drive_connection()

# Helper: Find or Create Folder in Drive
def get_folder_id(folder_name, parent_id=None):
    query = f"title='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    if parent_id:
        query += f" and '{parent_id}' in parents"
    
    file_list = drive.ListFile({'q': query}).GetList()
    if file_list:
        return file_list[0]['id']
    else:
        meta = {'title': folder_name, 'mimeType': 'application/vnd.google-apps.folder'}
        if parent_id:
            meta['parents'] = [{'id': parent_id}]
        folder = drive.CreateFile(meta)
        folder.Upload()
        return folder['id']

# --- 2. MAIN APP ---
if check_password() and drive:
    st.set_page_config(layout="wide", page_title="Vision Jet Analytics", page_icon="✈️")

    st.markdown("""
        <style>
        [data-testid="stMetricValue"] { font-size: 1.8rem; color: #d33612; }
        .stTabs [data-baseweb="tab-list"] { gap: 24px; }
        .stTabs [data-baseweb="tab"] { height: 50px; font-weight: bold; }
        </style>
        """, unsafe_allow_html=True)

    ROOT_ID = get_folder_id("sf50-fleet-data")

    with st.sidebar:
        st.title("🚀 SF50 Fleet Control")
        st.subheader("📁 Aircraft Profile")
        
        profiles = drive.ListFile({'q': f"'{ROOT_ID}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"}).GetList()
        profile_names = [p['title'] for p in profiles]
        
        selected_profile = st.selectbox("Select Aircraft", ["New Profile..."] + sorted(profile_names))
        
        if selected_profile == "New Profile...":
            tail_number = st.text_input("Tail Number (New)", placeholder="N123SF").upper().strip()
        else:
            tail_number = selected_profile

        aircraft_sn = st.text_input("Aircraft S/N", placeholder="e.g. 1234")
        st.divider()

        if tail_number:
            tail_id = get_folder_id(tail_number, ROOT_ID)
            history_files = drive.ListFile({'q': f"'{tail_id}' in parents and trashed=false"}).GetList()
            history_map = {f['title']: f['id'] for f in history_files}
            selected_history = st.selectbox("📜 Flight History", ["-- Load Previous --"] + sorted(history_map.keys(), reverse=True))
        else:
            selected_history = "-- Load Previous --"

        st.divider()
        uploaded_file = st.file_uploader("Upload New Log", type="csv")
        flight_dt = st.date_input("Flight Date", value=datetime.now())
        flight_tm = st.time_input("Flight Time", value=datetime.now().time())
        flight_notes = st.text_area("Flight Notes")

    # --- 3. DATA LOGIC ---
    df = None
    active_source = ""

    if uploaded_file:
        try:
            with st.spinner("Processing & Syncing to Drive..."):
                uploaded_file.seek(0)
                df = cleaner.clean_data(uploaded_file)
                active_source = uploaded_file.name
                dt_stamp = f"{flight_dt.strftime('%Y%m%d')}_{flight_tm.strftime('%H%M')}"
                save_name = f"{dt_stamp}_{active_source}"
                
                csv_buffer = io.StringIO()
                df.to_csv(csv_buffer, index=False)
                
                f_drive = drive.CreateFile({'title': save_name, 'parents': [{'id': tail_id}]})
                f_drive.SetContentString(csv_buffer.getvalue())
                f_drive.Upload()
                st.sidebar.success(f"Saved: {save_name}")
        except Exception as e:
            st.error(f"Upload Error: {e}")

    elif selected_history != "-- Load Previous --":
        try:
            file_id = history_map[selected_history]
            f_drive = drive.CreateFile({'id': file_id})
            content = f_drive.GetContentString()
            df = pd.read_csv(io.StringIO(content))
            active_source = selected_history
        except Exception as e:
            st.error(f"Load Error: {e}")

    # --- 4. DASHBOARD ---
    if df is not None:
        st.title(f"✈️ {tail_number} Analysis")
        st.caption(f"S/N: {aircraft_sn} | Source: {active_source}")

        m1, m2, m3, m4 = st.columns(4)
        with m1: st.metric("Max GS", f"{df['Groundspeed'].max():.0f} kts")
        with m2: st.metric("Peak ITT", f"{df['ITT (F)'].max():.0f} °F")
        with m3: st.metric("Max N1", f"{df['N1 %'].max():.1f}%")
        with m4: st.metric("Duration", f"{(len(df) / 60):.1f} min")

        fig = visualizer.generate_dashboard(df)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.title("SF50 Fleet Analytics")
        st.info("Ready for analysis. Select a profile or upload a file in the sidebar.")
