import streamlit as st
import pandas as pd
import clean_flight_data as cleaner
import graph_flight_interactive as visualizer
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

@st.cache_resource
def get_backend_connection():
    try:
        token_str = st.secrets["github_token"]["github_token"]
        repo_path_str = st.secrets["repo_path"]["repo_path"]
        g = Github(token_str)
        return g.get_repo(repo_path_str)
    except Exception:
        st.error("Connection Error: Cloud storage unavailable.")
        return None

repo = get_backend_connection()

# Initialize session state for the uploader and the active data
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0
if "active_df" not in st.session_state:
    st.session_state.active_df = None
if "active_source" not in st.session_state:
    st.session_state.active_source = ""

# --- 2. MAIN APP ---
if check_password() and repo:
    st.set_page_config(layout="wide", page_title="Vision Jet Analytics", page_icon="✈️")

    with st.sidebar:
        st.title("🚀 SF50 Fleet Control")
        
        try:
            contents = repo.get_contents("data")
            profile_names = [c.name for c in contents if c.type == "dir"]
        except:
            profile_names = []

        selected_profile = st.selectbox("Select Aircraft", ["+ Create New Profile"] + sorted(profile_names))
        
        # Reset active data if we switch aircraft
        if "last_profile" not in st.session_state:
            st.session_state.last_profile = selected_profile
        if st.session_state.last_profile != selected_profile:
            st.session_state.active_df = None
            st.session_state.active_source = ""
            st.session_state.last_profile = selected_profile

        # --- REGISTRATION MODE ---
        if selected_profile == "+ Create New Profile":
            st.subheader("🆕 Register New Aircraft")
            new_tail = st.text_input("Tail Number", placeholder="N123SF", key="reg_tail").upper().strip()
            new_sn = st.text_input("Aircraft S/N", placeholder="e.g. 1234", key="reg_sn")
            
            if st.button("Register Aircraft", use_container_width=True, type="primary"):
                if new_tail:
                    try:
                        repo.create_file(f"data/{new_tail}/.profile", f"Init {new_tail}", f"S/N: {new_sn}")
                        st.success(f"Profile {new_tail} Created!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
                else:
                    st.warning("Tail Number is required.")
            st.stop()

        # --- ACTIVE MODE ---
        else:
            tail_number = selected_profile
            try:
                sn_file = repo.get_contents(f"data/{tail_number}/.profile")
                aircraft_sn = sn_file.decoded_content.decode('utf-8').replace("S/N: ", "")
            except:
                aircraft_sn = "N/A"
            
            st.success(f"Active Tail: **{tail_number}**")
            st.caption(f"Serial Number: {aircraft_sn}")
            st.divider()

            # History Selection
            try:
                history_files = repo.get_contents(f"data/{tail_number}")
                history_map = {f.name: f for f in history_files if f.name.endswith(".csv")}
                selected_history = st.selectbox("📜 Flight History", ["-- Load Previous --"] + sorted(history_map.keys(), reverse=True))
                
                # If user selects from history, it overrides any temporary "active_df"
                if selected_history != "-- Load Previous --":
                    full_file_path = f"data/{tail_number}/{selected_history}"
                    file_data = repo.get_contents(full_file_path)
                    st.session_state.active_df = pd.read_csv(io.StringIO(file_data.decoded_content.decode('utf-8')))
                    st.session_state.active_source = selected_history
                else:
                    # NEW: Clear the screen if the user resets the dropdown
                    st.session_state.active_df = None
                    st.session_state.active_source = ""
            except:
                selected_history = "-- Load Previous --"

            # Danger Zone
            if selected_history != "-- Load Previous --":
                with st.expander("⚠️ Danger Zone"):
                    confirm_delete = st.checkbox("Confirm Delete")
                    if st.button("🗑️ Delete Log", type="primary", disabled=not confirm_delete):
                        file_to_delete = history_map[selected_history]
                        repo.delete_file(file_to_delete.path, f"Removed {selected_history}", file_to_delete.sha)
                        st.session_state.active_df = None
                        st.session_state.active_source = ""
                        st.rerun()

            st.divider()
            st.subheader("📤 Upload Data")
            uploaded_file = st.file_uploader(
                "Drop CSV here", 
                type="csv", 
                key=f"uploader_{st.session_state.uploader_key}"
            )
            upload_btn = st.button("Upload", use_container_width=True, type="primary")

    # --- 3. DATA LOGIC ---
    if uploaded_file and upload_btn:
        with st.spinner("Uploading & Opening..."):
            try:
                processed_df = cleaner.clean_data(uploaded_file)
                save_name = uploaded_file.name
                file_path = f"data/{tail_number}/{save_name}"
                
                try:
                    repo.get_contents(file_path)
                    st.error("This file already exists.")
                except:
                    # Upload to GitHub
                    repo.create_file(file_path, f"Add: {save_name}", processed_df.to_csv(index=False))
                    
                    # Update session state so it displays immediately
                    st.session_state.active_df = processed_df
                    st.session_state.active_source = save_name
                    
                    # Clear uploader for next time
                    st.session_state.uploader_key += 1
                    st.success("File uploaded and opened!")
                    st.rerun()
            except Exception as e:
                st.error(f"Processing error: {e}")

    # --- 4. DASHBOARD ---
    df = st.session_state.active_df
    active_source = st.session_state.active_source

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
        st.info(f"Dashboard for **{tail_number}** is empty.")
