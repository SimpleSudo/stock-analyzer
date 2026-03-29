"""
RAG 上下文构建器
- 检索相关文档 + 历史相似分析
- 组装为 LLM prompt 的上下文段落
"""
import logging
from typing import Optional
from .document_loader import load_stock_announcements, load_stock_research
from memory.vector_store import vector_store

logger = logging.getLogger(__name__)


def build_analysis_context(
    symbol: str,
    current_analysis: dict = None,
    max_docs: int = 5,
    max_similar: int = 3,
) -> str:
    """
    为 LLM 构建 RAG 上下文
    :return: 格式化的上下文文本
    """
    sections = []

    # 1. 近期公告/新闻
    announcements = load_stock_announcements(symbol, limit=max_docs)
    if announcements:
        news_text = "\n".join(
            f"- [{d.get('time', '')}] {d.get('title', '')}" for d in announcements[:max_docs]
        )
        sections.append(f"## 近期新闻公告\n{news_text}")

    # 2. 研报
    research = load_stock_research(symbol, limit=max_docs)
    if research:
        research_text = "\n".join(
            f"- [{d.get('date', '')}] {d.get('institution', '')}: {d.get('title', '')}"
            for d in research[:max_docs]
        )
        sections.append(f"## 机构研报\n{research_text}")

    # 3. 历史相似分析（从向量存储检索）
    if current_analysis:
        try:
            similar = vector_store.search(symbol, current_analysis, top_k=max_similar)
            if similar:
                similar_text = []
                for s in similar:
                    data = s.get("data", {})
                    similar_text.append(
                        f"- 信号: {data.get('signal', '?')} | "
                        f"评分: {data.get('score', '?')} | "
                        f"理由: {'; '.join(data.get('reasons', [])[:3])}"
                    )
                sections.append(f"## 历史相似分析\n" + "\n".join(similar_text))
        except Exception as e:
            logger.debug("检索相似分析失败: %s", e)

    if not sections:
        return ""

    return "\n\n".join(sections)
