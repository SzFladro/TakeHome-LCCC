from pathlib import Path

from src.Data import load_data
from src.Plotting import (
    plot_generation_mix,
    plot_generation_mix_comparison,
    plot_prices,
    plot_prices_comparison,
)
from src.Reporting import compare_summaries, write_excel
from src.Simulation import simulate_market
from src.Storage import Storage

_PROJECT_FOLDER = Path(__file__).resolve().parent
_DATA_PATH = _PROJECT_FOLDER / "data.xlsx"
_OUTPUT_FOLDER = _PROJECT_FOLDER / "Output"


def main():
    _OUTPUT_FOLDER.mkdir(exist_ok=True)

    data = load_data(_DATA_PATH)
    no_storage_hourly, no_storage_dispatch = simulate_market(data)
    with_storage_hourly, with_storage_dispatch = simulate_market(data, storage=Storage())
    summary = compare_summaries(no_storage_hourly, with_storage_hourly)

    write_excel(_OUTPUT_FOLDER / "results.xlsx", summary,
                no_storage_hourly, with_storage_hourly, no_storage_dispatch, with_storage_dispatch)

    plot_generation_mix(no_storage_hourly, _OUTPUT_FOLDER / "no_storage_generation_mix.png", "no-storage")
    plot_prices(no_storage_hourly, _OUTPUT_FOLDER / "no_storage_prices.png", "no-storage")
    plot_generation_mix(with_storage_hourly, _OUTPUT_FOLDER / "with_storage_generation_mix.png", "with-storage")
    plot_prices(with_storage_hourly, _OUTPUT_FOLDER / "with_storage_prices.png", "with-storage")
    plot_generation_mix_comparison(no_storage_hourly, with_storage_hourly, _OUTPUT_FOLDER / "comparison_generation_mix.png")
    plot_prices_comparison(no_storage_hourly, with_storage_hourly, _OUTPUT_FOLDER / "comparison_prices.png")

    print("Results written to " + str(_OUTPUT_FOLDER))


if __name__ == "__main__":
    main()