from typing import Dict, Any, List
from .sensor_manager import SensorManager
from .visualization import MapVisualizer, TemporalVisualizer
from .persistence import PersistenceManager

# Global service instances
_sensor_manager: SensorManager = None
_map_visualizer: MapVisualizer = None
_temporal_visualizer: TemporalVisualizer = None


def initialize_services(server_config_path: str, sensors_config_path: str) -> None:
    global _sensor_manager, _map_visualizer, _temporal_visualizer
    
    # Load configurations
    server_config = PersistenceManager.load_config(server_config_path)
    sensors_config = PersistenceManager.load_config(sensors_config_path)
    
    # Initialize services
    _sensor_manager = SensorManager(server_config, sensors_config)
    _map_visualizer = MapVisualizer(
        thresholds=server_config["thresholds"],
        map_config=server_config["map_config"]
    )
    _temporal_visualizer = TemporalVisualizer()


def reset_services() -> None:
    global _sensor_manager, _map_visualizer, _temporal_visualizer
    _sensor_manager = None
    _map_visualizer = None
    _temporal_visualizer = None


def get_sensor_manager() -> SensorManager:
    if _sensor_manager is None:
        raise RuntimeError("SensorManager not initialized. Call initialize_services() first.")
    return _sensor_manager


def get_map_visualizer() -> MapVisualizer:
    if _map_visualizer is None:
        raise RuntimeError("MapVisualizer not initialized. Call initialize_services() first.")
    return _map_visualizer


def get_temporal_visualizer() -> TemporalVisualizer:
    if _temporal_visualizer is None:
        raise RuntimeError("TemporalVisualizer not initialized. Call initialize_services() first.")
    return _temporal_visualizer