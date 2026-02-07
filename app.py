import streamlit as st
import clean_flight_data as cleaner
import graph_flight_interactive as visualizer

st.set_page_config(layout="wide", page_title="Flight Data Analysis")

st.title("🛫 Flight Data Analysis Suite")
st.write("Upload your raw engine CSV to clean, format, and visualize the data.")

uploaded_file = st.file_uploader("Upload Raw CSV", type="csv")

if uploaded_file:
    try:
        # Step 1: Clean
        with st.spinner("Cleaning and formatting data..."):
            df = cleaner.clean_data(uploaded_file)
        
        st.success("✅ Data Processed Successfully")

        # Step 2: Display & Download
        col1, col2 = st.columns([4, 1])
        with col1:
            st.dataframe(df.head(10), use_container_width=True)
        with col2:
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("Download Cleaned CSV", csv, "cleaned_flight_data.csv", "text/csv")

        # Step 3: Graph
        st.divider()
        st.subheader("Interactive Dashboard")
        fig = visualizer.generate_dashboard(df)
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"An error occurred: {e}")
