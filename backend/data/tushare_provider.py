"""
Tushare 数据提供者 - 备用数据源
需要设置环境变量 TUSHARE_TOKEN
"""
import os
import pandas as pd
from datetime import datetime
from typing import Optional

from .base_provider import BaseDataProvider, DataProviderError, FundamentalData


class TushareProvider(BaseDataProvider):

    def __init__(self):
        self._api = None

    @property
    def name(self) -> str:
        return "Tushare"

    def _get_api(self):
        """懒加载 Tushare API 实例"""
        if self._api is None:
            try:
                import tushare as ts
                token = os.getenv("TUSHARE_TOKEN", "")
                if not token:
                    raise DataProviderError("未设置 TUSHARE_TOKEN 环境变量")
                ts.set_token(token)
                self._api = ts.pro_api()
            except ImportError:
                raise DataProviderError("tushare 未安装，请执行: pip install tushare")
        return self._api

    def _to_ts_symbol(self, symbol: str) -> str:
        """将 A 股代码转换为 Tushare 格式（如 000001 -> 000001.SZ）"""
        if symbol.startswith(("0", "3")):
            return f"{symbol}.SZ"
        elif symbol.startswith(("6", "9")):
            return f"{symbol}.SH"
        return symbol

    def get_history(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """通过 Tushare 获取 A 股历史行情数据"""
        try:
            pro = self._get_api()
            ts_symbol = self._to_ts_symbol(symbol)

            df = pro.daily(ts_code=ts_symbol, start_date=start_date, end_date=end_date)
            if df is None or df.empty:
                raise DataProviderError(f"Tushare 返回空数据: {symbol}")

            # 标准化列名
            df = df.rename(columns={
                "trade_date": "date",
                "open": "open",
                "high": "high",
                "low": "low",
                "close": "close",
                "vol": "volume",
                "amount": "amount",
                "pct_chg": "change_pct",
                "change": "change",
            })
            df["date"] = pd.to_datetime(df["date"])
            df = df.set_index("date").sort_index()
            return df

        except DataProviderError:
            raise
        except Exception as e:
            raise DataProviderError(f"Tushare 获取行情失败 [{symbol}]: {e}") from e

    def get_fundamental(self, symbol: str) -> FundamentalData:
        """通过 Tushare 获取基本面数据"""
        try:
            pro = self._get_api()
            ts_symbol = self._to_ts_symbol(symbol)

            # 获取基本信息
            name = symbol
            try:
                info_df = pro.stock_basic(ts_code=ts_symbol, fields="ts_code,name")
                if info_df is not None and not info_df.empty:
                    name = info_df.iloc[0]["name"]
            except Exception:
                pass

            # 获取每日基本面（PE、PB 等）
            pe_ratio = None
            pb_ratio = None
            today = datetime.now().strftime("%Y%m%d")
            try:
                daily_basic = pro.daily_basic(
                    ts_code=ts_symbol,
                    trade_date=today,
                    fields="pe_ttm,pb,roe,total_assets,total_liab",
                )
                if daily_basic is None or daily_basic.empty:
                    # 尝试最近一个交易日
                    daily_basic = pro.daily_basic(
                        ts_code=ts_symbol,
                        fields="pe_ttm,pb,roe,total_assets,total_liab",
                    )
                    if daily_basic is not None and not daily_basic.empty:
                        daily_basic = daily_basic.head(1)

                if daily_basic is not None and not daily_basic.empty:
                    row = daily_basic.iloc[0]
                    pe_ratio = _safe_float(row.get("pe_ttm"))
                    pb_ratio = _safe_float(row.get("pb"))
            except Exception:
                pass

            return FundamentalData(
                symbol=symbol,
                name=name,
                pe_ratio=pe_ratio,
                pb_ratio=pb_ratio,
            )

        except DataProviderError:
            raise
        except Exception as e:
            raise DataProviderError(f"Tushare 获取基本面失败 [{symbol}]: {e}") from e


def _safe_float(val) -> Optional[float]:
    try:
        return float(val)
    except (TypeError, ValueError):
        return None
