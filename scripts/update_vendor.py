"""
Met à jour le fichier vendor JS.

Usage :
    uv run python scripts/update_vendor.py
    uv run python scripts/update_vendor.py --version 5.3.0
"""
import argparse
import urllib.request
from pathlib import Path

DEFAULT_VERSION = "5.2.0"
VENDOR_PATH = (
    Path(__file__).parent.parent
    / "src"
    / "lwcharts"
    / "vendor"
    / "lightweight-charts.standalone.production.js"
)


def download(version: str) -> None:
    url = (
        f"https://unpkg.com/lightweight-charts@{version}"
        f"/dist/lightweight-charts.standalone.production.js"
    )
    print(f"Downloading lightweight-charts {version} from {url} ...")
    VENDOR_PATH.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(url, VENDOR_PATH)
    size_kb = VENDOR_PATH.stat().st_size / 1024
    print(f"Saved → {VENDOR_PATH}  ({size_kb:.0f} KB)")
    print("Done. Update the _CDN_URL version string in renderer.py if needed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default=DEFAULT_VERSION)
    args = parser.parse_args()
    download(args.version)
