"""
This module provides common utilities and classes for processing PDF documents,
building and querying vector store indices, and managing different types of query tools.

It includes functions for downloading files, processing PDFs, creating metadata filters,
and classes for different query tool types (RAG, Summarization, Pinecone).
The module also provides a PDFQueryEngineLoader class for loading and initializing query engines.

Key components:
- File download and PDF processing functions
- Metadata filter creation
- Abstract base class for query tool types
- PDFQueryEngineLoader for loading and initializing query engines
- Concrete implementations of query tool types (RagTool, SummarizationTool, PineconeTool)
"""

from typing import Type, List, Any, Optional
import wget
import os
from abc import ABC, abstractmethod
from dotenv import load_dotenv

from pinecone import Pinecone

from llama_index.vector_stores.pinecone import PineconeVectorStore
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, SummaryIndex
from llama_index.core.node_parser import TokenTextSplitter
from llama_index.core.vector_stores import (
    MetadataFilter,
    MetadataFilters,
    FilterCondition,
)

from llama_index.core import StorageContext, load_index_from_storage
from llama_index.core.base.base_query_engine import BaseQueryEngine
from llama_index.core.indices.postprocessor import SentenceTransformerRerank
from llama_index.core.postprocessor import LLMRerank
from llama_index.core.prompts.base import PromptTemplate
from llama_index.core.prompts.prompt_type import PromptType

from .configs.retriever_config import (
    CROSS_ENCODER_MODEL,
    LLM_RERANK_DOMAIN_KNOWLEDGE,
    LLM_RERANK_PROMPT_TEMPLATE,
    REFINE_TEMPLATE,
    TEXT_QA_TEMPLATE,
)


def download_files(urls: List[str], files: List[str]) -> None:
    """
    Downloads files from URLs and saves them with the specified file names.

    Args:
        urls: List of URLs to download files from.
        files: List of file names to save the downloaded files as.
    """
    for url, file in zip(urls, files):
        if os.path.exists(file):
            os.remove(file)
        wget.download(url, out=file)


def pdf_processing(
    files: List[str],
    output_dir: str,
    embed_model: Any,
    tool_type: 'QueryToolTypes',
    chunk_size: int = 256,
    chunk_overlap: int = 128
) -> None:
    """
    Processes PDF files and saves them to a vector store index.

    Args:
        files: List of file names to process.
        output_dir: Directory to save the processed vector store index.
        embed_model: The embedding model to use for processing.
        tool_type: The tool type to use for processing the files (RagTool or SummarizationTool).
        chunk_size: Size of chunks to split the text into. Defaults to 256.
        chunk_overlap: Overlap between chunks. Defaults to 128.

    Note:
        The chunk_size and chunk_overlap parameters can be adjusted based on the use case and model requirements.
    """

    filename_fn = lambda filename: {
        "file_name": filename,
    }

    # Load the documents
    docs = SimpleDirectoryReader(
        input_files=files, file_metadata=filename_fn
    ).load_data()

    # Split the text into nodes by token chunk size
    node_parser = TokenTextSplitter(
        separator=" ", chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )
    nodes = node_parser.get_nodes_from_documents(docs)

    # Apply embeddings and dump the nodes to a vector store index
    index = tool_type.build_tool_index(nodes, embed_model)
    index.storage_context.persist(persist_dir=output_dir)


def create_metadata_filters(kb_ids: List[str]) -> Optional[MetadataFilters]:
    """
    Creates MetadataFilters based on the provided kb_ids.

    Args:
        kb_ids: A list of knowledge base IDs.

    Returns:
        An instance of MetadataFilters with filters based on the provided kb_ids, or None if kb_ids is empty.
    """
    if not kb_ids:
        return None

    # Create a list of MetadataFilter objects
    filters = [MetadataFilter(key="kb_id", value=kb_id) for kb_id in kb_ids]

    # If there's more than one filter, use OR condition
    if len(filters) > 1:
        metadata_filters = MetadataFilters(
            filters=filters, condition=FilterCondition.OR
        )
    else:
        metadata_filters = MetadataFilters(filters=filters)

    return metadata_filters


class QueryToolTypes(ABC):
    """
    Abstract base class for different query tool types.

    This class defines the interface for building tool indices and query engines.
    Concrete implementations should inherit from this class and implement the abstract methods.
    """

    @abstractmethod
    def build_tool_index(self, nodes: List[Any], embed_model: Any) -> Any:
        """
        Builds the tool index.

        Args:
            nodes: List of nodes to build the index from.
            embed_model: The embedding model to use for the index.

        Returns:
            The built index.
        """
        pass

    @abstractmethod
    def build_tool_engine(
        self,
        index: Any,
        cross_encoder_reranker: Optional[Any],
        llm_reranker: Optional[Any],
        similarity_top_k: int = 100,
        filters: Optional[MetadataFilters] = None,
    ) -> BaseQueryEngine:
        """
        Builds the tool query engine.

        Args:
            index: The index containing the documents.
            cross_encoder_reranker: The cross-encoder reranker for ranking candidate documents.
            llm_reranker: The language model reranker for ranking candidate documents.
            similarity_top_k: The number of top similar documents to retrieve. Defaults to 100.
            filters: The metadata filters to apply to the index. Defaults to None.

        Returns:
            The query engine for retrieving relevant documents.
        """
        pass


class PDFQueryEngineLoader:
    """
    Class to load the query engine for PDF context retrieval across multiple tool types.

    This class provides methods for creating rerankers, building storage contexts,
    loading indices, and initializing query engines with various configurations.
    """

    def __init__(self, db_file_path: str = "index/"):
        """
        Initializes the PDFQueryEngineLoader object.

        Args:
            db_file_path: The file path to the index created from files. Defaults to "index/".
        """
        self.db_file_path = db_file_path

    def create_cross_encoder_reranker(
        self, top_n=10
    ) -> Type[SentenceTransformerRerank]:
        """
        Creates a cross-encoder reranker for sentence embeddings.

        Args:
            top_n (int): The number of top results to retrieve.

        Returns:
            SentenceTransformerRerank: The cross-encoder reranker object.
        """
        cross_encoder_reranker = SentenceTransformerRerank(
            model=CROSS_ENCODER_MODEL, top_n=top_n, device="cpu"
        )
        return cross_encoder_reranker

    def create_llm_reranker(self, batch_size, top_n) -> Type[LLMRerank]:
        """
        Creates an instance of LLMRerank with the specified parameters.

        Args:
            batch_size (int): The batch size for choice selection.
            top_n (int): The number of top choices to be returned.

        Returns:
            LLMRerank: An instance of LLMRerank with the specified parameters.
        """
        rerank_prompt = PromptTemplate(
            LLM_RERANK_DOMAIN_KNOWLEDGE + LLM_RERANK_PROMPT_TEMPLATE,
            prompt_type=PromptType.CHOICE_SELECT,
        )

        llm_reranker = LLMRerank(
            choice_select_prompt=rerank_prompt,
            choice_batch_size=batch_size,
            top_n=top_n,
        )

        return llm_reranker

    def build_storage_context(self) -> StorageContext:
        """
        Builds and returns a StorageContext object.

        Returns:
            A StorageContext object initialized with default values and the specified database file path.
        """
        return StorageContext.from_defaults(persist_dir=self.db_file_path)

    def load_index(self, storage_context: StorageContext):
        """
        Loads the index from the specified storage context.

        Args:
            storage_context (StorageContext): The storage context from which to load the index.

        Returns:
            Index: The loaded index.
        """
        return load_index_from_storage(storage_context)

    def load_pinecone_index(self, index_name: str):
        """
        Loads the index from Pinecone.

        Args:
            index_name: The name of the Pinecone index.

        Returns:
            Index: The loaded index.
        """
        # TODO
        pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
        pinecone_index = pc.Index(index_name)
        vector_store = PineconeVectorStore(pinecone_index=pinecone_index)
        index = VectorStoreIndex.from_vector_store(vector_store=vector_store)

        return index

    def update_prompts(self, query_engine: BaseQueryEngine):
        """
        Updates the prompts in the query engine with the specified templates.

        Args:
            query_engine (BaseQueryEngine): The query engine to update.

        Returns:
            BaseQueryEngine: The initialized query engine.
        """
        text_qa_prompt = PromptTemplate(TEXT_QA_TEMPLATE)
        query_engine.update_prompts(
            {"response_synthesizer:text_qa_template": text_qa_prompt}
        )
        refine_prompt = PromptTemplate(REFINE_TEMPLATE)
        query_engine.update_prompts(
            {"response_synthesizer:refine_template": refine_prompt}
        )

        return query_engine

    def load_query_engine(
        self,
        tool_type: QueryToolTypes,
        similarity_top_k: int = 100,
        cross_encoder_reranker: bool = False,
        cross_encoder_top_n: int = 10,
        llm_reranker: bool = False,
        llm_reranker_top_n: int = 10,
        llm_reranker_batch_size: int = 5,
        filters: Optional[MetadataFilters] = None,
    ) -> BaseQueryEngine:
        """
        Loads and initializes a query engine for retrieving relevant documents.

        Args:
            tool_type: The tool type to use for the query engine (RagTool, SummarizationTool, or PineconeTool).
            similarity_top_k: The number of similar documents to retrieve.
            cross_encoder_reranker: Whether to use cross-encoder reranking.
            cross_encoder_top_n: The number of top results to consider for cross encoder reranking.
            llm_reranker: Whether to use language model reranking.
            llm_reranker_top_n: The number of top results to consider for language model reranking.
            llm_reranker_batch_size: The batch size for language model reranking.
            filters: Optional metadata filters to apply during querying.

        Returns:
            The initialized query engine.
        """
        if self.db_file_path == "pinecone":
            # TODO
            load_dotenv()
            index = self.load_pinecone_index(os.environ["PINECONE_INDEX_NAME"])
        else:
            # Build the storage context
            storage_context = self.build_storage_context()

            # Load the index from the storage context
            index = self.load_index(storage_context)

        cross_encoder_reranker_obj = None
        if cross_encoder_reranker:
            cross_encoder_reranker_obj = self.create_cross_encoder_reranker(
                top_n=cross_encoder_top_n
            )

        llm_reranker_obj = None
        if llm_reranker:
            llm_reranker_obj = self.create_llm_reranker(
                batch_size=llm_reranker_batch_size, top_n=llm_reranker_top_n
            )

        # Create a query engine with the index, cross encoder reranker, and language model reranker
        query_engine = tool_type.build_tool_engine(
            index,
            cross_encoder_reranker_obj,
            llm_reranker_obj,
            similarity_top_k,
            filters,
        )

        # Update the prompts in the query engine
        query_engine = self.update_prompts(query_engine)

        return query_engine

    @abstractmethod
    def create_tool():
        """
        Creates the tool.

        Args:
            pdf_index_location (str): The location of the PDF index.

        Returns:
            Tool: The created tool.
        """
        pass


class RagTool(QueryToolTypes):
    def build_tool_index(self, nodes, embed_model):
        return VectorStoreIndex(nodes, embed_model=embed_model)

    def build_tool_engine(
        self,
        index,
        cross_encoder_reranker,
        llm_reranker,
        similarity_top_k=100,
        filters=None,
    ) -> BaseQueryEngine:
        node_postprocessors = []
        if cross_encoder_reranker:
            node_postprocessors.append(cross_encoder_reranker)
        if llm_reranker:
            node_postprocessors.append(llm_reranker)
        return index.as_query_engine(
            similarity_top_k=similarity_top_k,
            node_postprocessors=node_postprocessors,
            response_mode="compact",
            filters=filters,
        )

    def create_tool(self, pdf_index_location, filters=None):
        loader = PDFQueryEngineLoader(db_file_path=pdf_index_location)
        query_engine = loader.load_query_engine(
            tool_type=self,
            similarity_top_k=100,
            cross_encoder_reranker=False,
            cross_encoder_top_n=10,
            llm_reranker=False,
            llm_reranker_top_n=10,
            llm_reranker_batch_size=5,
            filters=filters,
        )
        return query_engine


class SummarizationTool(QueryToolTypes):
    def build_tool_index(self, nodes, embed_model):
        return SummaryIndex(nodes)

    def build_tool_engine(
        self,
        index,
        cross_encoder_reranker,
        llm_reranker,
        similarity_top_k=100,
        filters=None,
    ) -> BaseQueryEngine:
        node_postprocessors = []
        if cross_encoder_reranker:
            node_postprocessors.append(cross_encoder_reranker)
        if llm_reranker:
            node_postprocessors.append(llm_reranker)
        return index.as_query_engine(
            similarity_top_k=similarity_top_k,
            node_postprocessors=node_postprocessors,
            response_node="tree_summarize",
            filters=filters,
        )

    def create_tool(self, pdf_index_location, filters=None):
        loader = PDFQueryEngineLoader(db_file_path=pdf_index_location)
        query_engine = loader.load_query_engine(
            tool_type=self,
            similarity_top_k=100,
            cross_encoder_reranker=False,
            cross_encoder_top_n=10,
            llm_reranker=False,
            llm_reranker_top_n=10,
            llm_reranker_batch_size=5,
            filters=filters,
        )
        return query_engine


class PineconeTool(QueryToolTypes):
    # TODO
    def build_tool_index(self, nodes, embed_model):
        pass

    def build_tool_engine(
        self,
        index,
        cross_encoder_reranker,
        llm_reranker,
        similarity_top_k=20,
        filters=None,
    ) -> BaseQueryEngine:
        node_postprocessors = []
        if cross_encoder_reranker:
            node_postprocessors.append(cross_encoder_reranker)
        if llm_reranker:
            node_postprocessors.append(llm_reranker)
        return index.as_query_engine(
            similarity_top_k=similarity_top_k,
            node_postprocessors=node_postprocessors,
            response_mode="compact",
            vector_store_query_mode="hybrid",
            filters=filters,
        )

    def create_tool(self, pdf_index_location, filters=None):
        loader = PDFQueryEngineLoader(db_file_path=pdf_index_location)
        query_engine = loader.load_query_engine(
            tool_type=self,
            similarity_top_k=100,
            cross_encoder_reranker=True,
            cross_encoder_top_n=10,
            llm_reranker=False,
            llm_reranker_top_n=10,
            llm_reranker_batch_size=5,
            filters=filters,
        )
        return query_engine


if __name__ == "__main__":
    # Load the query engine
    loader = PDFQueryEngineLoader(
        db_file_path="../tools/rag/pdf_context_retrieval/index/"
    )
    query_engine = loader.load_query_engine(
        tool_type=RagTool(),
        similarity_top_k=100,
        cross_encoder_top_n=10,
        llm_reranker=False,
        llm_reranker_top_n=10,
        llm_reranker_batch_size=5,
    )
    print("Loader", loader)
    print("Query Engine", query_engine)
