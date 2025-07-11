from dotenv import load_dotenv
load_dotenv()
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from tools import save_text_to_file 


# Gemini LLM setup
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")

# Main: Ask question → get answer → auto-save it
if __name__ == "__main__":
    user_input = input("Ask me anything: ")

    print("\nThinking...\n")
    # Step 1: Get Gemini's response
    response = llm.invoke(user_input)
    # print("response:", response)
    answer = response.content.strip()

    # Step 2: Use the tool to save it
    tool_result = save_text_to_file.invoke({"text": "Q. " + user_input + "\nGemini AI. " + answer})

    # Step 3: Show result
    print(f"\nGemini's Answer:\n{answer}")
    print(f"\n{tool_result}")
