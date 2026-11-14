_TOLERANCE = 1e-6

class AuctionResult:
    def __init__(self, price, dispatch, marginal_units, demand_left):
        self.price = price
        self.dispatch = dispatch
        self.marginal_units = marginal_units
        self.demand_left = demand_left

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

       if mwh_offered < mwh_remaining - _TOLERANCE:
           for bid in same_price:
               dispatch[bid.unit] = bid.mwh_quantity
           mwh_remaining -= mwh_offered
       else:
           share = min(1.0,mwh_remaining / mwh_offered)
           for bid in same_price:
               dispatch[bid.unit] = bid.mwh_quantity * share
           marginal_units = tuple(bid.unit for bid in same_price)
           return AuctionResult(price, dispatch, marginal_units, 0.0)
    return AuctionResult(price_cap,dispatch,(), mwh_remaining)