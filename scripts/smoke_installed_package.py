from __future__ import annotations

import importlib.resources
import shutil
import subprocess
import sys
from pathlib import Path

import nyc311
from nyc311 import geographies, samples


def main() -> None:
    typing_marker = importlib.resources.files("nyc311").joinpath("py.typed")
    if not typing_marker.is_file():
        raise SystemExit("Installed package is missing `nyc311/py.typed`.")

    cli_path = Path(sys.executable).with_name("nyc311")
    if not cli_path.exists():
        fallback_cli = shutil.which("nyc311")
        cli_path = Path(fallback_cli) if fallback_cli is not None else cli_path
    if not cli_path.exists():
        raise SystemExit("Installed package is missing the `nyc311` console script.")

    subprocess.run([str(cli_path), "--help"], check=True)

    borough_boundaries = geographies.load_nyc_boundaries("borough", values="Queens")
    if [feature.geography_value for feature in borough_boundaries.features] != [
        "QUEENS"
    ]:
        raise SystemExit(
            "Installed package could not load packaged borough boundaries."
        )

    records = samples.load_sample_service_requests()
    if not records:
        raise SystemExit("Installed package could not load packaged sample records.")

    version = nyc311.__version__
    if not isinstance(version, str) or not version:
        raise SystemExit("Installed package did not expose a valid version string.")


if __name__ == "__main__":
    main()
