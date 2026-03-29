"""
事件触发器 - 定义回测中的事件驱动信号
"""
import pandas as pd
import numpy as np
from abc import ABC, abstractmethod
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class EventSignal:
    """事件触发信号"""
    action: str         # "BUY" / "SELL" / "HOLD"
    event_name: str     # 触发的事件名
    confidence: float   # 0~1


class EventTrigger(ABC):
    """事件触发器基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def check(self, df: pd.DataFrame, current_idx: int) -> Optional[EventSignal]:
        """
        检查当前时刻是否触发事件
        :param df: 完整历史数据
        :param current_idx: 当前行索引位置
        :return: EventSignal 或 None
        """
        pass


class VolumeBreakoutTrigger(EventTrigger):
    """成交量突增事件（量比 > threshold）"""

    def __init__(self, threshold: float = 2.0):
        self.threshold = threshold

    @property
    def name(self) -> str:
        return f"成交量突增(>{self.threshold}x)"

    def check(self, df: pd.DataFrame, current_idx: int) -> Optional[EventSignal]:
        if current_idx < 5:
            return None
        vol = df["volume"].iloc[current_idx]
        avg_vol = df["volume"].iloc[current_idx - 5:current_idx].mean()
        if avg_vol == 0:
            return None

        ratio = vol / avg_vol
        if ratio >= self.threshold:
            close = df["close"].iloc[current_idx]
            prev_close = df["close"].iloc[current_idx - 1]
            if close > prev_close:
                return EventSignal("BUY", self.name, min(0.5 + ratio / 10, 0.9))
            else:
                return EventSignal("SELL", self.name, min(0.5 + ratio / 10, 0.9))
        return None


class MACDGoldenCrossTrigger(EventTrigger):
    """MACD 金叉事件"""

    @property
    def name(self) -> str:
        return "MACD金叉"

    def check(self, df: pd.DataFrame, current_idx: int) -> Optional[EventSignal]:
        if current_idx < 26:
            return None

        close = df["close"].iloc[:current_idx + 1]
        exp12 = close.ewm(span=12, adjust=False).mean()
        exp26 = close.ewm(span=26, adjust=False).mean()
        macd = exp12 - exp26
        signal = macd.ewm(span=9, adjust=False).mean()

        if macd.iloc[-1] > signal.iloc[-1] and macd.iloc[-2] <= signal.iloc[-2]:
            return EventSignal("BUY", self.name, 0.7)
        if macd.iloc[-1] < signal.iloc[-1] and macd.iloc[-2] >= signal.iloc[-2]:
            return EventSignal("SELL", f"MACD死叉", 0.7)
        return None


class PriceBreakoutTrigger(EventTrigger):
    """价格突破 N 日新高/新低"""

    def __init__(self, lookback: int = 20):
        self.lookback = lookback

    @property
    def name(self) -> str:
        return f"价格突破{self.lookback}日"

    def check(self, df: pd.DataFrame, current_idx: int) -> Optional[EventSignal]:
        if current_idx < self.lookback:
            return None

        window = df.iloc[current_idx - self.lookback:current_idx]
        current_close = df["close"].iloc[current_idx]
        high_n = window["high"].max()
        low_n = window["low"].min()

        if current_close > high_n:
            return EventSignal("BUY", f"突破{self.lookback}日新高", 0.65)
        if current_close < low_n:
            return EventSignal("SELL", f"跌破{self.lookback}日新低", 0.65)
        return None


class RSIExtremeTrigger(EventTrigger):
    """RSI 极值事件"""

    def __init__(self, overbought: float = 75, oversold: float = 25):
        self.overbought = overbought
        self.oversold = oversold

    @property
    def name(self) -> str:
        return f"RSI极值({self.oversold}/{self.overbought})"

    def check(self, df: pd.DataFrame, current_idx: int) -> Optional[EventSignal]:
        if current_idx < 14:
            return None

        close = df["close"].iloc[:current_idx + 1]
        delta = close.diff()
        up = delta.clip(lower=0).rolling(14).mean()
        down = (-delta.clip(upper=0)).rolling(14).mean()
        rs = up.iloc[-1] / down.iloc[-1] if down.iloc[-1] != 0 else 0
        rsi = 100 - (100 / (1 + rs)) if rs != 0 else 50

        if rsi <= self.oversold:
            return EventSignal("BUY", f"RSI超卖({rsi:.0f})", 0.6)
        if rsi >= self.overbought:
            return EventSignal("SELL", f"RSI超买({rsi:.0f})", 0.6)
        return None


# 事件注册表
EVENT_REGISTRY = {
    "volume_breakout": VolumeBreakoutTrigger,
    "macd_golden_cross": MACDGoldenCrossTrigger,
    "price_breakout_20": lambda: PriceBreakoutTrigger(20),
    "price_breakout_60": lambda: PriceBreakoutTrigger(60),
    "rsi_extreme": RSIExtremeTrigger,
}


def get_available_events() -> List[str]:
    return list(EVENT_REGISTRY.keys())


def create_triggers(event_names: List[str]) -> List[EventTrigger]:
    triggers = []
    for name in event_names:
        factory = EVENT_REGISTRY.get(name)
        if factory:
            triggers.append(factory() if callable(factory) else factory)
    return triggers
