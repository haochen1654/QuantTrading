import pandas as pd


def backtest_always_half_position(
    df: pd.DataFrame,
    initial_cash: float,
    target_weight: float = 0.5,
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
    trade_counter = 0

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
            trade_counter += 1 if trade_shares > 0 else 0
        elif signal == -1:
            # 卖出信号时，直接空仓
            trade_shares = 0 - shares
            # # 卖出信号时，按目标仓位进行调仓
            # trade_shares = target_shares - shares
            trade_counter += 1 if trade_shares < 0 else 0

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
            "trade_count":
                trade_counter,
        })

    result = pd.DataFrame(records).set_index("Date")
    result["cum_ret"] = result["total_asset"] / initial_cash
    result["daily_ret"] = result["total_asset"].pct_change().fillna(0.0)
    return result


def backtest_weekly_dca(
    df: pd.DataFrame,
    weekly_amount: float = 500.0,
    initial_cash: float = 0.0,
) -> pd.DataFrame:
    """
    定投回测：每周五定投固定金额（默认 500 元）。

    参数:
        df: 含有 Close 列的行情数据（索引为日期）
        weekly_amount: 每周五投入金额
        initial_cash: 初始现金（可选）

    返回:
        每日账户明细（投入本金、持仓、总资产、收益、回撤等）
    """
    if "Close" not in df.columns:
        raise ValueError("df 缺少 Close 列，无法回测。")

    cash = initial_cash
    shares = 0.0
    total_invested = 0.0
    records = []
    trade_counter = 0

    for dt, row in df.iterrows():
        close = float(row["Close"])
        is_friday = dt.weekday() == 4  # Monday=0, Friday=4

        invest_amount = weekly_amount if is_friday else 0.0
        trade_shares = 0.0

        if invest_amount > 0 and close > 0 and cash >= invest_amount:
            # 先入金，再按当日收盘价买入同等金额
            cash -= invest_amount
            total_invested += invest_amount
            trade_shares = invest_amount / close
            shares += trade_shares
            trade_counter += 1

        stock_value = shares * close
        total_asset = cash + stock_value
        position_ratio = stock_value / total_asset if total_asset > 0 else 0.0

        records.append({
            "Date": dt,
            "Close": close,
            "is_friday": is_friday,
            "invest_amount": invest_amount,
            "total_invested": total_invested,
            "trade_shares": trade_shares,
            "cash": cash,
            "shares": shares,
            "stock_value": stock_value,
            "total_asset": total_asset,
            "position_ratio": position_ratio,
            "trade_count": trade_counter,
        })

    result = pd.DataFrame(records).set_index("Date")

    # 累计收益率：总资产相对累计投入本金
    invested = result["total_invested"].where(result["total_invested"] > 0)
    result["cum_ret"] = (result["total_asset"] / invested - 1.0).fillna(0.0)
    result["daily_ret"] = result["total_asset"].pct_change().fillna(0.0)

    # 用累计收益曲线计算回撤，更能反映定投策略表现
    nav = (1.0 + result["cum_ret"]).cummax()
    curve = 1.0 + result["cum_ret"]
    result["drawdown"] = curve / nav - 1.0
    result["max_drawdown"] = result["drawdown"].cummin()
    return result
