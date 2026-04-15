# Aether
A FastAPI backend service for real-time air quality monitoring across the Netherlands. Sensors ingest pollutant readings via a REST API, which are validated, stored, and visualised as interactive Plotly maps and time series charts.

# Aether — Air Quality Monitoring System

A FastAPI backend service for real-time air quality monitoring.
Authorised sensors submit pollutant readings via REST API.
Data is validated, persisted, and served as interactive
Plotly visualisations including a live map, time series
history, and monthly distribution charts.

---

## How to Run

### Quick start
```bash
./run.sh
```
---
### **Manual**
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m uvicorn src.aether.main:app --host 0.0.0.0 --port 8000 --reload
Then open http://localhost:8000

---
### **API Endpoints**
Method	Endpoint	Description
GET	/	Welcome page with links to all endpoints
POST	/ingest	Submit a sensor reading
GET	/status	System health, uptime, sensor and reading counts
GET	/map	Interactive real-time PM2.5 map of the Netherlands
GET	/history/{sensor_id}	Time series chart for a specific sensor
GET	/distribution/{year}/{month}	Monthly air quality distribution chart
GET	/docs	Auto-generated Swagger UI

---
POST /ingest
```
{
  "sensor_id": "sensor_amsterdam_001",
  "readings": {
    "pm25": 35.0,
    "pm10": 50.0,
    "no2": 30.0,
    "o3": 45.0
  }
}
```
Returns 403 for unauthorised sensors, 400 for invalid readings.

---

**Project Structure**
PY02/
├── run.sh                          # Startup script
├── requirements.txt                # Dependencies
├── historical_readings.csv         # Historical sensor data
├── config/
│   ├── server_config.json          # Thresholds, storage paths, map config
│   └── sensors.json                # Registered sensor definitions (WKT locations)
├── data/                           # Runtime JSON storage for ingested readings
├── tests/
│   ├── test_main.py                # API endpoint integration tests
│   ├── test_data_cleaning.py       # DataCleaner unit tests
│   └── test_wkt_parser.py          # WKTParser unit tests
└── src/aether/
    ├── main.py                     # FastAPI app, routes, lifespan
    ├── models.py                   # Pydantic request/response models
    ├── sensor.py                   # Domain models: SensorReading, SensorInfo
    ├── sensor_manager.py           # Business logic layer
    ├── dependencies.py             # FastAPI dependency injection
    ├── persistence.py              # File I/O: JSON and CSV
    ├── data_cleaning.py            # Pandas-based validation and cleaning
    ├── wkt_parser.py               # WKT POINT coordinate parser
    └── visualization.py            # Plotly map and chart generators
---

**Classes and Functions**
WKTParser
Parses sensor locations stored in WKT (Well-Known Text) format using regex.

parse_point(wkt_string) — parses a POINT(lon lat) string, returns (lon, lat) tuple or None if invalid

validate_coordinates(longitude, latitude) — returns True if coordinates are within valid ranges (lon: -180–180, lat: -90–90)

---
DataCleaner
Pandas-based data validation and cleaning.

validate_readings(readings) — validates a single reading dict, returns (is_valid, errors). Rejects negative values and PM2.5 > 500

clean_readings_batch(df) — cleans a DataFrame by dropping rows with missing sensor_id or timestamp, removing negative pollutant values, and filtering PM2.5 outliers > 500

aggregate_by_sensor(df) — groups by sensor_id and computes mean, median, min, max, std for all pollutants

filter_by_threshold(df, thresholds) — filters rows where any pollutant exceeds its threshold

calculate_statistics(df) — returns a dict of mean, median, min, max, std for each pollutant column

---
PersistenceManager
Handles all file I/O.

save_readings(readings) — writes full readings list to JSON

load_readings() — loads readings from JSON, returns empty list if file doesn't exist

append_reading(reading) — loads existing readings, appends one, saves back

load_historical_csv(file_path) — loads historical CSV into a DataFrame

load_config(file_path) — loads a JSON config file into a dict

---
SensorReading
Domain model for a single sensor submission.

sensor_id, readings, timestamp

to_dict() — serialises to a dictionary with ISO timestamp

---
SensorInfo
Domain model for a registered sensor.

id, location, latitude, longitude, metadata, last_reading, last_update

to_dict() — serialises to a dictionary

---
SensorManager
Core business logic layer. Manages sensors, readings, and historical data.

ingest_reading(sensor_id, readings) — validates sensor authorisation and reading values, persists, updates sensor state, returns SensorReading

get_system_status() — returns uptime, active sensor count, total readings, last update, and health status

get_sensors_for_map() — returns all sensor data as a list of dicts for map rendering

get_historical_data_for_sensor(sensor_id) — returns filtered DataFrame for a specific sensor

get_monthly_data(year, month) — filters historical data to a specific year and month

sensor_exists(sensor_id) — returns True if sensor is registered

has_historical_data(sensor_id) — returns True if historical data exists for the sensor

---
MapVisualizer
Generates interactive Plotly maps.

create_real_time_map(sensors_data) — creates a scatter map of the Netherlands with colour-coded PM2.5 levels (green/yellow/orange/red/gray)

_get_color_and_status(pm25_value) — maps a PM2.5 value to a colour and status label based on configured thresholds

---
TemporalVisualizer
Generates interactive Plotly time series and distribution charts.

create_time_series(df, sensor_id, title) — multi-line chart for PM2.5, PM10, NO2, O3 with a range slider

create_distribution_chart(df, thresholds, year, month) — stacked bar chart showing percentage of Safe/Moderate/Unhealthy/Dangerous readings for a given month

---
Configuration
config/server_config.json
```
{
  "storage_file": "data/readings.json",
  "historical_data_file": "historical_readings.csv",
  "thresholds": {
    "pm25_safe": 25.0,
    "pm25_moderate": 50.0,
    "pm25_danger": 75.0
  },
  "map_config": {
    "default_zoom": 7,
    "map_style": "open-street-map"
  }
}
```

config/sensors.json
```
[
  {
    "id": "sensor_amsterdam_001",
    "location": "POINT(4.9041 52.3676)",
    "metadata": {
      "region": "Amsterdam",
      "province": "North Holland"
    }
  }
]
```

### **Tests**
pytest tests/ -v
---
Test File	- Coverage
test_wkt_parser.py	- Valid/invalid WKT parsing, coordinate validation
test_data_cleaning.py	- Validation, batch cleaning, aggregation, filtering, statistics
test_main.py	- All API endpoints, integration flow, error handling

---
### **Built With**
Python 3.11+

FastAPI — REST API framework

Uvicorn — ASGI server

Pydantic — request/response validation

Pandas — data cleaning and analysis

Plotly — interactive visualisations

Pytest + HTTPX — testing

