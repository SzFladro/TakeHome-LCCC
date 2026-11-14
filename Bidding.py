from Models import Technology, Bid


_THERMS_PER_MWH = 34.121
_PENCE_PER_POUND = 100.0
_RENEWABLE_BID_PRICE = 0.0

def break_even_price(gas_price_pTherm, efficiency):
    gas_cost_per_mwh = gas_price_pTherm / _PENCE_PER_POUND * _THERMS_PER_MWH
    return gas_cost_per_mwh / efficiency

def hourly_bid(data,hour):
    load_factors = data.load_factors.loc[hour]
    gas_price = data.gas_price_pTherm.loc[hour]
    
    bids = []
    for plant in data.renewable_plants:
        mwh_available = plant.mw_capacity * load_factors[plant.name]
        bids.append(Bid(plant.name, plant.technology, mwh_available, _RENEWABLE_BID_PRICE))

    for plant in data.gas_plants:
        price = break_even_price(gas_price,plant.efficiency)
        bids.append(Bid(plant.name, Technology.GAS,plant.mw_capacity,price))

    return bids