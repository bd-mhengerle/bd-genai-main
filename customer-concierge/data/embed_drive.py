import os
from google.cloud import storage
from google.cloud import aiplatform
from pinecone import Pinecone
from vertexai.preview.language_models import TextEmbeddingInput, TextEmbeddingModel
import uuid
from tqdm import tqdm
from dotenv import load_dotenv
from typing import List, Optional
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Load environment variables from .env file
load_dotenv()

# Google Cloud setup
aiplatform.init(project="bd-genai-internal", location="us-central1")
bucket_name = "bd-drive-data"
location = "us-central1"
storage_client = storage.Client()


def setup_pinecone_index(index_name: str, dimension: int = 768):
    """
    Sets up a Pinecone index with the given name and dimension.

    Args:
        index_name (str): The name of the Pinecone index to create.
        dimension (int): The dimension of the vectors to store in the index. Default is 256.

    Returns:
        index: The Pinecone index object.
    """
    # Initialize Pinecone
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    print(pc.list_indexes().names())

    # Define index specifications
    spec = {
        "pod": {
            "environment": "gcp-starter",
            "pod_type": "starter",
            "pods": 1,
            "replicas": 1,
            "shards": 1,
        }
    }
    pc.delete_index("customer-concierge")

    # Create the index if it doesn't exist
    if index_name not in pc.list_indexes().names():
        print(f"Creating new index: {index_name}")
        pc.create_index(index_name, dimension=dimension, metric="dotproduct", spec=spec)

    # Connect to the index
    index = pc.Index(index_name)
    print(index.describe_index_stats())

    return index


def list_txt_blobs(bucket_name):
    """Lists all the .txt blobs in the bucket."""
    blobs = storage_client.list_blobs(bucket_name)
    return [blob for blob in blobs if blob.name.endswith(".txt")]


def read_blob_content(blob):
    """Reads the content of a blob from Google Cloud Storage."""
    content = blob.download_as_text()
    return content


def chunk_content(content, chunk_size=1024, chunk_overlap=0) -> List[str]:
    rec_text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )
    return rec_text_splitter.split_text(content)


def embed_text(
    texts: List[str],
    task: str = "RETRIEVAL_DOCUMENT",
    model_name: str = "text-embedding-004",
    dimensionality: Optional[int] = 768,
) -> List[List[float]]:
    """Embeds texts with a pre-trained, foundational model."""
    model = TextEmbeddingModel.from_pretrained(model_name)
    inputs = [TextEmbeddingInput(text, task) for text in texts]
    kwargs = dict(output_dimensionality=dimensionality) if dimensionality else {}
    embeddings = model.get_embeddings(inputs, **kwargs)
    return [embedding.values for embedding in embeddings]


def embed_and_upload(blob, content, index):
    """Embeds text content and uploads embeddings with metadata to Pinecone."""
    # Determine if the file is an image based on its name
    is_image = "jpeg" in blob.name.lower()

    # Chunk the content
    chunks = chunk_content(content)

    # Generate embeddings for chunks
    embeddings = embed_text(chunks)

    # Prepare metadata and upload to Pinecone
    for chunk, embedding in zip(chunks, embeddings):
        metadata = {
            "text": chunk,
            "kb_id": str(uuid.uuid4()),
            "file_name": blob.name,
            "is_image": is_image,
        }
        index.upsert([{"id": metadata["kb_id"], "values": embedding, "metadata": metadata}])


if __name__ == "__main__":
    index = setup_pinecone_index("customer-concierge")
    blobs = list_txt_blobs(bucket_name)
    for blob in tqdm(blobs):
        content = read_blob_content(blob)
        embed_and_upload(blob, content, index)