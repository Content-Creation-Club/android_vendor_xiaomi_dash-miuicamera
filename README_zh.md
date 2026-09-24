# Redmi Turbo 5 Max (dash) 移植相机

[EN](README.md) | 中文

Aperture 是什么？真不熟。

## 版本

- 提取自: `OS3.0.305.0.WPLCNXM`
- Vendor: 不动
- 输入: 
  * MiuiCamera `6.3.005550.0` (`630055500`)
  * panorama `8.4.1@17`

## 构建

将本仓库映射至 `vendor/xiaomi/dash-miuicamera`:

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

Release 中提供两个原版 APK，以及从 OS3.0.305.0.WPLCNXM 的
`system_ext/lib64` 提取的六个未修改相机库 ZIP。脚本校验并解包后，
将库文件修补到 `prebuilts/lib64`。

设备树中可按需引入:

```make
$(call inherit-product-if-exists, vendor/xiaomi/dash-miuicamera/miuicamera.mk)
```

手动 patch 后请自行签名。

作为 ROM 的一部分构建时，会自动使用 platform 签名。

## 致谢

[xiaomi-dash-dev - android_device_xiaomi_dash-miuicamera](https://github.com/xiaomi-dash-dev/android_device_xiaomi_dash-miuicamera)

[xiaomi-onyx-dev - android_device_xiaomi_onyx-miuicamera](https://github.com/xiaomi-onyx-dev/android_device_xiaomi_onyx-miuicamera)

本项目参考了 onyx 相机集成及后续 dash 移植中的实现和历史，针对 305 相机版本使用的 Python 构建及 patch 工具由本仓库重新实现。

## 啥能用

- [x] MTK ISP 依赖补全
- [x] 恢复混淆资源
- [x] 修复 HDR 编码器状态
- [x] 50MP
- [x] 内置全景照片组件
- [x] 120/240/960 FPS 慢动作
- [x] 120/240 FPS 图库编辑（Google Photos 测试通过）
- [x] 亮度修复（给我的设备树用的）
- [x] [DashLED](https://github.com/YorokobiMaster/android_device_xiaomi_dash/tree/lineage-23.2/dashled) 倒计时桥接支持

## 许可证

WTFPL 仅适用于本仓库原创的脚本及代码。

小米专有应用、库、固件、资源及其他第三方内容不在此许可证覆盖范围内，仍受各自的版权及许可条款约束。

## 免责声明

这是个与小米或 LineageOS 没有任何关联，也未获得其认可或支持的非官方项目。

别当傻逼，自己折腾，后果自负。
