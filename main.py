from pathlib import Path

from src.Data import load_data
from src.Plotting import plot_generation_mix, plot_prices
from src.Reporting import summarise, write_excel
from src.Simulation import simulate_market


_PROJECT_FOLDER = Path(__file__).resolve().parent
_DATA_PATH = _PROJECT_FOLDER / "data.xlsx"
_OUTPUT_FOLDER = _PROJECT_FOLDER / "Output"

def main():
    _OUTPUT_FOLDER.mkdir(exist_ok=True)

    data = load_data(_DATA_PATH)
    hourly, unit_dispatch = simulate_market(data)
    summary = summarise(hourly)

    write_excel(_OUTPUT_FOLDER / "results.xlsx", hourly, unit_dispatch, summary)
    plot_generation_mix(hourly, _OUTPUT_FOLDER / "generation_mix.png")
    plot_prices(hourly, _OUTPUT_FOLDER / "prices.png")
    print("\nResults written to " + str(_OUTPUT_FOLDER))


if __name__ == "__main__":
    main()
