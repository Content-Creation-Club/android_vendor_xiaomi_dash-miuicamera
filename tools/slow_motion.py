"""OS3.0.305: record 120/240 slow motion using Android's timed MP4 writer.

The stock MediaCodec recorder sets capture-rate but does not implement the
corresponding video AND audio timeline conversion. Use the existing platform
MediaRecorder adapter for these two modes. StagefrightRecorder then writes
com.android.capture.fps as float32 and stretches both media timelines.

960 retains Xiaomi's stock interpolator and dual-track output unchanged.
"""

CONTROLLER = "smali/com/android/camera/module/video/x.smali"
OWNER = "Lcom/android/camera/module/video/x;"
SETTINGS = "Lcom/android/camera/module/video/B;"
FIELD_OLD = ".field public a:LYg/q;"
FIELD_NEW = FIELD_OLD + "\n\n.field private dashStandardSlowMotion:Z"

SELECT_OLD = """    iget-object v3, p0, Lcom/android/camera/module/video/x;->a:LYg/q;

    const/4 v4, 0x0

    if-nez v3, :cond_5

    invoke-static {}, Lcom/android/camera/module/S;->e()Z
"""
SELECT_NEW = """    iget-object v3, p0, Lcom/android/camera/module/video/x;->a:LYg/q;

    const/4 v4, 0x0

    iget-object v5, p0, Lcom/android/camera/module/video/x;->e:Lcom/android/camera/module/video/B;

    invoke-static {v5}, Lcom/android/camera/module/video/x;->dashCaptureFps(Lcom/android/camera/module/video/B;)I

    move-result v5

    if-eqz v5, :dash_stock_recorder

    const/4 v5, 0x1

    :dash_stock_recorder
    iget-boolean v6, p0, Lcom/android/camera/module/video/x;->dashStandardSlowMotion:Z

    if-eq v5, v6, :dash_recorder_selected

    # A mode switch may reuse this controller. Release the old backend before
    # choosing another one, including when returning from 120/240 to 960.
    if-eqz v3, :dash_recorder_selected

    invoke-interface {v3}, LYg/q;->release()V

    const/4 v3, 0x0

    iput-object v3, p0, Lcom/android/camera/module/video/x;->a:LYg/q;

    :dash_recorder_selected
    iput-boolean v5, p0, Lcom/android/camera/module/video/x;->dashStandardSlowMotion:Z

    if-nez v3, :cond_5

    if-eqz v5, :dash_original_recorder_selection

    goto/16 :cond_4

    :dash_original_recorder_selection
    invoke-static {}, Lcom/android/camera/module/S;->e()Z
"""

HELPERS = """
# Standard slow motion is limited to the selected 120/240 modes. In particular,
# the interpolated 960 mode also captures 240 fps, so checking B.f is WRONG.
.method private static dashCaptureFps(Lcom/android/camera/module/video/B;)I
    .locals 2

    const/4 v0, 0x0

    if-eqz p0, :dash_fps_done

    iget-object p0, p0, Lcom/android/camera/module/video/B;->h:Ljava/lang/String;

    const-string v1, "slow_motion_120"

    invoke-virtual {v1, p0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v1

    if-eqz v1, :dash_check_240

    const/16 v0, 0x78

    return v0

    :dash_check_240
    const-string v1, "slow_motion_240"

    invoke-virtual {v1, p0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v1

    if-eqz v1, :dash_fps_done

    const/16 v0, 0xf0

    :dash_fps_done
    return v0
.end method

.method private static dashConfigureSlowMotion(Lcom/android/camera/module/video/B;LYg/r;)V
    .locals 4

    invoke-static {p0}, Lcom/android/camera/module/video/x;->dashCaptureFps(Lcom/android/camera/module/video/B;)I

    move-result v0

    if-eqz v0, :dash_config_done

    const/16 v1, 0x1e

    iput v1, p1, LYg/r;->j:I

    int-to-double v2, v0

    iput-wide v2, p1, LYg/r;->m:D

    div-int/2addr v0, v1

    # Bitrate is per playback second. Keep the stock bits per captured frame.
    iget v1, p1, LYg/r;->h:I

    div-int/2addr v1, v0

    iput v1, p1, LYg/r;->h:I

    # Stagefright captures audio at outputSampleRate * slowdown. Its hard
    # source limit is 192 kHz: at 240/30 the AAC output must be <=24 kHz.
    # Preserve audio, with the SAME slowdown as video, rather than just
    # stretching AAC timestamps while leaving its sample duration unchanged.
    iget-boolean v1, p1, LYg/r;->a:Z

    if-eqz v1, :dash_config_done

    const v1, 0x2ee00

    div-int/2addr v1, v0

    iget v2, p1, LYg/r;->e:I

    invoke-static {v1, v2}, Ljava/lang/Math;->min(II)I

    move-result v1

    iput v1, p1, LYg/r;->e:I

    :dash_config_done
    return-void
.end method
"""


def replacements():
    yield FIELD_OLD, FIELD_NEW
    yield SELECT_OLD, SELECT_NEW
    # Both normal start and motion-detection restart produce fresh parameters.
    # p0 is a high register in these methods: use move-object/from16 first.
    for result in ("v8", "v5"):
        old = f"    return-object {result}\n.end method"
        new = f"""    move-object/from16 v0, p0

    iget-object v1, v0, {OWNER}->e:{SETTINGS}

    invoke-static {{v1, {result}}}, {OWNER}->dashConfigureSlowMotion({SETTINGS}LYg/r;)V

{old}"""
        yield old, new


def transform(text):
    for old, new in replacements():
        if new in text:
            assert text.count(new) == 1
            continue
        assert text.count(old) == 1, f"Slow-motion patch target mismatch: {old}"
        text = text.replace(old, new)
    if HELPERS not in text:
        assert "dashCaptureFps(Lcom/android/camera/module/video/B;)I\n    .locals" not in text
        text += HELPERS
    check_text(text)
    return text


def check_text(text):
    for _, new in replacements():
        assert text.count(new) == 1, "Missing/duplicated slow-motion patch"
    assert text.count(HELPERS) == 1


def apply(decoded):
    path = decoded / CONTROLLER
    text = path.read_text()
    updated = transform(text)
    if updated != text:
        path.write_text(updated)


def check(decoded):
    check_text((decoded / CONTROLLER).read_text())
    assert "dashCaptureMetadata" not in (decoded / CONTROLLER).read_text()
    for name in (
        "com/miui/extravideo/interpolation/VideoInterpolatorAsyncImp",
        "com/miui/extravideoxmalgo/XiaomiAlgoVideoInterpolatorImp/XiaomiAlgoVideoInterpolatorImp",
    ):
        text = (decoded / f"smali_classes2/{name}.smali").read_text()
        assert "dash_keep_capture_metadata" not in text
        assert "com.android.capture.fps" not in text
