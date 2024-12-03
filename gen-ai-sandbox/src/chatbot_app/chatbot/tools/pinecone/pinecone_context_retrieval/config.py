"""
Place all strings related to the pinecone context retrieval tool here.
"""


INDEX_LOCATION_PINECONE = "pinecone"

# Description of the Pinecone index tool goes here. This is what the agent will use
# to determine whether or not this is the appropriate tool to use to answer
# the questions.
INDEX_DESCRIPTION_PINECONE = """
Search tool to retrieve context from the Pinecone index for question answering.  This is the knowledge location for most specific information requested.  This should be the default choice for search.
"""