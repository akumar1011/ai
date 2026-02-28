# MyLocalAIAgent

A simple Python-based AI agent that leverages Ollama's LLaMA 3.2 model to assist with corporate tasks. This agent provides a professional, concise interface for task completion and analysis.

## Features

- **Professional AI Assistant**: Configured with corporate-friendly tone and boundaries
- **Local AI Processing**: Uses Ollama for local LLaMA 3.2 model execution
- **Interactive Interface**: Command-line interface for task input
- **Efficient Task Processing**: Focused on accuracy and professional responses

## Prerequisites

Before running this application, ensure you have:

1. **Python 3.7+** installed on your system
2. **Ollama** installed and running locally
3. **LLaMA 3.2 model** downloaded through Ollama

### Installing Ollama

1. Visit [Ollama's official website](https://ollama.ai/) and download the installer for your operating system
2. Install Ollama following the provided instructions
3. Pull the LLaMA 3.2 model:
   ```bash
   ollama pull llama3.2
   ```

## Installation

1. Clone or download this repository
2. Navigate to the project directory
3. Install the required Python package:
   ```bash
   pip install ollama
   ```

## Usage

### Running the Agent

1. Ensure Ollama is running on your system
2. Navigate to the project directory
3. Run the agent:
   ```bash
   python ai/AIAgent/myLocalAIAgent.py
   ```
4. Enter your task when prompted
5. The agent will analyze and respond to your request

### Example Interaction

```
What task can I help you with today? Analyze the quarterly sales data and provide key insights

--- [Agent is analyzing: Analyze the quarterly sales data and provide key insights] ---

--- [AGENT RESPONSE] ---

[AI-generated response with professional analysis]
```

## Code Structure

### Main Components

- **`run_agent(task)`**: Core function that processes tasks using the Ollama model
  - Sets professional system rules for the AI
  - Sends user tasks to LLaMA 3.2 model
  - Returns processed responses

- **Main Execution Block**: Interactive command-line interface
  - Prompts user for task input
  - Calls the agent function
  - Displays formatted responses

### System Configuration

The agent is configured with the following professional guidelines:
- Professional Corporate Task Assistant identity
- Helpful, concise, and professional tone
- Focus on efficiency and accuracy

## File Structure

```
project/
├── ai/
│   └── AIAgent/
│       └── myLocalAIAgent.py
└── README.md
```

## Dependencies

- **ollama**: Python client for interacting with Ollama models

## Troubleshooting

### Common Issues

1. **"Connection Error"**: Ensure Ollama is running locally
2. **"Model not found"**: Verify LLaMA 3.2 is installed via `ollama list`
3. **Import Error**: Install the ollama package using `pip install ollama`

### Verification Steps

1. Check Ollama installation: `ollama --version`
2. Verify model availability: `ollama list`
3. Test Ollama directly: `ollama run llama3.2`

## Customization

### Modifying System Rules

To customize the agent's behavior, modify the `system_rules` variable in the `run_agent()` function:

```python
system_rules = (
    "Your custom system prompt here. "
    "Define the agent's role and behavior. "
    "Set specific guidelines and tone."
)
```

### Changing the Model

To use a different Ollama model, update the model parameter:

```python
response = ollama.chat(model='your-preferred-model', messages=[...])
```

## Contributing

Feel free to submit issues, feature requests, or pull requests to improve this AI agent.

## License

This project is open source. Please check the license file for specific terms.

## Support

For issues related to:
- **Ollama**: Visit [Ollama Documentation](https://ollama.ai/docs)
- **LLaMA Models**: Check the official model documentation
- **Python Dependencies**: Refer to the respective package documentation

---

**Note**: This agent runs entirely locally using Ollama, ensuring privacy and control over your data processing.