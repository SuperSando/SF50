import streamlit as st
import pandas as pd
import clean_flight_data as cleaner
import graph_flight_interactive as visualizer
import io
from github import Github 

# --- 1. AUTHENTICATION & CONNECTION ---
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

# Initialize Session State
if "active_df" not in st.session_state: st.session_state.active_df = None
if "active_source" not in st.session_state: st.session_state.active_source = ""
if "uploader_key" not in st.session_state: st.session_state.uploader_key = 0

# --- 2. MAIN APP ---
if check_password() and repo:
    st.set_page_config(layout="wide", page_title="Vision Jet Analytics", page_icon="✈️")

    with st.sidebar:
        st.title("🚀 SF50 Fleet Control")
        
        try:
            contents = repo.get_contents("data")
            profile_names = [c.name for c in contents if c.type == "dir"]
        except: profile_names = []

        selected_profile = st.selectbox("Select Aircraft", ["+ Create New Profile"] + sorted(profile_names))
        
        if selected_profile == "+ Create New Profile":
            # (Registration logic stays as is)
            st.stop()

        tail_number = selected_profile
        st.success(f"Active Tail: **{tail_number}**")
        
        view_mode = st.radio("Dashboard Layout", ["Single View", "Split View"], index=1)
        st.divider()

        # --- HISTORY & DELETE LOGIC ---
        st.subheader("📜 Flight History")
        try:
            history_files = repo.get_contents(f"data/{tail_number}")
            history_map = {f.name: f for f in history_files if f.name.endswith(".csv")}
            history_list = sorted(history_map.keys(), reverse=True)
            
            selected_history = st.selectbox("Select Log", ["-- Select a File --"] + history_list)
            
            if selected_history != "-- Select a File --":
                col1, col2 = st.columns(2)
                
                # OPEN BUTTON (Modified)
                if col1.button("Open", use_container_width=True, type="primary"):
                    with st.spinner("Opening 12MB log..."):
                        file_data = repo.get_contents(f"data/{tail_number}/{selected_history}")
                        raw_bytes = file_data.decoded_content
                        st.session_state.active_df = pd.read_csv(io.BytesIO(raw_bytes))
                        st.session_state.active_source = selected_history
                        st.rerun()

                # DELETE BUTTON
                if col2.button("🗑️ Delete", use_container_width=True):
                    st.session_state.delete_confirm = True

                if st.session_state.get("delete_confirm"):
                    st.warning(f"Delete {selected_history}?")
                    if st.button("Confirm Permanent Delete"):
                        file_to_del = history_map[selected_history]
                        repo.delete_file(file_to_del.path, f"Del {selected_history}", file_to_del.sha)
                        st.session_state.active_df = None
                        st.session_state.active_source = ""
                        st.session_state.delete_confirm = False
                        st.rerun()
                    if st.button("Cancel"):
                        st.session_state.delete_confirm = False
                        st.rerun()
        except Exception:
            st.info("No flight history found for this aircraft.")

        st.divider()
        # --- UPLOAD LOGIC ---
        uploaded_file = st.file_uploader("Upload New CSV", type="csv", key=f"up_{st.session_state.uploader_key}")
        if st.button("Sync & Open", use_container_width=True):
            if uploaded_file:
                with st.spinner("Processing..."):
                    processed_df = cleaner.clean_data(uploaded_file)
                    repo.create_file(f"data/{tail_number}/{uploaded_file.name}", f"Add {uploaded_file.name}", processed_df.to_csv(index=False))
                    st.session_state.active_df = processed_df
                    st.session_state.active_source = uploaded_file.name
                    st.session_state.uploader_key += 1
                    st.rerun()

    # --- 3. DASHBOARD RENDER ---
    df = st.session_state.active_df
    if df is not None:
        st.title(f"✈️ {tail_number} Analysis")
        st.caption(f"File: {st.session_state.active_source}")
        
        m = st.columns(4)
        m[0].metric("Max GS", f"{df['Groundspeed'].max():.0f} kts")
        m[1].metric("Peak ITT", f"{df['ITT (F)'].max():.0f} °F")
        m[2].metric("Max N1", f"{df['N1 %'].max():.1f}%")
        m[3].metric("Duration", f"{(len(df) / 60):.1f} min")
        
        st.plotly_chart(visualizer.generate_dashboard(df, view_mode=view_mode), use_container_width=True)
    else:
        st.info("👈 Select a flight log and click **Open** to begin.")
