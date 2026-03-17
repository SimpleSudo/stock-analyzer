"""
Simple custom indicator formula parser and evaluator.
Supports basic arithmetic and a few technical indicator functions.
Note: This is a simplified implementation for demonstration.
In production, consider using a proper expression parser and numexpr for safety.
"""
import pandas as pd
import numpy as np
from typing import Dict, Any

def ma(series: pd.Series, window: int) -> pd.Series:
    """Moving average"""
    return series.rolling(window=window).mean()

def ema(series: pd.Series, window: int) -> pd.Series:
    """Exponential moving average"""
    return series.ewm(span=window, adjust=False).mean()

def rsi(series: pd.Series, window: int = 14) -> pd.Series:
    """Relative Strength Index"""
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -delta.clip(upper=0)
    roll_up = up.rolling(window=window).mean()
    roll_down = down.rolling(window=window).mean()
    rs = roll_up / roll_down
    return 100 - (100 / (1 + rs))

def macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
    """MACD, returns dict with macd, signal, hist"""
    ema_fast = ema(series, fast)
    ema_slow = ema(series, slow)
    macd_line = ema_fast - ema_slow
    signal_line = ema(macd_line, signal)
    hist = macd_line - signal_line
    return {"macd": macd_line, "signal": signal_line, "hist": hist}

def bollinger(series: pd.Series, window: int = 20, num_std: float = 2.0) -> Dict[str, pd.Series]:
    """Bollinger Bands, returns dict with upper, mid, lower"""
    mid = series.rolling(window=window).mean()
    std = series.rolling(window=window).std()
    upper = mid + num_std * std
    lower = mid - num_std * std
    return {"upper": upper, "mid": mid, "lower": lower}

# Mapping of function names to implementations
FUNCTIONS = {
    "MA": ma,
    "EMA": ema,
    "RSI": rsi,
    "MACD": macd,
    "BOLLINGER": bollinger,
}

def parse_formula(formula: str) -> Dict[str, Any]:
    """
    Parse a simple formula string.
    Expected format: "INDICATOR_NAME = FUNCTION(PARAMS)" or arithmetic combinations.
    For simplicity, we only support a single function call for now.
    Returns a dict with keys: 'type', 'func', 'args', 'output_name' if applicable.
    """
    formula = formula.strip()
    # Check for assignment
    if "=" in formula:
        parts = formula.split("=")
        if len(parts) != 2:
            raise ValueError("Formula must have exactly one '='")
        output_name = parts[0].strip()
        expr = parts[1].strip()
    else:
        output_name = None
        expr = formula
    
    # For now, we only support function calls like MA(CLOSE,5)
    # We'll do a very simple parsing: find the first '('
    if "(" not in expr or ")" not in expr:
        raise ValueError("Expression must be a function call like FUNCTION(args)")
    
    func_name = expr[:expr.index("(")].strip().upper()
    args_str = expr[expr.index("(")+1:expr.rindex(")")].strip()
    # Split args by comma, strip, and try to convert to int
    args = []
    if args_str:
        for arg in args_str.split(","):
            arg = arg.strip()
            if arg.isdigit():
                args.append(int(arg))
            else:
                # Could be a series reference like "CLOSE", we'll handle later
                args.append(arg)
    
    if func_name not in FUNCTIONS:
        raise ValueError(f"Unsupported function: {func_name}")
    
    return {
        "output_name": output_name,
        "func": FUNCTIONS[func_name],
        "args": args,
        "func_name": func_name
    }

def compute_indicator(df: pd.DataFrame, parsed: Dict[str, Any]) -> pd.Series:
    """
    Compute the indicator given a DataFrame (with at least a 'close' column) and parsed formula.
    For simplicity, we assume the input series is the close price.
    """
    # For now, we only support close price as input
    close_series = df['close']
    # Prepare args: replace string 'CLOSE' with the series
    resolved_args = []
    for arg in parsed["args"]:
        if isinstance(arg, str) and arg.upper() == "CLOSE":
            resolved_args.append(close_series)
        else:
            resolved_args.append(arg)
    # Call the function
    result = parsed["func"](close_series, *resolved_args)
    # If the function returns a dict (like MACD or BOLLINGER), we need to handle it
    if isinstance(result, dict):
        # For now, we'll return the first item in the dict? Or we can return the dict and let the caller handle.
        # We'll return the dict and let the caller decide which key to use.
        # But our function expects to return a Series. So we'll adjust: for MACD, we return the macd line.
        # For BOLLINGER, we return the mid band.
        # This is a simplification.
        if parsed["func_name"] == "MACD":
            return result["macd"]
        elif parsed["func_name"] == "BOLLINGER":
            return result["mid"]
        else:
            # Default to first value
            return list(result.values())[0]
    else:
        return result