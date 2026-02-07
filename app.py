import streamlit as st
import pandas as pd
import clean_flight_data as cleaner
import graph_flight_interactive as visualizer

# --- 1. AUTHENTICATION LOGIC ---
def check_password():
    if "password_correct" not in st.session_state:
        st.title("🔒 SF50 Data Access")
        st.text_input("Enter Dashboard Password", type="password", key="password_input")
        if st.button("Log In"):
            if st.session_state["password_input"] == st.secrets["password"]:
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("😕 Password incorrect")
        return False
    return True

# --- 2. MAIN APP ---
if check_password():
    st.set_page_config(layout="wide", page_title="Vision Jet Analytics", page_icon="✈️")

    # Fixed CSS: Removed the dark sidebar background that was causing visibility issues
    st.markdown("""
        <style>
        [data-testid="stMetricValue"] { font-size: 1.8rem; color: #d33612; }
        .stTabs [data-baseweb="tab-list"] { gap: 24px; }
        .stTabs [data-baseweb="tab"] { height: 50px; font-weight: bold; }
        /* Cleaned up sidebar to ensure text is visible */
        section[data-testid="stSidebar"] { border-right: 1px solid #e6e9ef; }
        </style>
        """, unsafe_allow_html=True)

    # --- SIDEBAR CONTROLS ---
    with st.sidebar:
        # Use a highly reliable icon
        st.title("🚀 SF50 Control")
        st.divider()
        uploaded_file = st.file_uploader("Upload Raw Engine CSV", type="csv")
        st.divider()
        st.info("**Log Tip:** Use the raw CSV export from the G3000.")

    # --- MAIN DASHBOARD AREA ---
    if uploaded_file:
        try:
            with st.spinner("Analyzing SF50 Telemetry..."):
                # Reset file pointer to beginning in case it was read elsewhere
                uploaded_file.seek(0)
                df = cleaner.clean_data(uploaded_file)
            
            st.title("✈️ SF50 Vision Jet Performance")
            
            # --- METRICS ROW ---
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.metric("Max GS", f"{df['Groundspeed'].max():.0f} kts")
            with m2:
                st.metric("Peak ITT", f"{df['ITT (F)'].max():.0f} °F")
            with m3:
                st.metric("Max N1", f"{df['N1 %'].max():.1f}%")
            with m4:
                st.metric("Log Duration", f"{(len(df) / 60):.1f} min")

            st.divider()

            # --- TABS ---
            tab_graph, tab_data = st.tabs(["📊 Engine & Systems Graph", "📋 Raw Telemetry"])

            with tab_graph:
                fig = visualizer.generate_dashboard(df)
                st.plotly_chart(fig, use_container_width=True)

            with tab_data:
                st.dataframe(df, use_container_width=True)
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button("💾 Export Cleaned CSV", csv, f"CLEANED_{uploaded_file.name}", "text/csv")

        except Exception as e:
            st.error(f"Error: {e}")
    else:
        # WELCOME STATE - Using a new high-reliability image link
        st.title("SF50 Vision Jet Analytics")
        st.write("Ready for post-flight analysis. Please upload your engine logs in the sidebar.")
        
        # New stable image link for SF50
        st.image("https://images.fineartamerica.com/images/artworkimages/mediumlarge/3/cirrus-vision-sf50-vision-jet-air-history.jpg", 
                 caption="Cirrus Vision Jet SF50", 
                 use_container_width=True)

---

### Why this fix works:
1.  **Sidebar Visibility:** I removed the `background-color: #1c1e21;` line. Streamlit's default sidebar handles light/dark mode better on its own without custom overrides that can "hide" the menu items.
2.  **Image Loading:** I replaced the Wikimedia link with a direct JPG link that is more compatible with Streamlit's `st.image` function.
3.  **Authentication Stability:** I tweaked the `check_password` logic slightly to include a "Log In" button, which helps Streamlit manage the "state" of the page more reliably.

**Would you like me to show you how to host the image on GitHub so it never breaks again?**
