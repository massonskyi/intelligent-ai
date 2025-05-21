import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

class RetrieverService:
    def __init__(self, persist_dir="./chroma_index", embedding_model="all-MiniLM-L6-v2"):
        self.client = chromadb.Client(Settings(
            persist_directory=persist_dir,
            anonymized_telemetry=False
        ))
        self.collection = self.client.get_or_create_collection(name="rag_docs")
        self.embedder = SentenceTransformer(embedding_model)

    def add_docs(self, docs):
        # docs: [{id, text, metadata (dict)}]
        texts = [doc["text"] for doc in docs]
        ids = [doc["id"] for doc in docs]
        metadatas = [doc.get("metadata", {}) for doc in docs]
        embeddings = self.embedder.encode(texts).tolist()
        self.collection.add(
            documents=texts, metadatas=metadatas, ids=ids, embeddings=embeddings
        )

    def query(self, query: str, top_k=3) -> list:
        embedding = self.embedder.encode([query]).tolist()
        results = self.collection.query(
            query_embeddings=embedding,
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )
        docs = []
        for doc, meta, dist in zip(results["documents"][0], results["metadatas"][0], results["distances"][0]):
            docs.append({
                "title": meta.get("title", "Document"),
                "snippet": doc,
                "url": meta.get("url", ""),
                "score": 1.0 - dist  # Chroma: меньший distance — ближе
            })
        return docs

# Singleton
retriever_service = RetrieverService()
