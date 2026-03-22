"""
股票代码解析器
- 支持直接输入代码（000001）
- 支持输入股票名称（农产品、平安银行）→ 自动查找对应代码
- 内存缓存股票列表，首次加载后不再重复拉取
"""
import re
import akshare as ak
import pandas as pd
from typing import Optional, List, Dict

# 模块级缓存，进程生命周期内有效
_stock_list_cache: Optional[pd.DataFrame] = None


def _load_stock_list() -> pd.DataFrame:
    """加载 A 股全量代码-名称列表（带缓存）"""
    global _stock_list_cache
    if _stock_list_cache is not None:
        return _stock_list_cache
    try:
        df = ak.stock_info_a_code_name()
        # 去掉名称中可能存在的空格，方便匹配
        df["name_clean"] = df["name"].str.replace(r"\s+", "", regex=True)
        _stock_list_cache = df
        return df
    except Exception as e:
        raise RuntimeError(f"无法加载股票列表: {e}") from e


def is_stock_code(text: str) -> bool:
    """判断输入是否为标准 6 位股票代码"""
    return bool(re.fullmatch(r"\d{6}", text.strip()))


def resolve_symbol(query: str) -> str:
    """
    将用户输入解析为 6 位股票代码。
    - 若已是 6 位数字代码，直接返回
    - 否则在股票列表中做名称精确/模糊匹配
    :raises ValueError: 找不到对应股票时
    """
    query = query.strip()
    if not query:
        raise ValueError("请输入股票代码或名称")

    # 已是 6 位代码
    if is_stock_code(query):
        return query

    # 名称查找
    df = _load_stock_list()
    query_clean = re.sub(r"\s+", "", query)  # 去掉用户输入中的空格

    # 1. 精确匹配（忽略内部空格）
    exact = df[df["name_clean"] == query_clean]
    if not exact.empty:
        return exact.iloc[0]["code"]

    # 2. 部分匹配（名称包含关键词）
    partial = df[df["name_clean"].str.contains(query_clean, regex=False)]
    if len(partial) == 1:
        return partial.iloc[0]["code"]
    if len(partial) > 1:
        # 返回匹配数最少且名称最短的（最精准）
        best = partial.loc[partial["name_clean"].str.len().idxmin()]
        return best["code"]

    raise ValueError(
        f"找不到股票「{query}」，请检查名称或直接输入 6 位代码（如 000061）"
    )


def search_stocks(keyword: str, limit: int = 10) -> List[Dict]:
    """
    搜索股票，返回代码+名称列表（用于前端搜索建议）
    """
    if not keyword:
        return []
    try:
        df = _load_stock_list()
        kw = re.sub(r"\s+", "", keyword)
        # 代码前缀匹配 或 名称包含关键词
        mask = df["code"].str.startswith(kw) | df["name_clean"].str.contains(kw, regex=False)
        results = df[mask].head(limit)
        return [
            {"code": row["code"], "name": row["name_clean"]}
            for _, row in results.iterrows()
        ]
    except Exception:
        return []


def get_stock_name(query: str) -> Optional[str]:
    """
    根据代码或名称查询股票中文名称。
    - 若 query 是 6 位代码，在列表中查找对应名称
    - 若 query 是名称，先 resolve 再反查
    返回 None 时调用方自行降级。
    """
    query = query.strip()
    if not query:
        return None
    try:
        df = _load_stock_list()
        if is_stock_code(query):
            row = df[df["code"] == query]
            return row.iloc[0]["name_clean"] if not row.empty else None
        else:
            # 名称查找：先精确，再部分
            qc = re.sub(r"\s+", "", query)
            exact = df[df["name_clean"] == qc]
            if not exact.empty:
                return exact.iloc[0]["name_clean"]
            partial = df[df["name_clean"].str.contains(qc, regex=False)]
            if not partial.empty:
                best = partial.loc[partial["name_clean"].str.len().idxmin()]
                return best["name_clean"]
    except Exception:
        pass
    return None


def preload_stock_list():
    """预加载股票列表（可在应用启动时调用，避免首次请求慢）"""
    try:
        _load_stock_list()
    except Exception:
        pass  # 预加载失败不影响功能，请求时再试
