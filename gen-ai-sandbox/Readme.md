# Python-based Backend Generative AI Service

This README serves as the documentation for the Python-based backend generative AI service.

## API

The main interface for the Gen AI backend is a FastAPI-built API. The API is defined in `gen-ai-sandbox/src/chatbot_app/chatbot/api.py` and consists of the following endpoints:

1. **chat**: Generates a response to a user query.
2. **upload_files**: Uploads a given file from GCS to a specific Pinecone knowledge base.
3. **delete_files**: Removes a given file from a Pinecone knowledge base.
4. **health**: Performs a health check for the API service.

## Streamlit App

To run the Streamlit app:

1. Install the required dependencies:
   ```
   pip install -r gen-ai-sandbox/src/chatbot_app/requirements.txt
   ```

2. Navigate to the `gen-ai-sandbox/src/chatbot_app` directory.

3. Configure `main.py` with the necessary parameters for the Agent, including:
   - Message history
   - Knowledge base IDs (kb_ids)
   - Tool types

4. Run the Streamlit app:
   ```
   streamlit run main.py
   ```

## Project Structure

The project is organized as follows:

- `src/chatbot_app/`: Main application directory
  - `chatbot/`: Core chatbot functionality
    - `api.py`: FastAPI endpoints
    - `agent.py`: Agent implementation
    - `tools/`: Various tools used by the agent
    - `common.py`: Contains shared utility functions and classes for the chatbot
      - Includes `QueryToolTypes` abstract base class for different tool types
      - Implements `PDFQueryEngineLoader` for loading and configuring query engines
      - Defines `RagTool`, `SummarizationTool`, and `PineconeTool` classes
      - Provides utility functions for file downloading and PDF processing
  - `main.py`: Streamlit app entry point
  - `requirements.txt`: Project dependencies
  - `api_requirements.txt`: API-specific dependencies
  - `Dockerfile`: Docker configuration for the API

## Dependencies

The project relies on several key libraries:

- FastAPI and Uvicorn for the API
- Streamlit for the web interface
- LlamaIndex for core functionality
- Pinecone for vector storage
- Google Cloud libraries for GCS, Gemini, VertexAI, and Firestore integration

For a complete list of dependencies, refer to `requirements.txt` and `api_requirements.txt`.

## Environment Setup

Before running the application, you need to set up the following environment variables:

PINECONE_API_KEY=<Your Pinecone API Key>
PINECONE_INDEX_NAME=<Your Pinecone Index Name>
GOOGLE_API_KEY=<Your Google API Key>
GOOGLE_APPLICATION_CREDENTIALS=<Path to your Google credentials JSON file>
GCP_REGION=<Your GCP Region>

You can create a `.env` file based on the `env.sample` provided in the project.

## Docker

The project includes a Dockerfile for containerization. To build and run the Docker container:

1. Build the image:
   ```
   docker build -t genai-sandbox .
   ```

2. Run the container:
   ```
   docker run -p 8080:8080 genai-sandbox
   ```

3. To run the fully integrated app locally, see documentation at the top level of the repo.


## Deployment

The project is set up for deployment to Google Cloud Run. The deployment process is automated using GitHub Actions, as defined in the `.github/workflows/gen-ai-sandbox-deploy.yaml` file.

## Contributing

Please refer to the `.gitignore` file for files and directories that should not be committed to the repository. When contributing, ensure that you do not include any sensitive information or environment-specific files in your commits.
