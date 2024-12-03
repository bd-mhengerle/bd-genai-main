import logging
import sys

import streamlit as st
from chatbot.agent import Agent

##
class Chatbot:
    """
    A class representing a chatbot.

    Attributes:
        messages (list): A list of messages exchanged in the chat.

    Methods:
        __init__(): Initializes the Chatbot object.
        setup_streamlit(): Sets up the Streamlit application.
        submit_message(user_query: str) -> str: Submits a message to the chatbot and returns the response.
        clear(): Clears the messages stored in the session state.
        run(): Runs the chatbot application.
    """

    def __init__(self):
        self.setup_streamlit()

    def setup_streamlit(self):
        """
        Sets up the Streamlit application.
        """
        # Set up logging
        logging.basicConfig(level=logging.INFO, stream=sys.stdout)

        # Set up the Streamlit application
        st.set_page_config(page_title="My Chatbot", page_icon=":robot:")
        st.header("My Chatbot")

        # Add sidebar
        st.sidebar.markdown(
            """
            ## Important Note
            Add some important notes here
            """
        )

    def submit_message(self, user_query: str) -> str:
        """
        Submits a message to the chatbot and returns the response.

        Args:
            user_query (str): The user's query.

        Returns:
            str: The response from the chatbot.
        """
        # Display the user's query in the chat
        with st.chat_message("user"):
            st.markdown(user_query)

        # Prepare the message history for the agent
        message_history = [
            {
                "role": m["role"],
                "content": f"{m['content']}",
            }
            for m in st.session_state.messages
        ]

        # Instantiate the agent with the prepared message history, kb_ids, and tool_types
        agent = Agent(
            message_history=message_history,
            kb_ids=None,
            tool_types=None,
            embeddings_vertex_ai=True,
        )

        # Query the agent and get the output {"output": str, "metadata": list[str], "token_count": int}
        output = agent.query_agent(query=user_query)

        # Display the output in the chat
        with st.chat_message("assistant"):
            st.markdown(output)

        # Add the output to the message history
        st.session_state.messages.append({"role": "user", "content": user_query})
        st.session_state.messages.append({"role": "assistant", "content": output})

    def clear(self):
        """
        Clears the messages stored in the session state.
        """
        st.session_state["messages"] = []

    def run(self):
        """
        Runs the chatbot application.
        """
        if "messages" not in st.session_state:
            st.session_state.messages = []

        for m in st.session_state["messages"]:
            with st.chat_message(m["role"]):
                st.markdown(m["content"])

        if prompt := st.chat_input("Ask me anything..."):
            self.submit_message(prompt)

        st.button("Clear Conversation History", on_click=self.clear)


if __name__ == "__main__":
    chatbot = Chatbot()
    chatbot.run()
