# AI Agent for Predictive Maintenance & Notifications

This is an AI agent designed to predict maintenance needs and send notifications to users about specific parts that need to be changed or maintained.

## 🚀 Quick Start

### Prerequisites

1. **Python 3.7+** installed on your system
2. **OpenAI API Key** (optional but recommended for full AI capabilities)

### Installation

1. **Install required dependencies:**
```bash
pip install openai
```

2. **Set up your OpenAI API key (optional):**
```bash
export OPENAI_API_KEY="your-openai-api-key-here"
```

Or add it to your `.bashrc` or `.zshrc`:
```bash
echo 'export OPENAI_API_KEY="your-openai-api-key-here"' >> ~/.bashrc
source ~/.bashrc
```

## 🎯 How to Run

### Option 1: Interactive CLI (Recommended for testing)

Run the interactive command-line interface:

```bash
python openai_ai_agent.py
```

This will start an interactive session where you can:
- Get AI-generated system insights
- Generate maintenance alerts
- Analyze specific equipment health
- Predict part replacements
- Chat with the AI about maintenance questions
- Analyze costs and scheduling

### Option 2: Quick Test Script

Run the automated test script:

```bash
python openai_cli.py
```

This will run a series of automated tests to verify all AI agent functionality.

## 📊 Available Commands (Interactive CLI)

When running the interactive CLI, you can use these commands:

| Command | Description | Example |
|---------|-------------|---------|
| `help` or `h` | Show help information | `help` |
| `insights` or `i` | Get AI-generated system insights | `insights` |
| `alerts` or `a` | Get AI-generated maintenance alerts | `alerts` |
| `equipment <id>` or `e <id>` | AI analysis of specific equipment | `equipment 1` |
| `parts <equipment_id> <part_id>` | AI prediction for part replacement | `parts 1 4079` |
| `chat <message>` | Chat with AI about anything | `chat "Which equipment needs maintenance?"` |
| `costs` | AI analysis of maintenance costs | `costs` |
| `schedule [equipment_id]` | AI maintenance scheduling prediction | `schedule` or `schedule 1` |
| `quit`, `q`, or `exit` | Exit the application | `quit` |

## 🔧 Project Structure

```
ai-agent-hackathon/
├── openai_ai_agent.py    # Main AI agent implementation
├── openai_cli.py         # CLI test script
├── json/                 # Data files
│   ├── rollingstock.json     # Equipment data
│   ├── spareparts.json       # Spare parts data
│   ├── activities.json       # Maintenance activities
│   ├── contracts.json        # Contract information
│   ├── movements.json        # Movement data
│   └── joborders.json        # Job order data
└── README.md             # This file
```

## 🤖 AI Agent Features

### Core Capabilities

1. **System Insights**: Comprehensive analysis of overall system health
2. **Maintenance Alerts**: AI-generated alerts for urgent maintenance needs
3. **Equipment Analysis**: Detailed health assessment for specific equipment
4. **Part Replacement Prediction**: Predict when parts need replacement
5. **Cost Analysis**: Analyze maintenance costs and optimization opportunities
6. **Maintenance Scheduling**: Predict optimal maintenance schedules
7. **AI Chat**: Natural language interface for maintenance questions

### Data Analysis

The agent analyzes:
- **Equipment data** (rolling stock information)
- **Spare parts usage** and inventory
- **Maintenance activities** and history
- **Cost patterns** and trends
- **Performance metrics** and health indicators

## 🔑 Configuration

### Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key for full AI capabilities
  - If not set, the agent will use fallback responses
  - Recommended for best results

### Data Files

The agent automatically loads these JSON files from the `json/` directory:
- `rollingstock.json` - Equipment information
- `spareparts.json` - Spare parts data
- `activities.json` - Maintenance activities
- `contracts.json` - Contract data
- `movements.json` - Movement tracking
- `joborders.json` - Job order information

## 🚨 Troubleshooting

### Common Issues

1. **"No OpenAI API key found"**
   - Set your `OPENAI_API_KEY` environment variable
   - The agent will still work with fallback responses

2. **"Error loading data"**
   - Ensure all JSON files are in the `json/` directory
   - Check file permissions

3. **"Module not found" errors**
   - Install required dependencies: `pip install openai`

### Getting Help

- Run `help` in the interactive CLI for command reference
- Check the console output for error messages
- Ensure all data files are present and readable

## 🎯 Use Cases

This AI agent is perfect for:

- **Maintenance Managers**: Get AI insights on equipment health
- **Technicians**: Predict when parts need replacement
- **Operations Teams**: Optimize maintenance schedules
- **Management**: Analyze costs and efficiency
- **Planners**: Strategic maintenance planning

## 🔮 Future Enhancements

Potential improvements:
- Web interface for easier access
- Email/SMS notifications
- Integration with maintenance management systems
- Real-time data feeds
- Mobile app for field technicians

---