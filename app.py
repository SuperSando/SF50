import streamlit as st
import clean_flight_data as cleaner
import graph_flight_interactive as visualizer

# --- AUTHENTICATION LOGIC ---
def check_password():
    """Returns True if the user had the correct password."""
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input for password.
        st.text_input("Enter Password", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        # Password incorrect, show input + error.
        st.text_input("Enter Password", type="password", on_change=password_entered, key="password")
        st.error("😕 Password incorrect")
        return False
    else:
        # Password correct.
        return True

# --- MAIN APP EXECUTION ---
if check_password():
    # Everything below this line is only visible if the password is correct
    st.set_page_config(layout="wide", page_title="Flight Data Analysis")
    st.title("🛫 Flight Data Analysis Suite")
    
    uploaded_file = st.file_uploader("Upload Raw CSV", type="csv")

    if uploaded_file:
        try:
            with st.spinner("Cleaning data..."):
                df = cleaner.clean_data(uploaded_file)
            
            st.success("✅ Data Processed")
            
            # Display & Download logic...
            fig = visualizer.generate_dashboard(df)
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"An error occurred: {e}")
