"""
LightGBM 多因子评分器
- 整合技术面 + 基本面 + 情绪面特征
- 输出综合评分和特征重要度
"""
import os
import logging
import numpy as np
import pandas as pd
from typing import Dict, Optional

logger = logging.getLogger(__name__)

_MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "checkpoints", "lgbm_model.txt")


class LightGBMScorer:
    def __init__(self):
        self._model = None
        self._lgb_available = False
        try:
            import lightgbm
            self._lgb_available = True
        except ImportError:
            logger.info("LightGBM 未安装，多因子评分不可用")

    def _load_model(self):
        if not self._lgb_available or self._model is not None:
            return
        if os.path.exists(_MODEL_PATH):
            try:
                import lightgbm as lgb
                self._model = lgb.Booster(model_file=_MODEL_PATH)
            except Exception as e:
                logger.warning("LightGBM 模型加载失败: %s", e)

    def score(self, features: Dict) -> Optional[Dict]:
        """
        对股票进行多因子评分
        :param features: {"rsi": 45, "macd": 0.01, "pe": 15, ...}
        :return: {"score": 7.2, "percentile": 85, "top_factors": [...]}
        """
        if not features:
            return None

        self._load_model()

        # 特征顺序
        feature_names = [
            "rsi", "macd", "ma5_slope", "ma20_slope", "volume_ratio",
            "pe", "pb", "roe", "debt_ratio", "gross_margin",
            "sentiment_score", "north_flow",
        ]

        vals = [float(features.get(f, 0) or 0) for f in feature_names]

        if self._model is not None:
            try:
                pred = self._model.predict([vals])[0]
                return self._format_score(pred, feature_names, vals)
            except Exception as e:
                logger.warning("LightGBM 预测失败: %s", e)

        # 降级：简单线性加权
        return self._heuristic_score(features)

    def _heuristic_score(self, features: Dict) -> Dict:
        """无模型时的启发式评分"""
        score = 5.0  # 基础分 5/10

        rsi = features.get("rsi", 50)
        if rsi and rsi < 30:
            score += 1.5
        elif rsi and rsi > 70:
            score -= 1.5

        pe = features.get("pe")
        if pe and 0 < pe < 15:
            score += 1.0
        elif pe and pe > 50:
            score -= 1.0

        roe = features.get("roe")
        if roe and roe > 15:
            score += 0.5

        sentiment = features.get("sentiment_score", 0)
        score += sentiment * 0.3

        score = max(0, min(10, round(score, 1)))
        return {
            "score": score,
            "percentile": int(score * 10),
            "model": "Heuristic",
            "top_factors": [],
        }

    def _format_score(self, raw_pred: float, feature_names, vals) -> Dict:
        score = round(max(0, min(10, raw_pred * 10)), 1)
        return {
            "score": score,
            "percentile": int(score * 10),
            "model": "LightGBM",
            "top_factors": [],
        }

    def train(self, X: pd.DataFrame, y: pd.Series, **params) -> Dict:
        """训练 LightGBM 模型"""
        if not self._lgb_available:
            return {"error": "LightGBM 未安装"}

        import lightgbm as lgb
        train_data = lgb.Dataset(X, label=y)
        default_params = {
            "objective": "regression",
            "metric": "rmse",
            "num_leaves": 31,
            "learning_rate": 0.05,
            "feature_fraction": 0.8,
            "verbose": -1,
        }
        default_params.update(params)
        model = lgb.train(default_params, train_data, num_boost_round=200)
        os.makedirs(os.path.dirname(_MODEL_PATH), exist_ok=True)
        model.save_model(_MODEL_PATH)
        self._model = model
        return {"status": "ok", "num_trees": model.num_trees()}


lgbm_scorer = LightGBMScorer()
