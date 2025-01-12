import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# Set Streamlit page configuration
st.set_page_config(page_title="Usage Count Analysis", layout="wide")

# Helper functions
def load_data(file):
    """Load and preprocess data."""
    data = pd.read_csv(file)
    if 'timestamp' not in data.columns:
        st.error("The uploaded file must contain a 'timestamp' column.")
        return None
    # Convert timestamp column to datetime
    data['timestamp'] = pd.to_datetime(data['timestamp'], errors='coerce')
    if data['timestamp'].isna().any():
        st.error("Invalid timestamp format. Ensure 'timestamp' is in ISO 8601 format.")
        return None
    return data

def filter_and_group_data(data, date_range, time_period):
    """Filter data by date range and group by the selected time period."""
    filtered_data = data[(data['timestamp'] >= date_range[0]) & (data['timestamp'] <= date_range[1])]
    if time_period == 'day':
        filtered_data['period'] = filtered_data['timestamp'].dt.date
    elif time_period == 'week':
        filtered_data['period'] = filtered_data['timestamp'].dt.to_period('W').apply(lambda r: r.start_time)
    elif time_period == 'month':
        filtered_data['period'] = filtered_data['timestamp'].dt.to_period('M').apply(lambda r: r.start_time)
    grouped_data = filtered_data.groupby('period').size().reset_index(name='count')
    return grouped_data

# App layout
st.title("Usage Count Analysis")

# Sidebar inputs
uploaded_file = st.sidebar.file_uploader("Upload CSV File", type="csv")
time_period = st.sidebar.selectbox("Select Time Period:", ["day", "week", "month"], index=0)
start_date = st.sidebar.date_input("Start Date", value=datetime.now() - timedelta(days=30))
end_date = st.sidebar.date_input("End Date", value=datetime.now())
horizontal_line = st.sidebar.number_input("Horizontal Line (Default = 0):", value=0, step=1)

date_range = (pd.to_datetime(start_date), pd.to_datetime(end_date))

# Main panel
if uploaded_file:
    data = load_data(uploaded_file)
    if data is not None:
        # Filter and group data
        grouped_data = filter_and_group_data(data, date_range, time_period)

        # Display chart
        st.subheader("Usage Over Time")
        if grouped_data.empty:
            st.warning("No data available for the selected range.")
        else:
            y_axis_range = st.sidebar.slider(
                "Adjust Y-Axis Range:",
                min_value=0,
                max_value=int(grouped_data['count'].max() * 1.2),
                value=(0, int(grouped_data['count'].max()))
            )

            fig = px.line(grouped_data, x='period', y='count', title="Usage Over Time")
            fig.update_traces(mode='lines+markers')
            fig.add_hline(y=horizontal_line, line_dash="dash", line_color="red")
            fig.update_yaxes(range=y_axis_range)
            st.plotly_chart(fig, use_container_width=True)

        # Display table
        st.subheader("Data Table")
        st.dataframe(grouped_data)

        # Export button
        st.download_button(
            label="Export Data",
            data=grouped_data.to_csv(index=False),
            file_name=f"Usage_Data_{datetime.now().strftime('%Y-%m-%d')}.csv",
            mime="text/csv"
        )
    else:
        st.error("Failed to process the uploaded file. Please check the file format.")
