import pandas as pd

from src.Models import Technology

_TECHNOLOGIES = (Technology.WIND, Technology.SOLAR, Technology.GAS)

def summarise(hourly):
    price = hourly["price"]
    shortage = hourly["mwh_unserved"] > 0

    summary = {
        "hours": len(hourly),
        "average_price": price.mean(),
        "average_price_excl_shortage_hours": price[~shortage].mean(),
        "median_price": price.median(),
        "hours_with_unserved_demand": int(shortage.sum()),
        "hours_at_zero_price": int((price == 0).sum()),
        "mwh_demand": hourly["mwh_demand"].sum(),
        "mwh_unserved": hourly["mwh_unserved"].sum(),
        "mwh_curtailed": hourly["mwh_curtailed_wind"].sum() + hourly["mwh_curtailed_solar"].sum(),
    }

    mwh_generated = sum(hourly["mwh_" + technology].sum() for technology in _TECHNOLOGIES)
    for technology in _TECHNOLOGIES:
        mwh = hourly["mwh_" + technology].sum()
        summary["mwh_" + technology] = mwh
        summary["share_" + technology] = mwh / mwh_generated
    return pd.Series(summary)

def write_excel(path, hourly, dispatch, summary):
    hourly = hourly.copy()
    summary = summary.copy()
    for technology in _TECHNOLOGIES:
        name = "share_" + technology
        hourly[name] = (hourly[name] * 100).round(2)
        summary[name] = round(summary[name] * 100, 2)

    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        summary.to_frame("value").to_excel(writer, sheet_name="summary", index_label="metric")
        hourly.to_excel(writer, sheet_name="hourly")
        dispatch.to_excel(writer, sheet_name="dispatch_mwh")
        