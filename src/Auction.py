from dataclasses import dataclass

@dataclass(frozen=True)
class AuctionResult:
    price: float
    dispatch: dict
    marginal_units: tuple
    demand_left: float

def clear_auction(bids, mwh_demand, price_cap):
    dispatch = {bid.unit: 0.0 for bid in bids}
    offers = []
    for bid in bids:
        if bid.mwh_quantity > 0:
            offers.append(bid)

    mwh_remaining = mwh_demand
    for price in sorted({bid.price for bid in offers}):
       same_price =[]
       for bid in offers:
           if bid.price == price:
               same_price.append(bid)
       mwh_offered = sum(bid.mwh_quantity for bid in same_price)

       if mwh_offered < mwh_remaining:
           for bid in same_price:
               dispatch[bid.unit] = bid.mwh_quantity
           mwh_remaining -= mwh_offered
       else:
           share = mwh_remaining / mwh_offered
           for bid in same_price:
               dispatch[bid.unit] = bid.mwh_quantity * share
           marginal_units = tuple(bid.unit for bid in same_price)
           return AuctionResult(price, dispatch, marginal_units, 0.0)
    return AuctionResult(price_cap,dispatch,(), mwh_remaining)