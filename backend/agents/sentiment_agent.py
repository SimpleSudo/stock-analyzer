from .base_agent import BaseAgent
from tools.toolkit import Toolkit
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta

class SentimentAgent(BaseAgent):
    def __init__(self, llm=None, toolkit=None):
        super().__init__("Sentiment", llm, toolkit)

    def analyze(self, symbol: str) -> dict:
        """
        Perform sentiment analysis based on news.
        Returns a dict compatible with the decision committee expectations.
        """
        try:
            # Get stock news
            news_df = ak.stock_news_em(symbol=symbol)
            if news_df is None or news_df.empty:
                return {
                    "agent": self.name,
                    "score": 0,
                    "signal": "观望",
                    "reasons": ["无法获取新闻数据"],
                    "indicators": {},
                    "data": None
                }

            # Simple sentiment scoring based on keywords (in practice, use NLP model)
            positive_keywords = ['增长', '上涨', '利好', '买入', '推荐', '增持', '看好', '突', '创新高']
            negative_keywords = ['下跌', '利空', '卖出', '减持', '看空', '跌', '风险', '亏损']

            # We'll analyze the latest news (e.g., last 7 days)
            news_df['发布时间'] = pd.to_datetime(news_df['发布时间'])
            one_week_ago = datetime.now() - timedelta(days=7)
            recent_news = news_df[news_df['发布时间'] >= one_week_ago]

            if recent_news.empty:
                recent_news = news_df.head(10)  # fallback to latest 10

            pos_count = 0
            neg_count = 0
            total = len(recent_news)

            for title in recent_news['新闻标题']:
                title_lower = title.lower()
                pos_score = sum(1 for kw in positive_keywords if kw in title_lower)
                neg_score = sum(1 for kw in negative_keywords if kw in title_lower)
                if pos_score > neg_score:
                    pos_count += 1
                elif neg_score > pos_score:
                    neg_count += 1

            # Calculate sentiment score (-10 to +10)
            if total > 0:
                sentiment_score = ((pos_count - neg_count) / total) * 10
            else:
                sentiment_score = 0

            # Generate signal
            if sentiment_score >= 3:
                signal = "买入"
                reasons = [f"新闻情绪偏正面 ({pos_count}正面/{neg_count}负面)"]
            elif sentiment_score <= -3:
                signal = "卖出"
                reasons = [f"新闻情绪偏负面 ({pos_count}正面/{neg_count}负面)"]
            else:
                signal = "观望"
                reasons = [f"新闻情绪中性 ({pos_count}正面/{neg_count}负面)"]

            # Add some indicator-like data
            indicators = {
                "news_sentiment": round(sentiment_score, 2),
                "positive_news": pos_count,
                "negative_news": neg_count,
                "total_news_analyzed": total
            }

            return {
                "agent": self.name,
                "score": round(sentiment_score, 2),
                "signal": signal,
                "reasons": reasons,
                "indicators": indicators,
                "data": {
                    "recent_news": recent_news[['发布时间', '新闻标题']].head(5).to_dict('records') if not recent_news.empty else []
                }
            }
        except Exception as e:
            return {
                "agent": self.name,
                "score": 0,
                "signal": "错误",
                "reasons": [f"情绪分析失败: {str(e)}"],
                "indicators": {},
                "data": None
            }