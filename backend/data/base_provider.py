"""
数据提供者抽象层 - 定义所有数据源必须实现的接口
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
import pandas as pd


class DataProviderError(Exception):
    """数据提供者异常 - 当所有数据源都失败时抛出"""
    pass


@dataclass
class FundamentalData:
    """基本面数据契约 - 任何 Provider 都必须返回此结构"""
    symbol: str
    name: str
    pe_ratio: Optional[float] = None    # 市盈率（TTM）
    pb_ratio: Optional[float] = None    # 市净率
    roe: Optional[float] = None         # 净资产收益率（%）
    debt_ratio: Optional[float] = None  # 资产负债率（%）
    revenue: Optional[float] = None     # 营业收入（万元）
    net_profit: Optional[float] = None  # 净利润（万元）
    gross_margin: Optional[float] = None  # 毛利率（%）


class BaseDataProvider(ABC):
    """数据提供者抽象基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        """数据源名称，用于日志和响应标注"""
        pass

    @abstractmethod
    def get_history(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
    ) -> pd.DataFrame:
        """
        获取历史行情数据。

        :param symbol: A 股代码，如 "000001"
        :param start_date: 开始日期，格式 "YYYYMMDD"
        :param end_date: 结束日期，格式 "YYYYMMDD"
        :return: DataFrame，必须包含列: date(index), open, high, low, close, volume
                 可选列: amount, change_pct, change, turnover
        :raises DataProviderError: 获取失败时抛出，不返回空 DataFrame
        """
        pass

    @abstractmethod
    def get_fundamental(self, symbol: str) -> FundamentalData:
        """
        获取基本面数据。

        :param symbol: A 股代码
        :return: FundamentalData 实例，部分字段可为 None
        :raises DataProviderError: 获取失败时抛出
        """
        pass
