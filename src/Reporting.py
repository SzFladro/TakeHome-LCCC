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

    mwh_demand = hourly["mwh_demand"].sum()
    for technology in _TECHNOLOGIES:
        mwh = hourly["mwh_" + technology].sum()
        summary["mwh_" + technology] = mwh
        summary["share_" + technology] = mwh / mwh_demand
    summary["share_unserved"] = hourly["mwh_unserved"].sum() / mwh_demand
    return pd.Series(summary)

def write_excel(path, hourly, dispatch, summary):
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        summary.to_frame("value").to_excel(writer, sheet_name="summary", index_label="metric")
        hourly.to_excel(writer, sheet_name="hourly")
        dispatch.to_excel(writer, sheet_name="mwh_dispatch")

        for sheet in writer.sheets.values():
            for column in sheet.columns:
                header = column[0]
                sheet.column_dimensions[header.column_letter].width = max(12, len(str(header.value)) + 2)
                for cell in column[1:]:
                    if isinstance(cell.value, float):
                        if str(header.value).startswith("share_"):
                            cell.number_format = "0.00%"
                        else:
                            cell.number_format = "#,##0.00"

        summary_sheet = writer.sheets["summary"]
        summary_sheet.column_dimensions["A"].width = 36
        summary_sheet.column_dimensions["B"].width = 16
        for name_cell, value_cell in summary_sheet.iter_rows(min_row=2):
            if str(name_cell.value).startswith("share_"):
                value_cell.number_format = "0.00%"