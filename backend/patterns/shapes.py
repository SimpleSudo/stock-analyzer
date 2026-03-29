"""
K 线形态定义
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class PatternMatch:
    """形态匹配结果"""
    name: str           # 形态名称
    name_en: str        # 英文名
    direction: str      # "bullish" / "bearish" / "neutral"
    confidence: float   # 0~1 可信度
    start_idx: int      # 起始索引
    end_idx: int        # 结束索引
    description: str    # 描述
    target_pct: Optional[float] = None  # 预期涨跌幅
