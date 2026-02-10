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
        st.set_page_config(page_title="SF50 Dashboard", page_icon="✈️")
        st.title("🔒 SF50 Data Access")
        st.text_input("Enter Password", type="password", key="password_input")
        if st.button("Log In"):
            if st.session_state["password_input"] == st.secrets["password"]["password"]:
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("😕 Password incorrect")
        return False
    return True

@st.cache_resource
def get_backend():
    try:
        g = Github(st.secrets["github_token"]["github_token"])
        return g.get_repo(st.secrets["repo_path"]["repo_path"])
    except:
        st.error("GitHub connection failed.")
        return None

repo = get_backend()

# Initialize Session State
for key, val in [("active_df", None), ("active_source", ""), ("uploader_key", 0), 
                 ("delete_confirm", False), ("last_profile", None), ("profile_delete_confirm", False)]:
    if key not in st.session_state: st.session_state[key] = val

# --- 2. MAIN APP ---
if check_password() and repo:
    st.set_page_config(layout="wide", page_title="Vision Jet Analytics", page_icon="✈️")

    with st.sidebar:
        st.title("🚀 SF50 Fleet Control")
        
        # Aircraft Selection
        try:
            profile_names = [c.name for c in repo.get_contents("data") if c.type == "dir"]
        except: profile_names = []

        selected_profile = st.selectbox("Select Aircraft", ["+ Create New Profile"] + sorted(profile_names))
        
        # --- REFRESH LOGIC ---
        if selected_profile != st.session_state.last_profile:
            st.session_state.active_df = None
            st.session_state.active_source = ""
            st.session_state.last_profile = selected_profile
            st.session_state.profile_delete_confirm = False
            st.rerun()

        if selected_profile == "+ Create New Profile":
            st.subheader("🆕 Register New Aircraft")
            new_tail = st.text_input("Tail Number").upper().strip()
            new_sn = st.text_input("Aircraft S/N") 
            if st.button("Register Aircraft", use_container_width=True, type="primary"):
                if new_tail and new_sn:
                    repo.create_file(f"data/{new_tail}/.profile", f"Init {new_tail}", f"S/N: {new_sn}")
                    st.rerun()
            st.stop()

        # --- NEW: MANAGE ACTIVE AIRCRAFT ---
        tail_number = selected_profile
        with st.expander("🛠️ Manage Profile"):
            try:
                profile_file = repo.get_contents(f"data/{tail_number}/.profile")
                current_sn = profile_file.decoded_content.decode().replace("S/N: ", "")
                st.write(f"Tail: **{tail_number}**")
                edit_sn = st.text_input("Edit S/N", value=current_sn)
                
                if st.button("Update S/N"):
                    repo.update_file(profile_file.path, f"Update SN {tail_number}", f"S/N: {edit_sn}", profile_file.sha)
                    st.success("Updated!")
                    st.rerun()
                
                st.divider()
                if not st.session_state.profile_delete_confirm:
                    if st.button("🗑️ Delete Aircraft Profile", use_container_width=True):
                        st.session_state.profile_delete_confirm = True
                        st.rerun()
                else:
                    st.error("Delete all logs & profile?")
                    if st.button("CONFIRM PERMANENT DELETE"):
                        # Delete all files in folder
                        folder_contents = repo.get_contents(f"data/{tail_number}")
                        for item in folder_contents:
                            repo.delete_file(item.path, f"Purge {tail_number}", item.sha)
                        st.success(f"{tail_number} Deleted")
                        st.session_state.last_profile = None
                        st.rerun()
                    if st.button("Cancel"):
                        st.session_state.profile_delete_confirm = False
                        st.rerun()
            except:
                st.warning("Profile metadata missing.")

        view_mode = st.radio("Display Layout", ["Single View", "Split View"], index=1)
        st.divider()

        # --- HISTORY ---
        st.subheader("📜 History")
        h_map = {}
        try:
            contents = repo.get_contents(f"data/{tail_number}")
            h_map = {f.name: f for f in contents if f.name.endswith(".csv")}
        except: pass
            
        if not h_map:
            st.info("No logs found.")
            if st.button("🔍 Check Again"): st.rerun()
        else:
            history_list = sorted(h_map.keys(), reverse=True)
            sel_h = st.selectbox("Select Log", ["-- Select a File --"] + history_list, key=f"hist_{tail_number}")
            
            if sel_h != "-- Select a File --":
                c1, c2 = st.columns(2)
                if c1.button("Open", use_container_width=True, type="primary"):
                    resp = requests.get(h_map[sel_h].download_url)
                    st.session_state.active_df = pd.read_csv(io.BytesIO(resp.content))
                    st.session_state.active_source = sel_h
                    st.rerun()
                
                if c2.button("Delete Log", use_container_width=True):
                    st.session_state.delete_confirm = True

                if st.session_state.delete_confirm:
                    if st.button("Confirm Log Delete"):
                        repo.delete_file(h_map[sel_h].path, "Del Log", h_map[sel_h].sha)
                        st.session_state.active_df = None
                        st.session_state.delete_confirm = False
                        st.rerun()
                    if st.button("Cancel"):
                        st.session_state.delete_confirm = False
                        st.rerun()

        st.divider()
        # Upload
        up_files = st.file_uploader("Upload CSVs", type="csv", accept_multiple_files=True, key=f"up_{st.session_state.uploader_key}")
        if st.button("Sync & Open", use_container_width=True):
            if up_files:
                for f in up_files:
                    p_df = cleaner.clean_data(f)
                    repo.create_file(f"data/{tail_number}/{f.name}", f"Upload {f.name}", p_df.to_csv(index=False))
                    st.session_state.active_df = p_df
                    st.session_state.active_source = f.name
                st.session_state.uploader_key += 1
                st.rerun()

    # --- MAIN DISPLAY ---
    df = st.session_state.active_df
    if df is not None:
        st.title(f"✈️ {tail_number} Analysis")
        st.caption(f"Log: {st.session_state.active_source}")
        m = st.columns(4)
        m[0].metric("Max GS", f"{df['Groundspeed'].max():.0f} kts")
        m[1].metric("Peak ITT", f"{df['ITT (F)'].max():.0f} °F")
        m[2].metric("Max N1", f"{df['N1 %'].max():.1f}%")
        m[3].metric("Duration", f"{(len(df) / 60):.1f} min")
        
        st.plotly_chart(visualizer.generate_dashboard(df, view_mode=view_mode), use_container_width=True)
    else:
        st.info("👈 Select a file to begin.")
