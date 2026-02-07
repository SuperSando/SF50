import streamlit as st
import pandas as pd
import clean_flight_data as cleaner
import graph_flight_interactive as visualizer

# --- 1. AUTHENTICATION LOGIC ---
def check_password():
    """Returns True if the user had the correct password."""
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
    # Set Page Config
    st.set_page_config(layout="wide", page_title="Vision Jet Analytics", page_icon="✈️")

    # Custom CSS for Branding and Visibility
    st.markdown("""
        <style>
        [data-testid="stMetricValue"] { font-size: 1.8rem; color: #d33612; }
        .stTabs [data-baseweb="tab-list"] { gap: 24px; }
        .stTabs [data-baseweb="tab"] { height: 50px; font-weight: bold; }
        section[data-testid="stSidebar"] { border-right: 1px solid #e6e9ef; }
        </style>
        """, unsafe_allow_html=True)

    # --- SIDEBAR CONTROLS ---
    with st.sidebar:
        st.title("🚀 SF50 Control")
        st.divider()
        uploaded_file = st.file_uploader("Upload Raw Engine CSV", type="csv")
        st.divider()
        st.info("**Log Tip:** Use the raw CSV export from the G3000 system. The app will automatically filter and format columns.")

    # --- MAIN DASHBOARD AREA ---
    if uploaded_file:
        try:
            with st.spinner("Analyzing SF50 Telemetry..."):
                # Reset file pointer
                uploaded_file.seek(0)
                df = cleaner.clean_data(uploaded_file)
            
            st.title("✈️ SF50 Vision Jet Performance")
            st.caption(f"Source: {uploaded_file.name}")

            # --- METRICS ROW ---
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.metric("Max GS", f"{df['Groundspeed'].max():.0f} kts")
            with m2:
                st.metric("Peak ITT", f"{df['ITT (F)'].max():.0f} °F")
            with m3:
                st.metric("Max N1", f"{df['N1 %'].max():.1f}%")
            with m4:
                # Assuming 1Hz logging
                st.metric("Log Duration", f"{(len(df) / 60):.1f} min")

            st.divider()

            # --- TABS ---
            tab_graph, tab_data = st.tabs(["📊 Engine & Systems Graph", "📋 Raw Telemetry"])

            with tab_graph:
                fig = visualizer.generate_dashboard(df)
                st.plotly_chart(fig, use_container_width=True)

            with tab_data:
                st.subheader("Processed Log Data")
                st.dataframe(df, use_container_width=True)
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button("💾 Export Cleaned CSV", csv, f"CLEANED_{uploaded_file.name}", "text/csv")

        except Exception as e:
            st.error(f"Error processing flight data: {e}")
    else:
        # WELCOME STATE (Text-only for stability)
        st.title("SF50 Vision Jet Analytics")
        st.subheader("Ready for post-flight analysis.")
        st.write("---")
        st.markdown("""
        ### Getting Started
        1. Insert your SD card and locate the engine log CSV.
        2. Use the **sidebar on the left** to upload the file.
        3. The dashboard will automatically:
            * Clean and rename your telemetry columns.
            * Highlight peak performance metrics.
            * Generate interactive multi-system graphs.
        """)
        st.info("👈 Please upload a CSV file in the sidebar to begin.")
