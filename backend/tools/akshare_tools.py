import akshare as ak
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

class AkshareTools:
    """封装AKShare数据获取接口，提供统一的工具方法"""

    @staticmethod
    def get_stock_hist(symbol: str, period: str = "daily", 
                       start_date: Optional[str] = None, 
                       end_date: Optional[str] = None,
                       adjust: str = "") -> Optional[pd.DataFrame]:
        """
        获取个股历史行情数据
        :param symbol: 股票代码，如 "000001"
        :param period: 周期，默认 "daily"
        :param start_date: 开始日期，格式 "YYYYMMDD"，默认为一年前
        :param end_date: 结束日期，格式 "YYYYMMDD"，默认为今天
        :param adjust: 复权类型，"" 不复权，"qfq" 前复权，"hfq" 后复权
        :return: 包含历史行情的 DataFrame
        """
        try:
            if not start_date:
                start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
            if not end_date:
                end_date = datetime.now().strftime('%Y%m%d')
            
            df = ak.stock_zh_a_hist(symbol=symbol, period=period, 
                                    start_date=start_date, end_date=end_date, adjust=adjust)
            if df.empty:
                return None
            
            # 标准化列名
            df = df.rename(columns={
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
                "换手率": "turnover"
            })
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            return df
        except Exception as e:
            print(f"Error fetching stock hist for {symbol}: {e}")
            return None

    @staticmethod
    def get_stock_financial_analysis_indicator(symbol: str, 
                                               start_year: str = "2020") -> Optional[pd.DataFrame]:
        """
        获取财务分析指标（每年或每季度）
        :param symbol: 股票代码
        :param start_year: 开始年份，默认 "2020"
        :return: 财务指标 DataFrame
        """
        try:
            df = ak.stock_financial_analysis_indicator(symbol=symbol, start_year=start_year)
            if df.empty:
                return None
            return df
        except Exception as e:
            print(f"Error fetching financial indicators for {symbol}: {e}")
            return None

    @staticmethod
    def get_stock_balance_sheet_by_report_dt(symbol: str, 
                                             start_year: str = "2020") -> Optional[pd.DataFrame]:
        """
        获取资产负债表
        :param symbol: 股票代码
        :param start_year: 开始年份
        :return: 资产负债表 DataFrame
        """
        try:
            df = ak.stock_balance_sheet_by_report_dt(symbol=symbol, start_year=start_year)
            if df.empty:
                return None
            return df
        except Exception as e:
            print(f"Error fetching balance sheet for {symbol}: {e}")
            return None

    @staticmethod
    def get_stock_profit_statement_by_report_dt(symbol: str, 
                                                start_year: str = "2020") -> Optional[pd.DataFrame]:
        """
        获取利润表
        :param symbol: 股票代码
        :param start_year: 开始年份
        :return: 利润表 DataFrame
        """
        try:
            df = ak.stock_profit_statement_by_report_dt(symbol=symbol, start_year=start_year)
            if df.empty:
                return None
            return df
        except Exception as e:
            print(f"Error fetching profit statement for {symbol}: {e}")
            return None

    @staticmethod
    def get_stock_cash_flow_statement_by_report_dt(symbol: str, 
                                                   start_year: str = "2020") -> Optional[pd.DataFrame]:
        """
        获取现金流量表
        :param symbol: 股票代码
        :param start_year: 开始年份
        :return: 现金流量表 DataFrame
        """
        try:
            df = ak.stock_cash_flow_statement_by_report_dt(symbol=symbol, start_year=start_year)
            if df.empty:
                return None
            return df
        except Exception as e:
            print(f"Error fetching cash flow statement for {symbol}: {e}")
            return None

    @staticmethod
    def get_stock_realtime_quote(symbol: str) -> Optional[Dict]:
        """
        获取实时行情（单只股票）
        :param symbol: 股票代码
        :return: 实时行情字典
        """
        try:
            df = ak.stock_zh_a_spot_em()
            # 过滤出目标股票
            df_filtered = df[df['代码'] == symbol]
            if df_filtered.empty:
                return None
            # 转换为字典
            row = df_filtered.iloc[0]
            return {
                "symbol": row['代码'],
                "name": row['名称'],
                "price": float(row['最新价']),
                "change": float(row['涨跌额']),
                "change_pct": float(row['涨跌幅']),
                "volume": float(row['成交量']),
                "amount": float(row['成交额']),
                "amplitude": float(row['振幅']),
                "turnover": float(row['换手率'])
            }
        except Exception as e:
            print(f"Error fetching realtime quote for {symbol}: {e}")
            return None

    @staticmethod
    def get_stock_news(symbol: str, limit: int = 10) -> List[Dict]:
        """
        获取股票相关新闻（简易版，可后续替换为专业新闻接口）
        :param symbol: 股票代码
        :param limit: 返回条数
        :return: 新闻列表，每条包含 title, time, source, url
        """
        try:
            # 使用东方财富新闻接口作为示例
            df = ak.stock_news_em(symbol=symbol)
            if df.empty:
                return []
            # 取前 limit 条
            df = df.head(limit)
            news_list = []
            for _, row in df.iterrows():
                news_list.append({
                    "title": row['新闻标题'],
                    "time": row['发布时间'],
                    "source": row['文章来源'],
                    "url": row['新闻链接']
                })
            return news_list
        except Exception as e:
            print(f"Error fetching news for {symbol}: {e}")
            return []