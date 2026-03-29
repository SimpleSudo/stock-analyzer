"""
LSTM 价格走势预测器
- 输入：60 日 OHLCV + 技术指标（标准化）
- 输出：5 日后涨跌概率
- 支持训练和推理
"""
import os
import logging
import numpy as np
import pandas as pd
from typing import Optional, Dict

logger = logging.getLogger(__name__)

_CHECKPOINT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "checkpoints")
_FEATURE_COLS = ["close", "volume", "ma5", "ma10", "ma20", "rsi", "macd", "hist", "atr"]
_SEQ_LEN = 60
_PREDICT_DAYS = 5


def _prepare_features(df: pd.DataFrame) -> Optional[np.ndarray]:
    """准备特征矩阵并标准化"""
    cols = [c for c in _FEATURE_COLS if c in df.columns]
    if len(cols) < 5:
        return None
    data = df[cols].dropna().values
    if len(data) < _SEQ_LEN:
        return None
    # Z-score 标准化
    mean = data.mean(axis=0)
    std = data.std(axis=0)
    std[std == 0] = 1
    normalized = (data - mean) / std
    return normalized


class LSTMPredictor:
    """LSTM 涨跌预测器"""

    def __init__(self, input_size: int = len(_FEATURE_COLS), hidden_size: int = 64, num_layers: int = 2):
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.model = None
        self._torch_available = False
        self._try_import()

    def _try_import(self):
        try:
            import torch
            import torch.nn as nn
            self._torch_available = True
        except ImportError:
            logger.info("PyTorch 未安装，LSTM 预测不可用")

    def _build_model(self):
        if not self._torch_available:
            return None
        import torch
        import torch.nn as nn

        class StockLSTM(nn.Module):
            def __init__(self, input_size, hidden_size, num_layers):
                super().__init__()
                self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True, dropout=0.2)
                self.fc = nn.Sequential(
                    nn.Linear(hidden_size, 32),
                    nn.ReLU(),
                    nn.Dropout(0.1),
                    nn.Linear(32, 1),
                    nn.Sigmoid(),
                )

            def forward(self, x):
                lstm_out, _ = self.lstm(x)
                return self.fc(lstm_out[:, -1, :])

        return StockLSTM(self.input_size, self.hidden_size, self.num_layers)

    def predict(self, df: pd.DataFrame) -> Optional[Dict]:
        """
        预测未来涨跌概率
        :return: {"up_probability": 0.65, "direction": "看涨", "confidence": "中等"}
        """
        if not self._torch_available:
            return self._heuristic_predict(df)

        import torch
        features = _prepare_features(df)
        if features is None:
            return self._heuristic_predict(df)

        # 取最后 SEQ_LEN 行
        seq = features[-_SEQ_LEN:]
        actual_features = min(seq.shape[1], self.input_size)

        # 检查是否有预训练模型
        model_path = os.path.join(_CHECKPOINT_DIR, "lstm_model.pt")
        if os.path.exists(model_path):
            try:
                model = self._build_model()
                model.load_state_dict(torch.load(model_path, map_location="cpu", weights_only=True))
                model.eval()
                x = torch.FloatTensor(seq[:, :actual_features]).unsqueeze(0)
                with torch.no_grad():
                    prob = float(model(x).item())
                return self._format_prediction(prob)
            except Exception as e:
                logger.warning("LSTM 预测失败: %s", e)

        # 无预训练模型时使用启发式方法
        return self._heuristic_predict(df)

    def _heuristic_predict(self, df: pd.DataFrame) -> Dict:
        """无模型时的启发式预测（基于多指标综合）"""
        if len(df) < 20:
            return {"up_probability": 0.5, "direction": "不确定", "confidence": "低"}

        close = df["close"]
        # 短期动量
        ret_5 = (close.iloc[-1] / close.iloc[-5] - 1) if len(close) >= 5 else 0
        ret_20 = (close.iloc[-1] / close.iloc[-20] - 1) if len(close) >= 20 else 0

        # RSI
        rsi = df["rsi"].iloc[-1] if "rsi" in df.columns and pd.notna(df["rsi"].iloc[-1]) else 50

        # 综合评分 -> 概率
        score = 0.5
        score += ret_5 * 2  # 短期动量
        score += ret_20 * 0.5  # 中期趋势
        score += (50 - rsi) / 200  # RSI 均值回归

        prob = max(0.1, min(0.9, score))
        return self._format_prediction(prob)

    def _format_prediction(self, prob: float) -> Dict:
        if prob >= 0.65:
            direction = "看涨"
            confidence = "较高" if prob >= 0.75 else "中等"
        elif prob <= 0.35:
            direction = "看跌"
            confidence = "较高" if prob <= 0.25 else "中等"
        else:
            direction = "震荡"
            confidence = "低"

        return {
            "up_probability": round(prob, 4),
            "direction": direction,
            "confidence": confidence,
            "predict_days": _PREDICT_DAYS,
            "model": "LSTM" if self._torch_available else "Heuristic",
        }

    def train(self, df: pd.DataFrame, epochs: int = 50) -> Dict:
        """训练 LSTM 模型"""
        if not self._torch_available:
            return {"error": "PyTorch 未安装"}

        import torch
        import torch.nn as nn
        from torch.utils.data import DataLoader, TensorDataset

        features = _prepare_features(df)
        if features is None or len(features) < _SEQ_LEN + _PREDICT_DAYS + 10:
            return {"error": "数据不足"}

        # 构建训练数据
        X, y = [], []
        close_idx = 0  # close 是第一列
        for i in range(_SEQ_LEN, len(features) - _PREDICT_DAYS):
            X.append(features[i - _SEQ_LEN:i])
            future_return = (features[i + _PREDICT_DAYS - 1, close_idx] - features[i - 1, close_idx])
            y.append(1.0 if future_return > 0 else 0.0)

        X = torch.FloatTensor(np.array(X))
        y = torch.FloatTensor(np.array(y)).unsqueeze(1)

        dataset = TensorDataset(X, y)
        loader = DataLoader(dataset, batch_size=32, shuffle=True)

        model = self._build_model()
        optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
        criterion = nn.BCELoss()

        model.train()
        for epoch in range(epochs):
            total_loss = 0
            for xb, yb in loader:
                pred = model(xb)
                loss = criterion(pred, yb)
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
                total_loss += loss.item()

        # 保存模型
        os.makedirs(_CHECKPOINT_DIR, exist_ok=True)
        torch.save(model.state_dict(), os.path.join(_CHECKPOINT_DIR, "lstm_model.pt"))

        return {"status": "ok", "epochs": epochs, "final_loss": round(total_loss / len(loader), 4)}


# 全局实例
lstm_predictor = LSTMPredictor()
