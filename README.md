# Real-Time Weather Dashboard (Plotly Dash)

**DAV Lab — Experiment 5: Data Analytics using Plotly Dash**

A live dashboard that fetches current temperature and weather conditions
from the **OpenWeatherMap API** and visualizes them with **Plotly Dash** and
**Dash Bootstrap Components**.

## Features
1. Dropdown for city selection (Mumbai, Delhi, London, New York, Tokyo, Sydney by default)
2. Line chart of temperature history for the selected city
3. Live weather icons pulled from OpenWeatherMap
4. Real-time date & time display (updates every second)
5. "Export Latest Data to CSV" button
6. Text box to add any city in the world dynamically
7. Celsius / Fahrenheit unit toggle
8. Bar chart comparing the latest temperature across all tracked cities
9. Styled entirely with Dash Bootstrap Components (FLATLY theme)

## Project structure
```
weather_dashboard/
├── app.py              # main Dash application
├── requirements.txt    # Python dependencies
├── .env.example         # example environment file for the API key
└── README.md
```

## Setup

1. **Install Python 3.9+** if you don't already have it.

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set your OpenWeatherMap API key** (optional — a working key is already
   included as a default so the app runs immediately for this experiment):
   ```bash
   export OPENWEATHER_API_KEY="your_own_key_here"     # Linux / macOS
   setx OPENWEATHER_API_KEY "your_own_key_here"        # Windows
   ```

4. **Run the app:**
   ```bash
   python app.py
   ```

5. Open your browser at **http://127.0.0.1:8050**

## How it works (brief)

- `fetch_weather(city, units)` calls the OpenWeatherMap
  `/data/2.5/weather` endpoint and parses temperature, humidity, wind,
  description, and icon code for a city.
- A `dcc.Interval` component triggers a refresh every 60 seconds (the clock
  itself refreshes every second using a separate, faster interval).
- Each fetch appends `(timestamp, temperature)` to an in-memory history
  buffer (`collections.deque`, capped at 50 points) per city, which feeds
  the line chart.
- The bar chart compares the latest reading of every city currently being
  tracked (default cities + any the user has added).
- Clicking **Export Latest Data to CSV** builds a `pandas.DataFrame` from
  the most recent reading of every tracked city and streams it to the
  browser as a downloadable `.csv` via `dcc.Download`.

## Notes on the API key

For convenience in this lab experiment, the API key is included directly as
a fallback default in `app.py`. In any real-world project you should always
keep API keys out of source code — use an environment variable or a
`.env` file (see `.env.example`) instead, and add `.env` to `.gitignore`.

## Troubleshooting

- **"City not found" errors** — check the spelling of the city name; the
  OpenWeatherMap API expects a standard city name (optionally
  `"City,CountryCode"`, e.g. `"Paris,FR"`).
- **No data showing** — wait a few seconds after launching; the first
  weather fetch happens on the first interval tick / initial callback
  execution.
- **Rate limiting** — OpenWeatherMap's free tier allows 60 calls/minute;
  the default 60-second refresh interval and small city list stay well
  within this limit.
