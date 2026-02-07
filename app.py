import streamlit as st
import pandas as pd
import clean_flight_data as cleaner
import graph_flight_interactive as visualizer
from datetime import datetime
import io
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload
from google.oauth2 import service_account

# --- 1. AUTHENTICATION ---
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
            except:
                st.error("Secrets missing. Check the [password] block.")
        return False
    return True

@st.cache_resource
def get_drive_service():
    try:
        creds_info = dict(st.secrets["gdrive_service_account"])
        SCOPES = ['https://www.googleapis.com/auth/drive']
        creds = service_account.Credentials.from_service_account_info(creds_info, scopes=SCOPES)
        return build('drive', 'v3', credentials=creds)
    except Exception as e:
        st.error(f"Drive API Connection Error: {e}")
        return None

service = get_drive_service()

# --- DRIVE HELPERS ---
def get_folder_id(name, parent_id=None):
    query = f"name = '{name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    if parent_id: query += f" and '{parent_id}' in parents"
    
    results = service.files().list(
        q=query, 
        fields="files(id)",
        supportsAllDrives=True, 
        includeItemsFromAllDrives=True
    ).execute()
    
    files = results.get('files', [])
    if files: return files[0]['id']
    
    meta = {'name': name, 'mimeType': 'application/vnd.google-apps.folder'}
    if parent_id: meta['parents'] = [parent_id]
    
    folder = service.files().create(
        body=meta, 
        fields='id',
        supportsAllDrives=True
    ).execute()
    return folder.get('id')

def list_files_in_folder(folder_id):
    query = f"'{folder_id}' in parents and trashed = false"
    results = service.files().list(
        q=query, 
        fields="files(id, name)",
        supportsAllDrives=True, 
        includeItemsFromAllDrives=True
    ).execute()
    return results.get('files', [])

# --- 2. MAIN APP ---
if check_password() and service:
    st.set_page_config(layout="wide", page_title="Vision Jet Analytics", page_icon="✈️")

    # Initial Setup
    ROOT_ID = get_folder_id("sf50-fleet-data")

    with st.sidebar:
        st.title("🚀 SF50 Fleet Control")
        
        st.subheader("📁 Aircraft Profile")
        profiles = list_files_in_folder(ROOT_ID)
        profile_names = [p['name'] for p in profiles]
        
        selected_profile = st.selectbox("Select Aircraft", ["New Profile..."] + sorted(profile_names))
        
        if selected_profile == "New Profile...":
            tail_number = st.text_input("Tail Number (New)", placeholder="N123SF").upper().strip()
        else:
            tail_number = selected_profile

        aircraft_sn = st.text_input("Aircraft S/N", placeholder="e.g. 1234")
        st.divider()

        if tail_number:
            tail_id = get_folder_id(tail_number, ROOT_ID)
            history_list = list_files_in_folder(tail_id)
            history_map = {f['name']: f['id'] for f in history_list}
            selected_history = st.selectbox("📜 Flight History", ["-- Load Previous --"] + sorted(history_map.keys(), reverse=True))
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
        with st.spinner("Processing & Saving to Drive..."):
            df = cleaner.clean_data(uploaded_file)
            active_source = uploaded_file.name
            save_name = f"{flight_dt.strftime('%Y%m%d')}_{flight_tm.strftime('%H%M')}_{active_source}"
            
            csv_str = df.to_csv(index=False)
            fh = io.BytesIO(csv_str.encode())
            media = MediaIoBaseUpload(fh, mimetype='text/csv', resumable=True) # Switch to Resumable
            
            # THE FIX: Add 'appProperties' and 'viewersCanCopyContent'
            # This pushes the file as a shared asset rather than a personal one
            file_metadata = {
                'name': save_name,
                'parents': [tail_id]
            }
            
            try:
                service.files().create(
                    body=file_metadata, 
                    media_body=media,
                    supportsAllDrives=True,
                    fields='id'
                ).execute()
                st.sidebar.success(f"Saved: {save_name}")
            except Exception as e:
                if "storageQuotaExceeded" in str(e):
                    st.error("🚨 Google Drive Quota Error")
                    st.info("The Robot Account is being blocked. Please move the 'sf50-fleet-data' folder into a **Google Shared Drive** (Workspace feature) OR ensure you have shared it with Editor permissions.")
                else:
                    st.error(f"Save Error: {e}")

    elif selected_history != "-- Load Previous --":
        file_id = history_map[selected_history]
        request = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done: _, done = downloader.next_chunk()
        fh.seek(0)
        df = pd.read_csv(fh)
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
