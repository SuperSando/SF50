import streamlit as st
import pandas as pd
import clean_flight_data as cleaner
import graph_flight_interactive as visualizer
import io
import requests
from github import Github 

# --- 1. AUTHENTICATION ---
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

if "active_df" not in st.session_state: st.session_state.active_df = None
if "active_source" not in st.session_state: st.session_state.active_source = ""
if "uploader_key" not in st.session_state: st.session_state.uploader_key = 0
if "delete_confirm" not in st.session_state: st.session_state.delete_confirm = False

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
            st.subheader("🆕 Register New Aircraft")
            new_tail = st.text_input("Tail Number").upper().strip()
            if st.button("Register Aircraft", use_container_width=True):
                repo.create_file(f"data/{new_tail}/.profile", f"Init {new_tail}", "Registered")
                st.rerun()
            st.stop()

        tail_number = selected_profile
        view_mode = st.radio("Layout", ["Single View", "Split View"], index=1)
        st.divider()

        # Grouped Parameter Selector
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
                    if st.checkbox(item, value=(item in ["N2 %", "Bld Px PSI"]), key=f"cb_{item}"):
                        selected_params.append(item)

        st.divider()
        # History Selection
        st.subheader("📜 History")
        try:
            h_files = repo.get_contents(f"data/{tail_number}")
            h_map = {f.name: f for f in h_files if f.name.endswith(".csv")}
            sel_h = st.selectbox("Select Log", ["-- Select --"] + sorted(h_map.keys(), reverse=True))
            
            if sel_h != "-- Select --":
                c1, c2 = st.columns(2)
                if c1.button("Open", use_container_width=True):
                    resp = requests.get(h_map[sel_h].download_url)
                    st.session_state.active_df = pd.read_csv(io.BytesIO(resp.content))
                    st.session_state.active_source = sel_h
                    st.rerun()
                if c2.button("Delete", use_container_width=True):
                    repo.delete_file(h_map[sel_h].path, "Del", h_map[sel_h].sha)
                    st.session_state.active_df = None
                    st.rerun()
        except: st.info("No logs.")

        st.divider()
        # Batch Upload
        up_files = st.file_uploader("Upload CSVs", type="csv", accept_multiple_files=True, key=f"up_{st.session_state.uploader_key}")
        if st.button("Sync & Open", use_container_width=True):
            if up_files:
                for f in up_files:
                    p_df = cleaner.clean_data(f)
                    repo.create_file(f"data/{tail_number}/{f.name}", f"Add {f.name}", p_df.to_csv(index=False))
                    # Set the last one as active
                    st.session_state.active_df = p_df
                    st.session_state.active_source = f.name
                st.session_state.uploader_key += 1
                st.rerun()

    # --- 3. DASHBOARD ---
    df = st.session_state.active_df
    if df is not None:
        st.title(f"✈️ {tail_number} Analysis")
        st.caption(f"Log: {st.session_state.active_source}")
        m = st.columns(4)
        m[0].metric("Max GS", f"{df['Groundspeed'].max():.0f} kts")
        m[1].metric("Peak ITT", f"{df['ITT (F)'].max():.0f} °F")
        m[2].metric("Max N1", f"{df['N1 %'].max():.1f}%")
        m[3].metric("Duration", f"{(len(df) / 60):.1f} min")
        
        st.plotly_chart(visualizer.generate_dashboard(df, view_mode=view_mode, active_list=selected_params), use_container_width=True)
