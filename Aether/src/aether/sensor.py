from datetime import datetime
from typing import Dict, Any, Optional


class SensorReading:
    
    def __init__(self, sensor_id: str, readings: Dict[str, float], timestamp: Optional[datetime] = None):
        self.sensor_id = sensor_id
        self.readings = readings  # Store as-is, even if invalid
        self.timestamp = timestamp or datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "sensor_id": self.sensor_id,
            "readings": self.readings,
            "timestamp": self.timestamp.isoformat()
        }


class SensorInfo:
    
    def __init__(self, id: str, location: str, latitude: float, longitude: float, 
                 metadata: Dict[str, Any], last_reading: Optional[Dict[str, float]] = None, 
                 last_update: Optional[datetime] = None):
        self.id = id
        self.location = location
        self.latitude = latitude
        self.longitude = longitude
        self.metadata = metadata
        self.last_reading = last_reading
        self.last_update = last_update
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "location": self.location,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "metadata": self.metadata,
            "last_reading": self.last_reading,
            "last_update": self.last_update.isoformat() if self.last_update else None
        }