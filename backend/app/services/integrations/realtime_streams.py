"""
Real-time Data Streams Service

Handles real-time data ingestion from various sources:
- IoT sensors (temperature, humidity, production rates)
- Vehicle tracking systems (GPS, fuel consumption)
- Production line monitoring
- Inventory level sensors
- Quality control systems
"""

import asyncio
import json
import logging
import pandas as pd
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
import websockets
import pika
import redis
from sqlalchemy.orm import Session
import aioredis

from app.core.config import get_settings
from app.utils.exceptions import IntegrationError

logger = logging.getLogger(__name__)
settings = get_settings()


class RealTimeStreamService:
    """Service for handling real-time data streams."""
    
    def __init__(self):
        self.redis_client = None
        self.rabbitmq_connection = None
        self.websocket_connections = {}
        self.stream_handlers = {}
        
        # Stream configurations
        self.iot_config = {
            'broker_url': settings.IOT_BROKER_URL,
            'username': settings.IOT_USERNAME,
            'password': settings.IOT_PASSWORD,
            'topics': [
                'plant/+/production/rate',
                'plant/+/temperature',
                'plant/+/humidity',
                'plant/+/energy/consumption',
                'vehicle/+/location',
                'vehicle/+/fuel/level',
                'inventory/+/level',
                'quality/+/test/results'
            ]
        }
    
    async def initialize_connections(self):
        """Initialize all real-time connections."""
        try:
            logger.info("Initializing real-time stream connections")
            
            # Initialize Redis for caching real-time data
            self.redis_client = await aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            
            # Initialize RabbitMQ for message queuing
            await self._initialize_rabbitmq()
            
            # Start IoT data streams
            await self._start_iot_streams()
            
            logger.info("Real-time stream connections initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing real-time connections: {e}")
            raise IntegrationError(f"Real-time stream initialization failed: {str(e)}")
    
    async def _initialize_rabbitmq(self):
        """Initialize RabbitMQ connection for message queuing."""
        try:
            connection_params = pika.ConnectionParameters(
                host=settings.RABBITMQ_HOST,
                port=settings.RABBITMQ_PORT,
                virtual_host=settings.RABBITMQ_VHOST,
                credentials=pika.PlainCredentials(
                    settings.RABBITMQ_USERNAME,
                    settings.RABBITMQ_PASSWORD
                )
            )
            
            self.rabbitmq_connection = pika.BlockingConnection(connection_params)
            channel = self.rabbitmq_connection.channel()
            
            # Declare exchanges and queues
            channel.exchange_declare(exchange='iot_data', exchange_type='topic')
            channel.exchange_declare(exchange='vehicle_tracking', exchange_type='topic')
            channel.exchange_declare(exchange='production_monitoring', exchange_type='topic')
            
            # Declare queues
            queues = [
                'production_data',
                'vehicle_location',
                'inventory_levels',
                'quality_control',
                'energy_consumption'
            ]
            
            for queue in queues:
                channel.queue_declare(queue=queue, durable=True)
            
            logger.info("RabbitMQ connection initialized")
            
        except Exception as e:
            logger.error(f"RabbitMQ initialization error: {e}")
            raise
    
    async def _start_iot_streams(self):
        """Start IoT data stream listeners."""
        try:
            # Start different stream listeners
            tasks = [
                self._listen_production_sensors(),
                self._listen_vehicle_tracking(),
                self._listen_inventory_sensors(),
                self._listen_quality_control(),
                self._listen_energy_monitoring()
            ]
            
            # Run all listeners concurrently
            await asyncio.gather(*tasks, return_exceptions=True)
            
        except Exception as e:
            logger.error(f"Error starting IoT streams: {e}")
            raise
    
    async def _listen_production_sensors(self):
        """Listen to production line sensor data."""
        try:
            logger.info("Starting production sensor listener")
            
            while True:
                # Simulate production sensor data
                production_data = await self._generate_production_sensor_data()
                
                for data in production_data:
                    # Cache in Redis
                    cache_key = f"production:{data['plant_id']}:{data['line_id']}"
                    await self.redis_client.setex(
                        cache_key, 
                        300,  # 5 minutes TTL
                        json.dumps(data)
                    )
                    
                    # Trigger callbacks if registered
                    if 'production_data' in self.stream_handlers:
                        await self.stream_handlers['production_data'](data)
                
                await asyncio.sleep(30)  # Update every 30 seconds
                
        except Exception as e:
            logger.error(f"Production sensor listener error: {e}")
    
    async def _listen_vehicle_tracking(self):
        """Listen to vehicle GPS and status data."""
        try:
            logger.info("Starting vehicle tracking listener")
            
            while True:
                # Simulate vehicle tracking data
                vehicle_data = await self._generate_vehicle_tracking_data()
                
                for data in vehicle_data:
                    # Cache in Redis
                    cache_key = f"vehicle:{data['vehicle_id']}"
                    await self.redis_client.setex(
                        cache_key,
                        60,  # 1 minute TTL
                        json.dumps(data)
                    )
                    
                    # Trigger callbacks
                    if 'vehicle_tracking' in self.stream_handlers:
                        await self.stream_handlers['vehicle_tracking'](data)
                
                await asyncio.sleep(60)  # Update every minute
                
        except Exception as e:
            logger.error(f"Vehicle tracking listener error: {e}")
    
    async def _listen_inventory_sensors(self):
        """Listen to inventory level sensors."""
        try:
            logger.info("Starting inventory sensor listener")
            
            while True:
                # Simulate inventory sensor data
                inventory_data = await self._generate_inventory_sensor_data()
                
                for data in inventory_data:
                    # Cache in Redis
                    cache_key = f"inventory:{data['plant_id']}:{data['silo_id']}"
                    await self.redis_client.setex(
                        cache_key,
                        300,  # 5 minutes TTL
                        json.dumps(data)
                    )
                    
                    # Check for low inventory alerts
                    if data['level_percent'] < 20:
                        await self._trigger_low_inventory_alert(data)
                    
                    # Trigger callbacks
                    if 'inventory_levels' in self.stream_handlers:
                        await self.stream_handlers['inventory_levels'](data)
                
                await asyncio.sleep(120)  # Update every 2 minutes
                
        except Exception as e:
            logger.error(f"Inventory sensor listener error: {e}")
    
    async def _listen_quality_control(self):
        """Listen to quality control test results."""
        try:
            logger.info("Starting quality control listener")
            
            while True:
                # Simulate quality control data
                quality_data = await self._generate_quality_control_data()
                
                for data in quality_data:
                    # Cache in Redis
                    cache_key = f"quality:{data['plant_id']}:{data['batch_id']}"
                    await self.redis_client.setex(
                        cache_key,
                        3600,  # 1 hour TTL
                        json.dumps(data)
                    )
                    
                    # Check for quality issues
                    if not data['quality_passed']:
                        await self._trigger_quality_alert(data)
                    
                    # Trigger callbacks
                    if 'quality_control' in self.stream_handlers:
                        await self.stream_handlers['quality_control'](data)
                
                await asyncio.sleep(300)  # Update every 5 minutes
                
        except Exception as e:
            logger.error(f"Quality control listener error: {e}")
    
    async def _listen_energy_monitoring(self):
        """Listen to energy consumption monitoring."""
        try:
            logger.info("Starting energy monitoring listener")
            
            while True:
                # Simulate energy monitoring data
                energy_data = await self._generate_energy_monitoring_data()
                
                for data in energy_data:
                    # Cache in Redis
                    cache_key = f"energy:{data['plant_id']}:{data['equipment_id']}"
                    await self.redis_client.setex(
                        cache_key,
                        300,  # 5 minutes TTL
                        json.dumps(data)
                    )
                    
                    # Check for high energy consumption
                    if data['power_kw'] > data['threshold_kw']:
                        await self._trigger_energy_alert(data)
                    
                    # Trigger callbacks
                    if 'energy_monitoring' in self.stream_handlers:
                        await self.stream_handlers['energy_monitoring'](data)
                
                await asyncio.sleep(60)  # Update every minute
                
        except Exception as e:
            logger.error(f"Energy monitoring listener error: {e}")
    
    async def _generate_production_sensor_data(self) -> List[Dict]:
        """Generate simulated production sensor data."""
        import random
        
        plants = ['PLANT_MUM', 'PLANT_DEL', 'PLANT_CHE', 'PLANT_KOL']
        production_data = []
        
        for plant_id in plants:
            for line_id in range(1, 4):  # 3 production lines per plant
                # Simulate realistic production metrics
                base_rate = random.uniform(80, 120)  # tonnes/hour
                efficiency = random.uniform(0.85, 0.98)
                temperature = random.uniform(1400, 1600)  # Celsius for clinker
                
                data = {
                    'timestamp': datetime.now().isoformat(),
                    'plant_id': plant_id,
                    'line_id': f'LINE_{line_id}',
                    'production_rate_tph': round(base_rate * efficiency, 2),
                    'efficiency_percent': round(efficiency * 100, 1),
                    'temperature_celsius': round(temperature, 1),
                    'pressure_bar': round(random.uniform(2.0, 3.5), 2),
                    'vibration_mm_s': round(random.uniform(1.0, 4.0), 2),
                    'status': 'running' if efficiency > 0.8 else 'degraded'
                }
                production_data.append(data)
        
        return production_data
    
    async def _generate_vehicle_tracking_data(self) -> List[Dict]:
        """Generate simulated vehicle tracking data."""
        import random
        
        vehicles = [
            {'id': 'TRK001', 'type': 'truck', 'capacity': 25},
            {'id': 'TRK002', 'type': 'truck', 'capacity': 30},
            {'id': 'RAIL001', 'type': 'rail', 'capacity': 50},
            {'id': 'TRK003', 'type': 'truck', 'capacity': 25}
        ]
        
        vehicle_data = []
        
        for vehicle in vehicles:
            # Simulate GPS coordinates (somewhere in India)
            lat = random.uniform(8.0, 35.0)
            lon = random.uniform(68.0, 97.0)
            
            data = {
                'timestamp': datetime.now().isoformat(),
                'vehicle_id': vehicle['id'],
                'vehicle_type': vehicle['type'],
                'latitude': round(lat, 6),
                'longitude': round(lon, 6),
                'speed_kmh': round(random.uniform(0, 80), 1),
                'fuel_level_percent': round(random.uniform(20, 100), 1),
                'load_tonnes': round(random.uniform(0, vehicle['capacity']), 1),
                'status': random.choice(['in_transit', 'loading', 'unloading', 'idle']),
                'driver_id': f"DRV_{random.randint(100, 999)}"
            }
            vehicle_data.append(data)
        
        return vehicle_data
    
    async def _generate_inventory_sensor_data(self) -> List[Dict]:
        """Generate simulated inventory sensor data."""
        import random
        
        plants = ['PLANT_MUM', 'PLANT_DEL', 'PLANT_CHE', 'PLANT_KOL']
        inventory_data = []
        
        for plant_id in plants:
            for silo_id in range(1, 6):  # 5 silos per plant
                # Simulate inventory levels
                capacity_tonnes = random.uniform(5000, 10000)
                current_tonnes = random.uniform(500, capacity_tonnes)
                level_percent = (current_tonnes / capacity_tonnes) * 100
                
                data = {
                    'timestamp': datetime.now().isoformat(),
                    'plant_id': plant_id,
                    'silo_id': f'SILO_{silo_id}',
                    'material_type': 'clinker',
                    'capacity_tonnes': round(capacity_tonnes, 0),
                    'current_tonnes': round(current_tonnes, 0),
                    'level_percent': round(level_percent, 1),
                    'temperature_celsius': round(random.uniform(25, 45), 1),
                    'humidity_percent': round(random.uniform(30, 70), 1),
                    'last_movement': (datetime.now() - timedelta(minutes=random.randint(5, 120))).isoformat()
                }
                inventory_data.append(data)
        
        return inventory_data
    
    async def _generate_quality_control_data(self) -> List[Dict]:
        """Generate simulated quality control data."""
        import random
        
        plants = ['PLANT_MUM', 'PLANT_DEL', 'PLANT_CHE', 'PLANT_KOL']
        quality_data = []
        
        for plant_id in plants:
            # Generate quality test results
            compressive_strength = random.uniform(50, 60)  # MPa
            fineness = random.uniform(300, 400)  # m²/kg
            setting_time = random.uniform(30, 180)  # minutes
            
            # Determine if quality passed
            quality_passed = (
                compressive_strength >= 53 and
                fineness >= 320 and
                setting_time <= 120
            )
            
            data = {
                'timestamp': datetime.now().isoformat(),
                'plant_id': plant_id,
                'batch_id': f"BATCH_{datetime.now().strftime('%Y%m%d')}_{random.randint(100, 999)}",
                'test_type': 'cement_quality',
                'compressive_strength_mpa': round(compressive_strength, 1),
                'fineness_m2_kg': round(fineness, 0),
                'setting_time_minutes': round(setting_time, 0),
                'quality_passed': quality_passed,
                'grade': 'OPC_53' if quality_passed else 'REJECT',
                'tested_by': f"QC_{random.randint(100, 999)}"
            }
            quality_data.append(data)
        
        return quality_data
    
    async def _generate_energy_monitoring_data(self) -> List[Dict]:
        """Generate simulated energy monitoring data."""
        import random
        
        plants = ['PLANT_MUM', 'PLANT_DEL', 'PLANT_CHE', 'PLANT_KOL']
        energy_data = []
        
        for plant_id in plants:
            equipment_types = ['kiln', 'mill', 'crusher', 'conveyor', 'fan']
            
            for equipment_type in equipment_types:
                # Simulate energy consumption
                base_power = {
                    'kiln': 8000,
                    'mill': 3000,
                    'crusher': 1500,
                    'conveyor': 500,
                    'fan': 800
                }[equipment_type]
                
                current_power = base_power * random.uniform(0.7, 1.2)
                threshold_power = base_power * 1.1
                
                data = {
                    'timestamp': datetime.now().isoformat(),
                    'plant_id': plant_id,
                    'equipment_id': f"{equipment_type.upper()}_001",
                    'equipment_type': equipment_type,
                    'power_kw': round(current_power, 1),
                    'threshold_kw': round(threshold_power, 1),
                    'energy_kwh': round(current_power * 24, 1),  # Daily consumption
                    'efficiency_percent': round(random.uniform(80, 95), 1),
                    'status': 'normal' if current_power <= threshold_power else 'high_consumption'
                }
                energy_data.append(data)
        
        return energy_data
    
    async def _trigger_low_inventory_alert(self, data: Dict):
        """Trigger alert for low inventory levels."""
        alert = {
            'alert_type': 'low_inventory',
            'severity': 'warning',
            'plant_id': data['plant_id'],
            'silo_id': data['silo_id'],
            'current_level': data['level_percent'],
            'message': f"Low inventory alert: {data['silo_id']} at {data['plant_id']} is at {data['level_percent']:.1f}%",
            'timestamp': datetime.now().isoformat()
        }
        
        # Send to alert queue
        await self.redis_client.lpush('alerts:inventory', json.dumps(alert))
        logger.warning(f"Low inventory alert: {alert['message']}")
    
    async def _trigger_quality_alert(self, data: Dict):
        """Trigger alert for quality control failures."""
        alert = {
            'alert_type': 'quality_failure',
            'severity': 'critical',
            'plant_id': data['plant_id'],
            'batch_id': data['batch_id'],
            'message': f"Quality control failure: Batch {data['batch_id']} at {data['plant_id']} failed quality tests",
            'timestamp': datetime.now().isoformat()
        }
        
        # Send to alert queue
        await self.redis_client.lpush('alerts:quality', json.dumps(alert))
        logger.error(f"Quality alert: {alert['message']}")
    
    async def _trigger_energy_alert(self, data: Dict):
        """Trigger alert for high energy consumption."""
        alert = {
            'alert_type': 'high_energy_consumption',
            'severity': 'warning',
            'plant_id': data['plant_id'],
            'equipment_id': data['equipment_id'],
            'current_power': data['power_kw'],
            'threshold_power': data['threshold_kw'],
            'message': f"High energy consumption: {data['equipment_id']} at {data['plant_id']} consuming {data['power_kw']} kW (threshold: {data['threshold_kw']} kW)",
            'timestamp': datetime.now().isoformat()
        }
        
        # Send to alert queue
        await self.redis_client.lpush('alerts:energy', json.dumps(alert))
        logger.warning(f"Energy alert: {alert['message']}")
    
    def register_stream_handler(self, stream_type: str, handler: Callable):
        """Register a callback handler for specific stream types."""
        self.stream_handlers[stream_type] = handler
        logger.info(f"Registered handler for stream type: {stream_type}")
    
    async def get_latest_data(self, data_type: str, plant_id: Optional[str] = None) -> List[Dict]:
        """Get latest real-time data from Redis cache."""
        try:
            pattern = f"{data_type}:*"
            if plant_id:
                pattern = f"{data_type}:{plant_id}:*"
            
            keys = await self.redis_client.keys(pattern)
            data = []
            
            for key in keys:
                cached_data = await self.redis_client.get(key)
                if cached_data:
                    data.append(json.loads(cached_data))
            
            return data
            
        except Exception as e:
            logger.error(f"Error getting latest data: {e}")
            return []
    
    async def close_connections(self):
        """Close all real-time connections."""
        try:
            if self.redis_client:
                await self.redis_client.close()
            
            if self.rabbitmq_connection:
                self.rabbitmq_connection.close()
            
            logger.info("Real-time stream connections closed")
            
        except Exception as e:
            logger.error(f"Error closing connections: {e}")


# Singleton instance
realtime_service = RealTimeStreamService()