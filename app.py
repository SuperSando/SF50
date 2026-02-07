import streamlit as st
import pandas as pd
import clean_flight_data as cleaner
import graph_flight_interactive as visualizer

# --- 1. AUTHENTICATION LOGIC ---
def check_password():
    """Returns True if the user had the correct password."""
    def password_entered():
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.title("🔒 SF50 Data Access")
        st.text_input("Enter Dashboard Password", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Enter Dashboard Password", type="password", on_change=password_entered, key="password")
        st.error("😕 Password incorrect")
        return False
    return True

# --- 2. MAIN APP ---
if check_password():
    # Set Page Config
    st.set_page_config(layout="wide", page_title="Vision Jet Analytics", page_icon="✈️")

    # Custom CSS for Aviation Branding
    st.markdown("""
        <style>
        [data-testid="stMetricValue"] { font-size: 1.8rem; color: #d33612; }
        .stTabs [data-baseweb="tab-list"] { gap: 24px; }
        .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; font-weight: bold; }
        section[data-testid="stSidebar"] { background-color: #1c1e21; color: white; }
        </style>
        """, unsafe_allow_html=True)

    # --- SIDEBAR CONTROLS ---
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/2830/2830305.png", width=80)
        st.title("SF50 Control")
        st.divider()
        uploaded_file = st.file_uploader("Upload Raw Engine CSV", type="csv")
        st.divider()
        st.info("**Log Tip:** The cleaner is optimized for G2/G2+ Vision Jet logs. Ensure the CSV is the raw export from the G1000/G3000 system.")

    # --- MAIN DASHBOARD AREA ---
    if uploaded_file:
        try:
            # RUN CLEANING ENGINE
            with st.spinner("Analyzing SF50 Telemetry..."):
                df = cleaner.clean_data(uploaded_file)
            
            st.title("✈️ SF50 Vision Jet Performance")
            st.caption(f"Source Log: {uploaded_file.name}")

            # --- METRICS ROW ---
            m1, m2, m3, m4 = st.columns(4)
            
            with m1:
                max_speed = df['Groundspeed'].max() if 'Groundspeed' in df.columns else 0
                st.metric("Max GS", f"{max_speed:.0f} kts")
            with m2:
                max_itt = df['ITT (F)'].max() if 'ITT (F)' in df.columns else 0
                st.metric("Peak ITT", f"{max_itt:.0f} °F")
            with m3:
                max_n1 = df['N1 %'].max() if 'N1 %' in df.columns else 0
                st.metric("Max N1", f"{max_n1:.1f}%")
            with m4:
                # Calculate Duration (Assuming 1Hz logging)
                duration_mins = len(df) / 60
                st.metric("Log Duration", f"{duration_mins:.1f} min")

            st.divider()

            # --- TABS FOR CONTENT ---
            tab_graph, tab_data = st.tabs(["📊 Engine & Systems Graph", "📋 Raw Telemetry"])

            with tab_graph:
                # RUN VISUALIZER ENGINE
                fig = visualizer.generate_dashboard(df)
                st.plotly_chart(fig, use_container_width=True)

            with tab_data:
                st.subheader("Processed Log Data")
                st.dataframe(df, use_container_width=True)
                
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="💾 Export Cleaned CSV",
                    data=csv,
                    file_name=f"CLEANED_SF50_{uploaded_file.name}",
                    mime="text/csv",
                )

        except Exception as e:
            st.error(f"Error processing file: {e}")
            st.exception(e) 
    else:
        # WELCOME STATE - Explicit SF50 Image
        st.title("SF50 Vision Jet Analytics")
        st.write("Ready for post-flight analysis. Please upload your engine logs in the sidebar.")
        
        # Using a reliable image of a Cirrus Vision Jet
        st.image("https://upload.wikimedia.org/wikipedia/commons/e/e0/Cirrus_Vision_SF50_N271SF.jpg", 
                 caption="Cirrus Vision Jet SF50", 
                 use_container_width=True)
