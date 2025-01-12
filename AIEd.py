import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import io

# Set Streamlit page configuration
st.set_page_config(page_title="Usage Count Analysis", layout="wide")

# Sidebar Inputs
st.sidebar.title("Usage Count Analysis")
uploaded_file = st.sidebar.file_uploader("Upload CSV File", type="csv")
time_period = st.sidebar.selectbox(
    "Select Time Period:",
    options=["By Day", "By Week", "By Month"],
    index=0
)
date_range = st.sidebar.date_input(
    "Select Date Range:",
    [datetime.now() - timedelta(days=30), datetime.now()]
)
hline = st.sidebar.number_input("Horizontal Line (Default = 0):", value=0, step=1)

# Main Page Tabs
tab1, tab2 = st.tabs(["Usage Over Time", "Export Data"])

if uploaded_file:
    # Load and preprocess the data
    data = pd.read_csv(uploaded_file)
    if "timestamp" not in data.columns:
        st.error("The uploaded file must contain a 'timestamp' column.")
    else:
        # Convert 'timestamp' to datetime
        data["timestamp"] = pd.to_datetime(data["timestamp"], errors="coerce")

        # Filter by selected date range
        filtered_data = data[
            (data["timestamp"] >= pd.Timestamp(date_range[0])) &
            (data["timestamp"] <= pd.Timestamp(date_range[1]))
        ]
        if filtered_data.empty:
            st.warning("No data available for the selected range.")
        else:
            # Aggregate data by the selected time period
            if time_period == "By Day":
                filtered_data["period"] = filtered_data["timestamp"].dt.date
            elif time_period == "By Week":
                filtered_data["period"] = filtered_data["timestamp"].dt.to_period("W").apply(lambda r: r.start_time.date())
            elif time_period == "By Month":
                filtered_data["period"] = filtered_data["timestamp"].dt.to_period("M").apply(lambda r: r.start_time.date())
            
            aggregated_data = filtered_data.groupby("period").size().reset_index(name="count")

            # Display line chart
            with tab1:
                st.subheader("Line Chart: Usage Over Time")
                y_axis_range = st.slider(
                    "Adjust Y-Axis Range:",
                    min_value=0, max_value=int(aggregated_data["count"].max()) + 10,
                    value=(0, min(10000, int(aggregated_data["count"].max()))),
                    step=1
                )

                fig = px.line(
                    aggregated_data,
                    x="period",
                    y="count",
                    title="Usage Over Time",
                    labels={"period": "Time Period", "count": "Number of Counts"},
                    template="plotly_white"
                )
                fig.add_hline(y=hline, line_dash="dash", line_color="red")
                fig.update_yaxes(range=y_axis_range)
                st.plotly_chart(fig)

                # Display the table
                st.subheader("Data Table")
                st.dataframe(aggregated_data)

            # Export functionality
            with tab2:
                st.subheader("Export Filtered Data")
                st.write("The exported file will reflect the data shown in the table above.")

                # Convert the displayed table to a CSV file
                export_data = aggregated_data.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=export_data,
                    file_name=f"Usage_Data_{datetime.now().date()}.csv",
                    mime="text/csv"
                )
else:
    st.info("Please upload a CSV file to begin analysis.")
