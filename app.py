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

# --- 2. MAIN APP ---
if check_password() and repo:
    st.set_page_config(layout="wide", page_title="Vision Jet Analytics", page_icon="✈️")

    with st.sidebar:
        st.title("🚀 SF50 Fleet Control")
        
        # Aircraft Selection logic
        try:
            contents = repo.get_contents("data")
            profile_names = [c.name for c in contents if c.type == "dir"]
        except:
            profile_names = []

        selected_profile = st.selectbox("Select Aircraft", ["+ Create New Profile"] + sorted(profile_names))
        
        # --- REGISTRATION MODE ---
        if selected_profile == "+ Create New Profile":
            st.subheader("🆕 Register New Aircraft")
            # We use keys to allow us to clear them later if needed
            new_tail = st.text_input("Tail Number", placeholder="N123SF", key="reg_tail").upper().strip()
            new_sn = st.text_input("Aircraft S/N", placeholder="e.g. 1234", key="reg_sn")
            
            if st.button("Register Aircraft", use_container_width=True, type="primary"):
                if new_tail:
                    try:
                        # Initialize folder with S/N metadata
                        repo.create_file(f"data/{new_tail}/.profile", f"Init {new_tail}", f"S/N: {new_sn}")
                        st.success(f"Profile {new_tail} Created!")
                        # Clear inputs by forcing rerun with the new aircraft selected
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
                else:
                    st.warning("Tail Number is required.")
            
            # Hide the rest of the app until an aircraft is selected
            st.info("Register an aircraft to enable data uploading.")
            st.stop()

        # --- ACTIVE MODE (Aircraft Selected) ---
        else:
            tail_number = selected_profile
            # Fetch S/N from the cloud
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
            except:
                selected_history = "-- Load Previous --"

            # Danger Zone
            if selected_history != "-- Load Previous --":
                with st.expander("⚠️ Danger Zone"):
                    confirm_delete = st.checkbox("Confirm Delete")
                    if st.button("🗑️ Delete Log", type="primary", disabled=not confirm_delete):
                        file_to_delete = history_map[selected_history]
                        repo.delete_file(file_to_delete.path, f"Removed {selected_history}", file_to_delete.sha)
                        st.rerun()

            st.divider()
            # Upload section is now permanently visible for active profiles
            st.subheader("📤 Upload Data")
            uploaded_file = st.file_uploader("Drop CSV here", type="csv")
            upload_btn = st.button("Upload to Cloud", use_container_width=True)

    # --- 3. DATA LOGIC ---
    df = None
    active_source = ""

    if uploaded_file and upload_btn:
        with st.spinner("Uploading..."):
            try:
                df = cleaner.clean_data(uploaded_file)
                save_name = uploaded_file.name
                file_path = f"data/{tail_number}/{save_name}"
                
                # Double check for duplicates
                try:
                    repo.get_contents(file_path)
                    st.error("This file already exists in this profile.")
                except:
                    repo.create_file(file_path, f"Add: {save_name}", df.to_csv(index=False))
                    st.success("File uploaded successfully!")
                    st.rerun()
            except Exception as e:
                st.error(f"Processing error: {e}")

    elif selected_history != "-- Load Previous --":
        try:
            full_file_path = f"data/{tail_number}/{selected_history}"
            file_data = repo.get_contents(full_file_path)
            df = pd.read_csv(io.StringIO(file_data.decoded_content.decode('utf-8')))
            active_source = selected_history
        except Exception:
            st.error("Failed to load history.")

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
        st.info(f"Ready for **{tail_number}**. Upload a log or select from history.")
