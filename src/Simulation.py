import pandas as pd

from src.Auction import clear_auction
from src.Bidding import hourly_bid
from src.Models import Technology
from src.Storage import plan_storage


_PRICE_CAP = 6000.0

_TECHNOLOGIES = (Technology.WIND, Technology.SOLAR, Technology.GAS)

def simulate_market(data, price_cap=_PRICE_CAP, storage=None):
    plan = None
    if storage is not None:
        plan = plan_storage(data, storage, price_cap)

    hourly = []
    dispatch = []
    for hour in data.hours:
        bids = hourly_bid(data, hour)
        mwh_demand = data.mwh_demand.loc[hour]

        mwh_charge = 0.0
        mwh_discharge = 0.0
        if plan is not None:
            mwh_charge = plan.loc[hour, "mwh_charge"]
            mwh_discharge = plan.loc[hour, "mwh_discharge"]

        mwh_from_generators = max(0.0, mwh_demand + mwh_charge - mwh_discharge)
        result = clear_auction(bids, mwh_from_generators, price_cap)

        mwh_generated = {technology: 0.0 for technology in _TECHNOLOGIES}
        mwh_available = {technology: 0.0 for technology in _TECHNOLOGIES}
        technology_of_unit = {}
        for bid in bids:
            mwh_generated[bid.technology] += result.dispatch[bid.unit]
            mwh_available[bid.technology] += bid.mwh_quantity
            technology_of_unit[bid.unit] = bid.technology

        price = result.price
        if result.demand_left > 0:
            price_setter = "unserved"
        else:
            marginal = sorted({technology_of_unit[unit] for unit in result.marginal_units})
            price_setter = "+".join(marginal)

        if mwh_discharge > 0 and plan.loc[hour, "offer_price"] > price:
            price = plan.loc[hour, "offer_price"]
            price_setter = "storage"

        row = {
            "gas_price_pTherm": data.gas_price_pTherm.loc[hour],
            "mwh_demand": mwh_demand,
            "price": price,
            "price_setter": price_setter,
            "at_price_cap": bool(price >= price_cap),
        }
        for technology in _TECHNOLOGIES:
            row["mwh_" + technology] = mwh_generated[technology]
        if plan is not None:
            row["mwh_storage_discharge"] = mwh_discharge
        row["mwh_unserved"] = result.demand_left


        mwh_needed = mwh_demand + mwh_charge
        for technology in _TECHNOLOGIES:
            if mwh_needed > 0:
                row["share_" + technology] = mwh_generated[technology] / mwh_needed
            else:
                row["share_" + technology] = 0.0
        if plan is not None:
            if mwh_needed > 0: 
                row["share_storage_discharge"] = mwh_discharge / mwh_needed 
            else:
                row["share_storage_discharge"] = 0.0
        if mwh_needed > 0:
            row["share_unserved"] = result.demand_left / mwh_needed
        else:
            row["share_unserved"] = 0.0

        for technology in (Technology.WIND, Technology.SOLAR):
            row["mwh_curtailed_" + technology] = mwh_available[technology] - mwh_generated[technology]
        if plan is not None:
            row["mwh_storage_charge"] = mwh_charge
            row["mwh_stored"] = plan.loc[hour, "mwh_stored"]

        hourly.append(row)
        unit_row = dict(result.dispatch)
        if plan is not None:
            unit_row[storage.name] = mwh_discharge
        dispatch.append(unit_row)

    hourly = pd.DataFrame(hourly, index=data.hours)
    unit_dispatch = pd.DataFrame(dispatch, index=data.hours)
    return hourly, unit_dispatch