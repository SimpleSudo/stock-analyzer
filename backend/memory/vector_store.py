import json
import os
from typing import List, Dict, Any, Optional
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

try:
    import faiss
except ImportError:
    faiss = None

class VectorStore:
    """
    Simple vector store for storing and retrieving analysis results.
    Uses sentence-transformers for encoding and FAISS for similarity search.
    If dependencies are not installed, falls back to a simple in-memory list.
    """
    def __init__(self, model_name: str = 'shibing624/text2vec-base-chinese', 
                 index_path: str = "./vector_store.index",
                 metadata_path: str = "./vector_store_metadata.json"):
        self.model_name = model_name
        self.index_path = index_path
        self.metadata_path = metadata_path
        self.model = None
        self.index = None
        self.metadata: List[Dict[str, Any]] = []  # list of dicts with keys: id, symbol, timestamp, data
        self._initialize()

    def _initialize(self):
        # Initialize model
        if SentenceTransformer is not None:
            try:
                self.model = SentenceTransformer(self.model_name)
            except Exception as e:
                print(f"Warning: Could not load sentence transformer model: {e}")
                self.model = None
        else:
            print("Warning: sentence-transformers not installed, using fallback storage.")
            self.model = None

        # Initialize FAISS index
        if faiss is not None and self.model is not None:
            # Determine embedding dimension by encoding a dummy sentence
            try:
                dim = self.model.encode(["test"]).shape[1]
                self.index = faiss.IndexFlatL2(dim)  # L2 distance
                # Load existing index if available
                if os.path.exists(self.index_path):
                    self.index = faiss.read_index(self.index_path)
                    # Load metadata
                    if os.path.exists(self.metadata_path):
                        with open(self.metadata_path, 'r', encoding='utf-8') as f:
                            self.metadata = json.load(f)
                else:
                    self.metadata = []
            except Exception as e:
                print(f"Warning: Could not initialize FAISS: {e}")
                self.index = None
                self.metadata = []
        else:
            self.index = None
            self.metadata = []
            print("Warning: Using simple list storage for vectors.")

    def _get_text_for_embedding(self, symbol: str, analysis_data: Dict[str, Any]) -> str:
        """
        Convert analysis data into a text string for embedding.
        We'll include symbol, signal, score, reasons, and key indicators.
        """
        parts = [
            f"股票代码: {symbol}",
            f"信号: {analysis_data.get('signal', '')}",
            f"评分: {analysis_data.get('score', '')}",
            f"理由: {'; '.join(analysis_data.get('reasons', []))}",
        ]
        indicators = analysis_data.get('indicators', {})
        if indicators:
            ind_str = ', '.join([f"{k}: {v}" for k, v in indicators.items() if v is not None])
            parts.append(f"技术指标: {ind_str}")
        return "。 ".join(parts)

    def add(self, symbol: str, analysis_data: Dict[str, Any]) -> str:
        """
        Add an analysis result to the vector store.
        Returns a unique ID for the stored item.
        """
        # Generate a simple ID
        import time
        uid = f"{symbol}_{int(time.time()*1000)}"
        entry = {
            "id": uid,
            "symbol": symbol,
            "timestamp": analysis_data.get('timestamp', int(time.time())),
            "data": analysis_data
        }
        # If we have model and index, encode and add
        if self.model is not None and self.index is not None:
            text = self._get_text_for_embedding(symbol, analysis_data)
            try:
                embedding = self.model.encode([text])
                # FAISS expects float32
                embedding_np = np.array(embedding).astype('float32')
                self.index.add(embedding_np)
                self.metadata.append(entry)
                # Persist
                self._persist()
                return uid
            except Exception as e:
                print(f"Error adding to vector store: {e}")
                # Fallback to list only
                self.metadata.append(entry)
                self._persist()
                return uid
        else:
            # Simple list storage
            self.metadata.append(entry)
            self._persist()
            return uid

    def search(self, symbol: str, analysis_data: Dict[str, Any], top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Search for similar historical analyses.
        Returns list of metadata dicts (including data) sorted by similarity.
        """
        if self.model is None or self.index is None or len(self.metadata) == 0:
            # Fallback: return most recent entries for this symbol
            filtered = [m for m in self.metadata if m['symbol'] == symbol]
            # Sort by timestamp descending
            filtered.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
            return filtered[:top_k]
        text = self._get_text_for_embedding(symbol, analysis_data)
        try:
            embedding = self.model.encode([text])
            embedding_np = np.array(embedding).astype('float32')
            distances, indices = self.index.search(embedding_np, top_k)
            results = []
            for idx, dist in zip(indices[0], distances[0]):
                if idx < len(self.metadata):
                    results.append(self.metadata[idx])
            return results
        except Exception as e:
            print(f"Error searching vector store: {e}")
            # Fallback
            filtered = [m for m in self.metadata if m['symbol'] == symbol]
            filtered.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
            return filtered[:top_k]

    def _persist(self):
        """Save index and metadata to disk."""
        if self.index is not None:
            try:
                faiss.write_index(self.index, self.index_path)
            except Exception as e:
                print(f"Warning: Could not persist FAISS index: {e}")
        try:
            with open(self.metadata_path, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Warning: Could not persist metadata: {e}")

    def get_all(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all stored entries, optionally filtered by symbol."""
        if symbol is None:
            return self.metadata.copy()
        return [m for m in self.metadata if m['symbol'] == symbol]

# Global instance for easy use
vector_store = VectorStore()