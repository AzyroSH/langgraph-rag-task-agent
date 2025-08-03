import os
from langchain_ollama import ChatOllama, OllamaEmbeddings

class BasicConfig():
    """Basic configuration"""
    def __init__(self) -> None:
        # Path configuration
        self.PROJECT_PATH = os.path.dirname(os.path.dirname(__file__))
        self.CHROMADB_PATH = os.path.join(self.PROJECT_PATH, "chromadb_db")
        self.KNOWLEDGE_PATH = os.path.join(self.PROJECT_PATH, "knowledge_base")

        # Model configuration
        self.MODEL_NAME = "qwen3:4b"
        self.MODEL = ChatOllama(model=self.MODEL_NAME, temperature=0.3)
        self.EMBEDDING_MODEL_NAME = "quentinz/bge-large-zh-v1.5"
        self.EMBEDDING_MODEL = OllamaEmbeddings(model=self.EMBEDDING_MODEL_NAME)

        # Other configuration
        self.CHUNK_SIZE = 1000
        self.CHUNK_OVERLAP = 200
        self.SUMMARY_THRESHOLD = 5
        self.KEEP_RECENT_MESSAGES = 1