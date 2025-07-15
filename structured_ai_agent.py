import json
import openai
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
from dotenv import load_dotenv
import dateutil.parser
from collections import defaultdict
import requests
import re
from serpapi import GoogleSearch
from ai_lifespan_lookup import AILifespanLookup

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add default lifespans for parts (fallback only)
DEFAULT_PART_LIFESPANS = {
    3: 12,   # 1 year default
    4: 24,   # 2 years default
    9: 6,    # 6 months default
    5: 18,   # 1.5 years default
    6: 12,   # 1 year default
    7: 24,   # 2 years default
    8: 18,   # 1.5 years default
    10: 12,  # 1 year default
    11: 6,   # 6 months default
    12: 24,  # 2 years default
    13: 18,  # 1.5 years default
    14: 12,  # 1 year default
    15: 24,  # 2 years default
    16: 18,  # 1.5 years default
    17: 12,  # 1 year default
    # Add more as needed
}

class StructuredSparePartsAgent:
    """
    AI Agent that provides structured responses for dashboard implementation
    """
    
    def __init__(self, api_key: str = None):
        default_key = os.getenv("OPENAI_API_KEY", "")
        self.api_key = default_key
        if self.api_key:
            openai.api_key = self.api_key
            self.use_openai = True
        else:
            self.use_openai = False
            logger.warning("No OpenAI API key found. Using fallback responses.")
        
        # Initialize AI lifespan lookup
        self.ai_lifespan_lookup = AILifespanLookup()
        
        # Load data
        self.data = self._load_all_data()
        logger.info("🤖 Structured AI Agent initialized successfully")
    
    def _load_all_data(self) -> Dict:
        """Load all data from db.json"""
        data = {}
        
        try:
            # Load all data from db.json
            with open('json/real-data-db.json', 'r') as f:
                db_data = json.load(f)
            
            # Map db.json structure to expected format
            data['equipment'] = db_data.get('rollingstock', [])
            data['spare_parts'] = db_data.get('spareparts', [])
            data['activities'] = db_data.get('activities', [])
            data['contracts'] = db_data.get('contracts', [])
            data['movements'] = db_data.get('movements', [])
            data['job_orders'] = db_data.get('joborders', [])
            data['job_order_tasks'] = db_data.get('jobordertask', [])
            data['machines'] = db_data.get('machines', [])
            data['maintenance_schedules'] = db_data.get('maintenanceSchedules', [])
            data['machine_producers'] = db_data.get('machineProducers', [])
            
            logger.info(f"✅ Loaded data from db.json: {len(data['machines'])} machines, {len(data['equipment'])} equipment, {len(data['spare_parts'])} parts, {len(data['activities'])} activities")
            
        except Exception as e:
            logger.error(f"❌ Error loading data from db.json: {e}")
            raise
        
        return data
    
    def _create_structured_prompt(self, query: str, response_format: str) -> str:
        """Create a prompt that requests structured JSON response"""
        
        # Calculate comprehensive stats
        machines_count = len(self.data['machines'])
        equipment_count = len(self.data['equipment'])
        parts_count = len(self.data['spare_parts'])
        activities_count = len(self.data['activities'])
        contracts_count = len(self.data['contracts'])
        movements_count = len(self.data['movements'])
        job_orders_count = len(self.data['job_orders'])
        maintenance_schedules_count = len(self.data['maintenance_schedules'])
        producers_count = len(self.data['machine_producers'])
        total_cost = sum(part.get('UNITPRICE', 0) * part.get('QUANTITY', 1) for part in self.data['spare_parts'])
        
        # Small sample for context
        sample_machines = self.data['machines'][:2]
        sample_equipment = self.data['equipment'][:2]
        sample_parts = self.data['spare_parts'][:3]
        sample_activities = self.data['activities'][:3]
        sample_schedules = self.data['maintenance_schedules'][:2]
        
        prompt = f"""
You are an expert AI maintenance analyst. Analyze the following comprehensive maintenance data and provide a structured response.

COMPREHENSIVE DATA SUMMARY:
- Machines: {machines_count} (equipment inventory with locations and status)
- Equipment/Rolling Stock: {equipment_count} (detailed equipment specifications)
- Spare Parts: {parts_count} (maintenance parts with costs and quantities)
- Activities: {activities_count} (service records and work orders)
- Contracts: {contracts_count} (service agreements)
- Movements: {movements_count} (equipment location tracking)
- Job Orders: {job_orders_count} (work order management)
- Maintenance Schedules: {maintenance_schedules_count} (scheduled maintenance)
- Machine Producers: {producers_count} (manufacturer information)
- Total Cost: ${total_cost:,.2f}

SAMPLE DATA:
Machines: {json.dumps(sample_machines, indent=2)}
Equipment: {json.dumps(sample_equipment, indent=2)}
Parts: {json.dumps(sample_parts, indent=2)}
Activities: {json.dumps(sample_activities, indent=2)}

QUERY: {query}

RESPONSE FORMAT: {response_format}

IMPORTANT: Respond ONLY with valid JSON in the exact format specified. Do not include any text before or after the JSON.
"""
        return prompt
    
    def ask_ai_structured(self, query: str, response_format: str) -> Dict[str, Any]:
        """Ask OpenAI for structured analysis"""
        if not self.use_openai:
            return self._fallback_structured_response(query)
        
        try:
            prompt = self._create_structured_prompt(query, response_format)
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert maintenance AI analyst. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                max_tokens=1000
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Try to parse JSON response
            try:
                return json.loads(response_text)
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON response: {response_text}")
                return self._fallback_structured_response(query)
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return self._fallback_structured_response(query)
    
    def _fallback_structured_response(self, query: str) -> Dict[str, Any]:
        """Fallback structured response when OpenAI is not available"""
        return {
            "error": "OpenAI API not available",
            "message": f"Query: {query}",
            "data": {},
            "timestamp": datetime.now().isoformat()
        }
    
    def get_dashboard_metrics(self) -> Dict[str, Any]:
        """Get structured dashboard metrics"""
        response_format = """
{
  "total_machines": number,
  "total_equipment": number,
  "total_parts": number,
  "total_activities": number,
  "total_contracts": number,
  "total_movements": number,
  "total_job_orders": number,
  "total_maintenance_schedules": number,
  "total_cost": number,
  "active_machines": number,
  "machines_in_maintenance": number,
  "parts_needing_replacement": number,
  "urgent_alerts": number,
  "upcoming_maintenance": number,
  "cost_trend": "increasing|decreasing|stable",
  "health_score": number (0-100),
  "top_expensive_parts": [
    {
      "id": number,
      "name": string,
      "cost": number,
      "quantity": number
    }
  ],
  "machines_by_location": {
    "location_name": number
  },
  "machines_by_status": {
    "status": number
  },
  "recent_activities": number,
  "predicted_failures": number,
  "maintenance_schedule_coverage": number
}
"""
        
        query = "Analyze the comprehensive maintenance data and provide dashboard metrics including machine counts, costs, health scores, maintenance schedules, and key performance indicators. Consider all data types: machines, equipment, parts, activities, contracts, movements, and schedules."
        
        return self.ask_ai_structured(query, response_format)
    
    def get_maintenance_alerts(self) -> Dict[str, Any]:
        """Get structured maintenance alerts"""
        response_format = """
{
  "urgent_alerts": [
    {
      "id": string,
      "type": "equipment_failure|part_replacement|scheduled_maintenance|cost_alert",
      "severity": "critical|high|medium|low",
      "description": string,
      "equipment_id": number,
      "location": string,
      "estimated_cost": number,
      "due_date": string,
      "recommended_action": string
    }
  ],
  "upcoming_maintenance": [
    {
      "id": string,
      "machine_id": string,
      "schedule_type": string,
      "next_date": string,
      "estimated_duration": number,
      "priority": string,
      "location": string,
      "technician_assigned": number
    }
  ],
  "parts_needing_attention": [
    {
      "part_id": number,
      "equipment_id": number,
      "part_name": string,
      "current_cost": number,
      "replacement_frequency": number,
      "last_replacement": string,
      "next_expected_replacement": string,
      "risk_level": "high|medium|low"
    }
  ],
  "equipment_health_alerts": [
    {
      "machine_id": string,
      "health_score": number,
      "status": string,
      "location": string,
      "last_maintenance": string,
      "issues": [string],
      "recommendations": [string]
    }
  ],
  "cost_alerts": [
    {
      "type": "high_cost_part|budget_exceeded|unexpected_expense",
      "description": string,
      "amount": number,
      "impact": "high|medium|low"
    }
  ],
  "summary": {
    "total_alerts": number,
    "critical_alerts": number,
    "upcoming_maintenance_count": number,
    "total_estimated_cost": number
  }
}
"""
        
        query = "Analyze the comprehensive maintenance data and generate structured alerts. Include urgent equipment issues, upcoming scheduled maintenance, parts needing replacement, equipment health concerns, and cost alerts. Consider all data types: machines, equipment, parts, activities, contracts, movements, and schedules."
        
        return self.ask_ai_structured(query, response_format)
    
    def get_equipment_analysis(self, equipment_id: int) -> Dict[str, Any]:
        """Get structured equipment analysis"""
        response_format = """
{
  "equipment_id": number,
  "health_score": number (0-100),
  "status": "healthy|warning|critical",
  "last_maintenance": string (ISO date),
  "next_maintenance": string (ISO date),
  "total_cost": number,
  "parts_used": [
    {
      "part_id": number,
      "name": string,
      "cost": number,
      "last_replaced": string (ISO date),
      "next_replacement": string (ISO date)
    }
  ],
  "maintenance_history": [
    {
      "date": string (ISO date),
      "type": string,
      "cost": number,
      "description": string
    }
  ],
  "recommendations": [
    {
      "type": string,
      "description": string,
      "priority": "high|medium|low",
      "estimated_cost": number
    }
  ]
}
"""
        
        query = f"Analyze equipment {equipment_id} health, maintenance history, and provide structured recommendations."
        
        return self.ask_ai_structured(query, response_format)
    
    def get_cost_analysis(self) -> Dict[str, Any]:
        """Get structured cost analysis"""
        response_format = """
{
  "total_cost": number,
  "monthly_trend": [
    {
      "month": string,
      "cost": number
    }
  ],
  "cost_by_category": {
    "parts": number,
    "labor": number,
    "equipment": number
  },
  "top_expensive_items": [
    {
      "id": number,
      "name": string,
      "cost": number,
      "category": string
    }
  ],
  "cost_optimization": [
    {
      "area": string,
      "current_cost": number,
      "potential_savings": number,
      "recommendation": string
    }
  ],
  "budget_status": "under_budget|over_budget|on_track"
}
"""
        
        query = "Analyze maintenance costs, identify trends, expensive items, and optimization opportunities."
        
        return self.ask_ai_structured(query, response_format)
    
    def get_predictions(self) -> Dict[str, Any]:
        """Get structured predictions"""
        response_format = """
{
  "part_replacements": [
    {
      "part_id": number,
      "equipment_id": number,
      "predicted_date": string (ISO date),
      "confidence": number (0-100),
      "estimated_cost": number,
      "reason": string
    }
  ],
  "equipment_failures": [
    {
      "equipment_id": number,
      "predicted_date": string (ISO date),
      "confidence": number (0-100),
      "severity": "low|medium|high",
      "estimated_downtime": number (hours)
    }
  ],
  "maintenance_schedule": [
    {
      "equipment_id": number,
      "maintenance_type": string,
      "scheduled_date": string (ISO date),
      "estimated_duration": number (hours),
      "estimated_cost": number
    }
  ],
  "inventory_needs": [
    {
      "part_id": number,
      "quantity_needed": number,
      "urgency": "low|medium|high",
      "estimated_cost": number
    }
  ]
}
"""
        
        query = "Predict part replacements, equipment failures, maintenance schedules, and inventory needs based on historical data."
        
        return self.ask_ai_structured(query, response_format)

    def get_machine_analysis(self, machine_id: str) -> Dict[str, Any]:
        """Get structured analysis for a specific machine"""
        response_format = """
{
  "machine_id": string,
  "machine_name": string,
  "location": string,
  "status": string,
  "producer": string,
  "health_score": number (0-100),
  "last_maintenance": string (ISO date),
  "next_maintenance": string (ISO date),
  "total_cost": number,
  "parts_count": number,
  "alerts": [
    {
      "type": "part_replacement|scheduled_maintenance|health_alert",
      "severity": "critical|high|medium|low",
      "description": string,
      "due_date": string,
      "estimated_cost": number
    }
  ],
  "parts_needing_attention": [
    {
      "part_id": number,
      "part_name": string,
      "last_replacement": string,
      "next_expected_replacement": string,
      "lifespan_months": number,
      "risk_level": "high|medium|low"
    }
  ],
  "maintenance_history": [
    {
      "date": string,
      "type": string,
      "cost": number,
      "description": string
    }
  ],
  "recommendations": [
    {
      "type": string,
      "description": string,
      "priority": "high|medium|low",
      "estimated_cost": number
    }
  ]
}
"""
        
        query = f"Analyze machine {machine_id} and provide structured analysis including health status, maintenance history, parts needing attention, and recommendations."
        
        return self.ask_ai_structured(query, response_format)

    def _calculate_part_lifespans_from_data(self) -> Dict[int, float]:
        """Calculate average lifespan (in days) for each part type from historical data."""
        part_intervals = defaultdict(list)
        
        # Group all replacements by part type
        for part in self.data['spare_parts']:
            part_id = part.get('SPAREPARTID')
            equip_id = part.get('ROLLINGSTOCKID')
            replace_date = part.get('REPLACEDATE')
            
            # Accept string or int IDs, only skip if None
            if part_id is None or equip_id is None:
                continue
            if replace_date and replace_date != "NULL":
                try:
                    dt = dateutil.parser.parse(replace_date, fuzzy=True)
                    part_intervals[part_id].append((equip_id, dt))
                except Exception:
                    continue
        
        # Calculate average interval for each part type
        part_lifespans = {}
        for part_id, replacements in part_intervals.items():
            # Group by equipment to find intervals for each equipment
            equip_replacements = defaultdict(list)
            for equip_id, dt in replacements:
                equip_replacements[equip_id].append(dt)
            
            # Calculate intervals for each equipment
            all_intervals = []
            for equip_id, dates in equip_replacements.items():
                if len(dates) >= 2:
                    dates.sort()
                    intervals = [(dates[i] - dates[i-1]).days for i in range(1, len(dates))]
                    all_intervals.extend(intervals)
            
            # Calculate average interval for this part type
            if all_intervals:
                avg_interval = sum(all_intervals) / len(all_intervals)
                part_lifespans[part_id] = avg_interval
                print(f"[DEBUG] Part {part_id}: average lifespan = {avg_interval:.1f} days ({avg_interval/365:.1f} years)")
        
        return part_lifespans
    
    def predict_part_replacements(self) -> list:
        """Predict next replacement date for each (equipment, part) pair based on historical intervals."""
        # First, calculate average lifespans from data
        part_lifespans = self._calculate_part_lifespans_from_data()
        
        # Group replacement dates by (equipment, part)
        replacements = defaultdict(list)
        total_parts = 0
        valid_dates = 0
        
        for part in self.data['spare_parts']:
            part_id = part.get('SPAREPARTID')
            equip_id = part.get('ROLLINGSTOCKID')
            replace_date = part.get('REPLACEDATE')
            total_parts += 1
            # Accept string or int IDs, only skip if None
            if part_id is None or equip_id is None:
                continue
            if replace_date and replace_date != "NULL":
                try:
                    dt = dateutil.parser.parse(replace_date, fuzzy=True)
                    replacements[(equip_id, part_id)].append(dt)
                    valid_dates += 1
                except Exception as e:
                    print(f"[DEBUG] Failed to parse date '{replace_date}' for part {part_id} on equipment {equip_id}: {e}")
                    continue
        
        print(f"[DEBUG] Total parts processed: {total_parts}")
        print(f"[DEBUG] Valid dates found: {valid_dates}")
        print(f"[DEBUG] Unique (equipment, part) pairs: {len(replacements)}")
        
        # Count pairs with different numbers of replacements
        pairs_with_1 = sum(1 for v in replacements.values() if len(v) == 1)
        pairs_with_2_plus = sum(1 for v in replacements.values() if len(v) >= 2)
        print(f"[DEBUG] Pairs with 1 replacement: {pairs_with_1}")
        print(f"[DEBUG] Pairs with 2+ replacements: {pairs_with_2_plus}")
        
        predictions = []
        now = datetime.now()
        
        for (equip_id, part_id), dates in replacements.items():
            dates.sort()
            last_replacement = dates[-1]
            
            # Ensure timezone-naive comparison
            if last_replacement.tzinfo is not None:
                last_replacement = last_replacement.replace(tzinfo=None)
            if now.tzinfo is not None:
                now = now.replace(tzinfo=None)
            
            if len(dates) >= 2:
                # Calculate average interval from historical data for this specific equipment
                intervals = [(dates[i] - dates[i-1]).days for i in range(1, len(dates))]
                avg_interval = sum(intervals) / len(intervals)
                prediction_method = "equipment_specific_history"
            else:
                # Use average lifespan for this part type across all equipment
                avg_interval = part_lifespans.get(part_id, 365)  # 1 year default if no data
                prediction_method = "part_type_average"
            
            predicted_next = last_replacement + timedelta(days=avg_interval)
            due = now >= predicted_next

            # Get AI-powered lifespan in months for this part
            lifespan_months = self.get_smart_part_lifespan(part_id)

            # Gather machine data
            machine = next((m for m in self.data['machines'] if m.get('rollingstockId') == equip_id), None)
            machine_data = {
                'machine_id': machine.get('id') if machine else None,
                'machine_name': machine.get('name') if machine else None,
                'location': machine.get('location') if machine else None,
                'status': machine.get('status') if machine else None,
                'producer': machine.get('producer') if machine else None
            } if machine else {}

            # Gather part data
            part = next((p for p in self.data['spare_parts'] if p.get('SPAREPARTID') == part_id), None)
            part_data = {
                'part_name': part.get('NOTE') if part else None,
                'description': part.get('DESCRIPTION') if part else None,
                'manufacturer': part.get('MANUFACTURER') if part else None
            } if part else {}

            predictions.append({
                "equipment_id": equip_id,
                "part_id": part_id,
                "last_replacement": last_replacement.strftime("%Y-%m-%d"),
                "predicted_next_replacement": predicted_next.strftime("%Y-%m-%d"),
                "average_interval_days": avg_interval,
                "prediction_method": prediction_method,
                "due": due,
                "lifespan_months": lifespan_months,
                "machine": machine_data,
                "part": part_data
            })
        
        return predictions

    def get_due_part_checks(self) -> list:
        """Return a list of parts on equipment that are due for check/replacement based on lifespan."""
        due_checks = []
        now = datetime.now()
        for part in self.data['spare_parts']:
            part_id = part.get('SPAREPARTID')
            equip_id = part.get('ROLLINGSTOCKID')
            replace_date = part.get('REPLACEDATE')
            if not (isinstance(part_id, int) and isinstance(equip_id, int)):
                continue  # skip if IDs are not valid integers
            
            lifespan_months = self.get_smart_part_lifespan(part_id)
            if replace_date and replace_date != "NULL" and lifespan_months:
                try:
                    dt = dateutil.parser.parse(replace_date, fuzzy=True) # Use dateutil.parser.parse
                    # Ensure both dates are timezone-naive for comparison
                    if dt.tzinfo is not None:
                        dt = dt.replace(tzinfo=None)
                    if now.tzinfo is not None:
                        now = now.replace(tzinfo=None)
                    next_check = dt + timedelta(days=lifespan_months*30)
                    expected_next_check = next_check.strftime("%Y-%m-%d")
                except Exception as e:
                    print(f"[DEBUG] Failed to parse date '{replace_date}' for part {part_id}: {e}")
                    expected_next_check = "N/A"
            else:
                expected_next_check = "N/A"
            
            # Use smart lifespan source info
            lifespan_source = "online" if self.get_online_part_lifespan(part_id) else "default"
            
            if expected_next_check != "N/A" and now >= dateutil.parser.parse(expected_next_check, fuzzy=True):
                due_checks.append({
                    "equipment_id": equip_id,
                    "part_id": part_id,
                    "last_replacement": replace_date,
                    "expected_next_check": expected_next_check,
                    "lifespan_months": lifespan_months,
                    "lifespan_source": lifespan_source
                })
        return due_checks

    def _search_part_lifespan_online(self, part_name: str, machine_name: str, manufacturer: str = None) -> Optional[int]:
        """
        Search online for part lifespan information using SerpAPI and AI analysis
        Returns lifespan in months, or None if not found
        """
        try:
            # Get SerpAPI key from environment
            serpapi_key = os.getenv("SERPAPI_API_KEY")
            if not serpapi_key:
                logger.warning("No SERPAPI_API_KEY found. Using OpenAI-only search.")
                return self._search_part_lifespan_openai_only(part_name, machine_name, manufacturer)
            
            # Create search query
            search_query = f"{part_name} lifespan maintenance replacement schedule {manufacturer or ''} {machine_name or ''}"
            
            logger.info(f"🔍 Searching online for: {search_query}")
            
            # Perform web search using SerpAPI
            search = GoogleSearch({
                "q": search_query,
                "api_key": serpapi_key,
                "num": 5  # Get top 5 results
            })
            
            results = search.get_dict()
            
            # Extract search results
            search_results = []
            if "organic_results" in results:
                for result in results["organic_results"]:
                    search_results.append({
                        "title": result.get("title", ""),
                        "snippet": result.get("snippet", ""),
                        "link": result.get("link", "")
                    })
            
            if not search_results:
                logger.warning("No search results found")
                return self._search_part_lifespan_openai_only(part_name, machine_name, manufacturer)
            
            # Use OpenAI to analyze the search results
            analysis_prompt = f"""
You are a maintenance expert. Analyze the following search results to find the lifespan of this part:

Part Name: {part_name}
Machine/Equipment: {machine_name}
Manufacturer: {manufacturer or 'Unknown'}

SEARCH RESULTS:
{json.dumps(search_results, indent=2)}

Please analyze these search results and extract:
1. The typical lifespan in months for this part
2. Any specific maintenance intervals mentioned
3. Factors that affect the lifespan

If you find specific lifespan information, respond with ONLY the number of months.
If you cannot find specific information, respond with 'UNKNOWN'.

Examples of valid responses:
- "24" (for 24 months)
- "12" (for 12 months)
- "UNKNOWN" (if no specific information found)
"""
            
            if self.use_openai:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a maintenance expert. Extract specific lifespan information from search results. Respond with only a number (months) or 'UNKNOWN'."},
                        {"role": "user", "content": analysis_prompt}
                    ],
                    temperature=0.1,
                    max_tokens=50
                )
                
                result = response.choices[0].message.content.strip()
                
                # Try to extract a number from the response
                if result.isdigit():
                    lifespan = int(result)
                    logger.info(f"✅ Found lifespan from web search: {lifespan} months")
                    return lifespan
                elif "UNKNOWN" in result.upper():
                    logger.warning("No specific lifespan found in search results")
                    return None
                else:
                    # Try to extract number from text
                    numbers = re.findall(r'\d+', result)
                    if numbers:
                        lifespan = int(numbers[0])
                        logger.info(f"✅ Extracted lifespan from text: {lifespan} months")
                        return lifespan
            
            return None
            
        except Exception as e:
            logger.error(f"Error searching for part lifespan: {e}")
            return self._search_part_lifespan_openai_only(part_name, machine_name, manufacturer)
    
    def _search_part_lifespan_openai_only(self, part_name: str, machine_name: str, manufacturer: str = None) -> Optional[int]:
        """
        Fallback method using only OpenAI (no web search)
        Returns lifespan in months, or None if not found
        """
        try:
            # Create a more sophisticated search query
            search_terms = [
                f"{part_name} lifespan",
                f"{part_name} replacement interval",
                f"{part_name} maintenance schedule",
                f"{machine_name} {part_name} lifespan",
                f"{manufacturer} {part_name} maintenance"
            ]
            
            # Use OpenAI to search and analyze online information with better prompting
            prompt = f"""
You are a maintenance expert with access to manufacturer specifications and industry databases.

SEARCH QUERY: Find the typical lifespan for this part:

Part Name: {part_name}
Machine/Equipment: {machine_name}
Manufacturer: {manufacturer or 'Unknown'}

Search Terms: {', '.join(search_terms)}

Based on your knowledge of maintenance standards and manufacturer specifications, provide:

1. The typical lifespan in months for this specific part
2. Consider the manufacturer's recommended maintenance intervals
3. Account for the specific machine/equipment type
4. Use industry standards for similar parts if manufacturer data isn't available

Examples of typical lifespans:
- Air filters: 3-12 months
- Oil filters: 3-6 months  
- Belts: 12-24 months
- Bearings: 24-60 months
- Electronic components: 12-36 months
- Seals/gaskets: 12-24 months
- Sensors: 24-48 months
- Motors: 36-72 months

Respond with ONLY a number representing the lifespan in months, or 'UNKNOWN' if you cannot determine it.
"""
            
            if self.use_openai:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a maintenance expert with deep knowledge of industrial equipment, manufacturer specifications, and maintenance standards. Provide accurate lifespan estimates based on real-world experience and manufacturer data."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    max_tokens=50
                )
                
                result = response.choices[0].message.content.strip()
                
                # Try to extract a number from the response
                if result.isdigit():
                    lifespan = int(result)
                    logger.info(f"✅ Found online lifespan: {lifespan} months")
                    return lifespan
                elif "UNKNOWN" in result.upper():
                    return None
                else:
                    # Try to extract number from text
                    numbers = re.findall(r'\d+', result)
                    if numbers:
                        lifespan = int(numbers[0])
                        logger.info(f"✅ Extracted lifespan from text: {lifespan} months")
                        return lifespan
                
                logger.warning(f"Could not parse lifespan from response: {result}")
                return None
            
            return None
            
        except Exception as e:
            logger.error(f"Error in OpenAI-only search: {e}")
            return None
    
    def _get_part_info_from_data(self, part_id: int) -> Dict[str, Any]:
        """Get part information from the database"""
        for part in self.data['spare_parts']:
            if part.get('SPAREPARTID') == part_id:
                # Find the associated machine
                machine_id = part.get('ROLLINGSTOCKID')
                machine = None
                for m in self.data['machines']:
                    if m.get('rollingstockId') == machine_id:
                        machine = m
                        break
                
                return {
                    'part_name': part.get('NOTE', f'Part {part_id}'),
                    'machine_name': machine.get('name', 'Unknown Machine') if machine else 'Unknown Machine',
                    'manufacturer': machine.get('producer', 'Unknown') if machine else 'Unknown',
                    'part_id': part_id
                }
        return None
    
    def get_online_part_lifespan(self, part_id: int) -> Optional[int]:
        """
        Get part lifespan by searching online
        Returns lifespan in months, or None if not found
        """
        part_info = self._get_part_info_from_data(part_id)
        if not part_info:
            logger.warning(f"Part {part_id} not found in database")
            return None
        
        logger.info(f"🔍 Searching online for lifespan of {part_info['part_name']} on {part_info['machine_name']}")
        
        lifespan = self._search_part_lifespan_online(
            part_info['part_name'],
            part_info['machine_name'],
            part_info['manufacturer']
        )
        
        if lifespan:
            logger.info(f"✅ Found online lifespan for part {part_id}: {lifespan} months")
        else:
            logger.warning(f"❌ No online lifespan found for part {part_id}, using default")
        
        return lifespan
    
    def get_smart_part_lifespan(self, part_id: int) -> int:
        """
        Get part lifespan using AI-powered lookup
        Returns lifespan in months
        """
        part_info = self._get_part_info_from_data(part_id)
        if not part_info:
            logger.warning(f"Part {part_id} not found in database")
            return DEFAULT_PART_LIFESPANS.get(part_id, 12)  # 12 months default
        
        logger.info(f"🔍 AI analyzing lifespan for part {part_id}: {part_info['part_name']}")
        
        # Use AI-powered lifespan lookup
        lifespan = self.ai_lifespan_lookup.get_ai_lifespan(
            part_info['part_name'],
            part_info['machine_name'],
            part_info['manufacturer']
        )
        
        if lifespan:
            logger.info(f"✅ AI found lifespan for part {part_id}: {lifespan} months")
            return lifespan
        else:
            # If AI can't determine, use default
            default_lifespan = DEFAULT_PART_LIFESPANS.get(part_id, 12)  # 12 months default
            logger.info(f"📋 AI could not determine lifespan for part {part_id}, using default: {default_lifespan} months")
            return default_lifespan
    
    def get_ai_part_lifespan(self, part_id: int) -> Optional[int]:
        """
        Get part lifespan using AI analysis only
        Returns lifespan in months, or None if not found
        """
        part_info = self._get_part_info_from_data(part_id)
        if not part_info:
            logger.warning(f"Part {part_id} not found in database")
            return None
        
        logger.info(f"🔍 AI analyzing lifespan for part {part_id}: {part_info['part_name']}")
        
        # Use AI-powered lifespan lookup
        lifespan = self.ai_lifespan_lookup.get_ai_lifespan(
            part_info['part_name'],
            part_info['machine_name'],
            part_info['manufacturer']
        )
        
        if lifespan:
            logger.info(f"✅ AI found lifespan for part {part_id}: {lifespan} months")
        else:
            logger.warning(f"❌ AI could not determine lifespan for part {part_id}")
        
        return lifespan

# CLI Interface for the Structured AI Agent
class StructuredAI_CLI:
    def __init__(self):
        self.agent = None
        self.running = True
    
    def initialize_agent(self):
        """Initialize the Structured AI Agent"""
        try:
            print("🤖 Initializing Structured AI Agent...")
            self.agent = StructuredSparePartsAgent()
            print("✅ Structured AI Agent ready!")
            return True
        except Exception as e:
            print(f"❌ Error initializing AI Agent: {e}")
            return False
    
    def show_help(self):
        """Show available commands"""
        print("""
🤖 Available Commands:

📊 Dashboard & Metrics:
  metrics          - Get comprehensive dashboard metrics
  alerts           - Get maintenance alerts
  costs            - Get cost analysis

🔍 Equipment Analysis:
  analyze <id>     - Analyze specific equipment health (e.g., analyze 1)
  equipment <id>   - Get detailed equipment analysis (e.g., equipment 1)

📈 Predictions & Forecasting:
  predict          - Get part replacement predictions
  reppred          - Get replacement predictions with detailed analysis
  due              - Get parts due for replacement/check
  lifespan <id>    - AI-powered part lifespan analysis (e.g., lifespan 3)

💬 Chat & General:
  chat <message>   - Chat with AI about maintenance
  help             - Show this help message
  quit             - Exit the application

📋 Examples:
  analyze 1        - Analyze equipment ID 1
  lifespan 3       - AI-powered lifespan analysis for part ID 3
  chat "How is the system health?"
  metrics          - Get dashboard metrics
""")
    
    def run(self):
        """Run the CLI"""
        if not self.initialize_agent():
            return
        
        print("\n🤖 Structured AI Agent CLI")
        print("Type 'help' for available commands")
        print("Type 'quit' to exit")
        print("📊 Responses are structured JSON for dashboard integration")
        
        while self.running:
            try:
                command = input("\n🤖 AI> ").strip()
                
                if not command:
                    continue
                
                parts = command.split()
                cmd = parts[0].lower()
                args = parts[1:] if len(parts) > 1 else []
                
                if cmd in ['quit', 'q', 'exit']:
                    print("👋 Goodbye!")
                    self.running = False
                
                elif cmd in ['help', 'h']:
                    self.show_help()
                
                elif cmd in ['metrics', 'm']:
                    print("\n📊 Getting dashboard metrics...")
                    metrics = self.agent.get_dashboard_metrics()
                    print(json.dumps(metrics, indent=2))
                
                elif cmd in ['alerts', 'a']:
                    print("\n🚨 Getting maintenance alerts...")
                    alerts = self.agent.get_maintenance_alerts()
                    print(json.dumps(alerts, indent=2))
                
                elif cmd in ['equipment', 'e']:
                    if args:
                        try:
                            equipment_id = int(args[0])
                            print(f"\n🔍 Getting equipment {equipment_id} analysis...")
                            analysis = self.agent.get_equipment_analysis(equipment_id)
                            print(json.dumps(analysis, indent=2))
                        except ValueError:
                            print("❌ Please provide a valid equipment ID")
                    else:
                        print("❌ Please provide equipment ID")
                
                elif cmd in ['analyze']:
                    if args:
                        machine_id = args[0]
                        print(f"\n🔍 Analyzing machine {machine_id}...")
                        analysis = self.agent.get_machine_analysis(machine_id)
                        print(json.dumps(analysis, indent=2))
                    else:
                        print("❌ Please provide a machine ID")
                
                elif cmd in ['costs', 'c']:
                    print("\n💰 Getting cost analysis...")
                    analysis = self.agent.get_cost_analysis()
                    print(json.dumps(analysis, indent=2))
                
                elif cmd in ['predictions', 'p']:
                    print("\n🔮 Getting predictions...")
                    predictions = self.agent.get_predictions()
                    print(json.dumps(predictions, indent=2))
                
                elif cmd in ['duechecks', 'due']:
                    print("\n⏰ Getting due part checks...")
                    due = self.agent.get_due_part_checks()
                    print(json.dumps(due, indent=2))
                
                elif cmd in ['replacementpredictions', 'reppred']:
                    print("\n🔁 Getting replacement predictions...")
                    preds = self.agent.predict_part_replacements()
                    print(json.dumps(preds, indent=2))
                
                elif cmd in ['lifespan']:
                    if args:
                        try:
                            part_id = int(args[0])
                            print(f"\n🔍 AI analyzing lifespan for part {part_id}...")
                            lifespan = self.agent.get_ai_part_lifespan(part_id)
                            if lifespan is not None:
                                print(f"✅ Part {part_id} AI lifespan: {lifespan} months")
                            else:
                                print(f"❌ AI could not determine lifespan for part {part_id}, using default.")
                        except ValueError:
                            print("❌ Please provide a valid part ID")
                    else:
                        print("❌ Please provide a part ID")
                
                elif cmd in ['chat']:
                    if args:
                        print(f"\n💬 Chatting with AI about: {args[0]}")
                        # This is a placeholder for a real chat function.
                        # For now, it will just return a generic response.
                        print("This is a placeholder for a real chat function.")
                        print("The AI would typically respond to your message here.")
                    else:
                        print("❌ Please provide a message to chat about.")
                
                else:
                    print(f"❌ Unknown command: {cmd}")
                    print("Type 'help' for available commands")
            
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                self.running = False
            except Exception as e:
                print(f"❌ Error: {e}")

def main():
    """Main function"""
    cli = StructuredAI_CLI()
    cli.run()

if __name__ == "__main__":
    main() 