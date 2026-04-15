import pytest
import json
import tempfile
import os
from pathlib import Path
from fastapi.testclient import TestClient

from src.aether.main import create_app
from src.aether.dependencies import initialize_services, reset_services


@pytest.fixture
def server_config_file():
    config_data = {
        "storage_file": "test_data/readings.json",
        "historical_data_file": "historical_readings.csv",
        "host": "0.0.0.0",
        "port": 8000,
        "thresholds": {
            "pm25_safe": 25.0,
            "pm25_moderate": 50.0,
            "pm25_danger": 75.0,
            "pm10_safe": 50.0,
            "pm10_moderate": 100.0,
            "pm10_danger": 150.0
        },
        "map_config": {
            "default_zoom": 7,
            "map_style": "open-street-map"
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_data, f)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    os.unlink(temp_path)


@pytest.fixture
def sensors_config_file():
    sensors_data = [
        {
            "id": "test_sensor_001",
            "location": "POINT(4.9041 52.3676)",
            "metadata": {
                "region": "Test City",
                "province": "Test Province",
                "deployment_date": "2024-01-15",
                "site_type": "test_site"
            }
        },
        {
            "id": "test_sensor_002",
            "location": "POINT(5.1214 52.0907)",
            "metadata": {
                "region": "Test City 2",
                "province": "Test Province 2",
                "deployment_date": "2024-02-10",
                "site_type": "test_site_2"
            }
        }
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sensors_data, f)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    os.unlink(temp_path)


@pytest.fixture
def test_app(server_config_file, sensors_config_file):
    # Reset services before each test
    reset_services()
    
    # Create app with test configuration paths
    app = create_app(server_config_file, sensors_config_file)
    
    with TestClient(app) as client:
        yield client
    
    # Reset services after test
    reset_services()


class TestIngestionEndpoint:
    
    def test_successful_ingestion(self, test_app: TestClient):
        payload = {
            "sensor_id": "test_sensor_001",
            "readings": {
                "pm25": 30.5,
                "pm10": 45.2,
                "no2": 25.1,
                "o3": 40.0
            }
        }
        
        response = test_app.post("/ingest", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["sensor_id"] == "test_sensor_001"
        assert "timestamp" in data
    
    def test_unauthorized_sensor(self, test_app: TestClient):
        payload = {
            "sensor_id": "unauthorized_sensor",
            "readings": {
                "pm25": 30.5,
                "pm10": 45.2
            }
        }
        
        response = test_app.post("/ingest", json=payload)
        
        assert response.status_code == 403
        assert "not authorized" in response.json()["detail"]
    
    def test_invalid_readings(self, test_app: TestClient):
        payload = {
            "sensor_id": "test_sensor_001",
            "readings": {
                "pm25": -10.0,  # Negative value
                "pm10": 45.2
            }
        }
        
        response = test_app.post("/ingest", json=payload)
        
        assert response.status_code == 400
        assert "Invalid readings" in response.json()["detail"]
    
    def test_missing_sensor_id(self, test_app: TestClient):
        payload = {
            "readings": {
                "pm25": 30.5,
                "pm10": 45.2
            }
        }
        
        response = test_app.post("/ingest", json=payload)
        
        assert response.status_code == 422  # Validation error


class TestStatusEndpoint:
    
    def test_system_status(self, test_app: TestClient):
        response = test_app.get("/status")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "uptime_seconds" in data
        assert "active_sensors" in data
        assert "total_readings" in data
        assert data["uptime_seconds"] >= 0
        assert data["active_sensors"] >= 0
        assert data["total_readings"] >= 0


class TestMapEndpoint:
    
    def test_map_generation(self, test_app: TestClient):
        response = test_app.get("/map")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/html; charset=utf-8"
        
        # Check if response contains HTML
        html_content = response.text
        assert "<html>" in html_content
        assert "plotly" in html_content.lower()


class TestHistoryEndpoint:
    
    def test_nonexistent_sensor(self, test_app: TestClient):
        response = test_app.get("/history/nonexistent_sensor")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_sensor_without_data(self, test_app: TestClient):
        response = test_app.get("/history/test_sensor_001")
        
        assert response.status_code == 404
        # The sensor exists but has no historical data
        detail = response.json()["detail"]
        assert "not found" in detail or "No historical data" in detail


class TestDistributionEndpoint:
    
    def test_invalid_month(self, test_app: TestClient):
        response = test_app.get("/distribution/2024/13")
        
        assert response.status_code == 400
        assert "Month must be between 1 and 12" in response.json()["detail"]
    
    def test_no_data_for_month(self, test_app: TestClient):
        response = test_app.get("/distribution/2024/1")
        
        # The endpoint might return 200 with empty chart or 404
        assert response.status_code in [200, 404]
        if response.status_code == 404:
            assert "No data available" in response.json()["detail"]


class TestWelcomeEndpoint:
    
    def test_welcome_page(self, test_app: TestClient):
        response = test_app.get("/")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/html; charset=utf-8"
        
        html_content = response.text
        assert "Air Quality Monitoring System" in html_content
        assert "/map" in html_content
        assert "/status" in html_content


class TestDocsEndpoint:
    
    def test_docs_available(self, test_app: TestClient):
        response = test_app.get("/docs")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/html; charset=utf-8"


class TestIntegrationFlow:
    
    def test_full_workflow(self, test_app: TestClient):
        # 1. Check initial status
        status_response = test_app.get("/status")
        assert status_response.status_code == 200
        initial_readings = status_response.json()["total_readings"]
        
        # 2. Ingest data
        payload = {
            "sensor_id": "test_sensor_001",
            "readings": {
                "pm25": 35.0,
                "pm10": 50.0,
                "no2": 30.0,
                "o3": 45.0
            }
        }
        
        ingest_response = test_app.post("/ingest", json=payload)
        assert ingest_response.status_code == 200
        
        # 3. Check updated status
        status_response = test_app.get("/status")
        assert status_response.status_code == 200
        new_readings = status_response.json()["total_readings"]
        assert new_readings == initial_readings + 1
        
        # 4. Check map updates
        map_response = test_app.get("/map")
        assert map_response.status_code == 200
        
        # 5. Verify welcome page still works
        welcome_response = test_app.get("/")
        assert welcome_response.status_code == 200