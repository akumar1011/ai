from langchain_core.tools import tool
from datetime import datetime 
import os  


# Tool: Save Gemini's answer to a file
@tool
def save_text_to_file(text: str, filename: str = "response.txt") -> str:
    """
    Saves the given data to a file in the same directory as this script.
    """
    print("Inside save_to_txt function - filename is:", filename)

    # Get this script's directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, filename)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_text = f"--- Research Output ---\nTimestamp: {timestamp}\n\n{text}\n\n"

    try:
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(formatted_text)
        return f"Text successfully saved to '{file_path}'"
    except Exception as e:
        return f"Failed to save text: {str(e)}"