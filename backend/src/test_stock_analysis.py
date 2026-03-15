import unittest
from stock_analysis import get_stock_data, calculate_indicators, generate_signal, get_analysis

class TestStockAnalysis(unittest.TestCase):
    
    def test_get_stock_data_structure(self):
        """Test that we get expected data structure for a known stock"""
        # Using 000001 (Ping An Bank) as test stock
        df = get_stock_data('000001')
        self.assertIsNotNone(df)
        self.assertTrue(len(df) > 0)
        expected_columns = ['open', 'high', 'low', 'close', 'volume', 'amount']
        for col in expected_columns:
            self.assertIn(col, df.columns)
    
    def test_calculate_indicators_adds_columns(self):
        """Test that technical indicators are calculated"""
        df = get_stock_data('000001')
        if df is not None and len(df) > 60:
            df_with_indicators = calculate_indicators(df.copy())
            expected_indicators = ['MA5', 'MA10', 'MA20', 'MA60', 'RSI', 'MACD', 'Signal', 'Hist', 'BB_upper', 'BB_mid', 'BB_lower']
            for col in expected_indicators:
                self.assertIn(col, df_with_indicators.columns)
    
    def test_generate_signal_returns_valid_values(self):
        """Test that signal generation returns expected values"""
        df = get_stock_data('000001')
        if df is not None and len(df) > 60:
            df_with_indicators = calculate_indicators(df.copy())
            signal, score, reasons = generate_signal(df_with_indicators)
            self.assertIn(signal, ['强烈买入', '买入', '观望', '卖出', '强烈卖出', '数据不足', '错误'])
            self.assertIsInstance(score, int)
            self.assertGreaterEqual(score, -10)
            self.assertLessEqual(score, 10)
            self.assertIsInstance(reasons, list)
    
    def test_get_analysis_returns_expected_structure(self):
        """Test that full analysis returns expected structure"""
        result = get_analysis('000001')
        self.assertIn('symbol', result)
        self.assertEqual(result['symbol'], '000001')
        self.assertIn('data', result)
        self.assertIn('indicators', result)
        self.assertIn('signal', result)
        self.assertIn('score', result)
        self.assertIn('reasons', result)
        
        # Check data structure
        self.assertIn('latest', result['data'])
        self.assertIn('chart', result['data'])
        self.assertIsInstance(result['data']['latest'], dict)
        self.assertIsInstance(result['data']['chart'], list)
        
        # Check indicators structure
        indicators = result['indicators']
        expected_indicators = ['MA5', 'MA10', 'MA20', 'MA60', 'RSI', 'MACD', 'Signal', 'BB_upper', 'BB_mid', 'BB_lower']
        for indicator in expected_indicators:
            self.assertIn(indicator, indicators)
            
if __name__ == '__main__':
    unittest.main()
