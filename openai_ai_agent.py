import json
import openai
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
from dotenv import load_dotenv
import requests
import re
from serpapi import GoogleSearch
from enhanced_lifespan_lookup import EnhancedLifespanLookup

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OpenAI_SparePartsAgent:
    """
    AI Agent that uses OpenAI to analyze spare parts data and provide intelligent insights
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
        
        # Load data
        self.data = self._load_all_data()
        logger.info("🤖 OpenAI AI Agent initialized successfully")
    
    def _load_all_data(self) -> Dict:
        """Load all data from db.json"""
        data = {}
        
        try:
            # Load all data from updated_db.json
            with open('json/updated_db.json', 'r') as f:
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
    
    def _create_ai_prompt(self, query: str, context: str = "") -> str:
        """Create a comprehensive prompt for OpenAI"""
        
        # Prepare data summary with all available data types
        machines_count = len(self.data['machines'])
        equipment_count = len(self.data['equipment'])
        parts_count = len(self.data['spare_parts'])
        activities_count = len(self.data['activities'])
        contracts_count = len(self.data['contracts'])
        movements_count = len(self.data['movements'])
        job_orders_count = len(self.data['job_orders'])
        maintenance_schedules_count = len(self.data['maintenance_schedules'])
        producers_count = len(self.data['machine_producers'])
        
        # Calculate some basic stats for context
        total_cost = sum(part.get('UNITPRICE', 0) * part.get('QUANTITY', 1) for part in self.data['spare_parts'])
        
        # Sample some data for analysis (limit to avoid token limits)
        sample_machines = self.data['machines'][:3]  # First 3 machines
        sample_equipment = self.data['equipment'][:2]  # First 2 equipment
        sample_parts = self.data['spare_parts'][:3]   # First 3 parts
        sample_activities = self.data['activities'][:3]  # First 3 activities
        sample_schedules = self.data['maintenance_schedules'][:2]  # First 2 schedules
        sample_producers = self.data['machine_producers'][:2]  # First 2 producers
        
        prompt = f"""
You are an expert AI maintenance analyst specializing in spare parts management, equipment health, and predictive maintenance.

COMPREHENSIVE DATA CONTEXT:
- Machines: {machines_count} (equipment inventory with locations and status)
- Equipment/Rolling Stock: {equipment_count} (detailed equipment specifications)
- Spare Parts Used: {parts_count} (maintenance parts with costs and quantities)
- Maintenance Activities: {activities_count} (service records and work orders)
- Contracts: {contracts_count} (service agreements and relationships)
- Equipment Movements: {movements_count} (tracking equipment locations)
- Job Orders: {job_orders_count} (work order management)
- Maintenance Schedules: {maintenance_schedules_count} (scheduled maintenance)
- Machine Producers: {producers_count} (manufacturer information)
- Total Maintenance Cost: ${total_cost:,.2f}

SAMPLE DATA:
Machines (equipment inventory):
{json.dumps(sample_machines, indent=2)}

Equipment/Rolling Stock (detailed specs):
{json.dumps(sample_equipment, indent=2)}

Spare Parts (maintenance parts):
{json.dumps(sample_parts, indent=2)}

Maintenance Activities (service records):
{json.dumps(sample_activities, indent=2)}

Maintenance Schedules (scheduled work):
{json.dumps(sample_schedules, indent=2)}

Machine Producers (manufacturers):
{json.dumps(sample_producers, indent=2)}

USER QUERY: {query}

{context}

Please provide a comprehensive, intelligent analysis based on this comprehensive maintenance data. Include:
1. Specific insights relevant to the query using all available data types
2. Data-driven recommendations considering equipment health, costs, and schedules
3. Risk assessments based on maintenance history and schedules
4. Actionable next steps with priority levels
5. Confidence level in your analysis
6. Cross-references between machines, equipment, parts, and activities where relevant

Respond in a clear, professional manner suitable for a maintenance manager.
"""
        return prompt
    
    def ask_ai(self, query: str, context: str = "") -> str:
        """Ask OpenAI for analysis"""
        if not self.use_openai:
            return self._fallback_response(query)
        
        try:
            prompt = self._create_ai_prompt(query, context)
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert maintenance AI analyst with deep knowledge of spare parts management, equipment health monitoring, and predictive maintenance. Provide detailed, actionable insights based on the data provided."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                max_tokens=1000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return self._fallback_response(query)
    
    def _fallback_response(self, query: str) -> str:
        """Fallback response when OpenAI is not available"""
        return f"I understand you're asking about: {query}\n\nUnfortunately, I cannot provide detailed AI analysis without OpenAI access. Please set your OPENAI_API_KEY environment variable to enable full AI capabilities.\n\nI can still help with basic data analysis if needed."
    
    def analyze_equipment_health(self, equipment_id: int) -> str:
        """AI analysis of specific equipment health"""
        # Find equipment data (check both machines and rolling stock)
        machine = next((m for m in self.data['machines'] if m.get('id') == str(equipment_id)), None)
        equipment = next((e for e in self.data['equipment'] if e.get('ID') == equipment_id), None)
        
        if not machine and not equipment:
            return f"Equipment {equipment_id} not found in the data."
        
        # Get related parts and activities
        equipment_parts = [p for p in self.data['spare_parts'] if p.get('ROLLINGSTOCKID') == equipment_id]
        equipment_activities = [a for a in self.data['activities'] if a.get('ROLLSTOCKCROSSID') == equipment_id]
        equipment_schedules = [s for s in self.data['maintenance_schedules'] if s.get('rollingstockId') == equipment_id]
        equipment_movements = [m for m in self.data['movements'] if m.get('ROLLSTOCKID') == equipment_id]
        
        context = f"""
SPECIFIC EQUIPMENT ANALYSIS:
Equipment ID: {equipment_id}

Machine Data: {json.dumps(machine, indent=2) if machine else "Not found"}
Equipment Details: {json.dumps(equipment, indent=2) if equipment else "Not found"}
Related Parts: {json.dumps(equipment_parts, indent=2)}
Related Activities: {json.dumps(equipment_activities, indent=2)}
Maintenance Schedules: {json.dumps(equipment_schedules, indent=2)}
Equipment Movements: {json.dumps(equipment_movements, indent=2)}
"""
        
        query = f"Analyze the health and maintenance status of equipment {equipment_id}. Provide a detailed assessment including health score, risk level, maintenance recommendations, and any urgent issues that need attention. Consider the equipment's location, maintenance history, scheduled maintenance, and any recent movements."
        
        return self.ask_ai(query, context)
    
    def predict_part_replacement(self, equipment_id: int, part_id: int) -> str:
        """AI prediction for part replacement"""
        # Find part data
        part_data = [p for p in self.data['spare_parts'] if p.get('SPAREPARTID') == part_id and p.get('ROLLINGSTOCKID') == equipment_id]
        
        if not part_data:
            return f"No data found for part {part_id} on equipment {equipment_id}."
        
        # Get related equipment and maintenance data
        equipment = next((e for e in self.data['equipment'] if e.get('ID') == equipment_id), None)
        machine = next((m for m in self.data['machines'] if m.get('rollingstockId') == equipment_id), None)
        maintenance_schedules = [s for s in self.data['maintenance_schedules'] if s.get('rollingstockId') == equipment_id]
        
        context = f"""
PART REPLACEMENT ANALYSIS:
Equipment ID: {equipment_id}
Part ID: {part_id}
Part History: {json.dumps(part_data, indent=2)}
Equipment Details: {json.dumps(equipment, indent=2) if equipment else "Not found"}
Machine Data: {json.dumps(machine, indent=2) if machine else "Not found"}
Maintenance Schedules: {json.dumps(maintenance_schedules, indent=2)}
"""
        
        query = f"Predict when part {part_id} on equipment {equipment_id} needs replacement. Analyze the replacement history, calculate lifecycle patterns, consider maintenance schedules, and provide a prediction with confidence level and risk assessment."
        
        return self.ask_ai(query, context)
    
    def generate_maintenance_alerts(self) -> str:
        """AI-generated maintenance alerts"""
        # Get recent activities, parts, and schedules
        recent_activities = self.data['activities'][:50]  # Last 50 activities
        recent_parts = self.data['spare_parts'][:50]  # Last 50 parts
        maintenance_schedules = self.data['maintenance_schedules']
        machines = self.data['machines']
        
        # Calculate some basic stats
        urgent_activities = [a for a in recent_activities if a.get('PRIORITY', 0) >= 2]
        high_cost_parts = [p for p in recent_parts if p.get('UNITPRICE', 0) > 200]
        upcoming_schedules = [s for s in maintenance_schedules if s.get('nextMaintenanceDate')]
        
        context = f"""
MAINTENANCE ALERTS ANALYSIS:
Recent Activities: {json.dumps(recent_activities[:10], indent=2)}
Recent Parts: {json.dumps(recent_parts[:10], indent=2)}
Maintenance Schedules: {json.dumps(maintenance_schedules, indent=2)}
Machines: {json.dumps(machines[:5], indent=2)}

STATS:
- Urgent Activities: {len(urgent_activities)}
- High Cost Parts: {len(high_cost_parts)}
- Upcoming Schedules: {len(upcoming_schedules)}
"""
        
        query = "Generate comprehensive maintenance alerts based on the data. Identify urgent issues, upcoming scheduled maintenance, high-cost parts that need attention, equipment health concerns, and any patterns that suggest preventive actions are needed."
        
        return self.ask_ai(query, context)
    
    def get_system_insights(self) -> str:
        """Get comprehensive system insights"""
        query = "Provide a comprehensive analysis of the maintenance system including equipment health, cost analysis, efficiency metrics, risk assessment, and actionable recommendations."
        return self.ask_ai(query)
    
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
            # Use OpenAI to search and analyze online information
            prompt = f"""
You are a maintenance expert. Search for information about the lifespan of this part:

Part Name: {part_name}
Machine/Equipment: {machine_name}
Manufacturer: {manufacturer or 'Unknown'}

Please provide:
1. The typical lifespan in months for this part
2. The source of this information (manufacturer specs, industry standards, etc.)
3. Any factors that might affect the lifespan

If you cannot find specific information, provide a reasonable estimate based on similar parts.

Respond with ONLY a number representing the lifespan in months, or 'UNKNOWN' if you cannot determine it.
"""
            
            if self.use_openai:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a maintenance expert. Provide accurate lifespan information based on manufacturer specifications and industry standards."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    max_tokens=100
                )
                
                result = response.choices[0].message.content.strip()
                
                # Try to extract a number from the response
                if result.isdigit():
                    return int(result)
                elif "UNKNOWN" in result.upper():
                    return None
                else:
                    # Try to extract number from text
                    numbers = re.findall(r'\d+', result)
                    if numbers:
                        return int(numbers[0])
            
            return None
            
        except Exception as e:
            logger.error(f"Error in OpenAI-only search: {e}")
            return None
    
    def get_online_part_lifespan(self, part_id: int) -> Optional[int]:
        """
        Get part lifespan using enhanced lookup system
        Returns lifespan in months, or None if not found
        """
        # Import the simple lifespan lookup
        try:
            from simple_lifespan_solution import SimpleLifespanLookup
            lookup = SimpleLifespanLookup()
        except ImportError:
            logger.warning("Simple lifespan lookup not available, using fallback")
            return self._get_fallback_lifespan(part_id)
        
        # Find part information from data
        part_info = None
        for part in self.data['spare_parts']:
            if part.get('SPAREPARTID') == part_id:
                # Find the associated machine
                machine_id = part.get('ROLLINGSTOCKID')
                machine = None
                for m in self.data['machines']:
                    if m.get('rollingstockId') == machine_id:
                        machine = m
                        break
                
                part_info = {
                    'part_name': part.get('NOTE', f'Part {part_id}'),
                    'machine_name': machine.get('name', 'Unknown Machine') if machine else 'Unknown Machine',
                    'manufacturer': machine.get('producer', 'Unknown') if machine else 'Unknown',
                    'part_id': part_id
                }
                break
        
        if not part_info:
            logger.warning(f"Part {part_id} not found in database")
            return None
        
        logger.info(f"🔍 Looking up lifespan for {part_info['part_name']} on {part_info['machine_name']}")
        
        # Use enhanced lookup
        lifespan = lookup.get_smart_lifespan(
            part_info['part_name'],
            part_info['machine_name'],
            part_info['manufacturer']
        )
        
        if lifespan:
            logger.info(f"✅ Found lifespan for part {part_id}: {lifespan} months")
        else:
            logger.warning(f"❌ No lifespan found for part {part_id}, using fallback")
            lifespan = self._get_fallback_lifespan(part_id)
        
        return lifespan
    
    def _get_fallback_lifespan(self, part_id: int) -> int:
        """Fallback lifespan using default values"""
        # Default lifespans for common parts
        default_lifespans = {
            3: 12,   # Air filter - 1 year
            4: 24,   # Oil filter - 2 years
            9: 6,    # Fuel filter - 6 months
            5: 18,   # Belt - 1.5 years
            6: 12,   # Bearing - 1 year
            7: 24,   # Seal - 2 years
            8: 18,   # Sensor - 1.5 years
            10: 12,  # Motor - 1 year
            11: 6,   # Battery - 6 months
            12: 24,  # Screen - 2 years
            13: 18,  # Component - 1.5 years
            14: 12,  # Part - 1 year
            15: 24,  # Assembly - 2 years
            16: 18,  # Module - 1.5 years
            17: 12,  # Unit - 1 year
        }
        
        return default_lifespans.get(part_id, 12)  # Default 12 months
    
    def chat_with_ai(self, user_message: str) -> str:
        """General AI chat for any maintenance-related questions"""
        return self.ask_ai(user_message)
    
    def analyze_costs(self) -> str:
        """AI analysis of maintenance costs"""
        context = f"""
COST ANALYSIS DATA:
All Parts: {json.dumps(self.data['spare_parts'][:30], indent=2)}  # First 30 parts for analysis
"""
        
        query = "Analyze the maintenance costs, identify cost trends, expensive parts, cost optimization opportunities, and provide recommendations for cost management."
        
        return self.ask_ai(query, context)
    
    def predict_maintenance_schedule(self, equipment_id: int = None) -> str:
        """AI prediction for maintenance scheduling"""
        if equipment_id:
            # Specific equipment
            equipment_activities = [a for a in self.data['activities'] if a.get('ROLLINGSTOCKID') == equipment_id]
            context = f"""
MAINTENANCE SCHEDULING FOR EQUIPMENT {equipment_id}:
Activities: {json.dumps(equipment_activities, indent=2)}
"""
            query = f"Predict the optimal maintenance schedule for equipment {equipment_id}. Analyze activity patterns, recommend maintenance intervals, and identify the best timing for preventive maintenance."
        else:
            # System-wide
            context = f"""
SYSTEM MAINTENANCE SCHEDULING:
All Activities: {json.dumps(self.data['activities'][:50], indent=2)}  # First 50 activities
"""
            query = "Analyze the overall maintenance scheduling patterns, identify optimal maintenance intervals for different equipment types, and provide a comprehensive maintenance scheduling strategy."
        
        return self.ask_ai(query, context)

# CLI Interface for the OpenAI AI Agent
class OpenAI_AI_CLI:
    def __init__(self):
        self.agent = None
        self.running = True
    
    def initialize_agent(self):
        """Initialize the OpenAI AI Agent"""
        try:
            print("🤖 Initializing OpenAI AI Agent...")
            self.agent = OpenAI_SparePartsAgent()
            print("✅ OpenAI AI Agent ready!")
            return True
        except Exception as e:
            print(f"❌ Error initializing AI Agent: {e}")
            return False
    
    def show_help(self):
        """Show help information"""
        help_text = """
🤖 OpenAI AI Agent - Command Line Interface

Available Commands:
  help, h                    - Show this help message
  insights, i               - Get AI-generated system insights
  alerts, a                 - Get AI-generated maintenance alerts
  equipment <id>, e <id>    - AI analysis of specific equipment
  parts <equipment_id> <part_id> - AI prediction for part replacement
  chat <message>            - Chat with AI about anything
  costs                     - AI analysis of maintenance costs
  schedule [equipment_id]   - AI maintenance scheduling prediction
  quit, q, exit            - Exit the application

Examples:
  equipment 1               - AI analysis of equipment 1
  chat "Which equipment needs maintenance?"
  parts 1 4079             - AI prediction for part 4079 on equipment 1
  schedule                  - System-wide maintenance scheduling
  costs                     - Cost analysis and optimization
        """
        print(help_text)
    
    def run(self):
        """Run the CLI"""
        if not self.initialize_agent():
            return
        
        print("\n🤖 OpenAI AI Agent CLI")
        print("Type 'help' for available commands")
        print("Type 'quit' to exit")
        print("💡 Set OPENAI_API_KEY environment variable for full AI capabilities")
        
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
                
                elif cmd in ['insights', 'i']:
                    print("\n📊 Generating AI insights...")
                    insights = self.agent.get_system_insights()
                    print(insights)
                
                elif cmd in ['alerts', 'a']:
                    print("\n🚨 Generating AI alerts...")
                    alerts = self.agent.generate_maintenance_alerts()
                    print(alerts)
                
                elif cmd in ['equipment', 'e']:
                    if args:
                        try:
                            equipment_id = int(args[0])
                            print(f"\n🔍 AI Analysis of Equipment {equipment_id}...")
                            analysis = self.agent.analyze_equipment_health(equipment_id)
                            print(analysis)
                        except ValueError:
                            print("❌ Please provide a valid equipment ID")
                    else:
                        print("❌ Please provide equipment ID")
                
                elif cmd == 'parts':
                    if len(args) >= 2:
                        try:
                            equipment_id = int(args[0])
                            part_id = int(args[1])
                            print(f"\n🔧 AI Prediction for Part {part_id} on Equipment {equipment_id}...")
                            prediction = self.agent.predict_part_replacement(equipment_id, part_id)
                            print(prediction)
                        except ValueError:
                            print("❌ Please provide valid equipment ID and part ID")
                    else:
                        print("❌ Please provide equipment ID and part ID")
                
                elif cmd == 'chat':
                    if args:
                        message = ' '.join(args)
                        print(f"\n💬 AI Response:")
                        response = self.agent.chat_with_ai(message)
                        print(response)
                    else:
                        print("❌ Please provide a message")
                
                elif cmd == 'costs':
                    print("\n💰 AI Cost Analysis...")
                    analysis = self.agent.analyze_costs()
                    print(analysis)
                
                elif cmd == 'schedule':
                    if args:
                        try:
                            equipment_id = int(args[0])
                            print(f"\n📅 AI Maintenance Schedule for Equipment {equipment_id}...")
                            schedule = self.agent.predict_maintenance_schedule(equipment_id)
                            print(schedule)
                        except ValueError:
                            print("❌ Please provide a valid equipment ID")
                    else:
                        print("\n📅 AI System-wide Maintenance Schedule...")
                        schedule = self.agent.predict_maintenance_schedule()
                        print(schedule)
                
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
    cli = OpenAI_AI_CLI()
    cli.run()

if __name__ == "__main__":
    main() 