import logging
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, Depends, HTTPException, Response
from fastapi.responses import HTMLResponse

from .models import IngestRequest, IngestResponse, StatusResponse, ErrorResponse
from .sensor_manager import SensorManager, UnauthorizedSensorError, InvalidReadingError
from .visualization import MapVisualizer, TemporalVisualizer
from .dependencies import (
    initialize_services, 
    get_sensor_manager, 
    get_map_visualizer, 
    get_temporal_visualizer
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)





def create_app(config_path: str = None, sensors_path: str = None) -> FastAPI:
    
    @asynccontextmanager
    async def app_lifespan(app: FastAPI):
        # Startup
        logger.info("Starting Air Quality Monitoring System...")
        
        if config_path and sensors_path:
            server_config_path = config_path
            sensors_config_path = sensors_path
        else:
            config_dir = Path(__file__).parent.parent.parent / "config"
            server_config_path = str(config_dir / "server_config.json")
            sensors_config_path = str(config_dir / "sensors.json")
        
        try:
            initialize_services(server_config_path, sensors_config_path)
            logger.info("Services initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize services: {e}")
            raise
        
        yield
        
        # Shutdown
        logger.info("Shutting down Air Quality Monitoring System...")
    
    app = FastAPI(
        title="Air Quality Monitoring System",
        description="Professional backend service for Netherlands Air Quality Monitoring",
        version="1.0.0",
        lifespan=app_lifespan
    )
    
    @app.post("/ingest", response_model=IngestResponse)
    def ingest_data(
        request: IngestRequest,
        sensor_manager: Annotated[SensorManager, Depends(get_sensor_manager)]
    ) -> IngestResponse:
        try:
            reading = sensor_manager.ingest_reading(request.sensor_id, request.readings)
            
            return IngestResponse(
                status="success",
                message="Reading ingested successfully",
                sensor_id=request.sensor_id,
                timestamp=reading.timestamp
            )
            
        except UnauthorizedSensorError as e:
            raise HTTPException(status_code=403, detail=str(e))
        except InvalidReadingError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Ingestion error: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    @app.get("/map", response_class=HTMLResponse)
    def get_real_time_map(
        sensor_manager: Annotated[SensorManager, Depends(get_sensor_manager)],
        map_visualizer: Annotated[MapVisualizer, Depends(get_map_visualizer)]
    ) -> str:
        try:
            sensors_data = sensor_manager.get_sensors_for_map()
            html_content = map_visualizer.create_real_time_map(sensors_data)
            return html_content
            
        except Exception as e:
            logger.error(f"Map generation error: {e}")
            raise HTTPException(status_code=500, detail="Failed to generate map")
    
    @app.get("/status", response_model=StatusResponse)
    def get_system_status(
        sensor_manager: Annotated[SensorManager, Depends(get_sensor_manager)]
    ) -> StatusResponse:
        try:
            status_data = sensor_manager.get_system_status()
            
            return StatusResponse(
                status=status_data["status"],
                uptime_seconds=status_data["uptime_seconds"],
                active_sensors=status_data["active_sensors"],
                total_readings=status_data["total_readings"],
                last_update=status_data["last_update"]
            )
            
        except Exception as e:
            logger.error(f"Status error: {e}")
            raise HTTPException(status_code=500, detail="Failed to get system status")
    
    @app.get("/history/{sensor_id}", response_class=HTMLResponse)
    def get_sensor_history(
        sensor_id: str,
        sensor_manager: Annotated[SensorManager, Depends(get_sensor_manager)],
        temporal_visualizer: Annotated[TemporalVisualizer, Depends(get_temporal_visualizer)]
    ) -> str:
        try:
        if not sensor_manager.sensor_exists(sensor_id):
                raise HTTPException(status_code=404, detail=f"Sensor {sensor_id} not found")
            
            if not sensor_manager.has_historical_data(sensor_id):
                raise HTTPException(
                    status_code=404, 
                    detail=f"No historical data available for sensor {sensor_id}"
                )
            
            historical_data = sensor_manager.get_historical_data_for_sensor(sensor_id)
            title = f"Air Quality History - {sensor_id}"
            html_content = temporal_visualizer.create_time_series(
                historical_data, sensor_id, title
            )
            
            return html_content
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"History visualization error: {e}")
            raise HTTPException(status_code=500, detail="Failed to generate history chart")
    
    @app.get("/distribution/{year}/{month}", response_class=HTMLResponse)
    def get_monthly_distribution(
        year: int,
        month: int,
        sensor_manager: Annotated[SensorManager, Depends(get_sensor_manager)],
        temporal_visualizer: Annotated[TemporalVisualizer, Depends(get_temporal_visualizer)]
    ) -> str:
        try:
            if not (1 <= month <= 12):
                raise HTTPException(status_code=400, detail="Month must be between 1 and 12")
            
            monthly_data = sensor_manager.get_monthly_data(year, month)
            
            if monthly_data.empty:
                raise HTTPException(
                    status_code=404, 
                    detail=f"No data available for {year}-{month:02d}"
                )
            
            html_content = temporal_visualizer.create_distribution_chart(
                monthly_data, 
                sensor_manager.config["thresholds"], 
                year, 
                month
            )
            
            return html_content
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Distribution chart error: {e}")
            raise HTTPException(status_code=500, detail="Failed to generate distribution chart")
    
    @app.get("/", response_class=HTMLResponse)
    def get_welcome_page() -> str:
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Air Quality Monitoring System</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }
                .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                h1 { color: #2c3e50; text-align: center; }
                .description { color: #7f8c8d; text-align: center; margin-bottom: 30px; }
                .endpoints { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
                .endpoint { background: #ecf0f1; padding: 20px; border-radius: 8px; border-left: 4px solid #3498db; }
                .endpoint h3 { margin-top: 0; color: #2c3e50; }
                .endpoint a { color: #3498db; text-decoration: none; font-weight: bold; }
                .endpoint a:hover { text-decoration: underline; }
                .method { background: #3498db; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px; }
                .method.get { background: #27ae60; }
                .method.post { background: #e74c3c; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🌍 Air Quality Monitoring System</h1>
                <p class="description">
                    Professional backend service for Netherlands Air Quality Monitoring<br>
                    Real-time sensor data ingestion and interactive visualizations
                </p>
                
                <div class="endpoints">
                    <div class="endpoint">
                        <h3><span class="method get">GET</span> Real-time Map</h3>
                        <p>Interactive map showing current air quality across the Netherlands</p>
                        <a href="/map">View Map →</a>
                    </div>
                    
                    <div class="endpoint">
                        <h3><span class="method get">GET</span> System Status</h3>
                        <p>System health, uptime, and sensor statistics</p>
                        <a href="/status">View Status →</a>
                    </div>
                    
                    <div class="endpoint">
                        <h3><span class="method get">GET</span> Sensor History</h3>
                        <p>Time series data with interactive range slider</p>
                        <a href="/history/sensor_amsterdam_001">Example: Amsterdam →</a>
                    </div>
                    
                    <div class="endpoint">
                        <h3><span class="method get">GET</span> Monthly Distribution</h3>
                        <p>Province-level air quality distribution charts</p>
                        <a href="/distribution/2024/4">Example: April 2024 →</a>
                    </div>
                    
                    <div class="endpoint">
                        <h3><span class="method post">POST</span> Data Ingestion</h3>
                        <p>Secure endpoint for sensor data ingestion</p>
                        <a href="/docs#/default/ingest_data_ingest_post">API Documentation →</a>
                    </div>
                    
                    <div class="endpoint">
                        <h3><span class="method get">GET</span> API Documentation</h3>
                        <p>Auto-generated Swagger UI documentation</p>
                        <a href="/docs">View Docs →</a>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        return html_content
    
    return app


# Create the app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)