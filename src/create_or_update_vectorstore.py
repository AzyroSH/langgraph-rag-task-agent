import os
import hashlib
from config import BasicConfig
from pathlib import Path
from langchain_core.documents import Document
from langchain_chroma import Chroma
from chromadb.config import Settings
from langchain_community.document_loaders import (
    DirectoryLoader, UnstructuredMarkdownLoader, TextLoader
)
from langchain_text_splitters import RecursiveCharacterTextSplitter


# load configuration
config = BasicConfig()

def enrich_metadata(doc: Document):
    """
    Extract information from the file path to enrich the document chunk's metadata
    """
    source_path = Path(doc.metadata.get("source", ""))
    # get the path relative to the knowledge-base root
    relative_path = source_path.relative_to(config.KNOWLEDGE_PATH)
    # the path's components are returned as a tuple
    parts = relative_path.parts
    # the level depends on your need
    if len(parts) >= 3:
        doc.metadata["level1"] = parts[0]
        doc.metadata["level2"] = parts[1]
        doc.metadata["level3"] = parts[2]
    elif len(parts) ==2 :
        doc.metadata["level1"] = parts[0]
        doc.metadata["level2"] = parts[1]
        doc.metadata["level3"] = "N/A"
    else:
        doc.metadata['level1'] = relative_path.name
        doc.metadata["level2"] = "N/A"
        doc.metadata["level3"] = "N/A"

    return doc

# generate hash ID for the document chunks
def generate_doc_id(doc: Document):
    """
    Generate a unique, stable ID from the document content plus key metadata.

    This ID is critical for incremental updates: it must change whenever either
    the content changes or any metadata that could affect retrieval-such as 
    the file's location-changes.

    Therefore, we hash the concatenation of file path, chunk text.
    """
    id_string = (
        f"{doc.metadata.get('source', '')}"
        f"{doc.page_content}"
    )

    return hashlib.sha256(id_string.encode('utf-8')).hexdigest()

# define the knowledge class
class KnowledgeManager():
    """KnowledgeBaseManager initialization, creation, and updates"""
    def __init__(self):
        self.model = config.MODEL
        self.embedding_model = config.EMBEDDING_MODEL
        self.knowledge_base = self._create_or_connect_knowledge_base()

    def _create_or_connect_knowledge_base(self):
        """
        Create a new knowledge base if none exists; 
        otherwise, link to the existing one.
        """
        knowledge_base = Chroma(
            persist_directory=config.KNOWLEDGE_PATH,
            embedding_function=self.embedding_model,
            client_settings=Settings(anonymized_telemetry=False)
        )
        print("Knowledge base initializes successfully.")
        return knowledge_base
    
    def load_data(self):
        """load the data from the KNOWLEDGE_PATH"""
        documents: list[Document] = []

        print("loading the markdown files")
        md_loader = DirectoryLoader(
            path=config.KNOWLEDGE_PATH,
            glob="**/*.md",
            loader_cls=UnstructuredMarkdownLoader,
            show_progress=True,
            use_multithreading=True
        )
        documents.extend(md_loader.load())

        print("loading the sql files")
        sql_loader = DirectoryLoader(
            path=config.KNOWLEDGE_PATH,
            glob="**/*.sql",
            loader_cls=TextLoader,
            show_progress=True,
            use_multithreading=True
        )
        documents.extend(sql_loader.load())

        print("loading the shell files")
        sh_loader = DirectoryLoader(
            path=config.KNOWLEDGE_PATH,
            glob="**/*.sh",
            loader_cls=TextLoader,
            show_progress=True,
            use_multithreading=True
        )
        documents.extend(sh_loader.load())

        if not documents:
            print("Disable to load the documents from the knowledge base,\
                please check the directory of the knowledge base.")
            return documents
        
        print(f"Successfully loaded {len(documents)} documents")

    def processing_data(self,
            documents: list[Document], 
            chunk_size: int, 
            chunk_overlap: int):
        """processing the data, including document splitting"""
        print("Enriching metadata")
        for doc in documents:
            doc = enrich_metadata(doc)
        print("Splitting the documents")
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )     
        chunks = text_splitter.split_documents(documents)
        print(f"Documents split into {len(chunks)} chunks ")

        print("generate id for every chunk")
        for chunk in chunks:
            chunk.id = generate_doc_id(chunk)
        print("IDs generated for all chunks")

        return chunks
    
    def incremental_update_data_to_knowledge_base(self, chunks: list[Document]):
        """update the knowledge base incrementally"""
        existing_ids = self.knowledge_base.get(include=[]).get("ids", "")
        current_ids = [chunk.id for chunk in chunks]
        chunks_dict = {chunk.id: chunk for chunk in chunks}

        print("Updating the knowledge base incrementally")
        print(f"Knowledge base has {len(existing_ids)} chunks")

        # Identify IDs to delete - those present in the knowledge base 
        # but absent from the current chunks
        ids_to_deletes = list(existing_ids - current_ids)
        if ids_to_deletes:
            print(f"Detected {len(ids_to_deletes)} outdated chunks; removing... ")
            self.knowledge_base.delete(ids=ids_to_deletes)
            print("Delection completed")
        
        # Identify IDs to update - those present in current chunks
        # but absent from the knowledge base
        ids_to_update = list(current_ids - existing_ids)
        if ids_to_update:
            print(f"Need to update {len(ids_to_update)} chunks; updating...")
            chunk_to_update = [chunks_dict['id'] for id in ids_to_update]
            self.knowledge_base.add_documents(
                documents=chunk_to_update,
                ids=ids_to_update
            )
            print("Update completed")

        total_chunks = self.knowledge_base._collection.count()
        print(f"After update, knowledge base has {total_chunks} chunks now")

    def main(self, chunk_size: int, chunk_overlap: int):
        """main fuction"""
        documents = self.load_data()
        if not documents:
            print("No documents loaded, exiting...")
            return
        chunks = self.processing_data(
            documents=documents, 
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap)
        self.incremental_update_data_to_knowledge_base(chunks=chunks)
        print("Knowledge base is ready")

if __name__ == "__main__":
    kb_manager = KnowledgeManager()
    kb_manager.main(chunk_size=config.CHUNK_SIZE,
                    chunk_overlap=config.CHUNK_OVERLAP)





