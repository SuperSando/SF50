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

    # Custom CSS
    st.markdown("""
        <style>
        [data-testid="stMetricValue"] { font-size: 1.8rem; color: #d33612; }
        .stTabs [data-baseweb="tab-list"] { gap: 24px; }
        .stTabs [data-baseweb="tab"] { height: 50px; font-weight: bold; }
        </style>
        """, unsafe_allow_html=True)

    # --- SIDEBAR CONTROLS ---
    with st.sidebar:
        st.title("🚀 SF50 Control")
        st.divider()
        uploaded_file = st.file_uploader("Upload Raw Engine CSV", type="csv")
        
        # NEW: FLIGHT METADATA SECTION
        st.divider()
        st.subheader("📝 Flight Metadata")
        tail_number = st.text_input("Tail Number", placeholder="e.g. N123SF")
        pilot_name = st.text_input("Pilot Name")
        flight_notes = st.text_area("Flight Notes", placeholder="Describe flight phase or issues...")
        
        st.divider()
        st.info("**Log Tip:** Use raw CSV exports from the G3000.")

    # --- MAIN DASHBOARD AREA ---
    if uploaded_file:
        try:
            with st.spinner("Analyzing SF50 Telemetry..."):
                uploaded_file.seek(0)
                df = cleaner.clean_data(uploaded_file)
            
            st.title("✈️ SF50 Vision Jet Performance")
            if tail_number:
                st.subheader(f"Aircraft: {tail_number}")

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
                st.subheader("Processed Log Data")
                st.dataframe(df, use_container_width=True)
                
                # UPDATED: Download logic to include Metadata at the top
                metadata_header = (
                    f"# Tail Number: {tail_number}\n"
                    f"# Pilot: {pilot_name}\n"
                    f"# Notes: {flight_notes.replace(chr(10), ' ')}\n"
                    f"# Export Date: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}\n"
                )
                csv_body = df.to_csv(index=False)
                final_csv = metadata_header + csv_body

                st.download_button(
                    label="💾 Export Cleaned CSV with Notes", 
                    data=final_csv, 
                    file_name=f"CLEANED_{tail_number if tail_number else 'SF50'}_{uploaded_file.name}", 
                    mime="text/csv"
                )

        except Exception as e:
            st.error(f"Error: {e}")
    else:
        st.title("SF50 Vision Jet Analytics")
        st.subheader("Ready for post-flight analysis.")
        st.info("👈 Please upload a CSV file and enter flight details in the sidebar to begin.")
