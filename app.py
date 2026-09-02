"""
================================================================================
 DAV Experiment 5 - Data Analytics using Plotly Dash
 Real-Time Temperature Dashboard using OpenWeatherMap API
================================================================================

Problem Statement:
    Design and implement a real-time dashboard that displays the current
    temperature of various cities using Python and Plotly Dash. This helps
    visualize temperature trends and compare climate conditions in different
    regions.

Features implemented (Deliverables / Additions):
    1. Dropdown for City Selection
    2. Line Chart for Temperature History
    3. Weather Icons (fetched live from OpenWeatherMap)
    4. Real-Time Date & Time Display (updates every second)
    5. Export Latest Data to CSV Button
    6. User Input for Dynamic Cities (add any city in the world)
    7. Dash Bootstrap Components for Styling (FLATLY theme, cards, badges)

Author : Generated for B.E. Sem VII - Electronics and Computer Science
Subject: DAV Laboratory
================================================================================
"""

import os
import io
import base64
import requests
import pandas as pd
import plotly.graph_objs as go
from datetime import datetime
from collections import defaultdict, deque

import dash
from dash import dcc, html, Input, Output, State, ctx
import dash_bootstrap_components as dbc

# ------------------------------------------------------------------------
# CONFIGURATION
# ------------------------------------------------------------------------
# NOTE: For a real deployment, NEVER hard-code your API key. Instead set it
# as an environment variable, e.g.:
#       export OPENWEATHER_API_KEY="your_key_here"      (Linux/Mac)
#       setx OPENWEATHER_API_KEY "your_key_here"         (Windows)
# The line below falls back to the key supplied for this experiment so the
# app runs out-of-the-box, but the environment variable always takes
# priority if it is set.
import os
API_KEY = os.getenv("OPENWEATHER_API_KEY")
CURRENT_WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
ICON_URL_TEMPLATE = "https://openweathermap.org/img/wn/{icon}@2x.png"

DEFAULT_CITIES = ["Mumbai", "Delhi", "London", "New York", "Tokyo", "Sydney"]

UPDATE_INTERVAL_MS = 60 * 1000   # fetch fresh weather data every 60 seconds
CLOCK_INTERVAL_MS = 1 * 1000     # refresh the live clock every 1 second
MAX_HISTORY_POINTS = 50          # how many points to keep per city on the chart

# ------------------------------------------------------------------------
# IN-MEMORY DATA STORE
# ------------------------------------------------------------------------
# history[city] -> deque of (timestamp, temperature) tuples
history = defaultdict(lambda: deque(maxlen=MAX_HISTORY_POINTS))
# keeps the most recent full weather record per city (for the CSV export)
latest_records = {}


# ------------------------------------------------------------------------
# HELPER FUNCTIONS
# ------------------------------------------------------------------------
def fetch_weather(city: str, units: str = "metric"):
    """
    Calls the OpenWeatherMap 'Current Weather Data' API for a given city.
    Returns a dict with the parsed fields, or a dict containing an 'error'
    key if the request failed.
    """
    if not city or not city.strip():
        return {"error": "Empty city name"}

    params = {"q": city.strip(), "appid": API_KEY, "units": units}
    try:
        resp = requests.get(CURRENT_WEATHER_URL, params=params, timeout=8)
        data = resp.json()

        if resp.status_code != 200 or str(data.get("cod")) != "200":
            return {"error": data.get("message", "City not found")}

        result = {
            "city": data.get("name", city),
            "country": data["sys"].get("country", ""),
            "temp": data["main"]["temp"],
            "feels_like": data["main"]["feels_like"],
            "temp_min": data["main"]["temp_min"],
            "temp_max": data["main"]["temp_max"],
            "humidity": data["main"]["humidity"],
            "pressure": data["main"]["pressure"],
            "wind_speed": data["wind"].get("speed", 0),
            "description": data["weather"][0]["description"].title(),
            "icon": data["weather"][0]["icon"],
            "timestamp": datetime.now(),
        }
        return result
    except requests.exceptions.RequestException as exc:
        return {"error": f"Network error: {exc}"}
    except (KeyError, IndexError) as exc:
        return {"error": f"Unexpected API response: {exc}"}


def units_symbol(units: str) -> str:
    return "°C" if units == "metric" else "°F"


# ------------------------------------------------------------------------
# APP INITIALISATION
# ------------------------------------------------------------------------
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.FLATLY, dbc.icons.FONT_AWESOME],
    title="Real-Time Weather Dashboard",
)
server = app.server  # exposed for deployment (gunicorn, etc.)


# ------------------------------------------------------------------------
# LAYOUT
# ------------------------------------------------------------------------
app.layout = dbc.Container(
    fluid=True,
    className="p-4",
    children=[

        # ---------------- Header ----------------
        dbc.Row([
            dbc.Col([
                html.H2([
                    html.I(className="fa-solid fa-cloud-sun me-2"),
                    "Real-Time Weather Dashboard"
                ], className="fw-bold text-primary"),
                html.P("DAV Lab Experiment 5 — Data Analytics using Plotly Dash "
                       "(Live data via OpenWeatherMap API)",
                       className="text-muted"),
            ], width=8),
            dbc.Col([
                html.Div(id="live-clock", className="fs-5 fw-semibold text-end text-secondary mt-2"),
                dcc.Interval(id="clock-interval", interval=CLOCK_INTERVAL_MS, n_intervals=0),
            ], width=4, className="d-flex align-items-center justify-content-end"),
        ], className="mb-3"),

        html.Hr(),

        # ---------------- Controls Card ----------------
        dbc.Card(dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    dbc.Label("Select City", className="fw-semibold"),
                    dcc.Dropdown(
                        id="city-dropdown",
                        options=[{"label": c, "value": c} for c in DEFAULT_CITIES],
                        value="Mumbai",
                        clearable=False,
                    ),
                ], md=4),

                dbc.Col([
                    dbc.Label("Add a New City", className="fw-semibold"),
                    dbc.InputGroup([
                        dbc.Input(id="new-city-input", placeholder="e.g. Paris",
                                   type="text", debounce=True),
                        dbc.Button([html.I(className="fa-solid fa-plus")],
                                   id="add-city-btn", color="primary"),
                    ]),
                ], md=4),

                dbc.Col([
                    dbc.Label("Units", className="fw-semibold"),
                    dbc.RadioItems(
                        id="units-toggle",
                        options=[
                            {"label": "Celsius (°C)", "value": "metric"},
                            {"label": "Fahrenheit (°F)", "value": "imperial"},
                        ],
                        value="metric",
                        inline=True,
                    ),
                ], md=4),
            ], className="g-3"),

            dbc.Row([
                dbc.Col([
                    dbc.Button([html.I(className="fa-solid fa-download me-2"), "Export Latest Data to CSV"],
                               id="export-btn", color="success", className="mt-3"),
                    dcc.Download(id="download-csv"),
                ], className="d-flex justify-content-end"),
            ]),
        ]), className="shadow-sm mb-4"),

        # hidden store: holds the list of cities the user has added
        dcc.Store(id="city-store", data=DEFAULT_CITIES),
        # main auto-refresh interval for weather data
        dcc.Interval(id="weather-interval", interval=UPDATE_INTERVAL_MS, n_intervals=0),

        # ---------------- Current Weather Card ----------------
        dbc.Row([
            dbc.Col(dbc.Card(dbc.CardBody(id="current-weather-card"),
                              className="shadow-sm h-100"), md=4),
            dbc.Col(dbc.Card(dbc.CardBody([
                html.H5("Temperature History", className="fw-semibold mb-2"),
                dcc.Graph(id="temp-line-chart", config={"displayModeBar": False}),
            ]), className="shadow-sm h-100"), md=8),
        ], className="g-3 mb-4"),

        # ---------------- Multi-city comparison ----------------
        dbc.Row([
            dbc.Col(dbc.Card(dbc.CardBody([
                html.H5("Compare All Tracked Cities", className="fw-semibold mb-2"),
                dcc.Graph(id="compare-bar-chart", config={"displayModeBar": False}),
            ]), className="shadow-sm"), width=12),
        ], className="g-3 mb-4"),

        html.Div(id="status-msg", className="text-danger fw-semibold"),

        html.Footer(
            "Data source: OpenWeatherMap API  |  Built with Plotly Dash & Dash Bootstrap Components",
            className="text-center text-muted small mt-4",
        ),
    ],
)


# ------------------------------------------------------------------------
# CALLBACKS
# ------------------------------------------------------------------------

# 1. Live clock (real-time date & time display) -------------------------
@app.callback(
    Output("live-clock", "children"),
    Input("clock-interval", "n_intervals"),
)
def update_clock(_n):
    now = datetime.now()
    return now.strftime("%A, %d %B %Y  |  %H:%M:%S")


# 2. Add a new city to the dropdown (dynamic city input) -----------------
@app.callback(
    Output("city-store", "data"),
    Output("city-dropdown", "options"),
    Output("city-dropdown", "value"),
    Output("new-city-input", "value"),
    Input("add-city-btn", "n_clicks"),
    State("new-city-input", "value"),
    State("city-store", "data"),
    prevent_initial_call=True,
)
def add_city(_n_clicks, new_city, cities):
    cities = cities or list(DEFAULT_CITIES)
    if new_city and new_city.strip():
        clean = new_city.strip().title()
        if clean not in cities:
            cities = cities + [clean]
        options = [{"label": c, "value": c} for c in cities]
        return cities, options, clean, ""
    options = [{"label": c, "value": c} for c in cities]
    return cities, options, dash.no_update, ""


# 3. Main data refresh: current weather card + line chart + bar chart ----
@app.callback(
    Output("current-weather-card", "children"),
    Output("temp-line-chart", "figure"),
    Output("compare-bar-chart", "figure"),
    Output("status-msg", "children"),
    Input("weather-interval", "n_intervals"),
    Input("city-dropdown", "value"),
    Input("units-toggle", "value"),
    State("city-store", "data"),
)
def refresh_dashboard(_n_intervals, selected_city, units, all_cities):
    all_cities = all_cities or DEFAULT_CITIES
    errors = []

    # ---- fetch data for every tracked city (keeps history + comparison live) ----
    for city in all_cities:
        result = fetch_weather(city, units=units)
        if "error" in result:
            errors.append(f"{city}: {result['error']}")
            continue
        latest_records[city] = result
        history[city].append((result["timestamp"], result["temp"]))

    symbol = units_symbol(units)

    # ---- Current weather card for the selected city ----
    record = latest_records.get(selected_city)
    if record is None:
        card_children = dbc.Alert(
            f"No data available yet for {selected_city}.", color="warning"
        )
    else:
        icon_url = ICON_URL_TEMPLATE.format(icon=record["icon"])
        card_children = html.Div([
            dbc.Row([
                dbc.Col(html.Img(src=icon_url, style={"width": "80px"}), width="auto"),
                dbc.Col([
                    html.H4(f"{record['city']}, {record['country']}", className="fw-bold mb-0"),
                    html.Span(record["description"], className="text-muted"),
                ]),
            ], align="center", className="mb-3"),

            html.H1(f"{record['temp']:.1f}{symbol}", className="display-4 fw-bold text-primary"),
            html.P(f"Feels like {record['feels_like']:.1f}{symbol}", className="text-muted"),

            dbc.Row([
                dbc.Col(dbc.Badge(f"Min {record['temp_min']:.1f}{symbol}", color="info", className="me-1"), width="auto"),
                dbc.Col(dbc.Badge(f"Max {record['temp_max']:.1f}{symbol}", color="danger", className="me-1"), width="auto"),
                dbc.Col(dbc.Badge(f"Humidity {record['humidity']}%", color="secondary", className="me-1"), width="auto"),
                dbc.Col(dbc.Badge(f"Wind {record['wind_speed']} m/s", color="dark"), width="auto"),
            ], className="mt-2 g-1"),

            html.P(f"Last updated: {record['timestamp'].strftime('%H:%M:%S')}",
                   className="text-muted small mt-3 mb-0"),
        ])

    # ---- Line chart: temperature history for the selected city ----
    hist = history.get(selected_city, [])
    if hist:
        xs = [t for t, _ in hist]
        ys = [v for _, v in hist]
    else:
        xs, ys = [], []

    line_fig = go.Figure()
    line_fig.add_trace(go.Scatter(
        x=xs, y=ys, mode="lines+markers", name=selected_city,
        line=dict(color="#2c7be5", width=3),
        marker=dict(size=6),
        fill="tozeroy", fillcolor="rgba(44,123,229,0.1)",
    ))
    line_fig.update_layout(
        margin=dict(l=40, r=20, t=10, b=40),
        xaxis_title="Time",
        yaxis_title=f"Temperature ({symbol})",
        template="plotly_white",
        height=320,
    )

    # ---- Bar chart: compare latest temperature of every tracked city ----
    cities_with_data = [c for c in all_cities if c in latest_records]
    bar_fig = go.Figure()
    if cities_with_data:
        bar_fig.add_trace(go.Bar(
            x=cities_with_data,
            y=[latest_records[c]["temp"] for c in cities_with_data],
            marker_color=["#2c7be5" if c == selected_city else "#95aac9" for c in cities_with_data],
            text=[f"{latest_records[c]['temp']:.1f}{symbol}" for c in cities_with_data],
            textposition="outside",
        ))
    bar_fig.update_layout(
        margin=dict(l=40, r=20, t=10, b=40),
        yaxis_title=f"Temperature ({symbol})",
        template="plotly_white",
        height=320,
    )

    status = " | ".join(errors) if errors else ""
    return card_children, line_fig, bar_fig, status


# 4. Export latest data to CSV -------------------------------------------
@app.callback(
    Output("download-csv", "data"),
    Input("export-btn", "n_clicks"),
    prevent_initial_call=True,
)
def export_csv(_n_clicks):
    if not latest_records:
        return dash.no_update

    rows = []
    for city, rec in latest_records.items():
        rows.append({
            "City": rec["city"],
            "Country": rec["country"],
            "Temperature": rec["temp"],
            "Feels_Like": rec["feels_like"],
            "Temp_Min": rec["temp_min"],
            "Temp_Max": rec["temp_max"],
            "Humidity_%": rec["humidity"],
            "Pressure_hPa": rec["pressure"],
            "Wind_Speed_mps": rec["wind_speed"],
            "Description": rec["description"],
            "Timestamp": rec["timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
        })
    df = pd.DataFrame(rows)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return dcc.send_data_frame(df.to_csv, f"weather_data_{timestamp}.csv", index=False)


# ------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8050)
