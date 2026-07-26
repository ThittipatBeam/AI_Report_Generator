import os
import re
from typing import List, Dict, Any

# Resolve project root and set local models cache directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
MODELS_DIR = os.path.join(PROJECT_ROOT, "models")

# Redirect HuggingFace cache to project root /models directory
os.environ["HF_HOME"] = MODELS_DIR
os.environ["SENTENCE_TRANSFORMERS_HOME"] = MODELS_DIR

try:
    from langchain_huggingface import HuggingFaceEmbeddings
except ImportError:
    from langchain_community.embeddings import HuggingFaceEmbeddings

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from backend.config import settings

# Ultra-Lightweight Multilingual Model (~470MB download, fast CPU inference)
EMBEDDING_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

class SemanticKnowledgeBaseRetriever:
    """
    Custom Data Retriever Tool for knowledge/knowledge_base.txt.
    Uses Lightweight Multilingual Dense Vector Embeddings (MiniLM-L12-v2 + FAISS)
    to provide fast, accurate semantic search across Thai and English text.
    """
    def __init__(self, file_path: str = None):
        self.file_path = file_path or settings.KNOWLEDGE_BASE_PATH
        self.vectorstore = None
        self.embeddings = None
        self._load_and_index()

    def _load_and_index(self):
        """Reads knowledge_base.txt, chunks it, and builds a FAISS vector index in RAM."""
        if not os.path.exists(self.file_path):
            print(f"Warning: Knowledge base file not found at {self.file_path}")
            return

        with open(self.file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Split content by TOPIC headers or double newlines
        topic_blocks = re.split(r'===\s*TOPIC\s*\d+:', content)
        
        documents: List[Document] = []

        for block in topic_blocks:
            block = block.strip()
            if not block:
                continue

            lines = block.split("\n")
            header = lines[0].strip() if lines else "General Knowledge"
            
            # Split block into sub-paragraphs (chunks)
            paragraphs = block.split("\n\n")
            for para in paragraphs:
                para_clean = para.strip()
                if len(para_clean) < 30:  # Skip tiny metadata lines
                    continue

                doc = Document(
                    page_content=para_clean,
                    metadata={"header": header}
                )
                documents.append(doc)

        if not documents:
            print("No valid text documents extracted from knowledge base.")
            return

        print(f"🔄 Initializing Lightweight Multilingual Model [{EMBEDDING_MODEL_NAME}]...")
        print(f"📁 Model weights cached at: {MODELS_DIR}")
        
        self.embeddings = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL_NAME,
            cache_folder=MODELS_DIR,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )

        print(f"🧠 Building FAISS Vector Index for {len(documents)} text chunks...")
        self.vectorstore = FAISS.from_documents(documents, self.embeddings)
        print(f"✅ FAISS Vector Index successfully built!")

    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Searches the indexed chunks using Multilingual Vector Similarity.
        Returns top_k relevant chunk objects with similarity scores.
        """
        if not self.vectorstore:
            return []

        # Perform similarity search with relevance scores
        results_with_scores = self.vectorstore.similarity_search_with_score(query, k=top_k)

        formatted_results = []
        for doc, score in results_with_scores:
            # Convert L2 distance score to similarity score percentage
            similarity_score = max(0.0, 1.0 - float(score) / 2.0)
            formatted_results.append({
                "header": doc.metadata.get("header", "Knowledge"),
                "text": doc.page_content,
                "score": similarity_score
            })

        return formatted_results

# Global singleton instance for easy tool reuse
_semantic_retriever_instance = None

def get_semantic_retriever() -> SemanticKnowledgeBaseRetriever:
    global _semantic_retriever_instance
    if _semantic_retriever_instance is None:
        _semantic_retriever_instance = SemanticKnowledgeBaseRetriever()
    return _semantic_retriever_instance

def search_knowledge_base(query: str, top_k: int = 3) -> str:
    """
    Custom LangChain Tool function required for Agent 1 (Data Retriever).
    Reads knowledge_base.txt and returns semantically relevant text snippets.
    """
    retriever = get_semantic_retriever()
    results = retriever.search(query, top_k=top_k)

    if not results:
        return "No relevant information found in knowledge_base.txt for this query."

    formatted_snippets = []
    for i, res in enumerate(results, 1):
        snippet = (
            f"[Snippet {i} | Semantic Match: {res['score'] * 100:.1f}%]\n"
            f"{res['text']}"
        )
        formatted_snippets.append(snippet)

    return "\n\n---\n\n".join(formatted_snippets)
