import os

from llama_index.core import Settings, set_global_tokenizer
from llama_index.embeddings.gemini import GeminiEmbedding
from llama_index.llms.vertex import Vertex
from vertexai.generative_models import HarmCategory, HarmBlockThreshold, SafetySetting
from llama_index.core.callbacks import CallbackManager, TokenCountingHandler
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.huggingface import HuggingFaceLLM
from transformers import AutoTokenizer
from enum import Enum


class LlmIds(Enum):
    GEMINI_PRO = "gemini-1.5-pro"
    GEMINI_FLASH = "gemini-1.5-flash"


def settings_embed_model(vertex_ai: bool = False):
    """
    Sets the global embedding model used by LlamaIndex.

    Args:
        vertex_ai (bool): A boolean indicating whether to use a Vertex AI embedding model.

    Returns:
        None
    """
    if vertex_ai:
        embed_model = GeminiEmbedding(
            model_name="models/text-embedding-004", embed_batch_size=1
        )
        # Need to make sure the GOOGLE_API_KEY environment variable is set
        Settings.embed_model = embed_model
    else:
        Settings.embed_model = HuggingFaceEmbedding()


def settings_llm(llm_model_id: str = None):
    """
    Sets the global LLM used by LlamaIndex.

    Args:
        vertex_ai (bool): A boolean indicating whether to use a Vertex AI LLM.

    Returns:
        None
    """

    safety_config = [
        SafetySetting(
            category=HarmCategory.HARM_CATEGORY_HATE_SPEECH,
            threshold=HarmBlockThreshold.BLOCK_ONLY_HIGH,
        ),
        SafetySetting(
            category=HarmCategory.HARM_CATEGORY_HARASSMENT,
            threshold=HarmBlockThreshold.BLOCK_ONLY_HIGH,
        ),
        SafetySetting(
            category=HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
            threshold=HarmBlockThreshold.BLOCK_ONLY_HIGH,
        ),
        SafetySetting(
            category=HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
            threshold=HarmBlockThreshold.BLOCK_ONLY_HIGH,
        ),
    ]

    if llm_model_id == LlmIds.GEMINI_PRO.value:
        # Need to make sure the GOOGLE_APPLICATION_CREDENTIALS environment variable is set
        # or you have run gcloud auth application-default login in the terminal
        Vertex.update_forward_refs()
        llm = Vertex(
            model=llm_model_id, temperature=0.1, safety_settings=safety_config
        )
        Settings.llm = llm
    elif llm_model_id == LlmIds.GEMINI_FLASH.value:
        Vertex.update_forward_refs()
        llm = Vertex(
            model=llm_model_id, temperature=0.1, safety_settings=safety_config
        )
        Settings.llm = llm
    else:
        # Enable CUDA device-side assertions
        os.environ["TORCH_USE_CUDA_DSA"] = "1"
        # Set environment variable for CUDA synchronous error reporting
        os.environ["CUDA_LAUNCH_BLOCKING"] = "1"
        set_global_tokenizer(
            AutoTokenizer.from_pretrained("HuggingFaceH4/zephyr-7b-alpha").encode
        )
        Settings.llm = HuggingFaceLLM(
            model_name="HuggingFaceH4/zephyr-7b-alpha",
            tokenizer_name="HuggingFaceH4/zephyr-7b-alpha",
        )


def count_tokens():
    token_counter = TokenCountingHandler()
    Settings.callback_manager = CallbackManager([token_counter])
    return token_counter


if __name__ == "__main__":
    settings_embed_model(vertex_ai=False)
    settings_llm(llm_model_id=LlmIds.GEMINI_FLASH)
