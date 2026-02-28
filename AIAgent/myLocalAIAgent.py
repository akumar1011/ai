import ollama

def run_agent(task):
    print(f"\n--- [Agent is analyzing: {task}] ---")
    
    # Setting the Agent's identity and boundaries
    system_rules = (
        "You are a professional Corporate Task Assistant. "
        "Your tone is helpful, concise, and professional. "
        "Focus on efficiency and accuracy."
    )

    # Sending the task to the Ollama model
    response = ollama.chat(model='llama3.2', messages=[
        {'role': 'system', 'content': system_rules},
        {'role': 'user', 'content': task},
    ])

    return response['message']['content']

if __name__ == "__main__":
    # Prompting the user for input
    user_input = input("What task can I help you with today? ")
    
    # Running the agent
    agent_output = run_agent(user_input)
    
    print("\n--- [AGENT RESPONSE] ---\n")
    print(agent_output)