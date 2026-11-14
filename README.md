# TakeHome-LCCC Task

A Python model of a pay-as-clear electricity auction described in the brief.
It computes the clearing price in £/MWh and computes the wind/solar/gas generation mix for each of the 168 hours within the Excel dataset.
It then repeats with a storage asset that takes part in the market and compares the two to see the impact of introducing storage on shortages.


## Folder layout
 
```
main.py             runs both cases and writes the outputs
data.xlsx           input data supplied with the brief
src/
  Models.py         Technology, RenewablePlant, GasPlant, Bid
  Data.py           reads the excel dataset into a MarketData object
  Bidding.py        each plant's break-even bid for an hour
  Auction.py        clears one hourly auction
  Storage.py        the storage asset and how it plans its trades
  Simulation.py     runs every hour, with or without storage
  Reporting.py      summary figures and the Excel results
  Plotting.py       the 6 graphs created for the market allocation with and without storage.
Output/             results from a run
  comparison_generation_mix.png       Shows a comparison of the generation mix from different assets as well as the unserved demand difference when introducing storage
  comparison_prices.png               Shows an overlayed graph of the clearing prices with and without storage, as well as shows where the demand hasn't met and thus been priced as £6000/MWh (M6)
  no_storage_generation_mix.png       Shows the proportion of demand covered by generation assets as well as where the demand hasn't been met, given no storage assets
  no_storage_prices.png               Shows a graph of the clearing prices without storage as well as where the demand hasn't met and thus been priced as £6000/MWh (M6)
  results.xlsx						  Shows the results of the simulations for the market with and without storage, a summary and an hourly breakdown of which assets supplied what and the proportions.
  with_storage_generation_mix.png     Shows the proportion of demand covered by generation assets as well as where the demand hasn't been met, given storage assets
  with_storage_prices.png             Shows a graph of the clearing prices with storage as well as where the demand hasn't met and thus been priced as £6000/MWh (M6)
```

 
## Results.xlsx
 
| | No storage | With storage |
|---|---:|---:|
| Average price (£/MWh) | 1,087.09 | 806.02 |
| Average price excluding hours at the price cap (£/MWh) | 62.09 | 64.02 |
| Median price (£/MWh) | 67.44 | 67.86 |
| Hours at the price cap | 29 | 21 |
| Hours with unserved demand | 29 | 15 |
| Hours at zero price | 11 | 9 |
| Unserved demand (MWh) | 60,326 | 26,801 |
| Curtailed wind and solar (MWh) | 35,969 | 21,603 |
| Share of demand met: wind / solar / gas | 35.09% / 19.39% / 44.03% | 34.68% / 19.24% / 44.01% |
| Share met by storage discharge | – | 1.42% |
| Share unserved | 1.49% | 0.65% |
| Storage profit (£m) | – | 132.2 |
 

 ## How the model works
 
**Bids (`Bidding.py`).** Ahead of each hour every plant submits one bid: a
quantity and its break-even price.
 
* Wind and solar offer `capacity × load factor` at £0/MWh.

* Gas plants offer their full capacity at their fuel cost:
  `gas price (p/therm) ÷ 100 × 34.121 therms/MWh ÷ efficiency`.
  At 70p/therm that is £43.43/MWh for the 55%-efficient plant and £68.24/MWh
  for the 35%-efficient one.

**Auction (`Auction.py`).** Bids are accepted from cheapest to most expensive until
demand is met. The price is the bid of the last plant needed, and that plant
runs only for the volume still required. Every dispatched plant is paid that
price.
 
**Storage (`Storage.py`).** Storage takes part in the same auction and, like the
generators, bids at break-even. A generator's break-even price is its fuel cost.
Storage has no fuel: selling a MWh now means not selling it later, so its
break-even price is what the stored energy is worth in the hours ahead.
 
Storage is assumed to know the week in advance and not to try to move the
price (S5, S6). Under those two assumptions the market settles on the plan that
meets demand at the lowest cost, so `plan_storage` finds that plan with a
linear programme (SciPy's HiGHS solver). It minimises gas fuel cost plus
unserved demand priced at the cap, subject to the plants' bids, the storage's
power and capacity limits, and conservation of the energy in the store. The
solution gives the charge and discharge for every hour and the value of stored
energy, from which the bids follow:
 
* sell offer = value of stored energy ÷ discharge efficiency

* buy bid = value of stored energy × charge efficiency

**Clearing with storage (`Simulation.py`).** Each hour is then cleared in the
same way as without storage. Storage's charging adds to the demand generators must
meet, and its discharge reduces it. If storage's sell offer is higher than the
bid of the last generator needed, storage is the most expensive seller
accepted and sets the price.
 
## Assumptions
 
### Market
 
| # | Assumption | Reason |
|---|---|---|
| M1 | 1 MWh = 34.121 therms. | Brief. |
| M2 | Every plant submits one bid per hour at break-even, and nobody bids strategically. | Brief. |
| M3 | Gas plants are always fully available and can run at any level from zero to capacity, with no minimum output and no costs other than fuel. | Brief. |
| M4 | Demand is fixed and does not respond to price, in one national market with no network limits, losses, imports or exports. | Brief. |
| M5 | Each hour's MW figure is treated as MWh for that hour. | Hourly data. |
| M6 | **Price cap of £6,000/MWh.** When supply cannot meet demand, every plant runs flat out, the shortfall is recorded as unserved demand, and the price is equal to the cap. | £6,000/MWh is the administrative price GB's Balancing and Settlement Code puts on disconnections, which caps wholesale prices. |
| M7 | When wind and solar exceed demand the price is equal to their bid, £0, and the surplus is curtailed. Plants bidding the same price share the accepted volume in proportion to what they offered, so wind and solar are curtailed equally. | Brief. Prices cannot go negative as nobody bids below £0. |
| M8 | If demand lands exactly on the boundary between two bids, the lower bid sets the price. | Brief. |
 
### Storage
 
| # | Assumption | Reason |
|---|---|---|
| S1 | Storage asset of **7,500 MW**. | The UK's grid-scale battery power capacity in 2025 (UK government statistics), modelled as a single asset. |
| S2 | **1.6 hours at full power (12,000 MWh).** | The average duration of GB's battery fleet at the end of 2025 (Modo Energy), the government statistics give no energy capacity figure. |
| S3 | **92% charging and 92% discharging efficiency (85% average efficiency).** | GB's grid-scale batteries averaged 85% efficiency in 2025 (UK government statistics). The split between charging and discharging is assumed equal. |
| S4 | **No running cost** other than the electricity it buys and the losses on the way through. It starts empty and must finish at or above its starting level. | M3. |
| S5 | It knows demand, load factors and gas prices for the whole week when it plans. | The brief gives generators this knowledge ahead of time; it is extended to the full week here. This is the most optimistic assumption in the model. |
| S6 | It doesn't bid strategically, only at the break-even price | M2. |
| S7 | It plans against the price cap with unserved demand being priced at £6,000/MWh. | A shortage is worth as much as what the market pays and so its offer can't exceed the cap. |

## Numerical details
 
* `Auction.py` treats volumes below 0.000001 MWh as zero. The storage plan
  comes from a numerical solver, so demand can sit a fraction of a watt-hour
  past a plant's capacity and so without this tolerance, the next plant would wrongly
  set the price.

* `Storage.py` puts a cost of £0.0001/MWh on charging. Among plans that cost
  the same, this stops the solver charging and discharging in the same hour.
  Solver results below 0.000001 MWh are set to zero and bid prices are rounded
  up to six decimal places.

## Limitations
 
* **Perfect foresight (S5).** A real operator plans on forecasts a day or so
  ahead. Re-planning each day with forecast error would give storage a lower
  and more realistic value.
* **Shortage pricing (M6).** Results in the shortage hours depend entirely on
  the chosen cap. Price-responsive demand or imports would be a better
  treatment than a single administrative price.
* **Storage detail.** No battery degradation, self-discharge, or income from
  balancing and other grid services.
* **Plant detail.** Start-up costs, minimum output and ramp rates would make
  each hour depend on the last and turn the auction into a scheduling problem.

## Sources
 
* Elexon, [BSC modification P443](https://elexon.co.uk/mod-proposal/p443), and
  Ofgem, [P443 decision](https://www.ofgem.gov.uk/sites/default/files/2023-10/P443%20-%20Authority%20Decision%20to%20Reject%20Balancing%20and%20Settlement%20Code%20modification.pdf):
  the £6,000/MWh value in the Balancing and Settlement Code.
* NERA for the Energy Networks Association, *Value of Lost Load Study in Great
  Britain: Work Package 3 Report*, 17 October 2025: the status of the £6,000
  figure as an effective cap on wholesale prices.
* UK Department for Energy Security and Net Zero, [Grid-scale battery storage statistics](https://assets.publishing.service.gov.uk/media/6a3ea42433bc5beefd3c4bdb/Grid-scale_battery_storage_statistics.pdf):
  UK battery power capacity (7.5 GW), GB battery efficiency (85%) and UK
  electricity generation (294 TWh) in 2025.
* Modo Energy, [GB Battery Buildout Report, Q4 2025](https://modoenergy.com/research/en/gb-battery-energy-storage-capacity-buildout-q4-2025-projections-2026-clean-power):
  GB battery power and energy capacity at the end of 2025.