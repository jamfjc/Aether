import re
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)

# WKT POINT pattern with named capture groups
WKT_POINT_PATTERN = re.compile(
    r"POINT\s*\(\s*(?P<lon>-?\d+\.?\d*)\s+(?P<lat>-?\d+\.?\d*)\s*\)",
    re.IGNORECASE,
)


class WKTParser:
    
    @staticmethod
    def parse_point(wkt_string: str) -> Optional[Tuple[float, float]]:
        try:
            match = WKT_POINT_PATTERN.match(wkt_string.strip())
            if not match:
                logger.warning(f"Invalid WKT format: {wkt_string}")
                return None
            
            lon = float(match.group('lon'))
            lat = float(match.group('lat'))
            
            # Validate coordinate ranges
            if not WKTParser.validate_coordinates(lon, lat):
                logger.warning(f"Invalid coordinates: lon={lon}, lat={lat}")
                return None
            
            return lon, lat
            
        except (ValueError, AttributeError) as e:
            logger.warning(f"Failed to parse WKT '{wkt_string}': {e}")
            return None
    
    @staticmethod
    def validate_coordinates(longitude: float, latitude: float) -> bool:
        return (-180 <= longitude <= 180) and (-90 <= latitude <= 90)