# 🚗 Vehicle Telemetry Simulator

Simulador de telemetría vehicular en tiempo real con FastAPI y WebSocket.

## 🎯 Características

- ✅ Generación de datos sintéticos coherentes
- ✅ Transmisión en tiempo real vía WebSocket cada 5 segundos
- ✅ Gestión de IMEI (identificación de dispositivos)
- ✅ Timestamps ISO 8601 UTC con microsegundos
- ✅ Parámetros realistas: velocidad, GPS, RPM, temperatura, combustible
- ✅ Docker-ready con integración a red compartida
- ✅ Soporte multi-cliente
- ✅ CORS habilitado
- ✅ Logging detallado

## 🚀 Inicio Rápido

### 1. Crear red Docker
```bash
docker network create shared_net
```

### 2. Levantar servicio
```bash
docker-compose up --build
```

### 3. Probar el WebSocket

**Cliente HTML:**
```bash
# Abrir en el navegador
start test_client.html
# Hacer clic en "Conectar"
```

**JavaScript:**
```javascript
const ws = new WebSocket('ws://localhost:8003/ws/telemetria');
ws.onmessage = (e) => {
  const packet = JSON.parse(e.data);
  console.log('IMEI:', packet.imei);
  console.log('Timestamp:', packet.timestamp);
  console.log('Speed:', packet.data.speed);
};
```

## 📊 Estructura de Datos

Cada paquete incluye:

```json
{
  "imei": "352099001761481",
  "timestamp": "2025-10-27T13:30:00.123456Z",
  "data": {
    "ignition_status": 1,
    "movement_status": 1,
    "speed": 120,
    "gps_location": "+04.60971-074.08175/",
    "gsm_signal": 4,
    "rpm": 2500,
    "engine_temp": 92,
    "engine_load": 57,
    "oil_level": 80,
    "fuel_level": 68,
    "fuel_used_gps": 153.2,
    "instant_consumption": 14.5,
    "obd_faults": ["P0135", "P0420"],
    "odometer_total": 2456789,
    "odometer_trip": 34567,
    "event_type": 2,
    "event_g_value": 45
  }
}
```

## ⚙️ Configuración

### Variables de Entorno

**Opción 1: IMEI único**
```env
DEVICE_IMEI=352099001761481
```

**Opción 2: Múltiples dispositivos (CSV)**
```env
DEVICE_IMEI_LIST=352099001761481,352099001761482,352099001761483
```

**Opción 3: Generación automática**
```env
ALLOW_GENERATE_IMEI=true
```

### Puerto

El servicio se expone en el puerto `8003` por defecto.

## 📋 Parámetros de Telemetría

| ID | Parámetro | Rango | Descripción |
|----|-----------|-------|-------------|
| 239 | ignition_status | 0-1 | Estado de ignición |
| 240 | movement_status | 0-1 | Estado de movimiento |
| 24 | speed | 0-350 km/h | Velocidad actual |
| 387 | gps_location | ISO6709 | Ubicación GPS |
| 21 | gsm_signal | 1-5 | Señal GSM |
| 36 | rpm | 0-16384 | Revoluciones |
| 32 | engine_temp | -60 a 127°C | Temperatura |
| 31 | engine_load | 0-100% | Carga del motor |
| 1159 | oil_level | 0-100% | Nivel de aceite |
| 48 | fuel_level | 0-100% | Nivel de combustible |
| 12 | fuel_used_gps | 0-4,294,967 L | Combustible usado |
| 60 | instant_consumption | 0-32767 L/h | Consumo instantáneo |
| 281 | obd_faults | Array | Códigos de fallas |
| 16 | odometer_total | 0-2,147,483,647 m | Odómetro total |
| 199 | odometer_trip | 0-2,147,483,647 m | Odómetro viaje |
| 253 | event_type | 1-3 | Tipo de evento |
| 254 | event_g_value | 0-255 | Valor G |

## 🏗️ Estructura del Proyecto

```
TelemetrySimulator/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application
│   ├── config.py               # Settings management
│   ├── api/
│   │   ├── websocket.py        # WebSocket endpoint
│   ├── simulator/
│   │   └── generator.py        # Data generator
│   └── models/
│       └── telemetry_data.py   # Pydantic models
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── test_client.html            # Test client
├── test_websocket.py           # Test script
└── README.md
```

## 🛠️ Stack Tecnológico

- **Python 3.11**
- **FastAPI** - Framework web
- **Uvicorn** - ASGI server
- **WebSocket** - Real-time communication
- **Pydantic v2** - Data validation
- **Docker** - Containerization
- **PostgreSQL-ready** (schema preparado)

## 🧪 Testing

### Health Check
```bash
curl http://localhost:8003/health
```

### WebSocket (Postman)
```
ws://localhost:8003/ws/telemetria
```

### Documentación API
```
http://localhost:8003/docs
```

## 📝 Ejemplo de Uso

### JavaScript/TypeScript
```javascript
const ws = new WebSocket('ws://localhost:8003/ws/telemetria');

ws.onopen = () => {
  console.log('✅ Conectado al simulador');
};

ws.onmessage = (event) => {
  const packet = JSON.parse(event.data);
  console.log('📱 IMEI:', packet.imei);
  console.log('⏰ Timestamp:', packet.timestamp);
  console.log('🚗 Velocidad:', packet.data.speed, 'km/h');
  console.log('🔧 RPM:', packet.data.rpm);
  console.log('⛽ Combustible:', packet.data.fuel_level, '%');
};

ws.onerror = (error) => {
  console.error('❌ Error:', error);
};

ws.onclose = () => {
  console.log('🔌 Desconectado');
};
```

### Python
```python
import asyncio
import websockets
import json

async def connect():
    uri = "ws://localhost:8003/ws/telemetria"
    async with websockets.connect(uri) as websocket:
        while True:
            data = await websocket.recv()
            packet = json.loads(data)
            print(f"IMEI: {packet['imei']}")
            print(f"Speed: {packet['data']['speed']} km/h")

asyncio.run(connect())
```

## 🔧 Desarrollo

### Instalación Local
```bash
# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar
uvicorn app.main:app --reload
```

## 🔗 Integración

Este servicio se integra con:
- **AppMachineryPayrollBackend** (puerto 8000)
- **UsersMachPay** (puerto 8001)
- Todos comparten la red Docker `shared_net`

## 📄 Licencia

MIT License

## 👥 Autor

Desarrollado como parte del sistema de Gestión de Maquinaria y Nómina

## 🌟 Contribuir

Las contribuciones son bienvenidas. Por favor, abre un issue o pull request.

