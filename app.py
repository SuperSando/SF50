import streamlit as st
import clean_flight_data as cleaner
import graph_flight_interactive as visualizer

st.set_page_config(layout="wide", page_title="Flight Data Analysis")

st.title("🛫 Flight Data Analysis Suite")
st.write("Upload your raw engine CSV to generate interactive graphs instantly.")

uploaded_file = st.file_uploader("Upload Raw CSV", type="csv")

if uploaded_file:
    try:
        # Step 1: Clean (Internal processing only)
        with st.spinner("Processing flight data..."):
            df = cleaner.clean_data(uploaded_file)
        
        # Step 2: Graph (Render immediately)
        st.subheader("Interactive Dashboard")
        fig = visualizer.generate_dashboard(df)
        
        # This displays the interactive Plotly chart
        st.plotly_chart(fig, use_container_width=True)

        # Step 3: Minimal Download Option (Optional, tucked at the bottom)
        with st.expander("Export Cleaned Data"):
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("Download Cleaned CSV", csv, "cleaned_flight_data.csv", "text/csv")

    except Exception as e:
        st.error(f"An error occurred: {e}")
