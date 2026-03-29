# Stock Analyzer 演进路线图

> 基于 2025-2026 年业界前沿技术调研及项目代码深度审计，制定的系统性升级计划。
> 创建时间：2026-03-29

---

## 一、当前项目存在的硬伤（P0 必须修复）

### 1. 情绪分析 Agent 极其粗糙

**现状**：`SentimentAgent` 用 9 个正面关键词 + 8 个负面关键词做标题匹配。

**问题**：这不是 NLP，这是字符串搜索，准确率极低。

**改进方案**：接入 FinBERT / ChatGPT / 本地 Qwen 做真正的金融情绪分类，一条新闻输出 `[-1, +1]` 的情绪分数，而非关键词计数。

**涉及文件**：
- `backend/agents/sentiment_agent.py`

---

### 2. 回测引擎有前瞻偏差残留

**现状**：`_rolling_signal()` 虽然用了滚动窗口，但 RSI/MACD 的 `ewm()` 使用了全量历史。

**问题**：exponential moving average 会从序列第一个点开始计算，早期信号不准确。

**改进方案**：每次只取 `historical_slice` 做计算，或至少丢弃前 60 个预热点的信号。

**涉及文件**：
- `backend/backtest/engine.py` → `_rolling_signal()`

---

### 3. 缓存完全没用上

**现状**：`utils/cache.py` 定义了 `stock_data_cache` 和 `fundamental_cache`。

**问题**：但 `stock_analysis.py`、`fundamental_agent.py` 中没有任何地方调用缓存！每次分析同一只股票都重复请求 AKShare 5-6 次。

**改进方案**：
- `get_stock_data()` 加缓存（TTL 5 分钟）
- `_get_fundamental_data()` 加缓存（TTL 1 小时）
- `get_capital_flow()` 加缓存（TTL 10 分钟）

**涉及文件**：
- `backend/src/stock_analysis.py` → `get_stock_data()`、`_get_fundamental_data()`
- `backend/agents/fundamental_agent.py` → `_fetch_fundamental()`
- `backend/src/capital_flow.py` → `get_capital_flow()`

---

### 4. 告警系统只有存储没有触发

**现状**：`AlertManager` 能增删查告警，但没有后台任务去检查价格是否触达。

**问题**：设置了告警永远不会触发，前端也没有通知机制。

**改进方案**：
- 后端：在 FastAPI 启动时创建后台定时任务（`asyncio.create_task`），每 30 秒获取所有未触发告警的股票最新价，匹配后标记并推送
- 前端：通过 WebSocket 或 SSE 接收告警触发通知，弹出 Toast 提醒

**涉及文件**：
- `backend/alerts/alert_manager.py` → 新增 `check_alerts()` 方法
- `backend/src/main.py` → 新增后台定时任务
- `frontend/src/components/AlertPanel.tsx` → 新增通知展示

---

### 5. WebSocket 实时行情未鉴权且无重连

**现状**：前端 `useWebSocket` 连接断开后不会重连，后端无心跳机制。

**问题**：网络波动后实时行情永久失效，用户无感知。

**改进方案**：
- 前端：指数退避重连（1s → 2s → 4s → max 30s），连接状态 UI 指示器
- 后端：每 15 秒发送 ping 帧，客户端 30 秒无消息则重连

**涉及文件**：
- `frontend/src/hooks/useWebSocket.ts`
- `backend/src/main.py` → `websocket_realtime()`

---

### 6. VectorStore 全局单例 + 每次写盘

**现状**：每次 `store_analysis` 都调用 `faiss.write_index` + `json.dump`。

**问题**：高并发时磁盘 IO 阻塞事件循环，且 metadata 无限增长无清理策略。

**改进方案**：
- 批量写入：累计 N 条或每 60 秒刷盘一次
- 数据清理：保留最近 1000 条或 90 天内记录
- 异步写入：通过 `run_in_executor` 将 IO 操作放入线程池

**涉及文件**：
- `backend/memory/vector_store.py`

---

## 二、核心能力缺失（P1 应该补齐）

### 7. 没有深度学习预测模型

**现状**：所有信号都基于规则型技术指标（MA 交叉、RSI 阈值、MACD 金叉），这是 2010 年代的做法。

**改进方案**：
- **LSTM / GRU 短期价格预测**：输入近 60 日 OHLCV + 技术指标，预测 5 日后涨跌概率
- **LightGBM 多因子选股模型**：整合技术面 + 基本面 + 情绪面因子，输出综合评分
- 可使用微软开源的 [Qlib](https://github.com/microsoft/qlib) 框架快速集成 30+ SOTA 模型

**新增文件**：
- `backend/models/lstm_predictor.py`
- `backend/models/lightgbm_scorer.py`
- `backend/models/train_pipeline.py`

**参考**：
- [QuantML 2025 前沿论文与模型](https://zhuanlan.zhihu.com/p/19350957307)
- [国内A股开源量化模型推荐](https://blog.csdn.net/qq_16067891/articles/147782671)

---

### 8. 没有多因子 Alpha 模型

**现状**：技术评分是简单的 +2/-2 加减法，各指标权重固定。

**问题**：不同市场环境下因子有效性差异巨大（牛市动量因子强，熊市价值因子强）。

**改进方案**：构建动态因子加权系统，用 IC（信息系数）/ ICIR 滚动评估因子有效性，自动调整权重。

**新增文件**：
- `backend/factors/factor_evaluator.py` — IC/ICIR 计算
- `backend/factors/dynamic_weights.py` — 动态权重分配
- `backend/factors/factor_library.py` — 因子库（动量、价值、质量、成长等）

**参考**：
- [国金证券：多因子及AI量化选股框架](https://www.fxbaogao.com/detail/4752153)
- [2025量化研究：因子舒适区探寻与应用](https://www.vzkoo.com/read/20250917b9175c7847503fe1b9a22955.html)

---

### 9. 缺少风险管理模块

**现状**：回测有夏普比率和最大回撤，但实际分析没有任何风险量化。

**缺失**：VaR（在险价值）、波动率锥、相关性风险、仓位管理建议。

**新增文件**：
- `backend/risk/var_calculator.py` — 历史模拟法 / 蒙特卡洛 VaR
- `backend/risk/volatility_cone.py` — 波动率锥（不同时间窗口的波动率分位）
- `backend/risk/position_sizer.py` — Kelly 公式 / ATR 仓位管理建议

---

### 10. Agent 间没有真正的"辩论"

**现状**：`DecisionCommittee` 只是把各 Agent 分数加权平均。

**问题**：这不是辩论，是投票。没有分歧检测、没有信心调整。

**改进方案**：参考 [TradingAgents](https://tradingagents-ai.github.io/) 框架：
- 检测 Agent 间信号矛盾（如技术面强烈买入但基本面强烈卖出）
- 矛盾时启动 LLM 驱动的辩论流程，各 Agent 给出论据
- LLM 综合论据输出带推理链的最终决策
- 输出 "一致性指数"（consensus score），低一致性 → 建议观望

**涉及文件**：
- `backend/agents/decision_committee.py` → 重构为 `DebateCommittee`
- 新增 `backend/agents/debate_moderator.py` — LLM 辩论主持人

**参考**：
- [TradingAgents: Multi-Agent LLM Financial Trading Framework](https://tradingagents-ai.github.io/)
- [Integrating Traditional Technical Analysis with AI: Multi-Agent LLM Approach (arXiv)](https://arxiv.org/abs/2506.16813)

---

### 11. 缺少 RAG 增强分析

**现状**：VectorStore 存了历史分析但几乎没被使用。

**缺失**：没有对接财报 PDF、研报、公告等非结构化数据。

**改进方案**：
- 接入东方财富/巨潮资讯公告，用 RAG 检索相关研报段落
- 分析时自动召回"历史上相似技术形态的后续走势"作为 LLM 上下文
- 用 `text2vec-base-chinese` 已有的向量能力构建研报知识库

**新增文件**：
- `backend/rag/document_loader.py` — 公告/研报爬取与解析
- `backend/rag/knowledge_base.py` — 向量化存储与检索
- `backend/rag/context_builder.py` — 构建 LLM 分析上下文

---

### 12. 无用户认证和个性化

**现状**：所有用户共享同一个自选股列表和告警配置（SQLite 单表无 `user_id`）。

**缺失**：无登录、无个性化偏好、无分析报告历史回溯。

**改进方案**：
- JWT 认证（轻量方案）或 OAuth2（GitHub/微信登录）
- 数据表加 `user_id` 字段
- 个性化：风险偏好设置 → 影响信号阈值和仓位建议

**涉及文件**：
- `backend/src/main.py` → 新增 auth 中间件
- `backend/data/` → 所有 store 加 `user_id`
- 新增 `backend/auth/` 模块

---

## 三、前沿技术升级方向（P2 锦上添花）

### 13. Streaming AI 对话（SSE）

**现状**：AI 对话等全部生成完毕后一次性返回。

**体验问题**：用户等待 5-10 秒看到空白，然后突然出现一大段文字。

**改进方案**：使用 Server-Sent Events（SSE）流式返回，像 ChatGPT 一样逐字输出。

**涉及文件**：
- `backend/src/main.py` → `/api/v1/ai/chat` 改为 `StreamingResponse`
- `backend/src/llm_reporter.py` → 使用 `stream=True` 参数
- `frontend/src/components/AIAssistant.tsx` → 使用 `EventSource` 接收
- `frontend/src/services/api.ts` → 新增 SSE 请求方法

---

### 14. 多时间框架联合分析

**现状**：只分析日线级别。

**缺失**：周线趋势 + 日线信号 + 60分钟入场时机的多级联动。

**改进方案**：
- 后端获取多周期数据（周/日/60分钟）
- 大周期定方向、中周期找信号、小周期定入场
- 三个周期信号一致时信心最高，矛盾时降低评分

**涉及文件**：
- `backend/src/stock_analysis.py` → 新增 `get_multi_timeframe_analysis()`
- `backend/data/akshare_provider.py` → 支持 `period` 参数（weekly/60min）
- `frontend/src/components/` → 新增多周期切换组件

---

### 15. 前端 K 线图升级

**现状**：用 Recharts 的 ComposedChart 模拟 K 线。

**问题**：不支持缩放、拖拽、十字光标、画线工具。

**改进方案**：替换为专业金融图表库
- **[Lightweight Charts](https://github.com/nicolestandart/lightweight-charts)**（TradingView 开源版）：原生 K 线、技术指标叠加、高性能 Canvas 渲染
- 或 **ECharts** 的 K 线图组件，生态更成熟

**涉及文件**：
- `frontend/src/components/CandlestickChart.tsx` → 完全重写
- `frontend/src/components/IndicatorChart.tsx` → 整合进新图表组件
- `frontend/package.json` → 新增 `lightweight-charts` 依赖

---

### 16. 异常形态识别

**缺失**：头肩顶/底、双重底/顶、旗形、三角形等经典图形的自动识别。

**改进方案**：
- 方案 A：规则引擎识别（基于 swing high/low 模式匹配）
- 方案 B：CNN 图像识别（将 K 线渲染为图片后分类，参考 TrendSpider 识别 220+ 种形态）

**新增文件**：
- `backend/patterns/pattern_recognizer.py`
- `backend/patterns/shapes.py` — 各种形态定义

---

### 17. 宏观经济整合

**缺失**：没有考虑 Shibor 利率、M2 货币供应、北向资金等宏观因素。

**重要性**：A 股受政策和宏观面影响极大，纯技术分析在 A 股的有效性远低于美股。

**改进方案**：
- AKShare 已提供 Shibor、社融、北向资金等接口
- 新增 `MacroAgent`，分析宏观环境对大盘的影响
- 决策委员会加入宏观因子权重

**新增文件**：
- `backend/agents/macro_agent.py`
- `backend/src/macro_data.py`

---

### 18. 事件驱动回测

**现状**：回测只支持固定周期的日频信号。

**缺失**：不支持"财报发布日买入"、"北向资金连续流入 3 日买入"等事件驱动策略。

**改进方案**：
- 回测引擎支持注册事件触发器（EventTrigger）
- 内置常用事件：财报日、分红除权日、北向资金异动、龙虎榜上榜

**涉及文件**：
- `backend/backtest/engine.py` → 新增 `EventDrivenEngine`
- `backend/backtest/events.py` — 事件定义与触发器

---

## 四、优先级排序总表

| 优先级 | 编号 | 改进项 | 预估投入 | 核心收益 |
|--------|------|--------|----------|----------|
| **P0** | #3 | 缓存接入 | 1 天 | 性能提升 5x，减少 API 限流 |
| **P0** | #4 | 告警触发机制 | 1 天 | 功能完整性 |
| **P0** | #5 | WebSocket 重连 + 心跳 | 0.5 天 | 用户体验 |
| **P0** | #6 | VectorStore 批量写入 + 清理 | 0.5 天 | 稳定性 |
| **P1** | #1 | FinBERT 情绪分析 | 2 天 | 分析准确度大幅提升 |
| **P1** | #2 | 回测前瞻偏差修复 | 0.5 天 | 回测结果可信度 |
| **P1** | #10 | Agent 真正辩论机制 | 2 天 | 核心竞争力 |
| **P1** | #13 | SSE 流式 AI 对话 | 1 天 | 交互体验质变 |
| **P1** | #12 | 用户认证和个性化 | 3 天 | 产品化必要条件 |
| **P2** | #7 | LSTM/LightGBM 预测模型 | 5 天 | 从规则引擎升级到 AI 引擎 |
| **P2** | #15 | TradingView K 线图 | 3 天 | 专业感提升 |
| **P2** | #11 | RAG 研报检索 | 3 天 | 分析深度质变 |
| **P2** | #9 | 风险管理模块 | 3 天 | 投资安全性 |
| **P2** | #14 | 多时间框架分析 | 2 天 | 分析维度扩展 |
| **P3** | #8 | 多因子 Alpha 模型 | 5 天 | 专业量化能力 |
| **P3** | #16 | 异常形态识别 | 3 天 | 图表智能分析 |
| **P3** | #17 | 宏观经济整合 | 2 天 | A 股特色分析 |
| **P3** | #18 | 事件驱动回测 | 3 天 | 策略多样性 |

---

## 五、技术参考资料

| 领域 | 资料 | 链接 |
|------|------|------|
| 多Agent交易框架 | TradingAgents | https://tradingagents-ai.github.io/ |
| 学术论文 | 传统技术分析 + AI Multi-Agent | https://arxiv.org/abs/2506.16813 |
| AI交易工具 | 2026 年最佳 AI 交易工具 | https://monday.com/blog/ai-agents/best-ai-for-stock-trading/ |
| AI选股研究 | AI Stock Research Agent 完整指南 | https://www.jenova.ai/en/resources/ai-stock-research-agent |
| 多因子框架 | 国金证券多因子及AI量化选股 | https://www.fxbaogao.com/detail/4752153 |
| 因子研究 | 2025量化研究：因子舒适区探寻 | https://www.vzkoo.com/read/20250917b9175c7847503fe1b9a22955.html |
| 前沿模型 | QuantML 2025 SOTA 模型集合 | https://zhuanlan.zhihu.com/p/19350957307 |
| 开源量化 | 国内A股开源量化模型推荐 | https://blog.csdn.net/qq_16067891/articles/147782671 |
| 量化平台 | 微软 Qlib 端到端金融分析 | https://github.com/microsoft/qlib |
| K线图表 | TradingView Lightweight Charts | https://github.com/nicolestandart/lightweight-charts |

---

## 六、实施节奏建议

### 第一阶段（1 周）：修复硬伤
完成 P0 全部 4 项 + P1 的 #2 回测偏差修复。项目从 "Demo 级" 升级到 "可用级"。

### 第二阶段（2 周）：核心补齐
完成 P1 剩余 4 项（FinBERT 情绪、Agent 辩论、SSE 对话、用户认证）。项目达到 "产品级"。

### 第三阶段（3 周）：AI 升级
完成 P2 全部 5 项（深度学习预测、K 线升级、RAG、风险管理、多时间框架）。项目达到 "专业级"。

### 第四阶段（按需）：精细化
P3 各项根据用户反馈和业务需求选择性实施。
