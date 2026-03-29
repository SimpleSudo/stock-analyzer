"""
舆情分析 Agent
- 获取个股新闻，使用 NLP 模型（FinBERT/LLM/关键词）评分
- 输出情绪分数、信号、理由
"""
import logging
from datetime import datetime, timedelta

import akshare as ak
import pandas as pd

from .base_agent import BaseAgent
from .sentiment_nlp import get_sentiment_analyzer

logger = logging.getLogger(__name__)


class SentimentAgent(BaseAgent):
    def __init__(self, llm=None, toolkit=None):
        super().__init__("Sentiment", llm, toolkit)
        self._analyzer = None

    def _get_analyzer(self):
        if self._analyzer is None:
            self._analyzer = get_sentiment_analyzer()
        return self._analyzer

    def analyze(self, symbol: str) -> dict:
        try:
            news_df = ak.stock_news_em(symbol=symbol)
            if news_df is None or news_df.empty:
                return self._empty_result("无法获取新闻数据")

            # 筛选近 7 日新闻
            news_df["发布时间"] = pd.to_datetime(news_df["发布时间"])
            one_week_ago = datetime.now() - timedelta(days=7)
            recent = news_df[news_df["发布时间"] >= one_week_ago]
            if recent.empty:
                recent = news_df.head(10)

            titles = recent["新闻标题"].tolist()
            analyzer = self._get_analyzer()
            scores = analyzer.analyze_texts(titles)

            # 统计
            pos_count = sum(1 for s in scores if s > 0.1)
            neg_count = sum(1 for s in scores if s < -0.1)
            neu_count = len(scores) - pos_count - neg_count
            avg_score = sum(scores) / len(scores) if scores else 0

            # 映射到 -10 ~ +10
            sentiment_score = round(avg_score * 10, 2)

            # 信号判定
            if sentiment_score >= 3:
                signal = "买入"
            elif sentiment_score <= -3:
                signal = "卖出"
            else:
                signal = "观望"

            analyzer_name = type(analyzer).__name__
            reasons = [
                f"近期新闻 {len(titles)} 条：{pos_count} 正面 / {neg_count} 负面 / {neu_count} 中性",
                f"平均情绪分 {avg_score:+.3f}（引擎: {analyzer_name}）",
            ]
            # 添加最强情绪新闻
            if scores:
                max_idx = scores.index(max(scores))
                min_idx = scores.index(min(scores))
                if scores[max_idx] > 0.3:
                    reasons.append(f"最正面: {titles[max_idx][:40]}... ({scores[max_idx]:+.2f})")
                if scores[min_idx] < -0.3:
                    reasons.append(f"最负面: {titles[min_idx][:40]}... ({scores[min_idx]:+.2f})")

            indicators = {
                "news_sentiment": sentiment_score,
                "positive_news": pos_count,
                "negative_news": neg_count,
                "neutral_news": neu_count,
                "total_news": len(titles),
                "analyzer": analyzer_name,
            }

            news_preview = []
            for i, (_, row) in enumerate(recent.head(5).iterrows()):
                news_preview.append({
                    "title": row["新闻标题"],
                    "time": str(row["发布时间"]),
                    "score": scores[i] if i < len(scores) else 0,
                })

            analysis_output = {
                "agent": self.name,
                "score": sentiment_score,
                "signal": signal,
                "reasons": reasons,
                "indicators": indicators,
                "data": {"recent_news": news_preview},
            }

            try:
                self.store_analysis(symbol, analysis_output)
            except Exception as e:
                logger.warning("Failed to store sentiment analysis: %s", e)

            return analysis_output

        except Exception as e:
            logger.warning("情绪分析失败 [%s]: %s", symbol, e)
            return self._empty_result(f"情绪分析失败: {e}")

    def _empty_result(self, reason: str) -> dict:
        return {
            "agent": self.name,
            "score": 0,
            "signal": "观望",
            "reasons": [reason],
            "indicators": {},
            "data": None,
        }
