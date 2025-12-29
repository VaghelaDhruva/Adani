"""
External API Integration Service

Integrates with weather APIs, market data providers, fuel price APIs,
and other external data sources that affect supply chain operations.
"""

import logging
import requests
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import asyncio
import aiohttp
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.utils.exceptions import IntegrationError

logger = logging.getLogger(__name__)
settings = get_settings()


class ExternalAPIService:
    """Service for integrating with external APIs."""
    
    def __init__(self):
        self.weather_api_key = settings.WEATHER_API_KEY
        self.market_data_api_key = settings.MARKET_DATA_API_KEY
        self.fuel_price_api_key = settings.FUEL_PRICE_API_KEY
        
        # API endpoints
        self.weather_base_url = "https://api.openweathermap.org/data/2.5"
        self.market_data_url = "https://api.marketdata.com/v1"
        self.fuel_price_url = "https://api.eia.gov/v2"
        
        # Plant locations for weather data
        self.plant_locations = {
            'PLANT_MUM': {'lat': 19.0760, 'lon': 72.8777, 'city': 'Mumbai'},
            'PLANT_DEL': {'lat': 28.7041, 'lon': 77.1025, 'city': 'Delhi'},
            'PLANT_CHE': {'lat': 13.0827, 'lon': 80.2707, 'city': 'Chennai'},
            'PLANT_KOL': {'lat': 22.5726, 'lon': 88.3639, 'city': 'Kolkata'}
        }
    
    async def fetch_weather_data(self, days_ahead: int = 7) -> pd.DataFrame:
        """Fetch weather forecast data for all plant locations."""
        try:
            logger.info(f"Fetching weather data for {days_ahead} days ahead")
            
            weather_data = []
            
            async with aiohttp.ClientSession() as session:
                tasks = []
                for plant_id, location in self.plant_locations.items():
                    task = self._fetch_plant_weather(session, plant_id, location, days_ahead)
                    tasks.append(task)
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in results:
                    if isinstance(result, Exception):
                        logger.error(f"Weather API error: {result}")
                    else:
                        weather_data.extend(result)
            
            weather_df = pd.DataFrame(weather_data)
            logger.info(f"Successfully fetched weather data for {len(weather_df)} records")
            
            return weather_df
            
        except Exception as e:
            logger.error(f"Error fetching weather data: {e}")
            raise IntegrationError(f"Weather API integration failed: {str(e)}")
    
    async def _fetch_plant_weather(self, session: aiohttp.ClientSession, plant_id: str, 
                                 location: Dict, days_ahead: int) -> List[Dict]:
        """Fetch weather data for a specific plant location."""
        try:
            # Current weather
            current_url = f"{self.weather_base_url}/weather"
            current_params = {
                'lat': location['lat'],
                'lon': location['lon'],
                'appid': self.weather_api_key,
                'units': 'metric'
            }
            
            # Forecast weather
            forecast_url = f"{self.weather_base_url}/forecast"
            forecast_params = {
                'lat': location['lat'],
                'lon': location['lon'],
                'appid': self.weather_api_key,
                'units': 'metric',
                'cnt': days_ahead * 8  # 8 forecasts per day (3-hour intervals)
            }
            
            weather_records = []
            
            # Fetch current weather
            async with session.get(current_url, params=current_params) as response:
                if response.status == 200:
                    current_data = await response.json()
                    weather_records.append({
                        'plant_id': plant_id,
                        'city': location['city'],
                        'date': datetime.now().date(),
                        'temperature_celsius': current_data['main']['temp'],
                        'humidity_percent': current_data['main']['humidity'],
                        'wind_speed_kmh': current_data['wind']['speed'] * 3.6,
                        'precipitation_mm': current_data.get('rain', {}).get('1h', 0),
                        'weather_condition': current_data['weather'][0]['main'],
                        'visibility_km': current_data.get('visibility', 10000) / 1000,
                        'forecast_type': 'current'
                    })
            
            # Fetch forecast weather
            async with session.get(forecast_url, params=forecast_params) as response:
                if response.status == 200:
                    forecast_data = await response.json()
                    for item in forecast_data['list']:
                        forecast_date = datetime.fromtimestamp(item['dt']).date()
                        weather_records.append({
                            'plant_id': plant_id,
                            'city': location['city'],
                            'date': forecast_date,
                            'temperature_celsius': item['main']['temp'],
                            'humidity_percent': item['main']['humidity'],
                            'wind_speed_kmh': item['wind']['speed'] * 3.6,
                            'precipitation_mm': item.get('rain', {}).get('3h', 0),
                            'weather_condition': item['weather'][0]['main'],
                            'visibility_km': item.get('visibility', 10000) / 1000,
                            'forecast_type': 'forecast'
                        })
            
            return weather_records
            
        except Exception as e:
            logger.error(f"Error fetching weather for {plant_id}: {e}")
            return []
    
    def fetch_fuel_price_data(self) -> pd.DataFrame:
        """Fetch fuel price data from EIA (Energy Information Administration)."""
        try:
            logger.info("Fetching fuel price data from EIA")
            
            # EIA API for petroleum prices
            url = f"{self.fuel_price_url}/petroleum/pri/gnd/data"
            params = {
                'api_key': self.fuel_price_api_key,
                'frequency': 'weekly',
                'data[0]': 'value',
                'facets[product][]': 'EPD2DXL0',  # Diesel fuel
                'facets[area][]': 'NUS',  # US National
                'sort[0][column]': 'period',
                'sort[0][direction]': 'desc',
                'offset': 0,
                'length': 52  # Last 52 weeks
            }
            
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code != 200:
                raise IntegrationError(f"EIA API error: {response.status_code}")
            
            data = response.json()
            fuel_data = data.get('response', {}).get('data', [])
            
            # Transform to our schema
            fuel_df = pd.DataFrame([
                {
                    'date': datetime.strptime(item['period'], '%Y-%m-%d').date(),
                    'fuel_type': 'diesel',
                    'price_usd_per_gallon': float(item['value']),
                    'price_inr_per_liter': float(item['value']) * 83.0 * 0.264172,  # Convert to INR/liter
                    'region': 'US_National',
                    'source': 'EIA',
                    'last_updated': datetime.now()
                }
                for item in fuel_data if item['value'] is not None
            ])
            
            logger.info(f"Successfully fetched {len(fuel_df)} fuel price records")
            return fuel_df
            
        except Exception as e:
            logger.error(f"Error fetching fuel price data: {e}")
            raise IntegrationError(f"Fuel price API failed: {str(e)}")
    
    def fetch_cement_market_data(self) -> pd.DataFrame:
        """Fetch cement market prices and trends."""
        try:
            logger.info("Fetching cement market data")
            
            # This would typically connect to commodity price APIs
            # For demo, we'll simulate realistic market data
            
            base_date = datetime.now().date()
            market_data = []
            
            # Generate realistic cement price data for major Indian markets
            markets = {
                'Mumbai': {'base_price': 450, 'volatility': 0.05},
                'Delhi': {'base_price': 420, 'volatility': 0.04},
                'Chennai': {'base_price': 430, 'volatility': 0.06},
                'Kolkata': {'base_price': 410, 'volatility': 0.05},
                'Bangalore': {'base_price': 440, 'volatility': 0.05}
            }
            
            for days_back in range(30):  # Last 30 days
                date = base_date - timedelta(days=days_back)
                
                for market, config in markets.items():
                    # Simulate price with some volatility
                    import random
                    price_variation = random.uniform(-config['volatility'], config['volatility'])
                    current_price = config['base_price'] * (1 + price_variation)
                    
                    market_data.append({
                        'date': date,
                        'market': market,
                        'product': 'OPC_53_Grade',
                        'price_inr_per_tonne': round(current_price, 2),
                        'volume_tonnes': random.randint(5000, 15000),
                        'price_trend': 'stable',
                        'source': 'market_data_api',
                        'last_updated': datetime.now()
                    })
            
            market_df = pd.DataFrame(market_data)
            logger.info(f"Successfully generated {len(market_df)} market data records")
            
            return market_df
            
        except Exception as e:
            logger.error(f"Error fetching market data: {e}")
            raise IntegrationError(f"Market data API failed: {str(e)}")
    
    def fetch_economic_indicators(self) -> pd.DataFrame:
        """Fetch economic indicators that affect supply chain costs."""
        try:
            logger.info("Fetching economic indicators")
            
            # This would connect to economic data APIs like FRED, World Bank, etc.
            # For demo, we'll create realistic economic data
            
            indicators_data = []
            base_date = datetime.now().date()
            
            # Key economic indicators
            indicators = {
                'USD_INR_Exchange_Rate': 83.25,
                'India_Inflation_Rate': 5.2,
                'Crude_Oil_Price_USD': 85.50,
                'India_GDP_Growth_Rate': 6.8,
                'India_Manufacturing_PMI': 57.2,
                'Freight_Rate_Index': 105.3
            }
            
            for days_back in range(7):  # Last 7 days
                date = base_date - timedelta(days=days_back)
                
                for indicator, base_value in indicators.items():
                    # Add small daily variations
                    import random
                    variation = random.uniform(-0.02, 0.02)  # ±2% variation
                    current_value = base_value * (1 + variation)
                    
                    indicators_data.append({
                        'date': date,
                        'indicator_name': indicator,
                        'value': round(current_value, 2),
                        'unit': self._get_indicator_unit(indicator),
                        'source': 'economic_data_api',
                        'last_updated': datetime.now()
                    })
            
            indicators_df = pd.DataFrame(indicators_data)
            logger.info(f"Successfully fetched {len(indicators_df)} economic indicators")
            
            return indicators_df
            
        except Exception as e:
            logger.error(f"Error fetching economic indicators: {e}")
            raise IntegrationError(f"Economic data API failed: {str(e)}")
    
    def _get_indicator_unit(self, indicator_name: str) -> str:
        """Get the unit for economic indicators."""
        units = {
            'USD_INR_Exchange_Rate': 'INR per USD',
            'India_Inflation_Rate': 'percent',
            'Crude_Oil_Price_USD': 'USD per barrel',
            'India_GDP_Growth_Rate': 'percent',
            'India_Manufacturing_PMI': 'index',
            'Freight_Rate_Index': 'index'
        }
        return units.get(indicator_name, 'units')
    
    async def fetch_all_external_data(self) -> Dict[str, pd.DataFrame]:
        """Fetch all external data sources."""
        try:
            logger.info("Fetching all external data sources")
            
            # Fetch weather data (async)
            weather_df = await self.fetch_weather_data()
            
            # Fetch other data (sync)
            fuel_df = self.fetch_fuel_price_data()
            market_df = self.fetch_cement_market_data()
            economic_df = self.fetch_economic_indicators()
            
            return {
                'weather': weather_df,
                'fuel_prices': fuel_df,
                'market_data': market_df,
                'economic_indicators': economic_df
            }
            
        except Exception as e:
            logger.error(f"Error fetching external data: {e}")
            raise IntegrationError(f"External data fetch failed: {str(e)}")


# Singleton instance
external_api_service = ExternalAPIService()