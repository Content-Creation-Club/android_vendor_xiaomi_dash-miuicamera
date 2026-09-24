DASH_MIUI_CAMERA_PATH := vendor/xiaomi/dash-miuicamera

PRODUCT_SOONG_NAMESPACES += \
    $(DASH_MIUI_CAMERA_PATH)

# Aperture remains installed; this optional package adds Xiaomi Camera beside it.
PRODUCT_PACKAGES += \
    DashMiuiCamera \
    dash-miuicamera-init \
    libcamera_algoup_jni.xiaomi \
    libcamera_mianode_jni.xiaomi \
    libcamera_ispinterface_jni.xiaomi \
    libmtkisp_metadata_sys \
    dash-camera-isphal-hidl \
    dash-camera-isphal-aidl

PRODUCT_COPY_FILES += \
    $(DASH_MIUI_CAMERA_PATH)/configs/privapp-permissions-miuicamera.xml:$(TARGET_COPY_OUT_SYSTEM_EXT)/etc/permissions/privapp-permissions-miuicamera.xml \
    $(DASH_MIUI_CAMERA_PATH)/configs/public.libraries-xiaomi.txt:$(TARGET_COPY_OUT_SYSTEM_EXT)/etc/public.libraries-xiaomi.txt
