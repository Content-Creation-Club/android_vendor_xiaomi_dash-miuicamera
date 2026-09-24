#!/usr/bin/env python3

"""Fetch and unpack the pinned stock inputs for the dash camera port."""

import hashlib
from pathlib import Path
import urllib.request
import zipfile


REPOSITORY = "Content-Creation-Club/android_vendor_xiaomi_dash-miuicamera"
TAG = "OS3.0.305.0.WPLCNXM"
ASSETS = {
    "MiuiCamera-6.3.005550.0-OS3.0.305.0.WPLCNXM-stock.apk": (
        "MiuiCamera-stock.apk",
        "20125354d0794a1782442cb3e6c752dc963e4685a49f7e5223cd5c041b3af5b4",
    ),
    "Panorama-8.4.1_17-stock.apk": (
        "panorama.apk",
        "d3b13f58f5ff8c79017ec420b146f151664935f0bcd7eef2dacce526bfbcf610",
    ),
    "Camera-libs-OS3.0.305.0.WPLCNXM-stock.zip": (
        "Camera-libs-OS3.0.305.0.WPLCNXM-stock.zip",
        "884e8eb91ecbe1380ac79ad2adb26c2f673a546623c33de202686707bc454b15",
    ),
}

DEST = Path(__file__).resolve().parents[1] / "inputs"
STOCK_SYSTEM_EXT = DEST.parent / ".work/stock-system_ext"
STOCK_LIBRARIES = (
    "libcamera_algoup_jni.xiaomi.so",
    "libcamera_mianode_jni.xiaomi.so",
    "libcamera_ispinterface_jni.xiaomi.so",
    "libmtkisp_metadata_sys.so",
    "vendor.mediatek.hardware.camera.isphal@1.0.so",
    "vendor.mediatek.hardware.camera.isphal-V1-ndk.so",
)


def digest(path):
    result = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def fetch(asset, local_name, expected):
    target = DEST / local_name
    if target.is_file() and digest(target) == expected:
        print(f"Using verified {target}")
        return

    url = f"https://github.com/{REPOSITORY}/releases/download/{TAG}/{asset}"
    partial = target.with_suffix(target.suffix + ".part")
    partial.unlink(missing_ok=True)
    print(f"Downloading {url}")
    urllib.request.urlretrieve(url, partial)
    actual = digest(partial)
    if actual != expected:
        partial.unlink(missing_ok=True)
        raise ValueError(f"SHA-256 mismatch for {asset}: {actual}")
    partial.replace(target)
    print(f"Installed verified {target}")


def unpack_stock_libraries():
    archive = DEST / "Camera-libs-OS3.0.305.0.WPLCNXM-stock.zip"
    with zipfile.ZipFile(archive) as source:
        expected = {f"lib64/{name}" for name in STOCK_LIBRARIES}
        if set(source.namelist()) != expected:
            raise ValueError(f"Unexpected contents in {archive}")
        target_dir = STOCK_SYSTEM_EXT / "lib64"
        target_dir.mkdir(parents=True, exist_ok=True)
        for name in STOCK_LIBRARIES:
            (target_dir / name).write_bytes(source.read(f"lib64/{name}"))
    print(f"Unpacked verified stock libraries to {STOCK_SYSTEM_EXT}")


def main():
    DEST.mkdir(parents=True, exist_ok=True)
    for asset, (local_name, expected) in ASSETS.items():
        fetch(asset, local_name, expected)
    unpack_stock_libraries()


if __name__ == "__main__":
    main()
