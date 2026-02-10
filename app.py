import streamlit as st
import pandas as pd
import clean_flight_data as cleaner
import graph_flight_interactive as visualizer
import io
import requests
from github import Github 

# --- 1. AUTHENTICATION & CONNECTION ---
def check_password():
    if "password_correct" not in st.session_state:
        st.set_page_config(page_title="SF50 Login", page_icon="🔒")
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
if "delete_confirm" not in st.session_state: st.session_state.delete_confirm = False

# --- 2. MAIN APP ---
if check_password() and repo:
    st.set_page_config(layout="wide", page_title="Vision Jet Analytics", page_icon="✈️")

    with st.sidebar:
        st.title("🚀 SF50 Fleet Control")
        
        # Aircraft Selection
        try:
            contents = repo.get_contents("data")
            profile_names = [c.name for c in contents if c.type == "dir"]
        except Exception:
            profile_names = []

        selected_profile = st.selectbox("Select Aircraft", ["+ Create New Profile"] + sorted(profile_names))
        
        if selected_profile == "+ Create New Profile":
            st.subheader("🆕 Register New Aircraft")
            new_tail = st.text_input("Tail Number", placeholder="N123SF").upper().strip()
            new_sn = st.text_input("Aircraft S/N", placeholder="e.g. 1234")
            if st.button("Register Aircraft", use_container_width=True, type="primary"):
                if new_tail:
                    repo.create_file(f"data/{new_tail}/.profile", f"Init {new_tail}", f"S/N: {new_sn}")
                    st.success(f"Profile {new_tail} Created!")
                    st.rerun()
            st.stop()

        tail_number = selected_profile
        st.success(f"Active Tail: **{tail_number}**")
        
        # Display Mode
        view_mode = st.radio("Dashboard Layout", ["Single View", "Split View"], index=1)
        st.divider()

        # --- PARAMETER SELECTION (New Grouped Logic) ---
        st.subheader("📊 Data Selection")
        param_groups = {
            "🚀 Powerplant": ["N1 %", "N2 %", "ITT (F)", "Oil Temp (F)", "Oil Px PSI", "TLA DEG"],
            "🌬️ Environmental": ["Cabin Diff PSI", "Bld Px PSI", "Bleed On", "ECS PRI DUCT T (F)", "ECS PRI DUCT T2 (F)", "ECS CKPT T (F)"],
            "🛡️ Ice & Air": ["EIPS TMP (F)", "EIPS PRS PSI", "TT2 (C)", "PT2 PSI"],
            "⚙️ Misc": ["O2 BTL Px PSI", "O2 VLV Open", "CHPV", "Groundspeed"]
        }

        selected_params = []
        for g_name, items in param_groups.items():
            with st.expander(g_name, expanded=(g_name == "🚀 Powerplant")):
                for item in items:
                    # Set defaults for initial view
                    is_default = item in ["N2 %", "Bld Px PSI"]
                    if st.checkbox(item, value=is_default, key=f"sidebar_{item}"):
                        selected_params.append(item)
        st.divider()

        # --- HISTORY & DELETE ---
        st.subheader("📜 Flight History")
        try:
            history_path = f"data/{tail_number}"
            history_files = repo.get_contents(history_path)
            history_map = {f.name: f for f in history_files if f.name.lower().endswith(".csv")}
            history_list = sorted(history_map.keys(), reverse=True)
            
            if not history_list:
                st.info("No logs found.")
            else:
                selected_history = st.selectbox("Select Log", ["-- Select a File --"] + history_list)
                
                if selected_history != "-- Select a File --":
                    h_col1, h_col2 = st.columns(2)
                    
                    if h_col1.button("Open", use_container_width=True, type="primary"):
                        with st.spinner("Streaming data..."):
                            file_obj = history_map[selected_history]
                            response = requests.get(file_obj.download_url)
                            st.session_state.active_df = pd.read_csv(io.BytesIO(response.content))
                            st.session_state.active_source = selected_history
                            st.rerun()

                    if h_col2.button("🗑️ Delete", use_container_width=True):
                        st.session_state.delete_confirm = True

                    if st.session_state.delete_confirm:
                        st.warning("Delete permanently?")
                        if st.button("Confirm Delete"):
                            f_obj = history_map[selected_history]
                            repo.delete_file(f_obj.path, f"Del {selected_history}", f_obj.sha)
                            st.session_state.active_df = None
                            st.session_state.active_source = ""
                            st.session_state.delete_confirm = False
                            st.rerun()
                        if st.button("Cancel"):
                            st.session_state.delete_confirm = False
                            st.rerun()
        except Exception:
            st.info("Directory empty.")

        st.divider()
        # --- BATCH UPLOAD ---
        st.subheader("📤 Batch Upload")
        uploaded_files = st.file_uploader(
            "Select CSVs", 
            type="csv", 
            accept_multiple_files=True,
            key=f"up_{st.session_state.uploader_key}"
        )
        
        if st.button("Sync & Open Newest", use_container_width=True):
            if uploaded_files:
                sorted_files = sorted(uploaded_files, key=lambda x: x.name, reverse=True)
                newest_file = sorted_files[0]
                
                with st.spinner(f"Syncing {len(uploaded_files)} logs..."):
                    for uploaded_file in uploaded_files:
                        try:
                            p_df = cleaner.clean_data(uploaded_file)
                            f_path = f"data/{tail_number}/{uploaded_file.name}"
                            try:
                                repo.get_contents(f_path)
                            except:
                                repo.create_file(f_path, f"Batch Add: {uploaded_file.name}", p_df.to_csv(index=False))
                            
                            if uploaded_file.name == newest_file.name:
                                st.session_state.active_df = p_df
                                st.session_state.active_source = uploaded_file.name
                        except Exception as e:
                            st.error(f"Error with {uploaded_file.name}: {e}")
                
                st.session_state.uploader_key += 1
                st.rerun()

    # --- 3. DASHBOARD RENDER ---
    df = st.session_state.active_df
    if df is not None:
        st.title(f"✈️ {tail_number} Analysis")
        st.caption(f"Active Log: {st.session_state.active_source}")
        
        m = st.columns(4)
        m[0].metric("Max GS", f"{df['Groundspeed'].max():.0f} kts")
        m[1].metric("Peak ITT", f"{df['ITT (F)'].max():.0f} °F")
        m[2].metric("Max N1", f"{df['N1 %'].max():.1f}%")
        m[3].metric("Duration", f"{(len(df) / 60):.1f} min")
        
        # RENDER WITH ACTIVE LIST
        st.plotly_chart(
            visualizer.generate_dashboard(df, view_mode=view_mode, active_list=selected_params), 
            use_container_width=True
        )
    else:
        st.info("👈 Select a flight log and click **Open** to begin.")
