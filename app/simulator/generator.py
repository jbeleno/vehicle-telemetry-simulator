"""
Telemetry data generator with coherent value relationships
"""
import random
import math
from datetime import datetime, timezone
from typing import List, Tuple
from app.models.telemetry_data import TelemetryData
from app.config import settings
import logging

logger = logging.getLogger(__name__)


def generate_random_imei() -> str:
    """
    Generate a pseudo-random 15-digit IMEI.
    Note: This doesn't implement Luhn algorithm validation.
    
    Returns:
        str: 15-digit IMEI
    """
    return "".join(str(random.randint(0, 9)) for _ in range(15))


class TelemetryGenerator:
    """
    Generates realistic telemetry data with coherent relationships between values.
    For example: if ignition is ON and vehicle is moving, speed should increase.
    """
    
    # Base values that persist across generations for continuity
    _base_state = {
        'lat': 4.60971,  # Bogotá
        'lon': -74.08175,
        'total_odo': 2456789,
        'trip_odo': 34567,
        'fuel_level': 68,
        'oil_level': 80,
    }
    
    # Common OBD fault codes for realistic simulation
    _obd_faults_pool = [
        "P0135", "P0420", "P0300", "P0171", "P0174",
        "P0301", "P0302", "P0303", "P0304", "P0420",
        "U0100", "U0101", "B0001", "B0002"
    ]
    
    def __init__(self):
        """Initialize the generator with random initial state"""
        # Randomize initial state for variety
        self._base_state['ignition'] = random.choice([0, 1])
        self._base_state['in_motion'] = random.choice([0, 1])
        self._base_state['speed'] = random.randint(0, 80) if self._base_state['ignition'] else 0
        
        # Initialize IMEI selection
        self._imei_index = 0
        self._imeis = settings.imei_list
        if not self._imeis and settings.ALLOW_GENERATE_IMEI:
            # Will generate on first call
            self._imeis = []
        elif not self._imeis:
            raise RuntimeError("No IMEI configurado. Verifique DEVICE_IMEI o ALLOW_GENERATE_IMEI")
        
        # Get current IMEI
        self._selected_imei = settings.validate_imei_config()
        logger.info(f"Generador inicializado con IMEI: {self._selected_imei}")
        
    def _generate_gps_coordinate(self) -> str:
        """
        Generate GPS coordinate in ISO6709 format
        Returns format: +DD.MM.MMMm +DDD.MM.MMMm/  or +DD.MMSSS +DDD.MMSSS/
        Simplified version: +04.60971-074.08175/
        """
        # Simulate slight movement
        lat_change = random.uniform(-0.001, 0.001)
        lon_change = random.uniform(-0.001, 0.001)
        
        self._base_state['lat'] += lat_change
        self._base_state['lon'] += lon_change
        
        # Format as ISO6709: +lat-lon/
        return f"+{self._base_state['lat']:.5f}{self._base_state['lon']:.5f}/"
    
    def _generate_rpm(self, ignition: int, speed: int) -> int:
        """
        Generate RPM based on ignition status and speed
        """
        if ignition == 0:
            return 0
        
        if speed == 0:
            # Idle RPM (700-900)
            return random.randint(700, 900)
        elif speed < 40:
            # City driving (1200-2500)
            return random.randint(1200, 2500)
        elif speed < 80:
            # Highway cruising (2000-3500)
            return random.randint(2000, 3500)
        else:
            # High speed (3500-6000)
            return random.randint(3500, 6000)
    
    def _generate_engine_temp(self, ignition: int, engine_load: int) -> int:
        """
        Generate engine temperature based on operation status
        Normal operating temp: 90-95°C
        Cold start: 20-50°C
        """
        if ignition == 0:
            # Engine off, cooling down
            return random.randint(-60, 40)
        
        # Running engine temperature based on load
        base_temp = 75 if engine_load < 30 else 95
        return random.randint(base_temp - 5, base_temp + 5)
    
    def _generate_fuel_consumption(self, speed: int, engine_load: int, movement: int) -> float:
        """
        Generate realistic fuel consumption in L/h
        """
        if movement == 0:
            return round(random.uniform(0.2, 0.8), 1)  # Idle consumption
        
        # Consumption increases with speed and load
        base_consumption = 8.0 + (speed / 20) + (engine_load / 10)
        return round(base_consumption + random.uniform(-2, 3), 1)
    
    def _generate_obd_faults(self) -> List[str]:
        """
        Generate random OBD fault codes (occasional, not always)
        """
        faults = []
        if random.random() < 0.15:  # 15% chance of having faults
            num_faults = random.randint(1, 3)
            faults = random.sample(self._obd_faults_pool, num_faults)
        return faults
    
    def _generate_event_data(self, speed: int, prev_speed: int = None) -> tuple:
        """
        Generate event type and G-value based on speed changes
        Returns: (event_type, event_g_value)
        event_type: 1=Acceleration, 2=Braking, 3=Curve
        """
        if prev_speed is None:
            prev_speed = speed
            
        speed_diff = speed - prev_speed
        
        if speed_diff > 5:
            # Acceleration
            return (1, min(255, int(15 + speed_diff * 2)))
        elif speed_diff < -5:
            # Braking
            return (2, min(255, int(20 + abs(speed_diff) * 2)))
        else:
            # Normal driving or curve
            return (3 if random.random() < 0.3 else None, random.randint(10, 40))
    
    def generate_telemetry_data(self) -> TelemetryData:
        """
        Generate a complete set of telemetry data with coherent relationships
        """
        # Update ignition (can randomly change)
        if random.random() < 0.05:  # 5% chance to toggle
            self._base_state['ignition'] = 1 - self._base_state['ignition']
        
        ignition = self._base_state['ignition']
        
        # Update movement status
        if ignition == 1:
            # Vehicle can be moving or stationary
            if random.random() < 0.3:
                self._base_state['in_motion'] = 1 - self._base_state['in_motion']
            movement = self._base_state['in_motion']
        else:
            movement = 0
        
        # Update speed based on movement and ignition
        prev_speed = self._base_state.get('speed', 0)
        if ignition == 0:
            self._base_state['speed'] = 0
        elif movement == 0:
            self._base_state['speed'] = max(0, self._base_state['speed'] - random.randint(0, 5))
        else:
            # Gradually increase/decrease speed
            speed_change = random.randint(-3, 8)
            self._base_state['speed'] = max(0, min(350, self._base_state['speed'] + speed_change))
        
        speed = self._base_state['speed']
        
        # Generate dependent values
        rpm = self._generate_rpm(ignition, speed)
        engine_load = random.randint(30, 70)
        engine_temp = self._generate_engine_temp(ignition, engine_load)
        
        # Generate fuel consumption
        instant_consumption = self._generate_fuel_consumption(speed, engine_load, movement)
        
        # Update odometer (slight increase)
        if movement == 1:
            trip_inc = random.randint(200, 500)
            total_inc = random.randint(200, 500)
            self._base_state['trip_odo'] += trip_inc
            self._base_state['total_odo'] += total_inc
        
        # Update fuel level (gradual decrease)
        if movement == 1 and ignition == 1:
            fuel_decrease = random.uniform(0.01, 0.05)
            self._base_state['fuel_level'] = max(0, self._base_state['fuel_level'] - fuel_decrease)
        
        # Generate GPS location
        gps_location = self._generate_gps_coordinate()
        
        # Generate OBD faults
        obd_faults = self._generate_obd_faults()
        
        # Generate event data
        event_type, event_g_value = self._generate_event_data(speed, prev_speed)
        
        # Generate GSM signal (usually good, occasionally weak)
        gsm_signal = random.randint(1, 5) if random.random() < 0.9 else random.randint(3, 5)
        
        # Generate oil level (slight variations)
        oil_level = max(70, min(100, self._base_state['oil_level'] + random.randint(-2, 1)))
        
        # Calculate fuel used GPS (accumulative)
        if movement == 1:
            fuel_used_gps = self._base_state.get('fuel_used_total', 150.0) + instant_consumption / 7200  # per second approximation
            self._base_state['fuel_used_total'] = fuel_used_gps
        else:
            fuel_used_gps = self._base_state.get('fuel_used_total', 150.0)
        
        return TelemetryData(
            ignition_status=ignition,
            movement_status=movement,
            speed=speed,
            gps_location=gps_location,
            gsm_signal=gsm_signal,
            rpm=rpm,
            engine_temp=engine_temp,
            engine_load=engine_load,
            oil_level=oil_level,
            fuel_level=int(self._base_state['fuel_level']),
            fuel_used_gps=round(fuel_used_gps, 2),
            instant_consumption=instant_consumption,
            obd_faults=obd_faults,
            odometer_total=self._base_state['total_odo'],
            odometer_trip=self._base_state['trip_odo'],
            event_type=event_type,
            event_g_value=event_g_value
        )
    
    def _get_current_imei(self) -> str:
        """
        Get current IMEI, with round-robin rotation if multiple IMEIs configured
        
        Returns:
            str: Current IMEI to use
        """
        if len(self._imeis) > 1:
            # Round-robin selection
            self._imei_index = (self._imei_index + 1) % len(self._imeis)
            return self._imeis[self._imei_index]
        elif len(self._imeis) == 1:
            return self._imeis[0]
        else:
            # Generate if allowed
            if settings.ALLOW_GENERATE_IMEI:
                return generate_random_imei()
            return self._selected_imei
    
    def _get_current_timestamp(self) -> str:
        """
        Get current timestamp in ISO 8601 UTC format with microseconds
        
        Returns:
            str: ISO 8601 timestamp (e.g., "2025-10-27T13:30:00.123456Z")
        """
        return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")
    
    def generate_response(self) -> dict:
        """
        Generate a complete telemetry response with IMEI, timestamp, and data
        
        Returns:
            dict: Complete telemetry packet
        """
        # Get IMEI and timestamp
        imei = self._get_current_imei()
        timestamp = self._get_current_timestamp()
        
        # Generate telemetry data
        data = self.generate_telemetry_data()
        
        # Build complete packet
        packet = {
            "imei": imei,
            "timestamp": timestamp,
            "data": data.model_dump()
        }
        
        logger.debug(f"Paquete generado - IMEI: {imei}, TS: {timestamp}")
        
        return packet

