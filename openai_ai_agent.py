import json
import openai
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

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
        """Load all JSON data files"""
        data = {}
        
        try:
            # Load rolling stock (equipment)
            with open('rollingstock.json', 'r') as f:
                data['equipment'] = json.load(f)
            
            # Load spare parts
            with open('spareparts.json', 'r') as f:
                data['spare_parts'] = json.load(f)
            
            # Load activities
            with open('activities.json', 'r') as f:
                data['activities'] = json.load(f)
            
            # Load other data files if they exist
            try:
                with open('contracts.json', 'r') as f:
                    data['contracts'] = json.load(f)
            except:
                data['contracts'] = []
            
            try:
                with open('movements.json', 'r') as f:
                    data['movements'] = json.load(f)
            except:
                data['movements'] = []
            
            try:
                with open('jobordertask.json', 'r') as f:
                    data['job_orders'] = json.load(f)
            except:
                data['job_orders'] = []
            
            logger.info(f"✅ Loaded data: {len(data['equipment'])} equipment, {len(data['spare_parts'])} parts, {len(data['activities'])} activities")
            
        except Exception as e:
            logger.error(f"❌ Error loading data: {e}")
            raise
        
        return data
    
    def _create_ai_prompt(self, query: str, context: str = "") -> str:
        """Create a comprehensive prompt for OpenAI"""
        
        # Prepare data summary
        equipment_count = len(self.data['equipment'])
        parts_count = len(self.data['spare_parts'])
        activities_count = len(self.data['activities'])
        
        # Calculate some basic stats for context
        total_cost = sum(part.get('UNITPRICE', 0) * part.get('QUANTITY', 1) for part in self.data['spare_parts'])
        
        # Sample some data for analysis (limit to avoid token limits)
        sample_equipment = self.data['equipment'][:10]  # First 10 equipment
        sample_parts = self.data['spare_parts'][:20]   # First 20 parts
        sample_activities = self.data['activities'][:15]  # First 15 activities
        
        prompt = f"""
You are an expert AI maintenance analyst specializing in spare parts management and equipment health.

CONTEXT:
- Total Equipment: {equipment_count}
- Total Spare Parts Used: {parts_count}
- Total Maintenance Activities: {activities_count}
- Total Maintenance Cost: ${total_cost:,.2f}

SAMPLE DATA:
Equipment (first 10):
{json.dumps(sample_equipment, indent=2)}

Spare Parts (first 20):
{json.dumps(sample_parts, indent=2)}

Maintenance Activities (first 15):
{json.dumps(sample_activities, indent=2)}

USER QUERY: {query}

{context}

Please provide a comprehensive, intelligent analysis based on this data. Include:
1. Specific insights relevant to the query
2. Data-driven recommendations
3. Risk assessments if applicable
4. Actionable next steps
5. Confidence level in your analysis

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
                temperature=0.3,
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
        # Find equipment data
        equipment = next((e for e in self.data['equipment'] if e.get('ID') == equipment_id), None)
        if not equipment:
            return f"Equipment {equipment_id} not found in the data."
        
        # Get related parts and activities
        equipment_parts = [p for p in self.data['spare_parts'] if p.get('JOBORDERTASKID') == equipment_id]
        equipment_activities = [a for a in self.data['activities'] if a.get('ROLLINGSTOCKID') == equipment_id]
        
        context = f"""
SPECIFIC EQUIPMENT ANALYSIS:
Equipment ID: {equipment_id}
Equipment Details: {json.dumps(equipment, indent=2)}
Related Parts: {json.dumps(equipment_parts, indent=2)}
Related Activities: {json.dumps(equipment_activities, indent=2)}
"""
        
        query = f"Analyze the health and maintenance status of equipment {equipment_id}. Provide a detailed assessment including health score, risk level, maintenance recommendations, and any urgent issues that need attention."
        
        return self.ask_ai(query, context)
    
    def predict_part_replacement(self, equipment_id: int, part_id: int) -> str:
        """AI prediction for part replacement"""
        # Find part data
        part_data = [p for p in self.data['spare_parts'] if p.get('SPAREPARTID') == part_id and p.get('JOBORDERTASKID') == equipment_id]
        
        if not part_data:
            return f"No data found for part {part_id} on equipment {equipment_id}."
        
        context = f"""
PART REPLACEMENT ANALYSIS:
Equipment ID: {equipment_id}
Part ID: {part_id}
Part History: {json.dumps(part_data, indent=2)}
"""
        
        query = f"Predict when part {part_id} on equipment {equipment_id} needs replacement. Analyze the replacement history, calculate lifecycle patterns, and provide a prediction with confidence level and risk assessment."
        
        return self.ask_ai(query, context)
    
    def generate_maintenance_alerts(self) -> str:
        """AI-generated maintenance alerts"""
        # Get recent activities and parts
        recent_activities = self.data['activities'][:50]  # Last 50 activities
        recent_parts = self.data['spare_parts'][:50]     # Last 50 parts
        
        context = f"""
ALERT GENERATION DATA:
Recent Activities: {json.dumps(recent_activities, indent=2)}
Recent Parts: {json.dumps(recent_parts, indent=2)}
"""
        
        query = "Generate maintenance alerts based on the data. Identify urgent issues, equipment that needs attention, parts that need replacement, and any other critical maintenance needs. Prioritize by severity and provide specific recommendations."
        
        return self.ask_ai(query, context)
    
    def get_system_insights(self) -> str:
        """AI-generated system insights"""
        # Prepare summary data
        equipment_summary = {
            "total": len(self.data['equipment']),
            "active": len([e for e in self.data['equipment'] if e.get('ACTIVE', 1) == 1]),
            "types": len(set(e.get('MACHINETYPE', 0) for e in self.data['equipment']))
        }
        
        parts_summary = {
            "total": len(self.data['spare_parts']),
            "total_cost": sum(p.get('UNITPRICE', 0) * p.get('QUANTITY', 1) for p in self.data['spare_parts']),
            "avg_cost": sum(p.get('UNITPRICE', 0) * p.get('QUANTITY', 1) for p in self.data['spare_parts']) / len(self.data['spare_parts']) if self.data['spare_parts'] else 0
        }
        
        activities_summary = {
            "total": len(self.data['activities']),
            "technical": len([a for a in self.data['activities'] if a.get('TECHNICAL', 0) == 1]),
            "avg_duration": sum(a.get('DURATION', 0) for a in self.data['activities']) / len(self.data['activities']) if self.data['activities'] else 0
        }
        
        context = f"""
SYSTEM OVERVIEW:
Equipment Summary: {json.dumps(equipment_summary, indent=2)}
Parts Summary: {json.dumps(parts_summary, indent=2)}
Activities Summary: {json.dumps(activities_summary, indent=2)}
"""
        
        query = "Provide comprehensive system insights including overall health assessment, cost analysis, maintenance efficiency, risk areas, and strategic recommendations for improvement."
        
        return self.ask_ai(query, context)
    
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