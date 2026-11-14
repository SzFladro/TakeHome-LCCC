import numpy as np
import pandas as pd
from scipy.optimize import linprog

from src.Bidding import hourly_bid

_TIE_BREAK_COST = 1e-4
_NOISE = 1e-6
_DECIMALS = 6
_HOURS_AT_FULL_POWER = 1.6


class Storage:
    def __init__(self,name="storage",mw_power=7500, charge_efficiency=0.92, discharge_efficiency=0.92, mwh_initial=0.0):
        self.name = name
        self.mw_power = mw_power
        self.mwh_capacity = self.mw_power * _HOURS_AT_FULL_POWER
        self.charge_efficiency = charge_efficiency
        self.discharge_efficiency = discharge_efficiency
        self.mwh_initial = mwh_initial

def plan_storage(data,storage, price_cap):
    hours = list(data.hours)
    num_hours = len(hours)
    
    bids = [hourly_bid(data,hour) for hour in hours]
    num_bids = len(bids[0])
    
    num_per_hour = num_bids + 4
    num_unknowns = num_hours * num_per_hour

    cost = np.zeros(num_unknowns)
    lowest = np.zeros(num_unknowns)
    highest = np.full(num_unknowns, np.inf)

    rules = np.zeros((2 * num_hours, num_unknowns))
    targets = np.zeros(2 * num_hours)

    for t in range(num_hours):
        first = t * num_per_hour
        unserved = first + num_bids
        charge = unserved + 1
        discharge = unserved + 2
        stored = unserved + 3

        for i, bid in enumerate(bids[t]):
            cost[first + i] = bid.price
            highest[first + i] = bid.mwh_quantity

        cost[unserved] = price_cap
        cost[charge] = _TIE_BREAK_COST
        highest[charge] = storage.mw_power
        highest[discharge] = storage.mw_power
        highest[stored] = storage.mwh_capacity

        rules[t, first:first + num_bids] = 1.0
        rules[t, unserved] = 1.0
        rules[t, discharge] = 1.0
        rules[t, charge] = -1.0
        targets[t] = data.mwh_demand.loc[hours[t]]


        row = num_hours + t
        rules[row, stored] = 1.0
        rules[row, charge] = -storage.charge_efficiency
        rules[row, discharge] = 1.0 / storage.discharge_efficiency
        if t == 0:
            targets[row] = storage.mwh_initial
        else:
            rules[row, stored - num_per_hour] = -1.0

    lowest[num_unknowns - 1] = storage.mwh_initial

    solution = linprog(
        cost, A_eq=rules, b_eq=targets, bounds=list(zip(lowest, highest)), method="highs"
    )

    amounts = solution.x.reshape(num_hours, num_per_hour)
    amounts = np.where(np.abs(amounts) < _NOISE, 0.0, amounts)

    stored_value = np.maximum(0.0, -solution.eqlin.marginals[num_hours:])

    offer_price = stored_value / storage.discharge_efficiency
    bid_price = stored_value * storage.charge_efficiency

    return pd.DataFrame(
        {
            "mwh_charge": amounts[:, num_bids + 1],
            "mwh_discharge": amounts[:, num_bids + 2],
            "mwh_stored": amounts[:, num_bids + 3],
            "offer_price": np.round(offer_price, _DECIMALS),
            "bid_price": np.round(bid_price, _DECIMALS),
        },
        index=data.hours,
    )