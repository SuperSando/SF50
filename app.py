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

@st.cache_resource
def get_github_repo():
    try:
        token_str = st.secrets["github_token"]["github_token"]
        repo_path_str = st.secrets["repo_path"]["repo_path"]
        g = Github(token_str)
        return g.get_repo(repo_path_str)
    except Exception as e:
        st.error(f"GitHub Connection Error: {e}")
        return None

repo = get_github_repo()

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
        tail_number = st.text_input("Tail Number (New)", placeholder="N123SF").upper().strip() if selected_profile == "New Profile..." else selected_profile
        aircraft_sn = st.text_input("Aircraft S/N", placeholder="e.g. 1234")
        st.divider()

        # History Selection
        history_map = {}
        if tail_number:
            try:
                history_files = repo.get_contents(f"data/{tail_number}")
                # We store the full file object so we can get the 'sha' for deletion
                history_map = {f.name: f for f in history_files if f.name.endswith(".csv")}
                selected_history = st.selectbox("📜 Flight History", ["-- Load Previous --"] + sorted(history_map.keys(), reverse=True))
            except:
                selected_history = "-- Load Previous --"
        else:
            selected_history = "-- Load Previous --"

        # --- NEW: THE DANGER ZONE (DELETION) ---
        if selected_history != "-- Load Previous --":
            st.divider()
            with st.expander("⚠️ Danger Zone"):
                st.write(f"Delete **{selected_history}**?")
                confirm_delete = st.checkbox("I am sure I want to delete this log.")
                if st.button("🗑️ Permanently Delete Log", type="primary", disabled=not confirm_delete):
                    try:
                        file_to_delete = history_map[selected_history]
                        repo.delete_file(
                            path=file_to_delete.path,
                            message=f"Deleted log: {selected_history}",
                            sha=file_to_delete.sha
                        )
                        st.sidebar.success(f"Deleted {selected_history}")
                        st.rerun() # Refresh to update the dropdown list
                    except Exception as e:
                        st.error(f"Delete Failed: {e}")

        st.divider()
        uploaded_file = st.file_uploader("Upload New Log", type="csv")
        flight_dt = st.date_input("Flight Date", value=datetime.now())
        flight_tm = st.time_input("Flight Time", value=datetime.now().time())

    # --- 3. DATA LOGIC ---
    df = None
    active_source = ""

    if uploaded_file:
        df = cleaner.clean_data(uploaded_file)
        active_source = uploaded_file.name
        dt_stamp = f"{flight_dt.strftime('%Y%m%d')}_{flight_tm.strftime('%H%M')}"
        save_name = f"{dt_stamp}_{active_source}"
        file_path = f"data/{tail_number}/{save_name}"
        
        try:
            repo.get_contents(file_path)
            st.error(f"⚠️ Duplicate Error: {save_name} already exists.")
            df = None
        except:
            with st.spinner("Pushing to GitHub..."):
                repo.create_file(file_path, f"Upload: {save_name}", df.to_csv(index=False))
                st.sidebar.success(f"✅ Pushed: {save_name}")

    elif selected_history != "-- Load Previous --":
        file_content = history_map[selected_history]
        df = pd.read_csv(io.StringIO(file_content.decoded_content.decode()))
        active_source = selected_history

    # --- 4. DASHBOARD ---
    if df is not None:
        st.title(f"✈️ {tail_number} Analysis")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Max GS", f"{df['Groundspeed'].max():.0f} kts")
        m2.metric("Peak ITT", f"{df['ITT (F)'].max():.0f} °F")
        m3.metric("Max N1", f"{df['N1 %'].max():.1f}%")
        m4.metric("Duration", f"{(len(df) / 60):.1f} min")
        st.plotly_chart(visualizer.generate_dashboard(df), use_container_width=True)
    else:
        st.info("Select a log or upload data to begin.")
