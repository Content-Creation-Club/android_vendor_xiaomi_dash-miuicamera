#!/usr/bin/env python3

"""Build the unsigned dash port APK from the pinned stock release inputs."""

import hashlib
from pathlib import Path
import subprocess
import sys


REPOSITORY = Path(__file__).resolve().parents[1]
STOCK_APK = REPOSITORY / "inputs/MiuiCamera-stock.apk"
STOCK_SHA256 = "20125354d0794a1782442cb3e6c752dc963e4685a49f7e5223cd5c041b3af5b4"
PANORAMA = REPOSITORY / "inputs/panorama.apk"
PANORAMA_SHA256 = "d3b13f58f5ff8c79017ec420b146f151664935f0bcd7eef2dacce526bfbcf610"
WORK = REPOSITORY / ".work"
DECODED = WORK / "decoded"
STOCK_SYSTEM_EXT = WORK / "stock-system_ext"


def digest(path):
    result = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def require(path, expected):
    if not path.is_file():
        raise FileNotFoundError(f"Missing {path}; run tools/fetch-inputs.py first")
    actual = digest(path)
    if actual != expected:
        raise ValueError(f"SHA-256 mismatch for {path}: {actual}")


def main():
    require(STOCK_APK, STOCK_SHA256)
    require(PANORAMA, PANORAMA_SHA256)
    if not (STOCK_SYSTEM_EXT / "lib64").is_dir():
        raise FileNotFoundError("Missing stock camera libraries; run tools/fetch-inputs.py first")

    if not DECODED.is_dir():
        WORK.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["apktool", "d", str(STOCK_APK), "-o", str(DECODED)],
            check=True,
        )

    subprocess.run(
        [sys.executable, str(REPOSITORY / "tools/prepare.py"), str(DECODED), str(STOCK_SYSTEM_EXT)],
        check=True,
    )


if __name__ == "__main__":
    main()
