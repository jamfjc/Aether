# Air Quality Monitoring System

A professional backend service for Netherlands Air Quality Monitoring using FastAPI, pandas, Plotly, and Clean Architecture principles.

## Architecture

The system follows Clean Architecture principles with clear separation of layers:

```
src/aether/
├── main.py              # FastAPI application with modern lifespan pattern
├── models.py            # DTOs with Pydantic validation
├── sensor.py            # Domain models (framework-independent)
├── sensor_manager.py    # Service layer (business logic)
├── dependencies.py      # Dependency injection providers
├── persistence.py       # Data layer (file I/O)
├── data_cleaning.py     # Pandas-based data cleaning
├── wkt_parser.py        # WKT parsing with regex
└── visualization.py     # Plotly visualizations
```

### Design Principles

- **Domain Models**: Plain Python classes without validation
- **DTOs**: Pydantic models for API boundary validation
- **Service Layer**: Framework-independent business logic
- **Dependency Injection**: Type-safe FastAPI Depends() pattern
- **Configuration-Driven**: All behavior controlled by JSON files

## Installation

### Prerequisites

- Python 3.11 or higher
- Git

### Quick Start

1. **Clone and navigate to the project**:
   ```bash
   cd PY02
   ```

2. **Run the startup script**:
   ```bash
   ./run.sh
   ```

   The script will:
   - Create a virtual environment
   - Install dependencies
   - Start the server on http://localhost:8000

### Manual Installation

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create data directory
mkdir -p data

# Start the server
python -m uvicorn src.aether.main:app --host 0.0.0.0 --port 8000 --reload
```

## Usage

### API Endpoints

**Data Ingestion**
```http
POST /ingest
Content-Type: application/json

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

**Real-time Map**
```http
GET /map
```
Interactive Plotly map with color-coded air quality levels.

**System Status**
```http
GET /status
```
Returns system health, uptime, active sensors, and reading counts.

**Historical Time Series**
```http
GET /history/{sensor_id}
```
Interactive time series with range slider.

**Monthly Distribution**
```http
GET /distribution/{year}/{month}
```
100% stacked bar chart showing air quality distribution.

**Welcome Page**
```http
GET /
```
Navigation hub with links to all endpoints.

**API Documentation**
```http
GET /docs
```
Auto-generated Swagger UI documentation.

### Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src/aether --cov-report=html
```