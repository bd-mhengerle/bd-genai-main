import os

from llama_index.embeddings.huggingface import HuggingFaceEmbedding

from ..config import PDF_INDEX_LOCATION
from chatbot.common import download_files, pdf_processing, RagTool

embed_model = HuggingFaceEmbedding()

# Define URLs of papers to be downloaded
pdf_urls = [
    "https://openreview.net/pdf?id=VtmBAGCN7o",
    "https://openreview.net/pdf?id=6PmJoRfdaK",
    "https://openreview.net/pdf?id=hSyW5go0v8",
]

# Define file names of papers to be downloaded
papers = [
    os.path.join(os.path.dirname(__file__), "metagpt.pdf"),
    os.path.join(os.path.dirname(__file__), "longlora.pdf"),
    os.path.join(os.path.dirname(__file__), "selfrag.pdf"),
]

if __name__ == "__main__":
    # Download pdf files
    download_files(urls=pdf_urls, files=papers)
    # Process pdfs and save them to a vector store indexs
    pdf_processing(
        files=papers,
        tool_type=RagTool(),
        output_dir=PDF_INDEX_LOCATION,
        embed_model=embed_model,
        chunk_size=256,
        chunk_overlap=128,
    )
