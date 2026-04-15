import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging

from .sensor import SensorReading, SensorInfo
from .data_cleaning import DataCleaner
from .persistence import PersistenceManager
from .wkt_parser import WKTParser

logger = logging.getLogger(__name__)


class UnauthorizedSensorError(Exception):
    pass


class InvalidReadingError(Exception):
    pass


class SensorManager:
    
    def __init__(self, config: Dict[str, Any], sensors_config: List[Dict[str, Any]]):
        self.config = config
        self.sensors: Dict[str, SensorInfo] = {}
        self.readings: List[SensorReading] = []
        self.historical_data: Optional[pd.DataFrame] = None
        self.start_time = datetime.now()
        
        self.persistence = PersistenceManager(config["storage_file"])
        self._load_sensors(sensors_config)
        self._load_historical_data()
        self._load_existing_readings()
    
    def _load_sensors(self, sensors_config: List[Dict[str, Any]]) -> None:
        valid_sensors = 0
        
        for sensor_data in sensors_config:
            sensor_id = sensor_data["id"]
            wkt_location = sensor_data["location"]
            
            # Parse WKT using regex
            coordinates = WKTParser.parse_point(wkt_location)
            
            if coordinates is None:
                logger.warning(f"Skipping sensor {sensor_id} - invalid WKT: {wkt_location}")
                continue
            
            longitude, latitude = coordinates
            
            sensor_info = SensorInfo(
                id=sensor_id,
                location=wkt_location,
                latitude=latitude,
                longitude=longitude,
                metadata=sensor_data["metadata"]
            )
            
            self.sensors[sensor_id] = sensor_info
            valid_sensors += 1
        
        logger.info(f"Loaded {valid_sensors} valid sensors out of {len(sensors_config)} total")
    
    def _load_historical_data(self) -> None:
        try:
            df = PersistenceManager.load_historical_csv(self.config["historical_data_file"])
            
            if not df.empty:
                # Clean data using pandas vector operations
                self.historical_data = DataCleaner.clean_readings_batch(df)
                logger.info(f"Historical data loaded and cleaned: {len(self.historical_data)} records")
            else:
                logger.warning("No historical data loaded")
                
        except Exception as e:
            logger.error(f"Failed to load historical data: {e}")
            self.historical_data = pd.DataFrame()
    
    def _load_existing_readings(self) -> None:
        try:
            readings_data = self.persistence.load_readings()
            
            for reading_dict in readings_data:
                reading = SensorReading(
                    sensor_id=reading_dict["sensor_id"],
                    readings=reading_dict["readings"],
                    timestamp=datetime.fromisoformat(reading_dict["timestamp"])
                )
                self.readings.append(reading)
                
                # Update sensor's last reading
                if reading.sensor_id in self.sensors:
                    sensor = self.sensors[reading.sensor_id]
                    if sensor.last_update is None or reading.timestamp > sensor.last_update:
                        sensor.last_reading = reading.readings
                        sensor.last_update = reading.timestamp
                        
        except Exception as e:
            logger.error(f"Failed to load existing readings: {e}")
    
    def ingest_reading(self, sensor_id: str, readings: Dict[str, float]) -> SensorReading:
        if sensor_id not in self.sensors:
            raise UnauthorizedSensorError(f"Sensor {sensor_id} not authorized")
        
        is_valid, errors = DataCleaner.validate_readings(readings)
        if not is_valid:
            raise InvalidReadingError(f"Invalid readings: {', '.join(errors)}")
        
        reading = SensorReading(sensor_id=sensor_id, readings=readings)
        self.persistence.append_reading(reading.to_dict())
        sensor = self.sensors[sensor_id]
        sensor.last_reading = readings
        sensor.last_update = reading.timestamp
        
        # Add to in-memory collection
        self.readings.append(reading)
        
        logger.info(f"Ingested reading from {sensor_id}: {readings}")
        return reading
    
    def get_system_status(self) -> Dict[str, Any]:
        uptime = (datetime.now() - self.start_time).total_seconds()
        
        active_sensors = sum(1 for sensor in self.sensors.values() if sensor.last_reading is not None)
        last_update = None
        if self.readings:
            last_update = max(reading.timestamp for reading in self.readings)
        
        status = "healthy" if active_sensors > 0 else "degraded"
        
        return {
            "status": status,
            "uptime_seconds": uptime,
            "active_sensors": active_sensors,
            "total_readings": len(self.readings),
            "last_update": last_update
        }
    
    def get_sensors_for_map(self) -> List[Dict[str, Any]]:
        return [sensor.to_dict() for sensor in self.sensors.values()]
    
    def get_historical_data_for_sensor(self, sensor_id: str) -> pd.DataFrame:
        if self.historical_data is None or self.historical_data.empty:
            return pd.DataFrame()
        
        return self.historical_data[self.historical_data["sensor_id"] == sensor_id].copy()
    
    def get_monthly_data(self, year: int, month: int) -> pd.DataFrame:
        if self.historical_data is None or self.historical_data.empty:
            return pd.DataFrame()
        
        # Filter by year and month
        df = self.historical_data.copy()
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        
        monthly_data = df[
            (df["timestamp"].dt.year == year) & 
            (df["timestamp"].dt.month == month)
        ]
        
        return monthly_data
    
    def sensor_exists(self, sensor_id: str) -> bool:
        return sensor_id in self.sensors
    
    def has_historical_data(self, sensor_id: str) -> bool:
        if self.historical_data is None or self.historical_data.empty:
            return False
        
        return sensor_id in self.historical_data["sensor_id"].values