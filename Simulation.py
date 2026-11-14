import pandas as pd

from Auction import clear_auction
from Bidding import hourly_bid
from Models import Technology


_PRICE_CAP = 6000.0 

_TECHNOLOGIES = (Technology.WIND, Technology.SOLAR, Technology.GAS)

def simulate_market(data, price_cap=_PRICE_CAP):
	hourly = []
	dispatch =[]
	for hour in data.hours:
		bids = hourly_bid(data,hour)
		mwh_demand = data.mwh_demand.loc[hour]
		result = clear_auction(bids, mwh_demand, price_cap)

		mwh_generated = {technology: 0.0 for technology in _TECHNOLOGIES}
		mwh_available = {technology: 0.0 for technology in _TECHNOLOGIES}
		technology_proportion ={}
		for bid in bids:
			mwh_generated[bid.technology] += result.dispatch[bid.unit]
			mwh_available[bid.technology]  bid.mwh_quantity
			technology_proportion[bid.unit] = bid.technology

		if result.mwh_unserved > 0:
            price_setter = "unserved"
        else:
            marginal = sorted({technology_of[unit] for unit in result.marginal_units})
            price_setter = "+".join(marginal)

        mwh_total = sum(mwh_generated.values())
        row = {
            "gas_price_pTherm": data.gas_price_pTherm.loc[hour],
            "mwh_demand": mwh_demand,
            "price": result.price,
            "price_setter": price_setter,
        }
        for technology in TECHNOLOGIES:
            row["mwh_" + technology] = mwh_generated[technology]
        for technology in TECHNOLOGIES:
            row["share_" + technology] = mwh_generated[technology] / mwh_total if mwh_total > 0 else 0.0
        row["mwh_unserved"] = result.mwh_unserved
        for technology in (Technology.WIND, Technology.SOLAR):
            row["mwh_curtailed_" + technology] = mwh_available[technology] - mwh_generated[technology]

        hourly.append(row)
        dispatch.append(result.dispatch)

    hourly = pd.DataFrame(hourly, index=data.hours)
    unit_dispatch = pd.DataFrame(dispatch, index=data.hours)
    return hourly, unit_dispatch

