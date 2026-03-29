"""
stock_analysis 模块单元测试
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pandas as pd
import numpy as np
import pytest
from src.stock_analysis import calculate_indicators, generate_signal


class TestCalculateIndicators:
    def test_returns_all_expected_columns(self, sample_ohlcv):
        df = calculate_indicators(sample_ohlcv)
        expected = [
            "ma5", "ma10", "ma20", "ma60",
            "rsi", "macd", "signal_line", "hist",
            "bb_mid", "bb_upper", "bb_lower",
            "kdj_k", "kdj_d", "kdj_j",
            "wr", "obv", "atr",
        ]
        for col in expected:
            assert col in df.columns, f"Missing column: {col}"

    def test_ma_values_are_reasonable(self, sample_ohlcv):
        df = calculate_indicators(sample_ohlcv)
        # MA5 最后一个值应该接近最近5个收盘价的均值
        last_5_close = sample_ohlcv["close"].iloc[-5:].mean()
        assert abs(df["ma5"].iloc[-1] - last_5_close) < 0.01

    def test_rsi_in_range(self, sample_ohlcv):
        df = calculate_indicators(sample_ohlcv)
        rsi_valid = df["rsi"].dropna()
        assert (rsi_valid >= 0).all() and (rsi_valid <= 100).all()

    def test_bollinger_bands_ordering(self, sample_ohlcv):
        df = calculate_indicators(sample_ohlcv)
        valid = df.dropna(subset=["bb_lower", "bb_mid", "bb_upper"])
        assert (valid["bb_lower"] <= valid["bb_mid"]).all()
        assert (valid["bb_mid"] <= valid["bb_upper"]).all()

    def test_kdj_in_reasonable_range(self, sample_ohlcv):
        df = calculate_indicators(sample_ohlcv)
        k_valid = df["kdj_k"].dropna()
        d_valid = df["kdj_d"].dropna()
        # K and D should be roughly 0-100 (J can exceed)
        assert (k_valid >= -10).all() and (k_valid <= 110).all()
        assert (d_valid >= -10).all() and (d_valid <= 110).all()

    def test_wr_in_range(self, sample_ohlcv):
        df = calculate_indicators(sample_ohlcv)
        wr_valid = df["wr"].dropna()
        assert (wr_valid >= -100).all() and (wr_valid <= 0).all()

    def test_obv_is_computed(self, sample_ohlcv):
        df = calculate_indicators(sample_ohlcv)
        assert df["obv"].iloc[0] == 0
        assert not df["obv"].isna().all()

    def test_atr_positive(self, sample_ohlcv):
        df = calculate_indicators(sample_ohlcv)
        atr_valid = df["atr"].dropna()
        assert (atr_valid >= 0).all()

    def test_does_not_modify_original(self, sample_ohlcv):
        original_cols = list(sample_ohlcv.columns)
        calculate_indicators(sample_ohlcv)
        assert list(sample_ohlcv.columns) == original_cols


class TestGenerateSignal:
    def test_returns_three_values(self, sample_ohlcv):
        df = calculate_indicators(sample_ohlcv)
        result = generate_signal(df)
        assert len(result) == 3
        signal, score, reasons = result
        assert isinstance(signal, str)
        assert isinstance(score, (int, float))
        assert isinstance(reasons, list)

    def test_short_data_returns_insufficient(self, sample_ohlcv_short):
        df = calculate_indicators(sample_ohlcv_short)
        signal, score, reasons = generate_signal(df)
        assert signal == "数据不足"

    def test_signal_is_valid_value(self, sample_ohlcv):
        df = calculate_indicators(sample_ohlcv)
        signal, _, _ = generate_signal(df)
        valid = {"强烈买入", "买入", "卖出", "强烈卖出", "观望"}
        assert signal in valid

    def test_reasons_not_empty(self, sample_ohlcv):
        df = calculate_indicators(sample_ohlcv)
        _, _, reasons = generate_signal(df)
        assert len(reasons) > 0
