# Stock Analyzer

A股智能分析系统 - 基于FastAPI和React+Vite+TypeScript的股票技术分析平台

## 项目概述

本项目是一个专注于中国A股市场的智能股票分析系统，提供技术指标计算、买卖信号生成和可视化展示。系统采用前后端分离架构：

- **后端**：FastAPI + Python + AKShare，提供股票数据获取和技术分析API
- **前端**：React + Vite + TypeScript + Recharts，提供交互式界面和数据可视化

## 功能特点

- 📈 实时股票行情和历史数据获取
- 📊 多种技术指标：MA、RSI、MACD、布林带等
- 🎯 智能买卖信号生成和评分系统
- 🖼️ 交互式K线图和技术指标面板
- 🔍 股票搜索和自选股管理
- 🎨 主题切换（浅色/深色）
- 📊 股票比较功能
- 💾 图表导出（PNG/JPG）
- ⚠️ 价格告警设置
- 🤖 AI分析助手提供操作建议
- 📱 响应式设计，支持移动端
- 🧪 完整的单元测试覆盖

## 技术栈

### 后端
- Python 3.9+
- FastAPI
- AKShare (A股数据接口)
- Uvicorn (ASGI服务器)
- Pydantic (数据验证)
- Python-dotenv (环境变量)

### 前端
- React 18+
- Vite (构建工具)
- TypeScript
- Recharts (数据可视化)
- Axios (HTTP客户端)
- CSS3 (响应式布局)

## 快速开始

### 前提条件
- Python 3.9+
- Node.js 16+
- Git

### 安装步骤

1. 克隆仓库
```bash
git clone https://github.com:SimpleSudo/stock-analyzer.git
cd stock-analyzer
```

2. 后端设置
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. 前端设置
```bash
cd ../frontend
npm install
```

### 运行项目

1. 启动后端API
```bash
cd backend
source venv/bin/activate
uvicorn src.main:app --reload
```
API将在 http://localhost:8000 运行

2. 启动前端开发服务器
```bash
cd ../frontend
npm run dev
```
前端将在 http://localhost:5173 运行

3. 访问应用
打开浏览器访问 http://localhost:5173

### 生产构建

```bash
cd frontend
npm run build
```
构建产出将在 `dist` 目录中

## API文档

后端启动后，访问 http://localhost:8000/docs 查看交互式API文档（Swagger UI）

## 项目结构

```
stock-analyzer/
├── backend/
│   ├── src/
│   │   ├── main.py              # FastAPI入口
│   │   ├── stock_analysis.py    # 核心分析逻辑
│   │   └── __pycache__/
│   ├── test_stock_analysis.py   # 单元测试
│   ├── requirements.txt
│   └── venv/                    # 虚拟环境（git忽略）
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/          # React组件
│   │   │   ├── StockAnalyzer.tsx
│   │   │   ├── CandlestickChart.tsx
│   │   │   ├── IndicatorChart.tsx
│   │   │   ├── StockSearch.tsx
│   │   │   └── AIAssistant.tsx
│   │   ├── services/            # API服务
│   │   │   └── api.ts
│   │   ├── utils/               # 工具函数和类型
│   │   │   └── types.ts
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   ├── index.css
│   │   └── App.css
│   ├── package.json
│   └── vite.config.ts
├── README.md
└.gitignore
```

## 数据说明

- 数据来源：AKShare (https://github.com/akfamily/akshare)
- 仅支持中国A股市场股票
- 股票代码格式：6位数字（如000001、600000）
- 自动处理交易所前缀（sz/sh）和后缀(.SZ/.SH)

## 功能演示

1. **基本分析**：在搜索框中输入股票代码或名称（如“平安银行”或“000001”），点击“开始分析”
2. **查看结果**：
   - 最新价格和涨跌幅
   - 技术评分和买卖信号
   - K线图与均线
   - RSI、MACD、布林带指标面板
   - 分析依据列表
3. **高级功能**：
   - 点击“AI分析助手”获取操作建议
   - 使用主题切换按钮在浅色/深色间切换
   - 搜索框支持代码和名称模糊搜索
   - 股票比较：分析多只股票后可横向对比
   - 图表导出：点击图表右上角的下载按钮
   - 价格告警：设置目标价格提醒
   - 自选股：添加常用股票到自选列表

## 贡献指南

欢迎提交Issue和Pull Request！请遵循以下步骤：

1. Fork 本仓库
2. 创建功能分支：`git checkout -b feature/your-feature-name`
3. 提交更改：`git commit -m 'Add some feature'`
4. 推送到分支：`git push origin feature/your-feature-name`
5. 提交Pull Request

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 联系方式

如有问题或建议，请通过GitHub Issues联系。

祝您使用愉快！📈