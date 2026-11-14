from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from src.Models import Technology, RenewablePlant, GasPlant

_RENEWABLE_SHEETS = {Technology.WIND: "windplants", Technology.SOLAR: "solarplants"}
_LOAD_FACTOR_SHEETS = {Technology.WIND: "wind_loadfactors", Technology.SOLAR: "solar_loadfactors"}


@dataclass(frozen=True)
class MarketData:
    renewable_plants: tuple
    gas_plants: tuple
    load_factors: pd.DataFrame
    mwh_demand: pd.Series
    gas_price_pTherm: pd.Series

    @property
    def hours(self):
        return self.mwh_demand.index


def load_data(path):
    path = Path(path)
    sheets = pd.read_excel(path, sheet_name=None)

    renewable_plants = []
    load_factor_columns = {}
    for technology, sheet in _RENEWABLE_SHEETS.items():
        plants = sheets[sheet]
        for row in plants.itertuples(index=False):
            renewable_plants.append(RenewablePlant(str(row.name), technology, float(row.capacity)))

        factors = sheets[_LOAD_FACTOR_SHEETS[technology]].set_index("hour")
        for plant_name in factors.columns:
            load_factor_columns[plant_name] = factors[plant_name]
    load_factors = pd.DataFrame(load_factor_columns)

    gas = sheets["gasplants"]
    gas_plants = []
    for row in gas.itertuples(index=False):
        gas_plants.append(GasPlant(str(row.name), float(row.capacity), float(row.efficiency)))

    demand = sheets["demand"].set_index("hour")["demand"]
    gas_price = sheets["gas_prices"].set_index("hour")["price"]

    return MarketData(
        renewable_plants=tuple(renewable_plants),
        gas_plants=tuple(gas_plants),
        load_factors=load_factors.astype(float),
        mwh_demand=demand.astype(float),
        gas_price_pTherm=gas_price.astype(float),
    )