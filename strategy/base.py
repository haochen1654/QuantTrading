import pandas as pd


def backtest_always_half_position(
    df: pd.DataFrame,
    initial_cash: float,
    target_weight: float,
) -> pd.DataFrame:
    """
    账户级回测:每天收盘后再平衡到固定仓位(默认50%)。

    参数:
        df: 含有 Close 列的行情数据（索引为日期）
        initial_cash: 起始资金
        target_weight: 目标仓位占比(0.5 代表半仓)

    返回:
        每日账户明细（现金、持仓市值、总资产、仓位比例、收益等）
    """
    if "signal" not in df.columns:
        raise ValueError("df 缺少 signal 列，无法按信号交易。")

    cash = initial_cash
    shares = 0.0
    records = []

    for dt, row in df.iterrows():
        close = float(row["Close"])
        signal = int(row["signal"])

        # 1) 先计算调仓前总资产
        total_asset = cash + shares * close

        # 2) 按目标仓位算出应持有的股票市值/股数
        target_stock_value = total_asset * target_weight
        target_shares = target_stock_value / close if close > 0 else 0.0

        # 3) 按信号调仓：
        #    signal = 1  -> 只允许买入（不允许在买入信号里卖出）
        #    signal = -1 -> 交易数量按“维持 target_weight”计算（调仓到目标股数）
        #    signal = 0  -> 不交易，保持当前仓位
        trade_shares = 0.0
        if signal == 1:
            # 买入信号时，只做加仓到目标仓位，不做减仓
            trade_shares = max(0.0, target_shares - shares)
        elif signal == -1:
            # 卖出信号时，按目标仓位进行调仓
            trade_shares = target_shares - shares

        cash -= trade_shares * close
        shares += trade_shares

        # 4) 记录调仓后的账户状态
        stock_value = shares * close
        total_asset = cash + stock_value

        records.append({
            "Date":
                dt,
            "Close":
                close,
            "signal":
                signal,
            "trade_shares":
                trade_shares,
            "cash":
                cash,
            "shares":
                shares,
            "stock_value":
                stock_value,
            "total_asset":
                total_asset,
            "position_ratio":
                stock_value / total_asset if total_asset > 0 else 0.0,
        })

    result = pd.DataFrame(records).set_index("Date")
    result["cum_ret"] = result["total_asset"] / initial_cash
    result["daily_ret"] = result["total_asset"].pct_change().fillna(0.0)
    return result
