"""
AKShare 数据提供者 - 主数据源（免费）
"""
import akshare as ak
import pandas as pd
from datetime import datetime
from typing import Optional

from .base_provider import BaseDataProvider, DataProviderError, FundamentalData


COLUMN_MAP = {
    "日期": "date",
    "开盘": "open",
    "收盘": "close",
    "最高": "high",
    "最低": "low",
    "成交量": "volume",
    "成交额": "amount",
    "振幅": "amplitude",
    "涨跌幅": "change_pct",
    "涨跌额": "change",
    "换手率": "turnover",
}


class AKShareProvider(BaseDataProvider):

    @property
    def name(self) -> str:
        return "AKShare"

    @staticmethod
    def _exchange_prefix(symbol: str) -> str:
        """根据股票代码自动判断交易所前缀（sh/sz）"""
        code = symbol.strip().lstrip("0")  # 去掉前导零后取首位
        # 上交所：60xxxx / 68xxxx (科创板)
        if symbol.startswith("6") or symbol.startswith("9"):
            return "sh"
        # 深交所：000/001/002/003/300/301
        return "sz"

    def get_history(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """通过 AKShare stock_zh_a_daily（新浪财经）获取 A 股历史行情数据"""
        try:
            prefix = self._exchange_prefix(symbol)
            full_symbol = f"{prefix}{symbol}"
            df = ak.stock_zh_a_daily(
                symbol=full_symbol,
                start_date=start_date,
                end_date=end_date,
                adjust="qfq",  # 前复权，消除分红/拆股对历史均线的影响
            )
            if df is None or df.empty:
                raise DataProviderError(f"AKShare 返回空数据: {symbol}")

            # stock_zh_a_daily 的列名已为英文（date/open/high/low/close/volume/amount...）
            df["date"] = pd.to_datetime(df["date"])
            df = df.set_index("date").sort_index()

            # 补充 change_pct 列（如果没有）
            if "change_pct" not in df.columns and "close" in df.columns:
                df["change_pct"] = df["close"].pct_change() * 100

            return df

        except DataProviderError:
            raise
        except Exception as e:
            raise DataProviderError(f"AKShare 获取行情失败 [{symbol}]: {e}") from e

    def get_fundamental(self, symbol: str) -> FundamentalData:
        """通过 AKShare 获取基本面数据"""
        name = symbol
        pe_ratio = None
        pb_ratio = None
        roe = None
        debt_ratio = None
        revenue = None
        net_profit = None
        gross_margin = None

        # 尝试获取股票基本信息（名称）
        try:
            info_df = ak.stock_individual_info_em(symbol=symbol)
            if info_df is not None and not info_df.empty:
                info_dict = dict(zip(info_df.iloc[:, 0], info_df.iloc[:, 1]))
                name = info_dict.get("股票简称", symbol)
        except Exception:
            pass

        # 尝试获取市盈率、市净率（实时行情中包含）
        try:
            spot_df = ak.stock_zh_a_spot_em()
            if spot_df is not None and not spot_df.empty:
                row = spot_df[spot_df["代码"] == symbol]
                if not row.empty:
                    r = row.iloc[0]
                    pe_ratio = _safe_float(r.get("市盈率-动态"))
                    pb_ratio = _safe_float(r.get("市净率"))
        except Exception:
            pass

        # 尝试获取财务指标（ROE、毛利率等）
        try:
            fin_df = ak.stock_financial_analysis_indicator(symbol=symbol, start_year="2022")
            if fin_df is not None and not fin_df.empty:
                latest = fin_df.iloc[0]  # 最新一期
                # 列名因 AKShare 版本而异，尝试常见列名
                roe = _find_col(latest, ["净资产收益率(%)", "ROE(%)", "加权净资产收益率(%)"])
                gross_margin = _find_col(latest, ["销售毛利率(%)", "毛利率(%)"])
        except Exception:
            pass

        # 尝试获取资产负债率（资产负债表）
        try:
            bal_df = ak.stock_balance_sheet_by_report_dt(symbol=symbol)
            if bal_df is not None and not bal_df.empty:
                latest = bal_df.iloc[0]
                total_assets = _find_col(latest, ["资产总计", "总资产"])
                total_liab = _find_col(latest, ["负债合计", "总负债"])
                if total_assets and total_liab and total_assets > 0:
                    debt_ratio = round(total_liab / total_assets * 100, 2)
        except Exception:
            pass

        # 尝试获取营收和净利润（利润表）
        try:
            profit_df = ak.stock_profit_statement_by_report_dt(symbol=symbol)
            if profit_df is not None and not profit_df.empty:
                latest = profit_df.iloc[0]
                revenue_raw = _find_col(latest, ["营业收入", "营业总收入"])
                profit_raw = _find_col(latest, ["净利润", "归属于母公司所有者的净利润"])
                if revenue_raw is not None:
                    revenue = round(revenue_raw / 10000, 2)  # 转换为万元
                if profit_raw is not None:
                    net_profit = round(profit_raw / 10000, 2)
        except Exception:
            pass

        return FundamentalData(
            symbol=symbol,
            name=name,
            pe_ratio=pe_ratio,
            pb_ratio=pb_ratio,
            roe=roe,
            debt_ratio=debt_ratio,
            revenue=revenue,
            net_profit=net_profit,
            gross_margin=gross_margin,
        )


def _safe_float(val) -> Optional[float]:
    """安全转换为 float，失败返回 None"""
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _find_col(row, col_names: list) -> Optional[float]:
    """在 Series 中查找多个候选列名中的第一个有效值"""
    for col in col_names:
        if col in row.index:
            return _safe_float(row[col])
    return None
