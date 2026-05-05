# Vehicle Telemetry Simulator

[![Python](https://img.shields.io/badge/Python-3.12-3670A0?style=flat-square&logo=python&logoColor=ffdd54)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![WebSocket](https://img.shields.io/badge/WebSocket-Streaming-4A90E2?style=flat-square)](https://websockets.spec.whatwg.org/)
[![Pydantic](https://img.shields.io/badge/Pydantic-2.10-E92063?style=flat-square&logo=pydantic&logoColor=white)](https://docs.pydantic.dev/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white)](https://www.docker.com/)

Microservicio que **simula telemetría vehicular en tiempo real** sobre WebSocket. Genera paquetes JSON cada 5 segundos con datos coherentes (velocidad, GPS, RPM, temperatura, combustible, fallas OBD, eventos de aceleración) e identificador IMEI por dispositivo. Pensado como **mock controlable** para integrarse con sistemas backend que esperan datos de un dispositivo telemático real, sin necesidad del hardware.

> Componente de un sistema mayor de gestión de maquinaria. Útil para desarrollo, demos y testing de pipelines de telemetría sin depender de un dispositivo físico conectado.

---

## Highlights

- 📡 **WebSocket streaming** — JSON cada 5 segundos en `/ws/telemetria`, multi-cliente, CORS habilitado.
- 📱 **Gestión de IMEI** flexible — un solo IMEI fijo, lista CSV de IMEIs, o generación aleatoria opt-in (`ALLOW_GENERATE_IMEI=true`). Validación: 15 dígitos exactos.
- 🧪 **Datos coherentes** — el generador respeta correlaciones realistas (si hay movimiento → RPM > idle, etc.) en lugar de valores aleatorios sueltos.
- ⏰ **Timestamps ISO 8601 UTC** con microsegundos.
- 🐳 **Docker-ready** con red compartida (`shared_net`) para integrarse con otros microservicios.
- ⚙️ **FastAPI lifespan** (no `@app.on_event` deprecado).
- ✅ **Pydantic V2** con `field_validator` y `ConfigDict`.

## Stack

| Categoría | Tecnología |
|---|---|
| Framework | FastAPI 0.115 |
| Servidor | uvicorn[standard] 0.34 |
| WebSocket | `websockets` 14.1 |
| Validación | Pydantic 2.10 + pydantic-settings |
| Config | python-dotenv |
| Contenerización | Docker + docker-compose |

---

## Quick start

### Con Docker (recomendado)

```bash
# 1. Crear la red Docker compartida (una sola vez)
docker network create shared_net

# 2. Levantar el servicio
docker-compose up --build

# Acceso desde el host:
# - API:           http://localhost:8003
# - Docs:          http://localhost:8003/docs
# - WebSocket:     ws://localhost:8003/ws/telemetria
# - Health:        http://localhost:8003/health
```

### Local sin Docker

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Configurar IMEI antes de correr (uno de los tres):
export DEVICE_IMEI=352099001761481
# export DEVICE_IMEI_LIST=352099001761481,352099001761482
# export ALLOW_GENERATE_IMEI=true

uvicorn app.main:app --reload
```

---

## Configuración de IMEI

El servicio requiere al menos uno de estos modos. Si arranca sin ninguno, falla al arrancar (fail-fast).

| Variable | Uso | Ejemplo |
|---|---|---|
| `DEVICE_IMEI` | Un solo dispositivo fijo | `352099001761481` |
| `DEVICE_IMEI_LIST` | Lista CSV de dispositivos válidos | `352099001761481,352099001761482` |
| `ALLOW_GENERATE_IMEI` | Generar uno aleatorio si no hay nada | `true` |

Reglas:

- IMEI debe tener **exactamente 15 dígitos**. Cualquier otro formato se descarta con warning.
- Si `DEVICE_IMEI` y `DEVICE_IMEI_LIST` están ambos seteados, ambos se aplican.
- Modo aleatorio (`ALLOW_GENERATE_IMEI=true`) genera un IMEI sintético — útil para tests, no para integración real.

---

## API

### Endpoints HTTP

| Método | Path | Descripción |
|---|---|---|
| GET | `/` | Info del servicio |
| GET | `/health` | Health check con estado de IMEI |
| GET | `/docs` | Swagger UI |

### WebSocket

```
ws://localhost:8003/ws/telemetria
```

Cliente recibe un JSON cada 5 segundos:

```json
{
  "imei": "352099001761481",
  "timestamp": "2026-05-05T08:42:30.123456Z",
  "data": {
    "ignition": true,
    "movement": true,
    "speed": 45.2,
    "gps": { "lat": -2.94, "lon": -75.30 },
    "rpm": 2400,
    "engine_temp": 87,
    "engine_load": 35,
    "oil_level": 78,
    "fuel_level": 65.5,
    "fuel_consumption": 7.2,
    "obd_faults": [],
    "odometer": 124530,
    "event_type": "MOVING",
    "g_value": 1.02
  }
}
```

---

## Ejemplos de cliente

### JavaScript / TypeScript

```javascript
const ws = new WebSocket("ws://localhost:8003/ws/telemetria");

ws.onopen = () => console.log("Conectado al simulador");

ws.onmessage = (event) => {
  const packet = JSON.parse(event.data);
  console.log(`[${packet.imei}] speed=${packet.data.speed} km/h fuel=${packet.data.fuel_level}%`);
};

ws.onerror = (err) => console.error("WS error:", err);
ws.onclose = () => console.log("Desconectado");
```

### Python

```python
import asyncio
import json
import websockets

async def consume():
    uri = "ws://localhost:8003/ws/telemetria"
    async with websockets.connect(uri) as ws:
        async for message in ws:
            packet = json.loads(message)
            print(f"[{packet['imei']}] {packet['data']['speed']} km/h")

asyncio.run(consume())
```

> El repo incluye `test_websocket.py` y `test_client.html` listos para probar.

---

## Estructura del proyecto

```
vehicle-telemetry-simulator/
├── app/
│   ├── main.py                 # FastAPI app, routes, lifespan, CORS
│   ├── config.py               # pydantic-settings + IMEI validation
│   ├── api/
│   │   └── websocket.py        # WebSocket endpoint handler
│   ├── simulator/
│   │   └── generator.py        # Synthetic data generator (coherent values)
│   └── models/
│       └── telemetry_data.py   # Pydantic models for the payload
├── test_client.html            # HTML test client
├── test_websocket.py           # Python test client
├── Dockerfile                  # Python 3.12-slim + healthcheck
├── docker-compose.yml          # External shared_net network
├── docker-compose.override.yml # Dev overrides (DEBUG=1, hot reload)
├── requirements.txt
└── README.md
```

## Integración

El servicio se diseñó para vivir en una red Docker compartida (`shared_net`) junto a otros microservicios:

```
shared_net network
├─ telemetry_simulator    (this service, 8000 internal / 8003 external)
├─ users_machinery        (sister service)
└─ payroll_backend        (sister service)
```

Otros contenedores en `shared_net` pueden conectarse a `ws://telemetry_simulator:8000/ws/telemetria`.

---

## Mejoras pendientes (deuda técnica reconocida)

- **Tests automatizados**: agregar `pytest` con `httpx.AsyncClient` para HTTP y `websockets` para el WS endpoint.
- **CORS específico**: hoy `allow_origins=["*"]`; restringir en producción.
- **Persistencia de eventos**: el schema PostgreSQL está mencionado pero no implementado. Si se integra, evaluar si los paquetes deben emitirse a una cola (Redis/RabbitMQ/Kafka) en lugar de quedar volátiles.
- **Frecuencia configurable** del stream (5s hardcoded → env var `STREAM_INTERVAL_SECONDS`).
- **Múltiples IMEI emitiendo concurrentemente** (hoy se elige uno por conexión; podría rotarse o emitir en paralelo).
- **Backpressure**: si un cliente lee más lento de lo que produce, hoy se acumula en buffer. Considerar drop-on-slow o cap explícito.
- **Métricas Prometheus** (`prometheus-client`) para observabilidad: clientes conectados, paquetes/s, errores.
- **Schemas OpenAPI más explícitos** para los modelos (hoy hay Pydantic, falta documentar el formato del payload del WS en `/docs`).

---

## Licencia

MIT.

## Autor

Desarrollado por Jesús Beleño como componente del sistema de gestión de maquinaria y nómina.
