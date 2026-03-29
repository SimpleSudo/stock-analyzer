"""
情绪分析 NLP 引擎
- FinBERT 本地推理（默认）
- LLM API 情绪分类（备用）
- 关键词匹配（降级兜底）
通过 SENTIMENT_PROVIDER 环境变量切换：finbert / llm / keyword
"""
import os
import logging
from abc import ABC, abstractmethod
from typing import List

logger = logging.getLogger(__name__)


class BaseSentimentAnalyzer(ABC):
    @abstractmethod
    def analyze_texts(self, texts: List[str]) -> List[float]:
        """对文本列表进行情绪分析，返回 [-1, +1] 的分数列表"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        pass


class FinBERTAnalyzer(BaseSentimentAnalyzer):
    """使用 ProsusAI/finbert 进行金融情绪分类"""

    def __init__(self, model_name: str = "ProsusAI/finbert"):
        self.model_name = model_name
        self._pipeline = None
        self._loaded = False

    def _load(self):
        if self._loaded:
            return
        try:
            from transformers import pipeline
            self._pipeline = pipeline(
                "sentiment-analysis",
                model=self.model_name,
                tokenizer=self.model_name,
                top_k=None,
                truncation=True,
                max_length=512,
            )
            self._loaded = True
            logger.info("FinBERT 模型加载成功")
        except Exception as e:
            logger.warning("FinBERT 加载失败: %s", e)
            self._pipeline = None
            self._loaded = True

    def is_available(self) -> bool:
        self._load()
        return self._pipeline is not None

    def analyze_texts(self, texts: List[str]) -> List[float]:
        self._load()
        if not self._pipeline or not texts:
            return [0.0] * len(texts)

        scores = []
        try:
            # FinBERT 输出: [{"label": "positive", "score": 0.9}, ...]
            results = self._pipeline(texts, batch_size=16)
            for result in results:
                # result is list of dicts for each label
                score_map = {r["label"]: r["score"] for r in result}
                pos = score_map.get("positive", 0)
                neg = score_map.get("negative", 0)
                scores.append(round(pos - neg, 4))
        except Exception as e:
            logger.warning("FinBERT 推理失败: %s", e)
            scores = [0.0] * len(texts)
        return scores


class LLMSentimentAnalyzer(BaseSentimentAnalyzer):
    """使用 LLM API 进行情绪分类"""

    def is_available(self) -> bool:
        from llm.factory import LLMFactory
        llm = LLMFactory.create_llm()
        return llm is not None and llm.is_available()

    def analyze_texts(self, texts: List[str]) -> List[float]:
        if not texts:
            return []
        from llm.factory import LLMFactory
        llm = LLMFactory.create_llm()
        if llm is None:
            return [0.0] * len(texts)

        scores = []
        # 批量处理：每次最多 10 条
        for i in range(0, len(texts), 10):
            batch = texts[i:i + 10]
            numbered = "\n".join(f"{j + 1}. {t}" for j, t in enumerate(batch))
            prompt = (
                f"请对以下{len(batch)}条 A 股相关新闻标题进行情绪分析。"
                f"对每条新闻输出一个 -1 到 +1 的情绪分数（-1 极度负面，0 中性，+1 极度正面）。"
                f"只输出数字，每行一个，不要其他文字。\n\n{numbered}"
            )
            try:
                response = llm.generate(prompt, max_tokens=200, temperature=0)
                lines = response.strip().split("\n")
                for line in lines:
                    try:
                        val = float(line.strip().lstrip("0123456789. "))
                        scores.append(max(-1, min(1, val)))
                    except ValueError:
                        scores.append(0.0)
            except Exception as e:
                logger.warning("LLM 情绪分析失败: %s", e)
                scores.extend([0.0] * len(batch))

        return scores[:len(texts)]


class KeywordSentimentAnalyzer(BaseSentimentAnalyzer):
    """关键词匹配降级方案"""

    POSITIVE = ['增长', '上涨', '利好', '买入', '推荐', '增持', '看好', '突破', '创新高', '大涨', '涨停']
    NEGATIVE = ['下跌', '利空', '卖出', '减持', '看空', '跌', '风险', '亏损', '暴跌', '跌停', '警示']

    def is_available(self) -> bool:
        return True

    def analyze_texts(self, texts: List[str]) -> List[float]:
        scores = []
        for text in texts:
            pos = sum(1 for kw in self.POSITIVE if kw in text)
            neg = sum(1 for kw in self.NEGATIVE if kw in text)
            total = pos + neg
            if total == 0:
                scores.append(0.0)
            else:
                scores.append(round((pos - neg) / total, 4))
        return scores


def get_sentiment_analyzer() -> BaseSentimentAnalyzer:
    """
    根据 SENTIMENT_PROVIDER 环境变量返回分析器。
    优先级：finbert → llm → keyword
    """
    provider = os.getenv("SENTIMENT_PROVIDER", "finbert").lower()

    if provider == "finbert":
        analyzer = FinBERTAnalyzer()
        if analyzer.is_available():
            return analyzer
        logger.info("FinBERT 不可用，尝试 LLM 降级")

    if provider in ("finbert", "llm"):
        analyzer = LLMSentimentAnalyzer()
        if analyzer.is_available():
            return analyzer
        logger.info("LLM 情绪分析不可用，降级到关键词匹配")

    return KeywordSentimentAnalyzer()
