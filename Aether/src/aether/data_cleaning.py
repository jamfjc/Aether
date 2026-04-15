import pandas as pd
from typing import List, Tuple, Dict, Any
import logging

logger = logging.getLogger(__name__)


class DataCleaner:
    
    @staticmethod
    def validate_readings(readings: Dict[str, float]) -> Tuple[bool, List[str]]:
        errors = []
        
        # Check for negative values
        for pollutant, value in readings.items():
            if value < 0:
                errors.append(f"Negative value for {pollutant}: {value}")
        
        # Check for extreme outliers (PM2.5 > 500)
        if "pm25" in readings and readings["pm25"] > 500:
            errors.append(f"Extreme PM2.5 value: {readings['pm25']}")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def clean_readings_batch(df: pd.DataFrame) -> pd.DataFrame:
        initial_count = len(df)
        
        # Drop rows with missing critical values
        df = df.dropna(subset=["sensor_id", "timestamp"])
        
        # Remove rows with negative pollutant values
        pollutant_cols = ["pm25", "pm10", "no2", "o3"]
        for col in pollutant_cols:
            if col in df.columns:
                df = df[df[col] >= 0]
        
        # Filter extreme outliers (PM2.5 > 500)
        if "pm25" in df.columns:
            df = df[df["pm25"] <= 500]
        
        # Convert timestamp to datetime if it's not already
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
            df = df.dropna(subset=["timestamp"])
        
        final_count = len(df)
        dropped_count = initial_count - final_count
        percentage_cleaned = (dropped_count / initial_count * 100) if initial_count > 0 else 0
        
        logger.info(f"Cleaned data: {initial_count} -> {final_count} rows "
                   f"({dropped_count} dropped, {percentage_cleaned:.2f}%)")
        
        return df
    
    @staticmethod
    def aggregate_by_sensor(df: pd.DataFrame) -> pd.DataFrame:
        return df.groupby("sensor_id").agg({
            "pm25": ["mean", "median", "min", "max", "std"],
            "pm10": ["mean", "median", "min", "max", "std"],
            "no2": ["mean", "median", "min", "max", "std"],
            "o3": ["mean", "median", "min", "max", "std"]
        }).round(2)
    
    @staticmethod
    def filter_by_threshold(df: pd.DataFrame, thresholds: Dict[str, float]) -> pd.DataFrame:
        filtered_df = df.copy()
        
        for pollutant, threshold in thresholds.items():
            if pollutant in filtered_df.columns:
                filtered_df = filtered_df[filtered_df[pollutant] <= threshold]
        
        return filtered_df
    
    @staticmethod
    def calculate_statistics(df: pd.DataFrame) -> Dict[str, Any]:
        stats = {}
        pollutant_cols = ["pm25", "pm10", "no2", "o3"]
        
        for col in pollutant_cols:
            if col in df.columns:
                stats[col] = {
                    "mean": df[col].mean(),
                    "median": df[col].median(),
                    "min": df[col].min(),
                    "max": df[col].max(),
                    "std": df[col].std()
                }
        
        return stats