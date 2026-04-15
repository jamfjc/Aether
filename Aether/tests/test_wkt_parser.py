import pytest
from src.aether.wkt_parser import WKTParser


class TestWKTParser:
    
    def test_valid_point_parsing(self):
        test_cases = [
            ("POINT(4.9041 52.3676)", (4.9041, 52.3676)),
            ("POINT(-74.0060 40.7128)", (-74.0060, 40.7128)),
            ("POINT(0 0)", (0.0, 0.0)),
            ("point(5.1214 52.0907)", (5.1214, 52.0907)),
            ("POINT( 4.9041  52.3676 )", (4.9041, 52.3676)),
        ]
        
        for wkt_string, expected in test_cases:
            result = WKTParser.parse_point(wkt_string)
            assert result is not None
            lon, lat = result
            expected_lon, expected_lat = expected
            assert abs(lon - expected_lon) < 0.0001
            assert abs(lat - expected_lat) < 0.0001
    
    def test_invalid_wkt_format(self):
        invalid_cases = [
            "INVALID(4.9041 52.3676)",
            "POINT(4.9041)",
            "POINT(4.9041, 52.3676)",
            "POINT 4.9041 52.3676",
            "POINT(abc def)",
            "",
            "POINT()",
        ]
        
        for invalid_wkt in invalid_cases:
            result = WKTParser.parse_point(invalid_wkt)
            assert result is None
    
    def test_coordinate_validation(self):
        # Valid coordinates
        assert WKTParser.validate_coordinates(0, 0) is True
        assert WKTParser.validate_coordinates(180, 90) is True
        assert WKTParser.validate_coordinates(-180, -90) is True
        assert WKTParser.validate_coordinates(4.9041, 52.3676) is True
        
        # Invalid coordinates
        assert WKTParser.validate_coordinates(181, 0) is False  # Longitude too high
        assert WKTParser.validate_coordinates(-181, 0) is False  # Longitude too low
        assert WKTParser.validate_coordinates(0, 91) is False  # Latitude too high
        assert WKTParser.validate_coordinates(0, -91) is False  # Latitude too low
    
    def test_invalid_coordinates_in_wkt(self):
        invalid_coords = [
            "POINT(181 52.3676)",
            "POINT(4.9041 91)",
            "POINT(-181 -91)",
        ]
        
        for invalid_wkt in invalid_coords:
            result = WKTParser.parse_point(invalid_wkt)
            assert result is None