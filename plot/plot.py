import os
from matplotlib.rcsetup import cycler
import pandas as pd
import matplotlib.pyplot as plt


def plot_graph(df: pd.DataFrame,) -> None:
    base_dir = os.path.dirname(__file__)
    style_path = os.path.join(base_dir, 'google.mplstyle')
    plt.style.use(style_path)
    plt.rcParams['axes.prop_cycle'] = cycler(
        color=["#4285F4", "#DB4437", "#F4B400", "#0F9D58"])
    plt.figure(figsize=(8, 5))
    plt.plot(df["ma10"].tail(30), label="MA10")
    plt.plot(df["ma200"].tail(30), label="MA200")

    plt.legend()
    plt.title("Custom Plot")
    plt.show()
