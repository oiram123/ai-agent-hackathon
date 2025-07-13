#!/usr/bin/env python3
"""
Manufacturer API Integration for Accurate Part Lifespan Data
"""

import requests
import json
import os
from typing import Dict, Optional, List
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)

class ManufacturerAPIIntegration:
    """
    Integration with manufacturer APIs for accurate part lifespan data
    """
    
    def __init__(self):
        # API keys for different manufacturer services
        self.cat_api_key = os.getenv("CAT_API_KEY")  # Caterpillar API
        self.cummins_api_key = os.getenv("CUMMINS_API_KEY")  # Cummins API
        self.volvo_api_key = os.getenv("VOLVO_API_KEY")  # Volvo API
        self.komatsu_api_key = os.getenv("KOMATSU_API_KEY")  # Komatsu API
        
        # Technical database APIs
        self.partslink_api_key = os.getenv("PARTSLINK_API_KEY")  # PartsLink24
        self.tecnet_api_key = os.getenv("TECNET_API_KEY")  # TecNet
        
    def get_caterpillar_part_info(self, part_number: str) -> Optional[Dict]:
        """Get part information from Caterpillar API"""
        if not self.cat_api_key:
            return None
            
        try:
            # Caterpillar Parts API endpoint
            url = f"https://api.cat.com/parts/{part_number}"
            headers = {"Authorization": f"Bearer {self.cat_api_key}"}
            
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                return {
                    "lifespan_months": data.get("maintenance_interval_months"),
                    "manufacturer": "Caterpillar",
                    "part_number": part_number,
                    "source": "caterpillar_api"
                }
        except Exception as e:
            logger.error(f"Caterpillar API error: {e}")
        
        return None
    
    def get_cummins_part_info(self, part_number: str) -> Optional[Dict]:
        """Get part information from Cummins API"""
        if not self.cummins_api_key:
            return None
            
        try:
            # Cummins Parts API endpoint
            url = f"https://api.cummins.com/parts/{part_number}"
            headers = {"Authorization": f"Bearer {self.cummins_api_key}"}
            
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                return {
                    "lifespan_months": data.get("service_interval_months"),
                    "manufacturer": "Cummins",
                    "part_number": part_number,
                    "source": "cummins_api"
                }
        except Exception as e:
            logger.error(f"Cummins API error: {e}")
        
        return None
    
    def get_partslink_info(self, part_name: str, machine_type: str) -> Optional[Dict]:
        """Get part information from PartsLink24 database"""
        if not self.partslink_api_key:
            return None
            
        try:
            # PartsLink24 API endpoint
            url = "https://api.partslink24.com/search"
            headers = {"Authorization": f"Bearer {self.partslink_api_key}"}
            params = {
                "part_name": part_name,
                "machine_type": machine_type,
                "include_lifespan": True
            }
            
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                data = response.json()
                if data.get("results"):
                    result = data["results"][0]
                    return {
                        "lifespan_months": result.get("lifespan_months"),
                        "manufacturer": result.get("manufacturer"),
                        "part_number": result.get("part_number"),
                        "source": "partslink24"
                    }
        except Exception as e:
            logger.error(f"PartsLink24 API error: {e}")
        
        return None
    
    def get_tecnet_info(self, part_name: str, equipment_type: str) -> Optional[Dict]:
        """Get part information from TecNet database"""
        if not self.tecnet_api_key:
            return None
            
        try:
            # TecNet API endpoint
            url = "https://api.tecnet.com/parts/search"
            headers = {"Authorization": f"Bearer {self.tecnet_api_key}"}
            params = {
                "query": part_name,
                "equipment_type": equipment_type,
                "include_maintenance_data": True
            }
            
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                data = response.json()
                if data.get("parts"):
                    part = data["parts"][0]
                    return {
                        "lifespan_months": part.get("maintenance_interval_months"),
                        "manufacturer": part.get("manufacturer"),
                        "part_number": part.get("part_number"),
                        "source": "tecnet"
                    }
        except Exception as e:
            logger.error(f"TecNet API error: {e}")
        
        return None

class TechnicalDatabaseIntegration:
    """
    Integration with technical databases and maintenance standards
    """
    
    def __init__(self):
        # Load technical standards data
        self.maintenance_standards = self._load_maintenance_standards()
        self.part_categories = self._load_part_categories()
    
    def _load_maintenance_standards(self) -> Dict:
        """Load industry maintenance standards"""
        return {
            "air_filters": {
                "typical_lifespan_months": 6,
                "range_months": (3, 12),
                "factors": ["operating_conditions", "dust_levels", "humidity"]
            },
            "oil_filters": {
                "typical_lifespan_months": 6,
                "range_months": (3, 12),
                "factors": ["oil_quality", "operating_hours", "contamination"]
            },
            "fuel_filters": {
                "typical_lifespan_months": 12,
                "range_months": (6, 24),
                "factors": ["fuel_quality", "operating_conditions"]
            },
            "belts": {
                "typical_lifespan_months": 18,
                "range_months": (12, 36),
                "factors": ["tension", "alignment", "operating_conditions"]
            },
            "bearings": {
                "typical_lifespan_months": 36,
                "range_months": (24, 60),
                "factors": ["load", "speed", "lubrication", "contamination"]
            },
            "seals": {
                "typical_lifespan_months": 24,
                "range_months": (12, 36),
                "factors": ["pressure", "temperature", "chemical_exposure"]
            },
            "sensors": {
                "typical_lifespan_months": 36,
                "range_months": (24, 48),
                "factors": ["environment", "accuracy_requirements"]
            },
            "motors": {
                "typical_lifespan_months": 60,
                "range_months": (36, 84),
                "factors": ["load", "operating_hours", "maintenance"]
            }
        }
    
    def _load_part_categories(self) -> Dict:
        """Load part categorization data"""
        return {
            "filtro aria": "air_filters",
            "air filter": "air_filters",
            "oil filter": "oil_filters",
            "fuel filter": "fuel_filters",
            "belt": "belts",
            "bearing": "bearings",
            "seal": "seals",
            "gasket": "seals",
            "sensor": "sensors",
            "motor": "motors",
            "pump": "motors",
            "compressor": "motors"
        }
    
    def categorize_part(self, part_name: str) -> str:
        """Categorize part based on name"""
        part_name_lower = part_name.lower()
        
        for keyword, category in self.part_categories.items():
            if keyword in part_name_lower:
                return category
        
        return "unknown"
    
    def get_standard_lifespan(self, part_name: str, operating_conditions: Dict = None) -> Optional[int]:
        """Get standard lifespan based on part category and conditions"""
        category = self.categorize_part(part_name)
        
        if category == "unknown":
            return None
        
        standard = self.maintenance_standards.get(category)
        if not standard:
            return None
        
        base_lifespan = standard["typical_lifespan_months"]
        
        # Adjust based on operating conditions
        if operating_conditions:
            adjustment_factor = self._calculate_adjustment_factor(operating_conditions, standard["factors"])
            adjusted_lifespan = int(base_lifespan * adjustment_factor)
            return max(standard["range_months"][0], min(standard["range_months"][1], adjusted_lifespan))
        
        return base_lifespan
    
    def _calculate_adjustment_factor(self, conditions: Dict, factors: List[str]) -> float:
        """Calculate lifespan adjustment based on operating conditions"""
        adjustment = 1.0
        
        # Example adjustments (simplified)
        if "dust_levels" in factors and conditions.get("dust_levels") == "high":
            adjustment *= 0.7  # Reduce lifespan by 30%
        
        if "operating_hours" in factors and conditions.get("operating_hours") == "high":
            adjustment *= 0.8  # Reduce lifespan by 20%
        
        if "temperature" in factors and conditions.get("temperature") == "high":
            adjustment *= 0.9  # Reduce lifespan by 10%
        
        return adjustment

class HybridLifespanLookup:
    """
    Hybrid approach combining manufacturer APIs, technical databases, and standards
    """
    
    def __init__(self):
        self.manufacturer_api = ManufacturerAPIIntegration()
        self.technical_db = TechnicalDatabaseIntegration()
    
    def get_part_lifespan(self, part_info: Dict) -> Optional[int]:
        """
        Get part lifespan using multiple sources
        Returns lifespan in months
        """
        part_name = part_info.get("part_name", "")
        part_number = part_info.get("part_number", "")
        machine_type = part_info.get("machine_type", "")
        manufacturer = part_info.get("manufacturer", "")
        operating_conditions = part_info.get("operating_conditions", {})
        
        logger.info(f"🔍 Looking up lifespan for: {part_name}")
        
        # Priority 1: Manufacturer API (most accurate)
        if part_number and manufacturer:
            manufacturer_result = self._try_manufacturer_api(part_number, manufacturer)
            if manufacturer_result:
                logger.info(f"✅ Found manufacturer data: {manufacturer_result['lifespan_months']} months")
                return manufacturer_result['lifespan_months']
        
        # Priority 2: Technical database
        if part_name and machine_type:
            db_result = self._try_technical_database(part_name, machine_type)
            if db_result:
                logger.info(f"✅ Found database data: {db_result['lifespan_months']} months")
                return db_result['lifespan_months']
        
        # Priority 3: Industry standards
        standard_result = self.technical_db.get_standard_lifespan(part_name, operating_conditions)
        if standard_result:
            logger.info(f"✅ Found standard data: {standard_result} months")
            return standard_result
        
        logger.warning(f"❌ No lifespan data found for {part_name}")
        return None
    
    def _try_manufacturer_api(self, part_number: str, manufacturer: str) -> Optional[Dict]:
        """Try manufacturer-specific APIs"""
        manufacturer_lower = manufacturer.lower()
        
        if "caterpillar" in manufacturer_lower or "cat" in manufacturer_lower:
            return self.manufacturer_api.get_caterpillar_part_info(part_number)
        elif "cummins" in manufacturer_lower:
            return self.manufacturer_api.get_cummins_part_info(part_number)
        
        return None
    
    def _try_technical_database(self, part_name: str, machine_type: str) -> Optional[Dict]:
        """Try technical databases"""
        # Try PartsLink24
        result = self.manufacturer_api.get_partslink_info(part_name, machine_type)
        if result:
            return result
        
        # Try TecNet
        result = self.manufacturer_api.get_tecnet_info(part_name, machine_type)
        if result:
            return result
        
        return None

# Example usage
if __name__ == "__main__":
    lookup = HybridLifespanLookup()
    
    # Test with sample part
    part_info = {
        "part_name": "Filtro aria principale",
        "part_number": "CAT-123456",
        "machine_type": "excavator",
        "manufacturer": "Caterpillar",
        "operating_conditions": {
            "dust_levels": "high",
            "operating_hours": "normal",
            "temperature": "normal"
        }
    }
    
    lifespan = lookup.get_part_lifespan(part_info)
    print(f"Lifespan: {lifespan} months") 