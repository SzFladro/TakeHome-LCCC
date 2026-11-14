import pandas as pd

from src.Models import Technology

_TECHNOLOGIES = (Technology.WIND, Technology.SOLAR, Technology.GAS)

def summarise(hourly):
    price = hourly["price"]
    at_price_cap = hourly["at_price_cap"]

    has_storage = "mwh_storage_discharge" in hourly.columns
    if has_storage:
        mwh_discharged = hourly["mwh_storage_discharge"].sum() 
        mwh_charged = hourly["mwh_storage_charge"].sum() 
        storage_revenue = (price * hourly["mwh_storage_discharge"]).sum() 
        storage_charging_cost = (price * hourly["mwh_storage_charge"]).sum()
    else:
        mwh_discharged = 0
        mwh_charged = 0
        storage_revenue = 0
        storage_charging_cost = 0

    summary = {
        "hours": len(hourly),
        "average_price": price.mean(),
        "average_price_excluding_price_cap_hours": price[~at_price_cap].mean(),
        "median_price": price.median(),
        "hours_at_price_cap": int(at_price_cap.sum()),
        "hours_with_unserved_demand": int((hourly["mwh_unserved"] > 0).sum()),
        "hours_at_zero_price": int((price == 0).sum()),
        "mwh_demand": hourly["mwh_demand"].sum(),
        "mwh_unserved": hourly["mwh_unserved"].sum(),
        "mwh_curtailed": hourly["mwh_curtailed_wind"].sum() + hourly["mwh_curtailed_solar"].sum(),
    }


    mwh_needed = hourly["mwh_demand"].sum() + mwh_charged
    for technology in _TECHNOLOGIES:
        mwh = hourly["mwh_" + technology].sum()
        summary["mwh_" + technology] = mwh
        summary["share_" + technology] = mwh / mwh_needed
    summary["mwh_storage_discharge"] = mwh_discharged
    summary["share_storage_discharge"] = mwh_discharged / mwh_needed
    summary["share_unserved"] = hourly["mwh_unserved"].sum() / mwh_needed

    summary["mwh_storage_charge"] = mwh_charged
    summary["storage_revenue"] = storage_revenue
    summary["storage_charging_cost"] = storage_charging_cost
    summary["storage_profit"] = storage_revenue - storage_charging_cost
    return pd.Series(summary)

def compare_summaries(no_storage_hourly, with_storage_hourly):
    return pd.DataFrame({
        "no_storage": summarise(no_storage_hourly),
        "with_storage": summarise(with_storage_hourly),
    })

def write_excel(path, summary, no_storage_hourly, with_storage_hourly, no_storage_dispatch, with_storage_dispatch):
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        summary.to_excel(writer, sheet_name="summary", index_label="metric")
        no_storage_hourly.to_excel(writer, sheet_name="no_storage_hourly")
        with_storage_hourly.to_excel(writer, sheet_name="with_storage_hourly")
        no_storage_dispatch.to_excel(writer, sheet_name="no_storage_dispatch_mwh")
        with_storage_dispatch.to_excel(writer, sheet_name="with_storage_dispatch_mwh")

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
        summary_sheet.column_dimensions["A"].width = 38
        summary_sheet.column_dimensions["B"].width = 18
        summary_sheet.column_dimensions["C"].width = 18
        for row in summary_sheet.iter_rows(min_row=2):
            name = str(row[0].value)
            for value_cell in row[1:]:
                if name.startswith("share_"):
                    value_cell.number_format = "0.00%"
                elif name.startswith("hours"):
                    value_cell.number_format = "0"