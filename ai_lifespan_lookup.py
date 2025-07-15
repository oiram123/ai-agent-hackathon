#!/usr/bin/env python3
"""
AI-Powered Part Lifespan Lookup - Fixed Version
Uses AI to get accurate lifespan data without external APIs
"""

import json
import os
from typing import Dict, Optional
from dotenv import load_dotenv
import logging
import openai
import re

load_dotenv()
logger = logging.getLogger(__name__)

class AILifespanLookup:
    """
    AI-powered lifespan lookup using intelligent prompts
    """
    
    def __init__(self):
        self.openai_key = os.getenv("OPENAI_API_KEY")
        if self.openai_key:
            openai.api_key = self.openai_key
            self.use_openai = True
        else:
            self.use_openai = False
            logger.warning("No OpenAI API key found. Using fallback responses.")
    
    def get_ai_lifespan(self, part_name: str, machine_name: str, manufacturer: str = None, part_number: str = None) -> Optional[int]:
        """
        Get part lifespan using AI analysis
        Returns lifespan in months
        """
        logger.info(f"🔍 AI analyzing lifespan for: {part_name}")
        
        if not self.use_openai:
            logger.warning("No OpenAI API key found. Using fallback lifespan.")
            return self._get_fallback_lifespan(part_name)
        
        try:
            # Create intelligent prompt based on part type
            prompt = self._create_intelligent_prompt(part_name, machine_name, manufacturer, part_number)
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system", 
                        "content": """You are a professional maintenance engineer with 20+ years of experience. 
                        Your job is to provide accurate maintenance intervals for industrial parts.
                        
                        CRITICAL INSTRUCTIONS:
                        - You MUST provide a specific number of months
                        - NEVER respond with "UNKNOWN" or "I don't know"
                        - Base your answer on industry standards and manufacturer recommendations
                        - If you're unsure, provide the most reasonable estimate based on similar parts
                        - Response format: ONLY the number (e.g., "12" for 12 months)
                        - No explanations, no additional text, just the number"""
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,  # Lower temperature for more consistent results
                max_tokens=10
            )
            
            result = response.choices[0].message.content.strip()
            logger.info(f"🤖 AI Response: '{result}'")
            
            # Enhanced parsing to extract numbers
            lifespan = self._parse_lifespan_response(result)
            
            if lifespan:
                logger.info(f"✅ AI found lifespan: {lifespan} months")
                return lifespan
            else:
                logger.warning(f"Could not parse AI response: '{result}', using fallback")
                return self._get_fallback_lifespan(part_name)
            
        except Exception as e:
            logger.error(f"AI analysis error: {e}")
            return self._get_fallback_lifespan(part_name)
    
    def _parse_lifespan_response(self, response: str) -> Optional[int]:
        """Parse AI response to extract lifespan number"""
        # Remove common words and clean the response
        cleaned = response.lower().strip()
        
        # Direct number check
        if cleaned.isdigit():
            return int(cleaned)
        
        # Extract numbers from text
        numbers = re.findall(r'\d+', cleaned)
        if numbers:
            # Take the first number found
            return int(numbers[0])
        
        # If no numbers found, return None
        return None
    
    def _create_intelligent_prompt(self, part_name: str, machine_name: str, manufacturer: str = None, part_number: str = None) -> str:
        """Create intelligent prompt based on part type and context"""
        
        # Analyze part type
        part_type = self._categorize_part(part_name)
        
        # Get context-specific examples
        examples = self._get_lifespan_examples(part_type)
        
        # Build comprehensive prompt
        prompt = f"""
MAINTENANCE INTERVAL REQUEST:

Part Details:
- Part Name: {part_name}
- Machine/Equipment: {machine_name}
- Manufacturer: {manufacturer or 'Industrial standard'}
- Part Number: {part_number or 'N/A'}

Part Category: {part_type.title()}

Industry Standards for {part_type}:
{examples}

TASK: Determine the recommended maintenance/replacement interval for this specific part.

Consider:
1. Manufacturer specifications (if known)
2. Industry best practices
3. Equipment type and usage
4. Environmental conditions (industrial use)
5. Safety requirements

Provide the interval in MONTHS only. Examples of good responses:
- "6" (for 6 months)
- "12" (for 12 months)
- "24" (for 24 months)

Your response (number only):"""
        
        return prompt
    
    def _categorize_part(self, part_name: str) -> str:
        """Categorize part based on name with expanded detection"""
        part_name_lower = part_name.lower()
        
        # Filters (air, oil, fuel, hydraulic, etc.)
        if any(word in part_name_lower for word in [
            "filter", "filtro", "air filter", "oil filter", "fuel filter", 
            "hydraulic filter", "cabin filter", "element"
        ]):
            return "filter"
        
        # Bearings
        elif any(word in part_name_lower for word in [
            "bearing", "cuscinetto", "ball bearing", "roller bearing", 
            "thrust bearing", "pillow block"
        ]):
            return "bearing"
        
        # Belts
        elif any(word in part_name_lower for word in [
            "belt", "cintura", "v-belt", "serpentine", "timing belt", 
            "drive belt", "fan belt"
        ]):
            return "belt"
        
        # Sensors
        elif any(word in part_name_lower for word in [
            "sensor", "sensore", "temperature sensor", "pressure sensor", 
            "proximity sensor", "level sensor", "flow sensor"
        ]):
            return "sensor"
        
        # Motors and pumps
        elif any(word in part_name_lower for word in [
            "motor", "motore", "pump", "pompa", "electric motor", 
            "hydraulic pump", "gear pump"
        ]):
            return "motor"
        
        # Seals and gaskets
        elif any(word in part_name_lower for word in [
            "seal", "gasket", "guarnizione", "o-ring", "oil seal", 
            "hydraulic seal", "shaft seal"
        ]):
            return "seal"
        
        # Electrical components
        elif any(word in part_name_lower for word in [
            "switch", "relay", "contactor", "fuse", "circuit breaker", 
            "transformer", "capacitor"
        ]):
            return "electrical"
        
        # Hydraulic components
        elif any(word in part_name_lower for word in [
            "hydraulic", "cylinder", "valve", "hose", "fitting", 
            "accumulator"
        ]):
            return "hydraulic"
        
        else:
            return "general"
    
    def _get_lifespan_examples(self, part_type: str) -> str:
        """Get industry standard examples for each part type"""
        examples = {
            "filter": """
- Air filters: 3-12 months (depending on environment)
- Oil filters: 3-6 months or per oil change
- Fuel filters: 6-12 months
- Hydraulic filters: 6-18 months
- Cabin filters: 6-12 months
""",
            "bearing": """
- Ball bearings: 24-60 months (industrial use)
- Roller bearings: 36-72 months
- Thrust bearings: 24-48 months
- Sealed bearings: 36-60 months
- High-speed bearings: 12-24 months
""",
            "belt": """
- V-belts: 12-24 months
- Serpentine belts: 18-36 months
- Timing belts: 24-48 months
- Drive belts: 12-24 months
- Heavy-duty belts: 18-30 months
""",
            "sensor": """
- Temperature sensors: 24-48 months
- Pressure sensors: 24-36 months
- Proximity sensors: 36-60 months
- Level sensors: 18-36 months
- Flow sensors: 24-48 months
""",
            "motor": """
- Electric motors: 60-120 months
- Hydraulic pumps: 36-72 months
- Gear pumps: 24-48 months
- Servo motors: 48-84 months
- Stepper motors: 36-60 months
""",
            "seal": """
- O-rings: 12-24 months
- Oil seals: 18-36 months
- Hydraulic seals: 12-24 months
- Gaskets: 12-36 months
- Shaft seals: 18-30 months
""",
            "electrical": """
- Switches: 24-48 months
- Relays: 24-60 months
- Contactors: 36-72 months
- Fuses: Check annually, replace as needed
- Circuit breakers: 60-120 months
""",
            "hydraulic": """
- Hydraulic cylinders: 36-72 months
- Hydraulic valves: 24-48 months
- Hydraulic hoses: 12-24 months
- Hydraulic fittings: 24-60 months
- Accumulators: 36-72 months
""",
            "general": """
- Mechanical components: 12-36 months
- Wear parts: 6-18 months
- Structural components: 36-120 months
- Consumables: 3-12 months
- Safety components: 12-24 months
"""
        }
        
        return examples.get(part_type, examples["general"])
    
    def _get_fallback_lifespan(self, part_name: str) -> int:
        """Get fallback lifespan based on part type with enhanced detection"""
        part_name_lower = part_name.lower()
        
        # Enhanced fallback rules with more specific detection
        if any(word in part_name_lower for word in [
            "air filter", "engine air", "cabin filter"
        ]):
            return 6  # Air filters - 6 months
        elif any(word in part_name_lower for word in [
            "oil filter", "hydraulic filter", "fuel filter"
        ]):
            return 6  # Fluid filters - 6 months
        elif any(word in part_name_lower for word in [
            "filter", "filtro", "element"
        ]):
            return 6  # Generic filters - 6 months
        elif any(word in part_name_lower for word in [
            "bearing", "cuscinetto", "ball bearing", "roller"
        ]):
            return 36  # Bearings - 36 months
        elif any(word in part_name_lower for word in [
            "belt", "cintura", "v-belt", "serpentine", "timing"
        ]):
            return 18  # Belts - 18 months
        elif any(word in part_name_lower for word in [
            "sensor", "sensore", "temperature", "pressure"
        ]):
            return 30  # Sensors - 30 months
        elif any(word in part_name_lower for word in [
            "motor", "motore", "pump", "pompa"
        ]):
            return 60  # Motors/pumps - 60 months
        elif any(word in part_name_lower for word in [
            "seal", "gasket", "guarnizione", "o-ring"
        ]):
            return 24  # Seals - 24 months
        elif any(word in part_name_lower for word in [
            "switch", "relay", "contactor", "electrical"
        ]):
            return 36  # Electrical - 36 months
        elif any(word in part_name_lower for word in [
            "hydraulic", "cylinder", "valve", "hose"
        ]):
            return 30  # Hydraulic - 30 months
        else:
            return 18  # Default - 18 months

# Test the AI lifespan lookup
if __name__ == "__main__":
    # Configure logging for testing
    logging.basicConfig(level=logging.INFO)
    
    lookup = AILifespanLookup()
    
    # Test cases from your data
    test_cases = [
        {
            "part_name": "Engine Air Filter - Mann C30195",
            "machine_name": "Caterpillar C9.3 Engine",
            "manufacturer": "Mann",
            "part_number": "C30195"
        },
        {
            "part_name": "Oil Filter - Mahle OC 195",
            "machine_name": "Grundfos CR Pump Unit",
            "manufacturer": "Mahle",
            "part_number": "OC 195"
        },
        {
            "part_name": "Wheel Bearing Kit - SKF VKBA 3539",
            "machine_name": "Unknown Machine",
            "manufacturer": "SKF",
            "part_number": "VKBA 3539"
        },
        {
            "part_name": "Serpentine Belt - Gates K060975",
            "machine_name": "HP LaserJet 1111X",
            "manufacturer": "Gates",
            "part_number": "K060975"
        },
        {
            "part_name": "Coolant Temperature Sensor - Bosch 0280130093",
            "machine_name": "KUKA Welding T1000",
            "manufacturer": "Bosch",
            "part_number": "0280130093"
        }
    ]
    
    print("🧪 Testing AI-Powered Lifespan Lookup (Fixed Version)")
    print("=" * 60)
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n📋 Test Case {i}:")
        print(f"Part: {test['part_name']}")
        print(f"Machine: {test['machine_name']}")
        print(f"Manufacturer: {test['manufacturer']}")
        
        lifespan = lookup.get_ai_lifespan(
            test["part_name"],
            test["machine_name"],
            test["manufacturer"],
            test["part_number"]
        )
        
        print(f"✅ Lifespan: {lifespan} months")
        print("-" * 40)
    
    # Test fallback functionality
    print("\n🔧 Testing Fallback Functionality:")
    print("=" * 40)
    
    fallback_tests = [
        "Generic Air Filter",
        "Hydraulic Pump Motor",
        "Temperature Sensor",
        "Drive Belt",
        "Wheel Bearing"
    ]
    
    for part in fallback_tests:
        fallback_lifespan = lookup._get_fallback_lifespan(part)
        print(f"Part: {part} -> Fallback: {fallback_lifespan} months")