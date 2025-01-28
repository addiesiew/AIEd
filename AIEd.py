import dash
from dash import dcc, html, Input, Output, State, callback_context
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from dash.dash_table import DataTable

# Initialize the app
app = dash.Dash(__name__)
app.title = "Usage Count Analysis"

# Define layout
app.layout = html.Div([
    html.H1("Usage Count Analysis"),
    
    # Sidebar layout
    html.Div([
        dcc.Upload(
            id="file-upload",
            children=html.Button("Upload CSV File"),
            multiple=False
        ),
        html.Label("Select Time Period:"),
        dcc.Dropdown(
            id="time-period",
            options=[
                {"label": "By Day", "value": "day"},
                {"label": "By Week", "value": "week"},
                {"label": "By Month", "value": "month"}
            ],
            value="day"
        ),
        html.Label("Select Date Range:"),
        dcc.DatePickerRange(
            id="date-range",
            start_date=(datetime.now() - timedelta(days=30)).date(),
            end_date=datetime.now().date()
        ),
        html.Label("Horizontal Line (Default = 0):"),
        dcc.Input(id="hline", type="number", value=0),
        html.Label("Adjust Y-Axis Range:"),
        dcc.RangeSlider(
            id="y-axis-range",
            min=0, max=50000, step=1000,
            marks={i: str(i) for i in range(0, 50001, 10000)},
            value=[0, 10000]
        ),
        html.Button("Refresh", id="refresh", n_clicks=0),
        html.Button("Export Detailed Dataset", id="export-detailed"),
        html.Button("Export Aggregated Counts", id="export-aggregated")
    ], style={"width": "25%", "display": "inline-block", "verticalAlign": "top", "padding": "20px"}),

    # Main panel
    html.Div([
        dcc.Tabs([
            dcc.Tab(label="Usage Over Time", children=[
                dcc.Graph(id="line-chart"),
                html.Br(),
                DataTable(
                    id="data-table",
                    style_table={"overflowX": "auto"},
                    page_size=10,
                )
            ])
        ])
    ], style={"width": "70%", "display": "inline-block", "padding": "20px"})
])

# Callbacks for interactivity
@app.callback(
    Output("line-chart", "figure"),
    Output("data-table", "data"),
    Output("data-table", "columns"),
    Input("refresh", "n_clicks"),
    State("file-upload", "contents"),
    State("file-upload", "filename"),
    State("time-period", "value"),
    State("date-range", "start_date"),
    State("date-range", "end_date"),
    State("hline", "value"),
    State("y-axis-range", "value")
)
def update_graph(n_clicks, file_contents, filename, time_period, start_date, end_date, hline, y_axis_range):
    if file_contents is None:
        return go.Figure(), [], []
    
    # Decode uploaded file and create a DataFrame
    content_type, content_string = file_contents.split(',')
    decoded = pd.read_csv(pd.compat.StringIO(base64.b64decode(content_string).decode('utf-8')))
    
    # Ensure 'timestamp' column exists
    if "timestamp" not in decoded.columns:
        return go.Figure(), [], []
    
    decoded["timestamp"] = pd.to_datetime(decoded["timestamp"])
    filtered_data = decoded[(decoded["timestamp"] >= start_date) & (decoded["timestamp"] <= end_date)]
    
    # Aggregate data by selected time period
    if time_period == "day":
        filtered_data["period"] = filtered_data["timestamp"].dt.date
    elif time_period == "week":
        filtered_data["period"] = filtered_data["timestamp"].dt.to_period("W").apply(lambda r: r.start_time)
    elif time_period == "month":
        filtered_data["period"] = filtered_data["timestamp"].dt.to_period("M").apply(lambda r: r.start_time)
    
    aggregated_data = filtered_data.groupby("period").size().reset_index(name="count")
    
    # Create the line chart
    fig = px.line(aggregated_data, x="period", y="count", title="Usage Over Time")
    fig.add_hline(y=hline, line_dash="dash", line_color="red")
    fig.update_yaxes(range=y_axis_range)
    
    # DataTable for aggregated data
    columns = [{"name": col, "id": col} for col in aggregated_data.columns]
    return fig, aggregated_data.to_dict("records"), columns

if __name__ == "__main__":
    app.run_server(debug=True)
