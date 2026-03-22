"""
数据源工厂 - 实现双数据源故障转移
主数据源: AKShare（免费）
备用数据源: Tushare（需要 Token）

重要原则：绝不返回 mock 数据，所有数据源失败时明确抛出异常
"""
import pandas as pd
from typing import Tuple

from .base_provider import DataProviderError, FundamentalData
from .akshare_provider import AKShareProvider
from .tushare_provider import TushareProvider


def get_history_with_fallback(
    symbol: str,
    start_date: str,
    end_date: str,
) -> Tuple[pd.DataFrame, str]:
    """
    获取历史行情，优先使用 AKShare，失败自动切换 Tushare。

    :return: (DataFrame, provider_name) 元组
    :raises DataProviderError: 所有数据源均失败时抛出，包含详细错误信息
    """
    providers = [AKShareProvider(), TushareProvider()]
    errors = []

    for provider in providers:
        try:
            df = provider.get_history(symbol, start_date, end_date)
            if df is not None and not df.empty:
                return df, provider.name
        except DataProviderError as e:
            errors.append(str(e))
        except Exception as e:
            errors.append(f"{provider.name}: {e}")

    raise DataProviderError(
        f"所有数据源均失败，无法获取 [{symbol}] 的行情数据。"
        f"详情: {' | '.join(errors)}"
    )


def get_fundamental_with_fallback(symbol: str) -> Tuple[FundamentalData, str]:
    """
    获取基本面数据，优先使用 AKShare，失败自动切换 Tushare。

    :return: (FundamentalData, provider_name) 元组
    :raises DataProviderError: 所有数据源均失败时抛出
    """
    providers = [AKShareProvider(), TushareProvider()]
    errors = []

    for provider in providers:
        try:
            data = provider.get_fundamental(symbol)
            return data, provider.name
        except DataProviderError as e:
            errors.append(str(e))
        except Exception as e:
            errors.append(f"{provider.name}: {e}")

    raise DataProviderError(
        f"所有数据源均失败，无法获取 [{symbol}] 的基本面数据。"
        f"详情: {' | '.join(errors)}"
    )
