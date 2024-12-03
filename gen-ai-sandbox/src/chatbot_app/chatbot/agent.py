"""
This module implements an AI-powered chatbot agent using various tools and models.

The Agent class is responsible for handling user queries, managing conversation history,
and utilizing different tools like RAG, summarization, and Pinecone for information retrieval.
"""

import logging
import sys
from typing import List, Dict, Any, Optional, Set

import retrying
from llama_index.core import Settings
from llama_index.core.llms import ChatMessage
from llama_index.core.chat_engine import SimpleChatEngine
from llama_index.core.agent import ReActAgent
from llama_index.core.tools import QueryEngineTool, ToolMetadata

from .memory import create_memory_buffer
from .settings import settings_embed_model, settings_llm, LlmIds, count_tokens
from .common import create_metadata_filters

from .tools.rag.pdf_context_retrieval.config import (
    PDF_INDEX_DESCRIPTION,
    PDF_INDEX_LOCATION,
)

from .tools.summarization.pdf_context_retrieval.config import (
    PDF_INDEX_DESCRIPTION_SUMMARIZATION,
    PDF_INDEX_LOCATION_SUMMARIZATION,
)

from .tools.pinecone.pinecone_context_retrieval.config import (
    INDEX_DESCRIPTION_PINECONE,
    INDEX_LOCATION_PINECONE,
)

from .common import RagTool, SummarizationTool, PineconeTool


logging.basicConfig(level=logging.INFO, stream=sys.stdout)


class Agent:
    """
    Represents a chatbot agent capable of answering queries using various tools and models.

    This class handles the initialization of the agent, loading of tools, and query processing.
    It can use different knowledge bases and tool types based on the configuration.

    Attributes:
        message_history (List[ChatMessage]): The conversation history.
        kb_ids (Optional[List[str]]): IDs of the knowledge bases to use.
        tool_types (Optional[Set[str]]): Types of tools to use for querying.
        token_counter (Callable): Function to count tokens in the conversation.
    """

    def __init__(
        self,
        message_history: List[ChatMessage],
        kb_ids: Optional[List[str]] = None,
        tool_types: Optional[Set[str]] = None,
        embeddings_vertex_ai: bool = True,
        chat_model_name: str = LlmIds.GEMINI_PRO.value,
    ):
        """
        Initialize the Agent with the given parameters.

        Args:
            message_history: A list of previous messages in the conversation.
            kb_ids: IDs of the knowledge bases to use. If None, a simple chat engine is used.
            tool_types: Types of tools to use for querying.
            embeddings_vertex_ai: Whether to use Vertex AI for embeddings.
            chat_model_name: The name of the chat model to use.
        """
        self.message_history = message_history
        self.kb_ids = kb_ids
        self.tool_types = tool_types
        self.token_counter = count_tokens()

        settings_embed_model(vertex_ai=embeddings_vertex_ai)

        llm_id = self._get_llm_id(chat_model_name)
        settings_llm(llm_model_id=llm_id)

    @retrying.retry(stop_max_attempt_number=3)
    def query_agent(self, query: str, return_tool_response: bool = True) -> Dict[str, Any]:
        """
        Query the agent with the given input.

        Args:
            query: The user's query string.
            return_tool_response: Whether to return the raw tool response or a summarized version.

        Returns:
            A dictionary containing the output, metadata, and token count.
        """
        # Check if kb_ids is None or empty
        if not self.kb_ids:
            llm = Settings.llm
            chat_engine = SimpleChatEngine.from_defaults(
                memory=create_memory_buffer(self.message_history),
                system_prompt="You are a helpful assistant named Scout. You work with Boston Dynamics \
                    to help answer general questions that are unrelated to their specific data needs. If \
                        anyone asks a question that you think requires their data to answer, please instruct \
                            them to turn on the relevant knowledge base in their settings.",
                llm=llm,
            )
            response = chat_engine.chat(query)
            output = response.response
            count = self.token_counter.total_llm_token_count

            return {"output": output, "metadata": [], "count": count}

        else:
            agent = self._load_agent()
            if return_tool_response:
                task = agent.create_task(query)
                response = agent.run_step(task.task_id).output
                output = response.response.replace("Observation: ", "")
                count = self.token_counter.total_llm_token_count
                source_nodes = []
                for node in response.source_nodes:
                    citation = None
                    if node.metadata["kb_id"] == "kb-sf-case-open":
                        node_id = node.id_.split("##")[2]
                        source_table = "case"
                        citation = f"{source_table}.{node_id}"
                        type = "sf_link"
                    elif node.metadata["kb_id"] == "kb-sf-case-closed":
                        node_id = node.id_.split("##")[2]
                        source_table = "case"
                        citation = f"{source_table}.{node_id}"
                        type = "sf_link"
                    elif node.metadata["kb_id"] == "kb-sf-knowledge":
                        citation = node.metadata["FULL_ARTICLE_LINK__C"]
                        type = "sf_link"
                    elif node.metadata["kb_id"] == "Case-Communication":
                        citation = node.metadata["CASENUMBER"]
                        type = "sf_link"
                    elif "file_path" in node.metadata:
                        citation = node.metadata["file_path"]
                        type = "uri"
                    elif node.metadata["kb_id"].startswith('kb-drive'):
                        citation = node.metadata["drive_name"]
                        type = "uri"
                    elif node.metadata["kb_id"] == "kb-github-bd-gh-data-spot-sdk":
                        citation = node.metadata["pdf_uri"]
                        type = "uri"

                    if citation:
                        source_nodes.append({"citation": citation, "type": type })

                return {"output": output, "metadata": source_nodes, "count": count}

    def _load_agent(self) -> ReActAgent:
        """
        Load the chatbot agent with the current message history and tools.

        Returns:
            The loaded ReActAgent instance.
        """
        memory = create_memory_buffer(self.message_history)
        agent_tools = (
            self._load_filtered_tools(tool_types=self.tool_types)
            if self.kb_ids is not None and self.tool_types
            else self._load_tools()
        )
        agent = ReActAgent.from_tools(agent_tools, verbose=True, memory=memory)

        return agent

    def _load_tools(self) -> List[QueryEngineTool]:
        """
        Load and return a list of all available agent tools.

        Returns:
            A list of QueryEngineTool instances.
        """
        # Load tools
        rag_tool_engine = RagTool().create_tool(pdf_index_location=PDF_INDEX_LOCATION)
        summary_tool_engine = SummarizationTool().create_tool(
            pdf_index_location=PDF_INDEX_LOCATION_SUMMARIZATION
        )
        pinecone_tool_engine = PineconeTool().create_tool(
            pdf_index_location=INDEX_LOCATION_PINECONE
        )

        # Create tools list
        agent_tools = [
            QueryEngineTool(
                query_engine=rag_tool_engine,
                metadata=ToolMetadata(
                    name="rag_tool_engine",
                    description=PDF_INDEX_DESCRIPTION,
                ),
            ),
            QueryEngineTool(
                query_engine=summary_tool_engine,
                metadata=ToolMetadata(
                    name="summary_tool_engine",
                    description=PDF_INDEX_DESCRIPTION_SUMMARIZATION,
                ),
            ),
            QueryEngineTool(
                query_engine=pinecone_tool_engine,
                metadata=ToolMetadata(
                    name="pinecone_tool_engine",
                    description=INDEX_DESCRIPTION_PINECONE,
                ),
            ),
        ]

        return agent_tools

    def _load_filtered_tools(self, tool_types: Set[str]) -> List[QueryEngineTool]:
        """
        Load and return a list of agent tools based on the provided tool types.

        Args:
            tool_types: A set of tool types to load.

        Returns:
            A list of QueryEngineTool instances for the specified tool types.
        """
        # Create metadata filters based on the active knowledge bases
        METADATA_FILTERS = create_metadata_filters(self.kb_ids)

        # Mapping of tool types to their corresponding tool creation functions and metadata
        tools_mapping = {
            "rag": {
                "create_tool": RagTool().create_tool,
                "params": {
                    "pdf_index_location": PDF_INDEX_LOCATION,
                    "filters": METADATA_FILTERS,
                },
                "metadata": ToolMetadata(
                    name="rag_tool_engine",
                    description=PDF_INDEX_DESCRIPTION,
                ),
            },
            "summary": {
                "create_tool": SummarizationTool().create_tool,
                "params": {
                    "pdf_index_location": PDF_INDEX_LOCATION_SUMMARIZATION,
                    "filters": METADATA_FILTERS,
                },
                "metadata": ToolMetadata(
                    name="summary_tool_engine",
                    description=PDF_INDEX_DESCRIPTION_SUMMARIZATION,
                ),
            },
            "pinecone": {
                "create_tool": PineconeTool().create_tool,
                "params": {
                    "pdf_index_location": INDEX_LOCATION_PINECONE,
                    "filters": METADATA_FILTERS,
                },
                "metadata": ToolMetadata(
                    name="pinecone_tool_engine",
                    description=INDEX_DESCRIPTION_PINECONE,
                ),
            },
        }

        # Initialize the list of tools to return
        agent_tools = []

        # Iterate over the provided tool_types and add the corresponding tools
        for tool_type in tool_types:
            if tool_type in tools_mapping:
                tool_config = tools_mapping[tool_type]
                tool_engine = tool_config["create_tool"](**tool_config["params"])
                agent_tools.append(
                    QueryEngineTool(
                        query_engine=tool_engine, metadata=tool_config["metadata"]
                    )
                )

        return agent_tools

    @staticmethod
    def _get_llm_id(chat_model_name: str) -> str:
        """
        Get the LLM ID based on the chat model name.

        Args:
            chat_model_name: The name of the chat model.

        Returns:
            The corresponding LLM ID.
        """
        for model in LlmIds:
            if model.value == chat_model_name:
                return model.value
        return LlmIds.GEMINI_PRO.value


if __name__ == "__main__":
    agent = Agent(
        message_history=[],
        kb_ids=None,
        tool_types=None,
        chat_model_name=LlmIds.GEMINI_FLASH.value
    )
    response = agent.query_agent(
        "Hello!"
    )
    print(response["output"])