import matplotlib
import matplotlib.pyplot as plt
import numpy as np

from src.Models import Technology

matplotlib.use("Agg")

_COLOURS = {
    Technology.WIND: "#2a78d6",
    Technology.SOLAR: "#eb6834",
    Technology.GAS: "#1baf7a",
    "unserved": "#e87ba4",
}
_BACKGROUND = "#fcfcfb"
_TEXT = "#0b0b0b"
_TEXT_SECONDARY = "#52514e"
_GRID = "#e4e3df"

_LABELS = {
    Technology.WIND: "Wind",
    Technology.SOLAR: "Solar",
    Technology.GAS: "Gas",
    "unserved": "Unserved demand",
}

_TECHNOLOGIES = (Technology.WIND, Technology.SOLAR, Technology.GAS)


def plot_generation_mix(hourly, path):
    edges = _hour_edges(hourly)
    figure, (top, bottom) = plt.subplots(2, 1, figsize=(13, 7.5), sharex=True)

    series = list(_TECHNOLOGIES) + ["unserved"]
    top.stackplot(
        edges,
        [_steps(hourly["mwh_" + name]) / 1000 for name in series],
        labels=[_LABELS[name] for name in series],
        colors=[_COLOURS[name] for name in series],
        step="post",
        edgecolor=_BACKGROUND,
        linewidth=0.4,
    )
    top.step(edges, _steps(hourly["mwh_demand"]) / 1000, where="post",
             color=_TEXT, linewidth=1.2, label="Demand")
    top.set_ylabel("GWh per hour")
    top.set_title("Generation by technology and demand", loc="left", color=_TEXT, fontsize=11)
    top.legend(loc="upper left", bbox_to_anchor=(1.005, 1), frameon=False, fontsize=9)

    bottom.stackplot(
        edges,
        [_steps(hourly["share_" + name]) * 100 for name in series],
        labels=[_LABELS[name] for name in series],
        colors=[_COLOURS[name] for name in series],
        step="post",
        edgecolor=_BACKGROUND,
        linewidth=0.4,
    )
    bottom.set_ylim(0, 100)
    bottom.set_ylabel("% of demand")
    bottom.set_xlabel("Hour")
    bottom.set_title("Share of demand met by each technology", loc="left", color=_TEXT, fontsize=11)
    bottom.legend(loc="upper left", bbox_to_anchor=(1.005, 1), frameon=False, fontsize=9)

    for axes in (top, bottom):
        _style(axes, hourly)
    _save(figure, path)


def plot_prices(hourly, path):
    edges = _hour_edges(hourly)
    price = hourly["price"]
    shortage = hourly["mwh_unserved"] > 0
    colour = _COLOURS[Technology.WIND]

    figure, (strip, main) = plt.subplots(
        2, 1, figsize=(13, 5), sharex=True, gridspec_kw={"height_ratios": [1, 6]}
    )

    blocks = [(hour - 1, 1) for hour in hourly.index[shortage]]
    strip.broken_barh(blocks, (0.15, 0.7), color=colour)
    strip.set_ylim(0, 1)
    strip.set_yticks([])
    title = "Hours with unserved demand: " + str(int(shortage.sum()))
    if shortage.any():
        title += ", priced at the cap of £{:,.0f}/MWh".format(price[shortage].max())
    strip.set_title(title, loc="left", color=_TEXT, fontsize=11)

    main.step(edges, _steps(price.where(~shortage)), where="post", color=colour, linewidth=1.6,
              clip_on=False)
    main.set_ylim(bottom=0)
    main.set_ylabel("£/MWh")
    main.set_xlabel("Hour")
    main.set_title("Clearing price in all other hours", loc="left", color=_TEXT, fontsize=11)

    for axes in (strip, main):
        _style(axes, hourly)
    strip.grid(False)
    _save(figure, path)


def _hour_edges(hourly):
    hours = hourly.index.to_numpy()
    return np.append(hours - 1, hours[-1])


def _steps(series):
    values = series.to_numpy(dtype=float)
    return np.append(values, values[-1])


def _style(axes, hourly):
    first_hour, last_hour = hourly.index[0], hourly.index[-1]
    axes.set_facecolor(_BACKGROUND)
    axes.set_xlim(first_hour - 1, last_hour)
    axes.set_xticks(np.arange(first_hour - 1, last_hour + 1, 24))
    axes.grid(axis="y", color=_GRID, linewidth=0.8)
    axes.set_axisbelow(True)
    for side in ("top", "right", "left"):
        axes.spines[side].set_visible(False)
    axes.spines["bottom"].set_color(_GRID)
    axes.tick_params(colors=_TEXT_SECONDARY, length=0, labelsize=9)
    axes.xaxis.label.set_color(_TEXT_SECONDARY)
    axes.yaxis.label.set_color(_TEXT_SECONDARY)


def _save(figure, path):
    figure.patch.set_facecolor(_BACKGROUND)
    figure.tight_layout()
    figure.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(figure)