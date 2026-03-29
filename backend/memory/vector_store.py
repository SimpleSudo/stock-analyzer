"""
向量存储 - 用于存储和检索历史分析结果
- sentence-transformers 编码 + FAISS 相似度搜索
- 批量写盘（累计 N 条或调用 flush()）
- 自动清理过期数据（max_entries / max_age_days）
"""
import json
import os
import time
import threading
import logging
from typing import List, Dict, Any, Optional

import numpy as np

logger = logging.getLogger(__name__)

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
    向量存储：支持 FAISS 索引 + 元数据持久化。
    批量写盘策略：累计 _FLUSH_THRESHOLD 条后自动刷盘，或手动调用 flush()。
    """

    _FLUSH_THRESHOLD = 10
    _MAX_ENTRIES = 1000
    _MAX_AGE_DAYS = 90

    def __init__(
        self,
        model_name: str = "shibing624/text2vec-base-chinese",
        index_path: str = "./vector_store.index",
        metadata_path: str = "./vector_store_metadata.json",
    ):
        self.model_name = model_name
        self.index_path = index_path
        self.metadata_path = metadata_path
        self.model = None
        self.index = None
        self.metadata: List[Dict[str, Any]] = []
        self._dirty_count = 0
        self._lock = threading.Lock()
        self._initialize()

    def _initialize(self):
        if SentenceTransformer is not None:
            try:
                self.model = SentenceTransformer(self.model_name)
            except Exception as e:
                logger.warning("Could not load sentence transformer model: %s", e)
                self.model = None
        else:
            logger.warning("sentence-transformers not installed, using fallback storage.")

        if faiss is not None and self.model is not None:
            try:
                dim = self.model.encode(["test"]).shape[1]
                self.index = faiss.IndexFlatL2(dim)
                if os.path.exists(self.index_path):
                    self.index = faiss.read_index(self.index_path)
                    if os.path.exists(self.metadata_path):
                        with open(self.metadata_path, "r", encoding="utf-8") as f:
                            self.metadata = json.load(f)
                else:
                    self.metadata = []
            except Exception as e:
                logger.warning("Could not initialize FAISS: %s", e)
                self.index = None
                self.metadata = []
        else:
            self.index = None
            self.metadata = []

    def _get_text_for_embedding(self, symbol: str, analysis_data: Dict[str, Any]) -> str:
        parts = [
            f"股票代码: {symbol}",
            f"信号: {analysis_data.get('signal', '')}",
            f"评分: {analysis_data.get('score', '')}",
            f"理由: {'; '.join(analysis_data.get('reasons', []))}",
        ]
        indicators = analysis_data.get("indicators", {})
        if indicators:
            ind_str = ", ".join([f"{k}: {v}" for k, v in indicators.items() if v is not None])
            parts.append(f"技术指标: {ind_str}")
        return "。 ".join(parts)

    def add(self, symbol: str, analysis_data: Dict[str, Any]) -> str:
        uid = f"{symbol}_{int(time.time() * 1000)}"
        entry = {
            "id": uid,
            "symbol": symbol,
            "timestamp": analysis_data.get("timestamp", int(time.time())),
            "data": analysis_data,
        }

        with self._lock:
            if self.model is not None and self.index is not None:
                text = self._get_text_for_embedding(symbol, analysis_data)
                try:
                    embedding = self.model.encode([text])
                    embedding_np = np.array(embedding).astype("float32")
                    self.index.add(embedding_np)
                except Exception as e:
                    logger.warning("Error encoding for vector store: %s", e)

            self.metadata.append(entry)
            self._dirty_count += 1

            if self._dirty_count >= self._FLUSH_THRESHOLD:
                self._async_persist()

        return uid

    def search(self, symbol: str, analysis_data: Dict[str, Any], top_k: int = 3) -> List[Dict[str, Any]]:
        if self.model is None or self.index is None or len(self.metadata) == 0:
            return self._fallback_search(symbol, top_k)

        text = self._get_text_for_embedding(symbol, analysis_data)
        try:
            embedding = self.model.encode([text])
            embedding_np = np.array(embedding).astype("float32")
            distances, indices = self.index.search(embedding_np, top_k)
            results = []
            for idx in indices[0]:
                if 0 <= idx < len(self.metadata):
                    results.append(self.metadata[idx])
            return results
        except Exception as e:
            logger.warning("Error searching vector store: %s", e)
            return self._fallback_search(symbol, top_k)

    def _fallback_search(self, symbol: str, top_k: int) -> List[Dict[str, Any]]:
        filtered = [m for m in self.metadata if m["symbol"] == symbol]
        filtered.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
        return filtered[:top_k]

    def flush(self):
        """手动刷盘"""
        with self._lock:
            if self._dirty_count > 0:
                self._persist_sync()

    def cleanup(self, max_entries: int = None, max_age_days: int = None):
        """清理过期或超量数据"""
        max_entries = max_entries or self._MAX_ENTRIES
        max_age_days = max_age_days or self._MAX_AGE_DAYS
        cutoff = time.time() - max_age_days * 86400

        with self._lock:
            original_len = len(self.metadata)
            # 按时间过滤
            self.metadata = [m for m in self.metadata if m.get("timestamp", 0) > cutoff]
            # 超量截断（保留最新的）
            if len(self.metadata) > max_entries:
                self.metadata = self.metadata[-max_entries:]

            if len(self.metadata) < original_len:
                # 需要重建 FAISS 索引
                self._rebuild_index()
                self._persist_sync()
                logger.info("VectorStore cleanup: %d -> %d entries", original_len, len(self.metadata))

    def _rebuild_index(self):
        """根据当前 metadata 重建 FAISS 索引"""
        if self.model is None or faiss is None:
            return
        try:
            dim = self.model.encode(["test"]).shape[1]
            self.index = faiss.IndexFlatL2(dim)
            if self.metadata:
                texts = [
                    self._get_text_for_embedding(m["symbol"], m.get("data", {}))
                    for m in self.metadata
                ]
                embeddings = self.model.encode(texts)
                self.index.add(np.array(embeddings).astype("float32"))
        except Exception as e:
            logger.warning("Failed to rebuild FAISS index: %s", e)

    def _async_persist(self):
        """异步写盘（在后台线程中执行）"""
        self._dirty_count = 0
        # 创建数据快照
        metadata_snapshot = self.metadata.copy()
        index_snapshot = self.index

        def _write():
            try:
                if index_snapshot is not None:
                    faiss.write_index(index_snapshot, self.index_path)
                with open(self.metadata_path, "w", encoding="utf-8") as f:
                    json.dump(metadata_snapshot, f, ensure_ascii=False)
            except Exception as e:
                logger.warning("Async persist failed: %s", e)

        threading.Thread(target=_write, daemon=True).start()

    def _persist_sync(self):
        """同步写盘"""
        self._dirty_count = 0
        try:
            if self.index is not None:
                faiss.write_index(self.index, self.index_path)
            with open(self.metadata_path, "w", encoding="utf-8") as f:
                json.dump(self.metadata, f, ensure_ascii=False)
        except Exception as e:
            logger.warning("Sync persist failed: %s", e)

    def get_all(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        if symbol is None:
            return self.metadata.copy()
        return [m for m in self.metadata if m["symbol"] == symbol]


# Global instance
vector_store = VectorStore()
