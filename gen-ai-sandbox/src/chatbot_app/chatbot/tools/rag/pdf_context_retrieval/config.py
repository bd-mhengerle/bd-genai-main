"""
Place all strings related to the rag pdf context retrieval tool here.
"""

import os

PDF_INDEX_LOCATION = os.path.join(os.path.dirname(__file__), "index/")

# Description of the PDF index tool goes here. This is what the agent will use
# to determine whether or not this is the appropriate tool to use to answer
# the questions.
PDF_INDEX_DESCRIPTION = """
This is a tool that allows the agent to search through specific context from a
collection of PDFs on major LLM topics like RAG, FineTuning, and newly developed LLMs.
The agent can use this tool to answer specific, context-dependent questions about the PDFs.
"""
