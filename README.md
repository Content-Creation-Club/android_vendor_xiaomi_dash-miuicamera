# Xiaomi Camera for Redmi Turbo 5 Max (dash)

EN | [中文](README_zh.md)

Aperture, hate it.

## Version

- Extracted from: `OS3.0.305.0.WPLCNXM`
- Vendor: Modifications, no necessary.
- Inputs: 
  * MiuiCamera `6.3.005550.0` (`630055500`)
  * panorama `8.4.1@17`

## Build

Map this repository to `vendor/xiaomi/dash-miuicamera`:

```xml
<project
    path="vendor/xiaomi/dash-miuicamera"
    name="Content-Creation-Club/android_vendor_xiaomi_dash-miuicamera"
    remote="gh"
    revision="main" />
```

```sh
python3 vendor/xiaomi/dash-miuicamera/tools/fetch-inputs.py
python3 vendor/xiaomi/dash-miuicamera/tools/build.py
```

The Release provides two unmodified stock APKs and a ZIP of six unmodified
camera libraries from OS3.0.305.0.WPLCNXM `system_ext/lib64`. The scripts
verify and unpack them, then patch the libraries into `prebuilts/lib64`.

The device product may include the integration conditionally:

```make
$(call inherit-product-if-exists, vendor/xiaomi/dash-miuicamera/miuicamera.mk)
```

After manually patching, you should sign it yourself.

Platform signature is used automatically when built as part of your ROM.

## Credits

[xiaomi-dash-dev](https://github.com/xiaomi-dash-dev/android_device_xiaomi_dash-miuicamera)

[xiaomi-onyx-dev](https://github.com/xiaomi-onyx-dev/android_device_xiaomi_onyx-miuicamera)

This port builds on the `onyx` camera integration and `dash` port, adapting selected configuration and blob fixes. 

Python build and patch tooling was written for the OS3.0.305 camera revision. 

## Working

- [x] MTK ISP dependency closure
- [x] Obfuscated resource restoration
- [x] HDR encoder state correction
- [x] 50MP
- [x] Panorama fusion
- [x] 120/240/960 FPS slow-motion
- [x] 120/240 FPS slow-motion Gallery editing (Google Photos tested)
- [x] Brightness fix (affecting my device tree builds)
- [x] [DashLED](https://github.com/YorokobiMaster/android_device_xiaomi_dash/tree/lineage-23.2/dashled) countdown bridge support

## License

The WTFPL applies only to original scripts and code authored specifically for this repository.

It does not apply to Xiaomi proprietary applications, libraries, firmware, resources, or other third-party material. Such components remain subject to their respective copyright and licensing terms.

## Disclaimer

This is an unofficial community project and is not affiliated with, endorsed by, or supported by Xiaomi or LineageOS.

Don't be a dick. Fuck around and find out.
