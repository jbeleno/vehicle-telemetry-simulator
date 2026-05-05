"""
Main FastAPI application for Telemetry Simulator
"""
import logging
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api.websocket import websocket_telemetry_endpoint
from app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup and shutdown lifecycle events
    """
    # Startup
    logger.info("🚀 Telemetry Simulator iniciándose...")
    
    # Validate IMEI configuration
    try:
        imeis = settings.imei_list
        logger.info(f"IMEI configurado: {len(imeis)} dispositivo(s)")
        
        # Try to get first IMEI to validate
        initial_imei = settings.validate_imei_config()
        logger.info(f"✅ IMEI inicial: {initial_imei}")
    except Exception as e:
        logger.error(f"❌ Error en configuración de IMEI: {str(e)}")
        raise
    
    logger.info("📡 Servicio WebSocket disponible en: ws://localhost:8000/ws/telemetria")
    logger.info("✅ Servicio listo para recibir conexiones")
    yield
    # Shutdown
    logger.info("🛑 Deteniendo Telemetry Simulator...")


# Create FastAPI application
app = FastAPI(
    title="Telemetry Simulator",
    description="Servicio de simulación de telemetría vehicular en tiempo real",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """
    Root endpoint with service information
    """
    return {
        "service": "Telemetry Simulator",
        "version": "1.0.0",
        "description": "Servicio de simulación de telemetría vehicular",
        "websocket_endpoint": "/ws/telemetria",
        "documentation": "/docs"
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint with IMEI configuration status
    """
    imeis = settings.imei_list
    
    return {
        "status": "healthy",
        "service": "Telemetry Simulator",
        "imei_config": {
            "configured_imeis": len(imeis),
            "allow_generate_imei": settings.ALLOW_GENERATE_IMEI,
            "imeis_preview": imeis[:3] if imeis else []
        }
    }


@app.websocket("/ws/telemetria")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for telemetry data streaming.

    Connects to ws://localhost:8000/ws/telemetria. Streams JSON every 5
    seconds with simulated telemetry values:
    - Ignition status, movement status, speed, GPS location
    - RPM, engine temperature, engine load
    - Oil level, fuel level, fuel consumption
    - OBD faults, odometer readings
    - Event types and G-values
    """
    await websocket_telemetry_endpoint(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

