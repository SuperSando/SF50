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
        st.title("🔒 Flight Data Access")
        st.text_input("Enter Dashboard Password", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Enter Dashboard Password", type="password", on_change=password_entered, key="password")
        st.error("😕 Password incorrect")
        return False
    return True

# --- 2. MAIN APP ---
if check_password():
    # Set Page Config (Must be first Streamlit command after auth)
    st.set_page_config(layout="wide", page_title="Flight Data Pro", page_icon="✈️")

    # Custom CSS for a clean "Aviation" look
    st.markdown("""
        <style>
        [data-testid="stMetricValue"] { font-size: 1.8rem; color: #d33612; }
        .stTabs [data-baseweb="tab-list"] { gap: 24px; }
        .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; font-weight: bold; }
        </style>
        """, unsafe_allow_html=True)

    # --- SIDEBAR CONTROLS ---
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/619/619043.png", width=100)
        st.title("Flight Control")
        st.divider()
        uploaded_file = st.file_uploader("Upload Raw Engine CSV", type="csv")
        st.divider()
        st.info("Instructions: Upload the raw CSV from the flight recorder. The system will clean and format the data automatically.")

    # --- MAIN DASHBOARD AREA ---
    if uploaded_file:
        try:
            # RUN CLEANING ENGINE
            with st.spinner("Processing flight data..."):
                df = cleaner.clean_data(uploaded_file)
            
            st.title("🛫 Flight Analysis Dashboard")
            st.caption(f"Filename: {uploaded_file.name}")

            # --- METRICS ROW ---
            # We calculate these from the 'df' returned by your cleaner
            m1, m2, m3, m4 = st.columns(4)
            
            with m1:
                max_speed = df['Groundspeed'].max() if 'Groundspeed' in df.columns else 0
                st.metric("Max Groundspeed", f"{max_speed:.0f} kts")
            with m2:
                max_itt = df['ITT (F)'].max() if 'ITT (F)' in df.columns else 0
                st.metric("Max ITT", f"{max_itt:.0f} °F")
            with m3:
                max_n1 = df['N1 %'].max() if 'N1 %' in df.columns else 0
                st.metric("Max N1", f"{max_n1:.1f}%")
            with m4:
                duration = len(df) # Assuming 1 sample per second/unit
                st.metric("Total Samples", f"{duration:,}")

            st.divider()

            # --- TABS FOR CONTENT ---
            tab_graph, tab_data = st.tabs(["📊 Interactive Analytics", "📋 Data Inspection"])

            with tab_graph:
                st.subheader("Flight Parameter Visualization")
                # RUN VISUALIZER ENGINE
                fig = visualizer.generate_dashboard(df)
                st.plotly_chart(fig, use_container_width=True)

            with tab_data:
                st.subheader("Processed Data Table")
                st.dataframe(df, use_container_width=True)
                
                # Download Button
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="💾 Download Cleaned CSV",
                    data=csv,
                    file_name=f"CLEANED_{uploaded_file.name}",
                    mime="text/csv",
                )

        except Exception as e:
            st.error(f"Error processing file: {e}")
            st.exception(e) # This helps debug during development
    else:
        # Welcome State
        st.title("Welcome to Flight Data Pro")
        st.write("Please upload a CSV file in the sidebar to begin analysis.")
        st.image("https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?auto=format&fit=crop&q=80&w=1000", caption="Ready for Upload", use_container_width=True)
