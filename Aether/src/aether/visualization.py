import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class MapVisualizer:
    
    def __init__(self, thresholds: Dict[str, float], map_config: Dict[str, Any]):
        self.thresholds = thresholds
        self.map_config = map_config
    
    def create_real_time_map(self, sensors_data: List[Dict[str, Any]]) -> str:
        if not sensors_data:
            return self._create_empty_map()
        
        # Prepare data for plotting
        df_data = []
        for sensor in sensors_data:
            pm25_value = None
            color = "gray"
            status = "No data"
            
            if sensor.get("last_reading") and "pm25" in sensor["last_reading"]:
                pm25_value = sensor["last_reading"]["pm25"]
                color, status = self._get_color_and_status(pm25_value)
            
            df_data.append({
                "sensor_id": sensor["id"],
                "latitude": sensor["latitude"],
                "longitude": sensor["longitude"],
                "pm25": pm25_value,
                "region": sensor["metadata"]["region"],
                "province": sensor["metadata"]["province"],
                "color": color,
                "status": status,
                "hover_text": f"{sensor['metadata']['region']}<br>"
                             f"PM2.5: {pm25_value if pm25_value is not None else 'No data'} µg/m³<br>"
                             f"Status: {status}"
            })
        
        df = pd.DataFrame(df_data)
        
        # Create scatter map
        fig = px.scatter_map(
            df,
            lat="latitude",
            lon="longitude",
            color="color",
            hover_name="region",
            hover_data={"pm25": True, "status": True, "province": True},
            color_discrete_map={
                "green": "#00FF00",
                "yellow": "#FFFF00", 
                "orange": "#FFA500",
                "red": "#FF0000",
                "gray": "#808080"
            },
            zoom=self.map_config["default_zoom"],
            map_style=self.map_config["map_style"],
            title="Netherlands Air Quality - Real-time PM2.5 Levels"
        )
        
        # Center map on Netherlands
        fig.update_layout(
            map=dict(center=dict(lat=52.1326, lon=5.2913)),
            height=600,
            title_x=0.5
        )
        
        return fig.to_html(include_plotlyjs='cdn', full_html=True)
    
    def _get_color_and_status(self, pm25_value: float) -> tuple:
        if pm25_value <= self.thresholds["pm25_safe"]:
            return "green", "Safe"
        elif pm25_value <= self.thresholds["pm25_moderate"]:
            return "yellow", "Moderate"
        elif pm25_value <= self.thresholds["pm25_danger"]:
            return "orange", "Unhealthy"
        else:
            return "red", "Dangerous"
    
    def _create_empty_map(self) -> str:
        fig = go.Figure()
        fig.add_trace(go.Scattermapbox(
            lat=[52.1326],
            lon=[5.2913],
            mode='markers',
            marker=dict(size=0),
            text="No sensor data available"
        ))
        
        fig.update_layout(
            mapbox=dict(
                style=self.map_config["map_style"],
                center=dict(lat=52.1326, lon=5.2913),
                zoom=self.map_config["default_zoom"]
            ),
            height=600,
            title="Netherlands Air Quality - No Data Available"
        )
        
        return fig.to_html(include_plotlyjs='cdn', full_html=True)


class TemporalVisualizer:
    
    @staticmethod
    def create_time_series(df: pd.DataFrame, sensor_id: str, title: str) -> str:
        if df.empty:
            return TemporalVisualizer._create_empty_chart(title)
        
        # Filter data for specific sensor
        sensor_data = df[df["sensor_id"] == sensor_id].copy()
        
        if sensor_data.empty:
            return TemporalVisualizer._create_empty_chart(f"{title} - No data for {sensor_id}")
        
        # Ensure timestamp is datetime
        sensor_data["timestamp"] = pd.to_datetime(sensor_data["timestamp"])
        sensor_data = sensor_data.sort_values("timestamp")
        
        # Create figure with subplots
        fig = go.Figure()
        
        # Add traces for different pollutants
        pollutants = [
            ("pm25", "PM2.5", "#FF6B6B"),
            ("pm10", "PM10", "#4ECDC4"), 
            ("no2", "NO2", "#45B7D1"),
            ("o3", "O3", "#96CEB4")
        ]
        
        for col, name, color in pollutants:
            if col in sensor_data.columns:
                fig.add_trace(go.Scatter(
                    x=sensor_data["timestamp"],
                    y=sensor_data[col],
                    mode='lines',
                    name=name,
                    line=dict(color=color),
                    hovertemplate=f"{name}: %{{y:.1f}} µg/m³<br>Time: %{{x}}<extra></extra>"
                ))
        
        # Update layout with range slider
        fig.update_layout(
            title=title,
            xaxis_title="Time",
            yaxis_title="Concentration (µg/m³)",
            hovermode="x unified",
            height=600,
            xaxis=dict(
                rangeslider=dict(visible=True),
                type="date"
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        return fig.to_html(include_plotlyjs='cdn', full_html=True)
    
    @staticmethod
    def create_distribution_chart(df: pd.DataFrame, thresholds: Dict[str, float], 
                                year: int, month: int) -> str:
        if df.empty:
            return TemporalVisualizer._create_empty_chart(f"Distribution for {year}-{month:02d}")
        
        # Filter data for specific month
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        monthly_data = df[
            (df["timestamp"].dt.year == year) & 
            (df["timestamp"].dt.month == month)
        ].copy()
        
        if monthly_data.empty:
            return TemporalVisualizer._create_empty_chart(f"No data for {year}-{month:02d}")
        
        # Categorize readings by PM2.5 thresholds
        def categorize_pm25(value):
            if pd.isna(value):
                return "No Data"
            elif value <= thresholds["pm25_safe"]:
                return "Safe"
            elif value <= thresholds["pm25_moderate"]:
                return "Moderate"
            elif value <= thresholds["pm25_danger"]:
                return "Unhealthy"
            else:
                return "Dangerous"
        
        monthly_data["category"] = monthly_data["pm25"].apply(categorize_pm25)
        
        # Group by province and category
        # Note: We need to map sensor_id to province - this would come from sensor metadata
        # For now, we'll use a simplified approach
        province_counts = monthly_data.groupby(["category"]).size().reset_index(name="count")
        
        # Calculate percentages
        total_readings = province_counts["count"].sum()
        province_counts["percentage"] = (province_counts["count"] / total_readings * 100).round(1)
        
        # Create stacked bar chart
        colors = {
            "Safe": "#00FF00",
            "Moderate": "#FFFF00",
            "Unhealthy": "#FFA500", 
            "Dangerous": "#FF0000",
            "No Data": "#808080"
        }
        
        fig = go.Figure()
        
        for category in ["Safe", "Moderate", "Unhealthy", "Dangerous", "No Data"]:
            category_data = province_counts[province_counts["category"] == category]
            if not category_data.empty:
                fig.add_trace(go.Bar(
                    name=category,
                    x=["Netherlands"],  # Simplified - would be provinces in full implementation
                    y=category_data["percentage"].values,
                    marker_color=colors.get(category, "#808080"),
                    hovertemplate=f"{category}: %{{y:.1f}}%<extra></extra>"
                ))
        
        fig.update_layout(
            title=f"Air Quality Distribution - {year}-{month:02d}",
            xaxis_title="Region",
            yaxis_title="Percentage (%)",
            barmode="stack",
            yaxis=dict(range=[0, 100]),
            height=500,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        return fig.to_html(include_plotlyjs='cdn', full_html=True)
    
    @staticmethod
    def _create_empty_chart(title: str) -> str:
        fig = go.Figure()
        fig.add_annotation(
            text="No data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=20)
        )
        fig.update_layout(
            title=title,
            height=400,
            xaxis=dict(visible=False),
            yaxis=dict(visible=False)
        )
        return fig.to_html(include_plotlyjs='cdn', full_html=True)