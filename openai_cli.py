#!/usr/bin/env python3
"""
Simple CLI to test the OpenAI AI Agent
"""

from openai_ai_agent import OpenAI_SparePartsAgent

def main():
    print("🤖 Testing OpenAI AI Agent...")
    
    try:
        # Initialize the agent
        agent = OpenAI_SparePartsAgent()
        
        print("✅ Agent initialized successfully!")
        print("=" * 50)
        
        # Test system insights
        print("\n📊 Testing AI System Insights...")
        insights = agent.get_system_insights()
        print(insights)
        
        print("\n" + "=" * 50)
        
        # Test alerts
        print("\n🚨 Testing AI Alerts...")
        alerts = agent.generate_maintenance_alerts()
        print(alerts)
        
        print("\n" + "=" * 50)
        
        # Test equipment analysis
        print("\n🔍 Testing Equipment Analysis...")
        if agent.data['equipment']:
            equipment_id = agent.data['equipment'][0]['ID']
            analysis = agent.analyze_equipment_health(equipment_id)
            print(analysis)
        
        print("\n" + "=" * 50)
        
        # Test AI chat
        print("\n💬 Testing AI Chat...")
        chat_responses = [
            "How is the overall system health?",
            "Which equipment needs immediate attention?",
            "What are the most expensive maintenance items?",
            "When should I schedule the next maintenance?"
        ]
        
        for question in chat_responses:
            print(f"\nQ: {question}")
            response = agent.chat_with_ai(question)
            print(f"A: {response}")
        
        print("\n✅ OpenAI AI Agent testing completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()