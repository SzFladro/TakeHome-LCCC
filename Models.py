from dataclasses import dataclass

class Technology:
    WIND ="wind"
    SOLAR = "solar"
    GAS = "gas"
    
@dataclass(frozen=True)
class RenewablePlant:
    name: str
    technology: str
    mw_capacity: float

@dataclass(frozen=True)
class GasPlant:
    name: str
    mw_capacity: float
    efficiency: float

@dataclass(frozen=True)
class Bid:
    unit: str
    technology: str
    mwh_quantity: float
    price: float