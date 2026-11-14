import matplotlib
import matplotlib.pyplot as plt
import numpy as np

from src.Models import Technology

matplotlib.use("Agg")

_COLOURS = {
    Technology.WIND: "#2a78d6",
    Technology.SOLAR: "#eb6834",
    Technology.GAS: "#1baf7a",
    "storage_discharge": "#eda100",
    "unserved": "#e87ba4",
}
_SCENARIO_COLOURS = ("#2a78d6", "#eb6834")
_BACKGROUND = "#fcfcfb"
_TEXT = "#0b0b0b"
_TEXT_SECONDARY = "#52514e"
_GRID = "#e4e3df"

_LABELS = {
    Technology.WIND: "Wind",
    Technology.SOLAR: "Solar",
    Technology.GAS: "Gas",
    "storage_discharge": "Storage discharge",
    "unserved": "Unserved demand",
}

_TECHNOLOGIES = (Technology.WIND, Technology.SOLAR, Technology.GAS)


def plot_generation_mix(hourly, path, scenario=""):
    figure, (top, bottom) = plt.subplots(2, 1, figsize=(13, 7.5), sharex=True)
    _draw_generation(top, hourly, "Generation by technology and demand" + _suffix(scenario))
    _draw_shares(bottom, hourly)
    bottom.set_xlabel("Hour")
    for axes in (top, bottom):
        _style(axes, hourly)
    _save(figure, path)


def plot_prices(hourly, path, scenario=""):
    _plot_price_figure({scenario: hourly}, path)


def plot_generation_mix_comparison(no_storage_hourly, with_storage_hourly, path):
    figure, (top, middle, bottom) = plt.subplots(3, 1, figsize=(13, 10.5), sharex=True)
    _draw_generation(top, no_storage_hourly, "Generation by technology and demand: no-storage")
    _draw_generation(middle, with_storage_hourly, "Generation by technology and demand: with-storage")
    highest = max(top.get_ylim()[1], middle.get_ylim()[1])
    top.set_ylim(0, highest)
    middle.set_ylim(0, highest)

    edges = _hour_edges(with_storage_hourly)
    for name in _series(with_storage_hourly):
        change = with_storage_hourly["mwh_" + name]
        if "mwh_" + name in no_storage_hourly.columns:
            change = change - no_storage_hourly["mwh_" + name]
        bottom.step(edges, _steps(change) / 1000, where="post",
                    color=_COLOURS[name], linewidth=1.6, label=_LABELS[name])
    bottom.axhline(0, color=_TEXT_SECONDARY, linewidth=0.8)
    bottom.set_ylabel("GWh per hour")
    bottom.set_xlabel("Hour")
    bottom.set_title("Difference when introducing storage",
                     loc="left", color=_TEXT, fontsize=11)
    bottom.legend(loc="upper left", bbox_to_anchor=(1.005, 1), frameon=False, fontsize=9)

    for axes in (top, middle, bottom):
        _style(axes, with_storage_hourly)
    _save(figure, path)


def plot_prices_comparison(no_storage_hourly, with_storage_hourly, path):
    _plot_price_figure({"No-storage": no_storage_hourly, "With-storage": with_storage_hourly}, path)


def _draw_generation(axes, hourly, title):
    edges = _hour_edges(hourly)
    series = _series(hourly)
    axes.stackplot(
        edges,
        [_steps(hourly["mwh_" + name]) / 1000 for name in series],
        labels=[_LABELS[name] for name in series],
        colors=[_COLOURS[name] for name in series],
        step="post",
        edgecolor=_BACKGROUND,
        linewidth=0.4,
    )
    axes.step(edges, _steps(hourly["mwh_demand"]) / 1000, where="post",
              color=_TEXT, linewidth=1.2, label="Demand")
    if _has_storage(hourly):
        title += " (supply above the demand line due to storage charging)"
    axes.set_ylabel("GWh per hour")
    axes.set_title(title, loc="left", color=_TEXT, fontsize=11)
    axes.legend(loc="upper left", bbox_to_anchor=(1.005, 1), frameon=False, fontsize=9)


def _draw_shares(axes, hourly):
    edges = _hour_edges(hourly)
    series = _series(hourly)
    axes.stackplot(
        edges,
        [_steps(hourly["share_" + name]) * 100 for name in series],
        labels=[_LABELS[name] for name in series],
        colors=[_COLOURS[name] for name in series],
        step="post",
        edgecolor=_BACKGROUND,
        linewidth=0.4,
    )
    axes.set_ylim(0, 100)
    if _has_storage(hourly):
        axes.set_ylabel("% of demand + charging")
        title = "Share of demand and storage charging met by each source"
    else:
        axes.set_ylabel("% of demand")
        title = "Share of demand met by each technology"
    axes.set_title(title, loc="left", color=_TEXT, fontsize=11)
    axes.legend(loc="upper left", bbox_to_anchor=(1.005, 1), frameon=False, fontsize=9)


def _plot_price_figure(scenarios, path):
    names = list(scenarios)
    first = scenarios[names[0]]
    edges = _hour_edges(first)
    comparing = len(names) > 1

    figure, (strip, main) = plt.subplots(
        2, 1, figsize=(13, 5.2), sharex=True, gridspec_kw={"height_ratios": [len(names), 6]}
    )

    price_cap = None
    for row, name in enumerate(names):
        hourly = scenarios[name]
        price = hourly["price"]
        at_price_cap = hourly["at_price_cap"]
        colour = _SCENARIO_COLOURS[row]
        if at_price_cap.any():
            price_cap = price[at_price_cap].max()

        level = len(names) - 1 - row
        blocks = [(hour - 1, 1) for hour in hourly.index[at_price_cap]]
        strip.broken_barh(blocks, (level + 0.15, 0.7), color=colour)
        label = str(int(at_price_cap.sum())) + " h"
        if comparing:
            label = name + ": " + label
        strip.text(hourly.index[-1] + 1.5, level + 0.5, label,
                   va="center", fontsize=9, color=_TEXT_SECONDARY)

        width = 3.0 if comparing and row == 0 else 1.6
        main.step(edges, _steps(price.where(~at_price_cap)), where="post",
                  color=colour, linewidth=width, clip_on=False, label=name)

    strip.set_ylim(0, len(names))
    strip.set_yticks([])
    title = "Hours priced at the cap"
    if price_cap is not None:
        title += " of £{:,.0f}/MWh".format(price_cap)
    strip.set_title(title, loc="left", color=_TEXT, fontsize=11)

    main.set_ylim(bottom=0)
    main.set_ylabel("£/MWh")
    main.set_xlabel("Hour")
    title = "Clearing price in other hours"
    if not comparing:
        title += _suffix(names[0])
    main.set_title(title, loc="left", color=_TEXT, fontsize=11)
    if comparing:
        main.legend(loc="upper left", bbox_to_anchor=(1.005, 1), frameon=False, fontsize=9)

    for axes in (strip, main):
        _style(axes, first)
    strip.grid(False)
    _save(figure, path)


def _has_storage(hourly):
    return "mwh_storage_discharge" in hourly.columns


def _series(hourly):
    series = list(_TECHNOLOGIES)
    if _has_storage(hourly):
        series.append("storage_discharge")
    series.append("unserved")
    return series


def _suffix(scenario):
    return ": " + scenario if scenario else ""


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