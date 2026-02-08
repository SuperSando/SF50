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
        
        # Aircraft Selection
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
        history_map = {}
        if tail_number:
            try:
                history_files = repo.get_contents(f"data/{tail_number}")
                history_map = {f.name: f for f in history_files if f.name.endswith(".csv")}
                selected_history = st.selectbox("📜 Flight History", ["-- Load Previous --"] + sorted(history_map.keys(), reverse=True))
            except:
                selected_history = "-- Load Previous --"
        else:
            selected_history = "-- Load Previous --"

        # Danger Zone
        if selected_history != "-- Load Previous --":
            st.divider()
            with st.expander("⚠️ Danger Zone"):
                confirm_delete = st.checkbox("Confirm Deletion")
                if st.button("🗑️ Delete Log", type="primary", disabled=not confirm_delete):
                    try:
                        file_to_delete = history_map[selected_history]
                        repo.delete_file(file_to_delete.path, f"Removed {selected_history}", file_to_delete.sha)
                        st.sidebar.success("Log removed.")
                        st.rerun()
                    except Exception:
                        st.error("Delete Failed.")

        st.divider()
        # Simplified Upload Section
        uploaded_file = st.file_uploader("Upload New Log", type="csv")
        
        # Manual upload trigger to prevent "sticky file" bugs
        upload_btn = st.button("Upload", use_container_width=True, type="primary")

    # --- 3. DATA LOGIC ---
    df = None
    active_source = ""

    if uploaded_file and upload_btn:
        with st.spinner("Processing & Saving..."):
            try:
                df = cleaner.clean_data(uploaded_file)
                # Filename is now exactly what the user uploaded
                save_name = uploaded_file.name
                file_path = f"data/{tail_number}/{save_name}"
                
                # Check for existing file with the same name
                try:
                    repo.get_contents(file_path)
                    st.error(f"Error: {save_name} already exists.")
                except:
                    repo.create_file(file_path, f"Add: {save_name}", df.to_csv(index=False))
                    st.sidebar.success(f"✅ Successfully Uploaded: {save_name}")
                    st.rerun()
            except Exception as e:
                st.error(f"Error processing file: {e}")

    elif selected_history != "-- Load Previous --":
        try:
            full_file_path = f"data/{tail_number}/{selected_history}"
            file_data = repo.get_contents(full_file_path)
            df = pd.read_csv(io.StringIO(file_data.decoded_content.decode('utf-8')))
            active_source = selected_history
        except Exception:
            st.error("Error loading history.")

    # --- 4. DASHBOARD ---
    if df is not None:
        st.title(f"✈️ {tail_number} Analysis")
        st.caption(f"S/N: {aircraft_sn} | File: {active_source}")
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Max GS", f"{df['Groundspeed'].max():.0f} kts")
        m2.metric("Peak ITT", f"{df['ITT (F)'].max():.0f} °F")
        m3.metric("Max N1", f"{df['N1 %'].max():.1f}%")
        m4.metric("Duration", f"{(len(df) / 60):.1f} min")
        
        st.plotly_chart(visualizer.generate_dashboard(df), use_container_width=True)
    else:
        st.info("Upload a log or select from history to begin.")
