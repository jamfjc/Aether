import json
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class PersistenceManager:
    
    def __init__(self, storage_file: str):
        self.storage_file = Path(storage_file)
        self.storage_file.parent.mkdir(parents=True, exist_ok=True)
    
    def save_readings(self, readings: List[Dict[str, Any]]) -> None:
        try:
            with open(self.storage_file, 'w') as f:
                json.dump(readings, f, indent=2, default=str)
            logger.info(f"Saved {len(readings)} readings to {self.storage_file}")
        except Exception as e:
            logger.error(f"Failed to save readings: {e}")
            raise
    
    def load_readings(self) -> List[Dict[str, Any]]:
        if not self.storage_file.exists():
            return []
        
        try:
            with open(self.storage_file, 'r') as f:
                readings = json.load(f)
            logger.info(f"Loaded {len(readings)} readings from {self.storage_file}")
            return readings
        except Exception as e:
            logger.error(f"Failed to load readings: {e}")
            return []
    
    def append_reading(self, reading: Dict[str, Any]) -> None:
        readings = self.load_readings()
        readings.append(reading)
        self.save_readings(readings)
    
    @staticmethod
    def load_historical_csv(file_path: str) -> pd.DataFrame:
        try:
            df = pd.read_csv(file_path)
            logger.info(f"Loaded historical data: {len(df)} rows from {file_path}")
            return df
        except Exception as e:
            logger.error(f"Failed to load historical data: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def load_config(file_path: str) -> Dict[str, Any]:
        try:
            with open(file_path, 'r') as f:
                config = json.load(f)
            logger.info(f"Loaded configuration from {file_path}")
            return config
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise