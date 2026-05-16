import streamlit as st
import ollama
from openai import OpenAI
from groq import Groq
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Initialize API clients
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# page configuration
st.set_page_config(
    page_title="my local ai assistant",
    layout="centered"
)

# sidebar controls
with st.sidebar:

    st.title("agent controls")
    st.info("this assistant supports ollama, openai, and groq models")

    model_options = [
        "llama3.2",  # Ollama
        "gpt-4o",  # OpenAI
        "gpt-4o-mini",  # OpenAI
        "llama-3.3-70b-versatile" # Groq
    ]

    selected_model = st.selectbox(
        "select ai model",
        model_options
    )

    # button to clear chat history
    if st.button("clear chat history"):
        st.session_state.messages = []
        st.rerun()

# initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# main ui
st.title("my private ai assistant")

# Determine provider based on selected model
if selected_model.startswith("gpt"):
    provider = "OpenAI"
elif selected_model in ["llama-3.3-70b-versatile"]:
    provider = "Groq"
else:
    provider = "Ollama (Local)"

st.caption(f"model: {selected_model} | provider: {provider}")

# display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# chat input
if prompt := st.chat_input("how can i help you today?"):

    # store user message
    st.session_state.messages.append(
        {"role": "user", "content": prompt}
    )

    with st.chat_message("user"):
        st.markdown(prompt)

    # generate assistant response
    with st.chat_message("assistant"):

        response_placeholder = st.empty()
        full_response = ""

        try:
            # Prepare messages for API call
            api_messages = [
                {"role": "system", "content": "you are a professional and helpful office assistant."},
                *st.session_state.messages
            ]

            # Route to appropriate API based on selected model
            if selected_model.startswith("gpt"):
                # OpenAI API
                stream = openai_client.chat.completions.create(
                    model=selected_model,
                    messages=api_messages,
                    stream=True
                )

                # Stream OpenAI response
                for chunk in stream:
                    if chunk.choices[0].delta.content is not None:
                        content = chunk.choices[0].delta.content
                        full_response += content
                        response_placeholder.markdown(full_response + "▌")

            elif selected_model in ["llama-3.3-70b-versatile", "mixtral-8x7b-32768"]:
                # Groq API
                stream = groq_client.chat.completions.create(
                    model=selected_model,
                    messages=api_messages,
                    stream=True
                )

                # Stream Groq response
                for chunk in stream:
                    if chunk.choices[0].delta.content is not None:
                        content = chunk.choices[0].delta.content
                        full_response += content
                        response_placeholder.markdown(full_response + "▌")

            else:
                # Ollama (local) API
                stream = ollama.chat(
                    model=selected_model,
                    messages=api_messages,
                    stream=True
                )

                # Stream Ollama response
                for chunk in stream:
                    content = chunk["message"]["content"]
                    full_response += content
                    response_placeholder.markdown(full_response + "▌")

            # finalize message
            response_placeholder.markdown(full_response)

            # store assistant response
            st.session_state.messages.append(
                {"role": "assistant", "content": full_response}
            )

        except Exception as e:
            st.error(f"error: {e}")
            if selected_model.startswith("gpt"):
                st.info("ensure your OpenAI API key is valid and set in .env")
            elif selected_model in ["llama-3.3-70b-versatile"]:
                st.info("ensure your Groq API key is valid and set in .env")
            else:
                st.info("ensure ollama is running and the model is installed.")