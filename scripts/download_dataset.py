#!/usr/bin/env python3
"""Download and safely extract the public Kaggle dataset without credentials."""

from __future__ import annotations

import argparse
import shutil
import urllib.request
import zipfile
from pathlib import Path


URL = "https://www.kaggle.com/api/v1/datasets/download/pacificrm/car-insurance-fraud-detection"


def safe_extract(archive: zipfile.ZipFile, destination: Path) -> None:
    root = destination.resolve()
    for member in archive.infolist():
        target = (destination / member.filename).resolve()
        if root not in target.parents and target != root:
            raise RuntimeError(f"Unsafe archive path: {member.filename}")
    archive.extractall(destination)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("data"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    archive_path = args.output / "car-insurance-fraud-detection.zip"
    print("Downloading approximately 827 MB…")
    with urllib.request.urlopen(URL) as response, archive_path.open("wb") as output:
        shutil.copyfileobj(response, output)
    print("Extracting dataset…")
    with zipfile.ZipFile(archive_path) as archive:
        safe_extract(archive, args.output)
    print(f"Ready in {args.output.resolve()}")


if __name__ == "__main__":
    main()

