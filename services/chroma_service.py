import chromadb
from chromadb.utils import embedding_functions

ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

chroma_client = chromadb.Client()
collection = chroma_client.get_or_create_collection(
    name="documents",
    embedding_function=ef
)
