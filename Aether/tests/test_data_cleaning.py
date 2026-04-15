import pytest
import pandas as pd
from src.aether.data_cleaning import DataCleaner


class TestDataCleaner:
    
    def test_validate_readings_valid(self):
        valid_readings = {
            "pm25": 30.5,
            "pm10": 45.2,
            "no2": 25.1,
            "o3": 40.0
        }
        
        is_valid, errors = DataCleaner.validate_readings(valid_readings)
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_readings_negative_values(self):
        invalid_readings = {
            "pm25": -10.0,
            "pm10": 45.2,
            "no2": -5.0
        }
        
        is_valid, errors = DataCleaner.validate_readings(invalid_readings)
        
        assert is_valid is False
        assert len(errors) == 2
        assert "Negative value for pm25" in errors[0]
        assert "Negative value for no2" in errors[1]
    
    def test_validate_readings_extreme_outliers(self):
        extreme_readings = {
            "pm25": 600.0,  # Extreme value > 500
            "pm10": 45.2
        }
        
        is_valid, errors = DataCleaner.validate_readings(extreme_readings)
        
        assert is_valid is False
        assert len(errors) == 1
        assert "Extreme PM2.5 value" in errors[0]
    
    def test_clean_readings_batch(self):
        # Create test DataFrame with various issues
        data = {
            "sensor_id": ["sensor1", "sensor2", None, "sensor3", "sensor4"],
            "timestamp": ["2024-01-01T00:00:00", "2024-01-01T01:00:00", 
                         "2024-01-01T02:00:00", None, "2024-01-01T04:00:00"],
            "pm25": [30.5, -10.0, 600.0, 25.0, 40.0],  # Negative and extreme values
            "pm10": [45.2, 50.0, 80.0, -5.0, 60.0],   # Negative value
            "no2": [25.1, 30.0, 35.0, 20.0, 28.0],
            "o3": [40.0, 45.0, 50.0, 38.0, 42.0]
        }
        
        df = pd.DataFrame(data)
        cleaned_df = DataCleaner.clean_readings_batch(df)
        
        # Should remove rows with missing sensor_id, timestamp, negative values, and extreme values
        assert len(cleaned_df) == 2  # Two valid rows should remain (sensor1 and sensor4)
        assert "sensor1" in cleaned_df["sensor_id"].values
        assert "sensor4" in cleaned_df["sensor_id"].values
        assert all(cleaned_df["pm25"] >= 0)
        assert all(cleaned_df["pm25"] <= 500)
        assert all(cleaned_df["pm10"] >= 0)
    
    def test_aggregate_by_sensor(self):
        data = {
            "sensor_id": ["sensor1", "sensor1", "sensor2", "sensor2"],
            "pm25": [30.0, 40.0, 25.0, 35.0],
            "pm10": [50.0, 60.0, 45.0, 55.0],
            "no2": [20.0, 30.0, 15.0, 25.0],
            "o3": [40.0, 50.0, 35.0, 45.0]
        }
        
        df = pd.DataFrame(data)
        aggregated = DataCleaner.aggregate_by_sensor(df)
        
        # Check that aggregation worked
        assert len(aggregated) == 2  # Two sensors
        assert "sensor1" in aggregated.index
        assert "sensor2" in aggregated.index
        
        # Check that statistics are calculated
        assert ("pm25", "mean") in aggregated.columns
        assert ("pm25", "std") in aggregated.columns
    
    def test_filter_by_threshold(self):
        data = {
            "pm25": [20.0, 30.0, 60.0, 80.0],
            "pm10": [40.0, 70.0, 120.0, 160.0]
        }
        
        df = pd.DataFrame(data)
        thresholds = {"pm25": 50.0, "pm10": 100.0}
        
        filtered_df = DataCleaner.filter_by_threshold(df, thresholds)
        
        # Should keep only rows where both pm25 <= 50 and pm10 <= 100
        assert len(filtered_df) == 2
        assert all(filtered_df["pm25"] <= 50.0)
        assert all(filtered_df["pm10"] <= 100.0)
    
    def test_calculate_statistics(self):
        data = {
            "pm25": [20.0, 30.0, 40.0, 50.0],
            "pm10": [40.0, 50.0, 60.0, 70.0],
            "no2": [15.0, 20.0, 25.0, 30.0],
            "o3": [35.0, 40.0, 45.0, 50.0]
        }
        
        df = pd.DataFrame(data)
        stats = DataCleaner.calculate_statistics(df)
        
        # Check that statistics are calculated for all pollutants
        assert "pm25" in stats
        assert "pm10" in stats
        assert "no2" in stats
        assert "o3" in stats
        
        # Check that all required statistics are present
        for pollutant in ["pm25", "pm10", "no2", "o3"]:
            assert "mean" in stats[pollutant]
            assert "median" in stats[pollutant]
            assert "min" in stats[pollutant]
            assert "max" in stats[pollutant]
            assert "std" in stats[pollutant]
        
        # Verify some calculations
        assert stats["pm25"]["mean"] == 35.0
        assert stats["pm25"]["min"] == 20.0
        assert stats["pm25"]["max"] == 50.0