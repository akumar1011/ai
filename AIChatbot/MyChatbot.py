import streamlit as st
import ollama


# page configuration
st.set_page_config(
    page_title="my local ai assistant",
    layout="centered"
)

# sidebar controls
with st.sidebar:

    st.title("agent controls")
    st.info("this assistant runs locally using ollama")

    model_options = [
        "llama3.2"
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
st.caption(f"model: {selected_model} | status: local & secure")

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

            # call ollama with streaming enabled
            stream = ollama.chat(
                model=selected_model,
                messages=[
                    {"role": "system", "content": "you are a professional and helpful office assistant."},
                    *st.session_state.messages
                ],
                stream=True
            )

            # stream response token by token
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
            st.info("ensure ollama is running and the model is installed.")