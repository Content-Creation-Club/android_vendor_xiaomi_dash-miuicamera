#!/usr/bin/env python3

"""Prepare dash OS3.0.305 camera prebuilts from the existing APK work tree."""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import zipfile

import slow_motion

ROOT = Path(__file__).resolve().parents[4]
REPOSITORY = ROOT / "vendor/xiaomi/dash-miuicamera"
DEST = REPOSITORY / "prebuilts"
INPUTS = REPOSITORY / "inputs"
PATCHELF = ROOT / "prebuilts/extract-tools/linux-x86/bin/patchelf-0_18"
UNUSED_GRAPHICS = "android.hardware.graphics.common-V6-ndk.so"
PANORAMA_SPLIT = INPUTS / "panorama.apk"
PANORAMA_MD5 = "3891f5ead83911e32d24b14c7ba7554b"
PANORAMA_FUSED_MODULE = (
    '        <meta-data android:name="shadow.bundletool.com.android.dynamic.apk.fused.modules" '
    'android:value="panorama"/>\n'
)
CAMERA_COUNTDOWN_PERMISSION = (
    '    <uses-permission android:name="me.sandai.dashled.permission.CAMERA_COUNTDOWN"/>\n'
)
LIBRARIES = (
    "libcamera_algoup_jni.xiaomi.so",
    "libcamera_mianode_jni.xiaomi.so",
    "libcamera_ispinterface_jni.xiaomi.so",
    "libmtkisp_metadata_sys.so",
    "vendor.mediatek.hardware.camera.isphal@1.0.so",
    "vendor.mediatek.hardware.camera.isphal-V1-ndk.so",
)

# OS3.0.305 stock resource table paths; apktool gives these resources full names.
# ResourceLoader opens assets/obfu_res/<resource table path>, not res/ directly.
ENCRYPTED_DRAWABLES = {
    "8NF.png": "clear_subject_capture_image_res.png",
    "4fk.xml": "ic_cv_logo.xml",
    "2Pc.xml": "ic_cvtype_item_master.xml",
    "RAu.xml": "ic_cvtype_item_master_top_menu.xml",
    "U7A.xml": "ic_cvtype_item_other.xml",
    "jd0.xml": "ic_cvtype_item_other_top_menu.xml",
    "9cp.webp": "ic_west_coast_princess.webp",
    "Gu2.webp": "ic_west_coast_queen.webp",
    "E-c.xml": "polaroid_print_btn.xml",
}


def restore_resource_paths(decoded):
    assets = decoded / "assets/obfu_res/res"
    (assets / "drawable").mkdir(exist_ok=True)
    for original, rebuilt in ENCRYPTED_DRAWABLES.items():
        assert (decoded / "res/drawable" / rebuilt).is_file(), rebuilt
        shutil.copyfile(assets / original, assets / "drawable" / rebuilt)


def embed_panorama(decoded):
    """Fuse the stock Panorama payload into the base APK instead of Qigsaw."""
    assert hashlib.md5(PANORAMA_SPLIT.read_bytes()).hexdigest() == PANORAMA_MD5
    with zipfile.ZipFile(PANORAMA_SPLIT) as split:
        for name in split.namelist():
            if name.startswith("lib/arm64-v8a/") or name in (
                "assets/beauty_ui9_intelligent_params.config",
                "assets/eyelineblush.cng",
            ):
                target = decoded / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(split.read(name))

    manifest = decoded / "AndroidManifest.xml"
    text = manifest.read_text()
    if PANORAMA_FUSED_MODULE not in text:
        marker = "        <meta-data android:name=\"miui.rear.policy\""
        assert text.count(marker) == 1
        text = text.replace(marker, PANORAMA_FUSED_MODULE + marker)
        manifest.write_text(text)

    split_info = decoded / "assets/qigsaw_5.0.0.0_2.0.json"
    info = json.loads(split_info.read_text())
    info["updateSplits"] = [name for name in info["updateSplits"] if name != "panorama"]
    split_info.write_text(json.dumps(info, ensure_ascii=False, indent=2) + "\n")


def add_camera_countdown_permission(decoded):
    manifest = decoded / "AndroidManifest.xml"
    text = manifest.read_text()
    if CAMERA_COUNTDOWN_PERMISSION not in text:
        marker = '    <original-package android:name="com.android.camera"/>\n'
        assert text.count(marker) == 1
        manifest.write_text(text.replace(marker, marker + CAMERA_COUNTDOWN_PERMISSION))

# Keep the existing class-presence probe, but do not force Xiaomi audio on MTK.
AUDIO_OLD = """    if-nez v0, :cond_0

    invoke-static {}, Ll6/a;->e()Z

    move-result v0

    if-eqz v0, :cond_1
"""
AUDIO_NEW = """    if-eqz v0, :cond_1
"""
LISTENER_OLD = """    new-instance v0, LYg/l$a;

    invoke-direct {v0}, Ljava/lang/Object;-><init>()V
"""
LISTENER_NEW = """    const/4 v0, 0x0
"""
# Static vendor capabilities are not capture-request keys, even outside MIUI.
VENDOR_KEYS_OLD = """    invoke-static {}, Lrk/U;->w()Z

    move-result p2

    if-eqz p2, :cond_1

    invoke-static {p1}, LIg/b;->c"""
VENDOR_KEYS_NEW = """    const/4 p2, 0x1

    if-eqz p2, :cond_1

    invoke-static {p1}, LIg/b;->c"""
# Xiaomi Camera implements this HDR mode as an HEVC session. Keep the stored
# controls aligned with the effective encoder instead of showing H.264 while
# the recorder silently selects HEVC.
VIDEO_ENCODER_HDR_OLD = """:cond_0
    instance-of v0, p1, Ljava/lang/String;
"""
VIDEO_ENCODER_HDR_NEW = """:cond_0
    const-string v0, "pref_video_encoder_key"

    invoke-virtual {v0, p2}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v0

    if-eqz v0, :cond_dash_video_encoder

    const-string v0, "h265"

    invoke-virtual {v0, p1}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v0

    if-nez v0, :cond_dash_video_encoder

    invoke-static {}, LO1/a;->a()LQ1/T0;

    move-result-object v0

    const-class v2, LR1/a;

    invoke-virtual {v0, v2}, Lqf/b;->v(Ljava/lang/Class;)Ljava/lang/Object;

    move-result-object v0

    check-cast v0, LR1/a;

    const/4 v3, 0x0

    invoke-virtual {v0, v3}, LR1/a;->t(Z)V

    invoke-static {}, Ls4/b;->Vd()LQ1/T0;

    move-result-object v0

    invoke-virtual {v0, v2}, Lqf/b;->v(Ljava/lang/Class;)Ljava/lang/Object;

    move-result-object v0

    check-cast v0, LR1/a;

    invoke-virtual {v0, v3}, LR1/a;->t(Z)V

    :cond_dash_video_encoder
    instance-of v0, p1, Ljava/lang/String;
"""
HDR_ENCODER_UI_OLD = """    if-eqz p1, :cond_10

    invoke-virtual {p0, v3}, Ls4/d;->bj(Ljava/lang/String;)V

    iget-object p0, p0, Ls4/b;->k0:Ls4/p;
"""
HDR_ENCODER_UI_NEW = """    if-eqz p1, :cond_10

    invoke-virtual {p0, v3}, Ls4/d;->bj(Ljava/lang/String;)V

    const-string p1, "h265"

    const-string v4, "pref_video_encoder_key"

    invoke-virtual {p0, p1, v4}, Ls4/b;->qh(Ljava/lang/Object;Ljava/lang/String;)V

    iget-object p1, p0, Ls4/b;->j0:Landroidx/preference/PreferenceScreen;

    invoke-virtual {p1, v4}, Landroidx/preference/PreferenceGroup;->c0(Ljava/lang/CharSequence;)Landroidx/preference/Preference;

    move-result-object p1

    instance-of v4, p1, Lcom/android/camera/ui/ValuePreference;

    if-eqz v4, :cond_dash_hdr_encoder_ui

    check-cast p1, Lcom/android/camera/ui/ValuePreference;

    invoke-virtual {p0, p1}, Ls4/m;->aj(Lcom/android/camera/ui/ValuePreference;)V

    :cond_dash_hdr_encoder_ui
    iget-object p0, p0, Ls4/b;->k0:Ls4/p;
"""
# Route Xiaomi Camera's stock color-strip countdown callback to DashLED. The
# explicit receiver is protected by a signature permission in DashLedService.
COLOR_LIGHT_BRIDGE_OLD = """.method public static a(Landroid/content/Context;I)V
    .locals 9

    invoke-virtual {p0}, Landroid/content/Context;->getContentResolver()Landroid/content/ContentResolver;
"""
COLOR_LIGHT_BRIDGE_NEW = """.method public static a(Landroid/content/Context;I)V
    .locals 9

    const-string v0, "me.sandai.dashled.permission.CAMERA_COUNTDOWN"

    invoke-virtual {p0, v0}, Landroid/content/Context;->checkSelfPermission(Ljava/lang/String;)I

    move-result v0

    if-eqz v0, :dash_led_available

    return-void

    :dash_led_available
    new-instance v0, Landroid/content/Intent;

    const-string v1, "me.sandai.dashled.action.CAMERA_COUNTDOWN_TICK"

    invoke-direct {v0, v1}, Landroid/content/Intent;-><init>(Ljava/lang/String;)V

    const-string v1, "me.sandai.dashled"

    const-string v2, "me.sandai.dashled.CameraCountdownReceiver"

    invoke-virtual {v0, v1, v2}, Landroid/content/Intent;->setClassName(Ljava/lang/String;Ljava/lang/String;)Landroid/content/Intent;

    const-string v1, "duration_ms"

    const/16 v2, 0x12c

    invoke-virtual {v0, v1, v2}, Landroid/content/Intent;->putExtra(Ljava/lang/String;I)Landroid/content/Intent;

    invoke-virtual {p0, v0}, Landroid/content/Context;->sendBroadcast(Landroid/content/Intent;)V

    return-void

    invoke-virtual {p0}, Landroid/content/Context;->getContentResolver()Landroid/content/ContentResolver;
"""
def patch(path, old, new, count):
    text = path.read_text()
    if old in text:
        if text.count(old) != count:
            raise ValueError(f"Unexpected APK revision: {path}")
        path.write_text(text.replace(old, new))
    else:
        assert text.count(new) >= count, f"Patch does not match: {path}"


# Keep internal reset state at zero; clear only the display override.
BRIGHTNESS_RESETS = (
    ("smali/o1/g0.smali", "v1, v0", "v0"),
    ("smali/E5/v.smali", "v3, p0", "p0"),
    ("smali/o1/m0.smali", "v3, v4", "v4"),
)


def brightness_reset_code(registers, value):
    call = f"    invoke-static {{{registers}}}, LKg/a;->a(Landroid/hardware/display/DisplayManager;F)V"
    return call, f"    const/high16 {value}, 0x7fc00000    # Float.NaN\n\n" + call


def patch_brightness_reset(decoded):
    for name, registers, value in BRIGHTNESS_RESETS:
        old, new = brightness_reset_code(registers, value)
        if new not in (decoded / name).read_text():
            patch(decoded / name, old, new, 1)


def check(decoded):
    slow_motion.check(decoded)
    for name, registers, value in BRIGHTNESS_RESETS:
        assert (decoded / name).read_text().count(brightness_reset_code(registers, value)[1]) == 1
    for name in ("smali/o1/g0.smali", "smali/E5/v.smali"):
        assert "0x3f000000    # 0.5f" in (decoded / name).read_text()
    assets = decoded / "assets/obfu_res/res"
    for original, rebuilt in ENCRYPTED_DRAWABLES.items():
        assert (assets / original).read_bytes() == (assets / "drawable" / rebuilt).read_bytes()
    audio = (decoded / "smali/r1/a.smali").read_text()
    listener = (decoded / "smali_classes4/Yg/l.smali").read_text()
    resources = (decoded / "smali_classes2/Ce/b.smali").read_text()
    capabilities = (decoded / "smali/b8/c.smali").read_text()
    preferences = (decoded / "smali/s4/b.smali").read_text()
    video_preferences = (decoded / "smali/s4/d.smali").read_text()
    color_light = (decoded / "smali_classes4/Lg/a.smali").read_text()
    assert VENDOR_KEYS_OLD not in capabilities
    assert capabilities.count(VENDOR_KEYS_NEW) == 1
    assert VIDEO_ENCODER_HDR_OLD not in preferences
    assert preferences.count(VIDEO_ENCODER_HDR_NEW) == 1
    assert HDR_ENCODER_UI_OLD not in video_preferences
    assert video_preferences.count(HDR_ENCODER_UI_NEW) == 1
    assert COLOR_LIGHT_BRIDGE_OLD not in color_light
    assert color_light.count(COLOR_LIGHT_BRIDGE_NEW) == 1
    assert AUDIO_OLD not in audio
    assert audio.count("invoke-static {}, Lr1/a;->h()Z") == 2
    assert audio.count(AUDIO_NEW) == 2
    assert LISTENER_OLD not in listener
    assert "const/4 v0, 0x0\n\n    iput-object v0, p0, LYg/l;->p:" in listener
    assert "invoke-static {v1, v0, v2}, LNd/e;->d(" in resources
    native = (DEST / "lib64/libcamera_algoup_jni.xiaomi.so").read_bytes()
    assert native[0x420c:0x4210] == bytes.fromhex("08 a9 40 f9")
    for name in LIBRARIES:
        assert (DEST / "lib64" / name).is_file()
    assert hashlib.md5(PANORAMA_SPLIT.read_bytes()).hexdigest() == PANORAMA_MD5
    manifest = (decoded / "AndroidManifest.xml").read_text()
    assert manifest.count(PANORAMA_FUSED_MODULE) == 1
    assert manifest.count(CAMERA_COUNTDOWN_PERMISSION) == 1
    info = json.loads((decoded / "assets/qigsaw_5.0.0.0_2.0.json").read_text())
    assert "panorama" not in info["updateSplits"]
    with zipfile.ZipFile(PANORAMA_SPLIT) as split:
        for name in split.namelist():
            if name.startswith("lib/arm64-v8a/") or name in (
                "assets/beauty_ui9_intelligent_params.config",
                "assets/eyelineblush.cng",
            ):
                assert (decoded / name).read_bytes() == split.read(name)
    isp = DEST / "lib64/vendor.mediatek.hardware.camera.isphal-V1-ndk.so"
    needed = subprocess.check_output([str(PATCHELF), "--print-needed", str(isp)], text=True)
    assert UNUSED_GRAPHICS not in needed
    print("Camera patch checks passed (6.3.005550.0).")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("decoded", type=Path)
    parser.add_argument("stock_system_ext", type=Path, nargs="?")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--restore-resource-paths", action="store_true")
    parser.add_argument("--patch-brightness-reset", action="store_true")
    args = parser.parse_args()
    if args.patch_brightness_reset:
        patch_brightness_reset(args.decoded)
        check(args.decoded)
        return
    if args.restore_resource_paths:
        restore_resource_paths(args.decoded)
        check(args.decoded)
        return
    if args.check:
        check(args.decoded)
        return
    patch(args.decoded / "smali/r1/a.smali", AUDIO_OLD, AUDIO_NEW, 2)
    patch(args.decoded / "smali_classes4/Yg/l.smali", LISTENER_OLD, LISTENER_NEW, 1)
    patch(args.decoded / "smali/b8/c.smali", VENDOR_KEYS_OLD, VENDOR_KEYS_NEW, 1)
    patch(args.decoded / "smali/s4/b.smali", VIDEO_ENCODER_HDR_OLD, VIDEO_ENCODER_HDR_NEW, 1)
    patch(args.decoded / "smali/s4/d.smali", HDR_ENCODER_UI_OLD, HDR_ENCODER_UI_NEW, 1)
    patch(args.decoded / "smali_classes4/Lg/a.smali", COLOR_LIGHT_BRIDGE_OLD, COLOR_LIGHT_BRIDGE_NEW, 1)
    add_camera_countdown_permission(args.decoded)
    restore_resource_paths(args.decoded)
    patch_brightness_reset(args.decoded)
    slow_motion.apply(args.decoded)
    embed_panorama(args.decoded)
    if args.stock_system_ext is not None:
        (DEST / "lib64").mkdir(parents=True, exist_ok=True)
        for name in LIBRARIES:
            source = args.stock_system_ext / "lib64" / name
            target = DEST / "lib64" / name
            if name == "libcamera_algoup_jni.xiaomi.so":
                data = source.read_bytes()
                # Local libgui vtable: +0x150 is connect, +0x158 is detachNextBuffer.
                assert data[0x420c:0x4210] == bytes.fromhex("08 ad 40 f9")
                target.write_bytes(
                    data[:0x420c] + bytes.fromhex("08 a9 40 f9") + data[0x4210:]
                )
            else:
                shutil.copyfile(source, target)
            if name == "vendor.mediatek.hardware.camera.isphal-V1-ndk.so":
                symbols = subprocess.check_output(
                    ["readelf", "--dyn-syms", "--wide", str(target)], text=True
                )
                assert not any(
                    " UND " in line and "8graphics" in line
                    for line in symbols.splitlines()
                )
                # This blob only uses graphics enums; there are no graphics symbol imports.
                subprocess.run(
                    [str(PATCHELF), "--remove-needed", UNUSED_GRAPHICS, str(target)],
                    check=True,
                )
    check(args.decoded)
    subprocess.run(["apktool", "b", str(args.decoded), "-o", str(DEST / "MiuiCamera.apk")], check=True)


if __name__ == "__main__":
    main()
