import yfinance as yf
import pandas as pd
from strategy.base import backtest_always_half_position

# ====== 可调参数 ======
# 初始资金（单位：元）
INITIAL_CASH = 1_000_000.0
# 永远半仓：始终50%资金持仓，50%现金
TARGET_WEIGHT = 0.5
# 回测标的与区间
SYMBOL = "AAPL"
START_DATE = "2020-01-01"
END_DATE = "2026-04-19"


def fetch_price_history(symbol: str, start: str, end: str) -> pd.DataFrame:
    """下载历史行情并做最小化校验。"""
    ticker = yf.Ticker(symbol)
    df = ticker.history(start=start, end=end)
    if df.empty:
        raise ValueError("未获取到历史数据，请检查网络、日期区间或股票代码。")
    if "Close" not in df.columns:
        raise ValueError("行情数据缺少 Close 列，无法回测。")
    return df


def summarize_result(bt: pd.DataFrame) -> dict:
    """计算常用回测指标：最终资产、累计收益、最大回撤。"""
    cummax = bt["total_asset"].cummax()
    drawdown = bt["total_asset"] / cummax - 1.0
    return {
        "final_asset": float(bt["total_asset"].iloc[-1]),
        "cum_return_pct": float((bt["cum_ret"].iloc[-1] - 1.0) * 100),
        "max_drawdown_pct": float(drawdown.min() * 100),
    }


def main() -> None:
    # 下载行情
    df = fetch_price_history(SYMBOL, START_DATE, END_DATE)

    # 计算移动平均线
    df["ma10"] = df["Close"].rolling(10).mean()
    df["ma200"] = df["Close"].rolling(200).mean()

    print("=== 行情数据预览 ===")
    # 显示最近15天的收盘价和均线，验证数据正确性
    print(df[["Close", "ma10", "ma200"]].tail(30))

    # 计算每日收益率
    df["ret"] = df["Close"].pct_change()

    print("=== 收益率数据预览 ===")
    # 显示最近15天的收盘价和收益率，验证数据正确
    print(df[["Close", "ret"]].tail(30))

    # 生成交易信号
    df["signal"] = 0

    # 当ma10上穿ma200时，产生买入信号（1），否则为0
    df.loc[df["ma10"] > df["ma200"], "signal"] = 1
    # 当ma10下穿ma200时，产生卖出信号（-1），否则为0
    df.loc[df["ma10"] < df["ma200"], "signal"] = -1

    backtest_always_half_position(df,
                                  initial_cash=INITIAL_CASH,
                                  target_weight=TARGET_WEIGHT)

    # df["position"] = df["signal"].shift(1).fillna(0)
    # # 计算策略收益率
    # df["ret"] = df["Close"].pct_change()
    # # 策略收益率 = 持仓 * 价格变动
    # df["strategy_ret"] = df["position"] * df["ret"]
    # # 计算累积收益率
    # cum_ret = (1 + df["strategy_ret"]).cumprod()

    # print(cum_ret.tail())

    # # 输出结果
    # print("=== 回测结果（永远半仓）===")
    # print(f"标的: {SYMBOL}")
    # print(f"区间: {START_DATE} ~ {END_DATE}")
    # print(f"起始资金: {INITIAL_CASH:.2f}")
    # print(f"目标仓位: {TARGET_WEIGHT:.0%}")
    # print(f"最终资产: {stats['final_asset']:.2f}")
    # print(f"累计收益: {stats['cum_return_pct']:.2f}%")
    # print(f"最大回撤: {stats['max_drawdown_pct']:.2f}%")
    # print("\n最近5天账户明细:")
    # print(bt[["Close", "cash", "stock_value", "total_asset",
    #           "position_ratio"]].tail())


if __name__ == "__main__":
    main()
