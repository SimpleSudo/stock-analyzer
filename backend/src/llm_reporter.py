"""
AI 分析报告生成器
- 支持多种 LLM 后端：Claude（Anthropic）/ OpenAI / 兼容 OpenAI 格式的接口
- 通过环境变量配置：LLM_PROVIDER（anthropic/openai）、对应 API Key 和模型名
- 将所有量化数据汇总，由 LLM 生成完整的中文分析报告
"""
import os
from typing import Optional


# ── 环境变量配置 ──────────────────────────────────────
# LLM_PROVIDER      : "anthropic"（默认）| "openai"
# ANTHROPIC_API_KEY : Claude API Key
# ANTHROPIC_MODEL   : 默认 "claude-sonnet-4-5-20251001"
# OPENAI_API_KEY    : OpenAI API Key
# OPENAI_BASE_URL   : 可覆盖（兼容其他 OpenAI 格式接口，如 DeepSeek）
# OPENAI_MODEL      : 默认 "gpt-4o"
# ─────────────────────────────────────────────────────


def _build_prompt(
    symbol: str,
    name: str,
    current_price: float,
    change_pct: float,
    tech: dict,
    fundamental: dict,
    industry: Optional[dict],
    capital_flow: Optional[dict],
    price_targets: Optional[dict],
) -> str:
    """构建发送给 LLM 的分析提示词"""

    # 技术指标摘要
    rsi = tech.get("rsi", "N/A")
    macd = tech.get("macd", "N/A")
    ma20 = tech.get("ma20", "N/A")
    ma60 = tech.get("ma60", "N/A")
    tech_score = tech.get("score", 0)
    tech_signal = tech.get("signal", "观望")
    tech_reasons = "\n".join(f"  - {r}" for r in tech.get("reasons", []))

    # 基本面摘要
    pe = fundamental.get("pe", "N/A")
    pb = fundamental.get("pb", "N/A")
    roe = fundamental.get("roe", "N/A")
    debt = fundamental.get("debt_ratio", "N/A")
    gross = fundamental.get("gross_margin", "N/A")

    # 行业对比
    if industry:
        ind_text = (
            f"所属行业：{industry.get('industry_name', '未知')}\n"
            f"  PE：{pe}（行业中位 {industry.get('industry_median_pe', 'N/A')}，"
            f"低于行业 {industry.get('pe_percentile', '?')}% 同行）\n"
            f"  PB：{pb}（行业中位 {industry.get('industry_median_pb', 'N/A')}，"
            f"低于行业 {industry.get('pb_percentile', '?')}% 同行）\n"
            f"  估值结论：{industry.get('valuation_verdict', '未知')}"
        )
    else:
        ind_text = f"所属行业：未知\nPE={pe}，PB={pb}（无行业对比数据）"

    # 资金流向
    if capital_flow:
        flow_text = (
            f"今日主力净流入：{capital_flow.get('today_main_net', 0):+.1f} 万元\n"
            f"  5日累计主力净流入：{capital_flow.get('five_day_main_net', 0):+.1f} 万元\n"
            f"  主力趋势：{capital_flow.get('main_trend', '未知')}\n"
            f"  博弈态势：{capital_flow.get('retail_vs_main', '未知')}"
        )
    else:
        flow_text = "资金流向数据暂不可用"

    # 价格目标
    if price_targets:
        st = price_targets.get("short_term", {})
        mt = price_targets.get("medium_term", {})
        lt = price_targets.get("long_term", {})
        target_text = (
            f"短线（{st.get('horizon','1-2周')}）：买入区 {st.get('buy_zone',['?','?'])[0]}~"
            f"{st.get('buy_zone',['?','?'])[1]} 元，止损 {st.get('stop_loss','?')} 元，"
            f"目标价 {'/'.join(str(t) for t in st.get('targets', []))} 元\n"
            f"  中线（{mt.get('horizon','1-3月')}）：买入区 {mt.get('buy_zone',['?','?'])[0]}~"
            f"{mt.get('buy_zone',['?','?'])[1]} 元，止损 {mt.get('stop_loss','?')} 元，"
            f"目标价 {'/'.join(str(t) for t in mt.get('targets', []))} 元\n"
            f"  长线（{lt.get('horizon','6-12月')}）：买入区 {lt.get('buy_zone',['?','?'])[0]}~"
            f"{lt.get('buy_zone',['?','?'])[1]} 元，止损 {lt.get('stop_loss','?')} 元，"
            f"目标价 {'/'.join(str(t) for t in lt.get('targets', []))} 元"
        )
    else:
        target_text = "价格目标数据暂不可用"

    prompt = f"""你是一位严谨专业的 A 股分析师，请基于以下量化数据，为 **{name}（{symbol}）** 撰写一份完整的投资分析报告。

## 当前行情
- 最新价格：{current_price:.2f} 元（今日涨跌幅 {change_pct:+.2f}%）

## 技术面分析数据
- RSI(14)：{rsi}
- MACD：{macd}，MA20：{ma20}，MA60：{ma60}
- 技术评分：{tech_score}，技术信号：{tech_signal}
- 技术分析依据：
{tech_reasons}

## 基本面数据
- PE(TTM)：{pe}，PB：{pb}
- ROE：{roe}%，资产负债率：{debt}%，毛利率：{gross}%

## 行业对比
{ind_text}

## 资金流向（近期）
{flow_text}

## 价格目标区间
{target_text}

---
请撰写一份完整的分析报告，**必须包含以下六个部分**，用 Markdown 格式，中文：

### 1. 综合研判
（2-3句话，给出核心结论，明确当前是否适合买入/持有/回避）

### 2. 技术面分析
（描述当前趋势、关键价位、近期短线走势判断，引用 RSI/MACD/均线数据）

### 3. 基本面评价
（估值是否合理、盈利能力、与行业的比较，指出优势和隐忧）

### 4. 资金面信号
（主力资金行为解读，与价格走势的配合或背离）

### 5. 操作建议
分三个时间维度给出具体建议：
- **短线（1-2周）**：买入区间、止损位、目标价
- **中线（1-3月）**：策略和目标
- **长线（6-12月）**：价值投资角度的判断

### 6. 主要风险
（列举2-3条具体风险，避免泛泛而谈）

**要求**：语言专业简洁，每个判断必须有数据支撑，不要复读我提供的原始数据，要有独立分析和洞见。"""

    return prompt


def generate_analysis_report(
    symbol: str,
    name: str,
    current_price: float,
    change_pct: float,
    tech: dict,
    fundamental: dict,
    industry: Optional[dict] = None,
    capital_flow: Optional[dict] = None,
    price_targets: Optional[dict] = None,
) -> Optional[str]:
    """
    调用 LLM 生成完整分析报告。
    优先使用 ANTHROPIC_API_KEY（Claude），其次使用 OPENAI_API_KEY（OpenAI/兼容接口）。
    均不可用时返回 None。
    """
    provider = os.getenv("LLM_PROVIDER", "anthropic").lower()
    prompt = _build_prompt(
        symbol, name, current_price, change_pct,
        tech, fundamental, industry, capital_flow, price_targets
    )

    # ── Claude（Anthropic）──────────────────────────
    if provider == "anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return None
        try:
            import anthropic
            model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5-20251001")
            client = anthropic.Anthropic(api_key=api_key)
            message = client.messages.create(
                model=model,
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}],
            )
            return message.content[0].text
        except Exception as e:
            return f"[AI 报告生成失败：{e}]"

    # ── OpenAI / 兼容格式（DeepSeek 等）────────────
    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return None
        try:
            from openai import OpenAI
            model = os.getenv("OPENAI_MODEL", "gpt-4o")
            base_url = os.getenv("OPENAI_BASE_URL")  # 可留空（使用默认）
            client = OpenAI(api_key=api_key, base_url=base_url) if base_url else OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model=model,
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"[AI 报告生成失败：{e}]"

    return None
