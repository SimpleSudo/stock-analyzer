"""
行业对比分析模块
- 根据股票代码内置行业映射，获取行业名称
- 通过 stock_zh_valuation_baidu + stock_financial_abstract 获取同行业代表股 PE/PB/ROE
- 计算行业中位数，判断目标股票的估值分位
"""
import time
import akshare as ak
import pandas as pd
import numpy as np
from typing import Optional

# ──────────────────────────────────────────────────────
# 主要行业代表股（每行业选10只左右流动性好的代表股，用于计算中位数）
# 代码 → 行业名
# ──────────────────────────────────────────────────────
_INDUSTRY_PEERS: dict[str, list[str]] = {
    "银行": ["000001", "600036", "601166", "601328", "600016", "600015", "600000", "002142", "002948", "601009"],
    "保险": ["601318", "601601", "601336", "600061", "601319"],
    "证券": ["000776", "600030", "601688", "600999", "000166", "601211", "002736"],
    "房地产": ["000002", "600048", "600162", "601155", "000房", "001979"],
    "医药生物": ["600276", "000538", "300760", "603259", "600196", "002390", "000661", "300015"],
    "食品饮料": ["600519", "000858", "002304", "000568", "603288", "600809", "000799"],
    "电子": ["002415", "600745", "002230", "000725", "603986", "002371", "000783"],
    "计算机": ["300750", "002236", "600588", "300033", "002065", "000100"],
    "通信": ["000063", "002281", "300212", "600498"],
    "汽车": ["600104", "000625", "601238", "002594", "000800"],
    "机械设备": ["002508", "601100", "000157", "002357"],
    "化工": ["600309", "002648", "000792", "600884"],
    "钢铁": ["600019", "601005", "000932", "600581"],
    "有色金属": ["600547", "002460", "603993", "601600"],
    "煤炭": ["601898", "600188", "000552", "601666"],
    "电力": ["600886", "000778", "600795", "002039"],
    "农林牧渔": ["000061", "600298", "002714", "000876", "300498"],
    "纺织服装": ["002029", "600177", "601566", "002154"],
    "传媒": ["002292", "000100", "300251", "601929"],
    "军工": ["600760", "000768", "002013", "600316"],
    "建筑材料": ["000401", "600585", "002233", "601992"],
    "建筑装饰": ["601668", "601669", "601800", "000060"],
    "交通运输": ["600518", "601808", "603052", "600011"],
    "商业贸易": ["600697", "601933", "002572", "000759"],
    "休闲服务": ["000069", "600054", "002174"],
    "轻工制造": ["600166", "002044"],
    "公用事业": ["600900", "600795", "601985"],
    "综合": ["000039", "600626"],
}

# 代码段 → 行业（粗略映射，用于无精确匹配时的回退）
_CODE_TO_INDUSTRY: list[tuple[tuple, str]] = [
    (("000001", "000010"), "银行"),
    (("600000", "600019"), "银行"),
    (("600519",), "食品饮料"),
    (("000858", "000568"), "食品饮料"),
    (("000002",), "房地产"),
    (("600276", "300760"), "医药生物"),
]

# 同行 PE/PB 缓存（每小时刷新一次）
_industry_cache: dict[str, dict] = {}
_cache_ts: dict[str, float] = {}
_CACHE_TTL = 3600  # 秒


def _get_industry_by_code(symbol: str) -> str:
    """根据股票代码判断所属行业（内置映射优先，再回退到代码段推断）"""
    # 先查各行业代表股列表
    for industry, peers in _INDUSTRY_PEERS.items():
        if symbol in peers:
            return industry

    # 按代码段粗略推断
    code = int(symbol)
    if 0 <= code <= 10 or 601166 <= code <= 601999:
        return "银行"
    if 600000 <= code <= 600036:
        return "银行"
    if 600500 <= code <= 600599:
        return "化工"
    if 300000 <= code <= 300999:
        return "计算机"  # 创业板多为科技
    if 688000 <= code <= 688999:
        return "电子"    # 科创板多为电子/半导体

    return "综合"


def _fetch_pe_pb(symbol: str) -> tuple[Optional[float], Optional[float]]:
    """获取单只股票的最新 PE(TTM) 和 PB"""
    try:
        pe_df = ak.stock_zh_valuation_baidu(symbol=symbol, indicator="市盈率(TTM)")
        pe = float(pe_df.iloc[-1]["value"]) if not pe_df.empty else None
    except Exception:
        pe = None
    try:
        pb_df = ak.stock_zh_valuation_baidu(symbol=symbol, indicator="市净率")
        pb = float(pb_df.iloc[-1]["value"]) if not pb_df.empty else None
    except Exception:
        pb = None
    return pe, pb


def get_industry_comparison(
    symbol: str,
    stock_pe: Optional[float],
    stock_pb: Optional[float],
    stock_roe: Optional[float],
) -> dict:
    """
    行业横向对比分析。

    :param symbol: 6位股票代码
    :param stock_pe: 目标股票的 PE（可从外部传入，避免重复请求）
    :param stock_pb: 目标股票的 PB
    :param stock_roe: 目标股票的 ROE（%）
    :return: 行业对比结果字典
    """
    industry = _get_industry_by_code(symbol)
    peers = _INDUSTRY_PEERS.get(industry, [])
    peers = [p for p in peers if p != symbol]  # 排除自身

    # 检查缓存
    cache_key = industry
    if cache_key in _industry_cache and time.time() - _cache_ts.get(cache_key, 0) < _CACHE_TTL:
        cached = _industry_cache[cache_key]
    else:
        # 批量获取同行 PE/PB（最多取前8只，控制耗时）
        sample = peers[:8]
        pe_list, pb_list = [], []
        for peer in sample:
            pe, pb = _fetch_pe_pb(peer)
            if pe and 0 < pe < 200:
                pe_list.append(pe)
            if pb and 0 < pb < 50:
                pb_list.append(pb)

        cached = {
            "industry_median_pe": float(np.median(pe_list)) if pe_list else None,
            "industry_median_pb": float(np.median(pb_list)) if pb_list else None,
            "peer_count": len(peers),
            "pe_list": pe_list,
            "pb_list": pb_list,
        }
        _industry_cache[cache_key] = cached
        _cache_ts[cache_key] = time.time()

    industry_median_pe = cached["industry_median_pe"]
    industry_median_pb = cached["industry_median_pb"]
    pe_list = cached["pe_list"]
    pb_list = cached["pb_list"]

    # 计算分位数（低于多少%的同行=估值低）
    def percentile(val, lst):
        if val is None or not lst:
            return None
        below = sum(1 for x in lst if x > val)  # 多少同行 PE 比我高（我便宜）
        return round(below / len(lst) * 100)

    pe_percentile = percentile(stock_pe, pe_list)
    pb_percentile = percentile(stock_pb, pb_list)

    # 估值结论
    verdict = _valuation_verdict(stock_pe, industry_median_pe, stock_pb, industry_median_pb)

    return {
        "industry_name": industry,
        "peer_count": cached["peer_count"],
        "stock_pe": stock_pe,
        "industry_median_pe": industry_median_pe,
        "pe_percentile": pe_percentile,
        "stock_pb": stock_pb,
        "industry_median_pb": industry_median_pb,
        "pb_percentile": pb_percentile,
        "stock_roe": stock_roe,
        "industry_median_roe": None,  # 批量 ROE 获取成本高，留空
        "valuation_verdict": verdict,
    }


def _valuation_verdict(pe, med_pe, pb, med_pb) -> str:
    """综合 PE/PB 给出估值结论"""
    cheap = 0
    total = 0
    if pe is not None and med_pe is not None and med_pe > 0:
        total += 1
        if pe < med_pe * 0.85:
            cheap += 1
        elif pe > med_pe * 1.20:
            cheap -= 1
    if pb is not None and med_pb is not None and med_pb > 0:
        total += 1
        if pb < med_pb * 0.85:
            cheap += 1
        elif pb > med_pb * 1.20:
            cheap -= 1

    if total == 0:
        return "估值数据不足"
    if cheap >= 1:
        return "估值偏低（低于行业中位数）"
    if cheap <= -1:
        return "估值偏高（高于行业中位数）"
    return "估值合理（接近行业中位数）"
