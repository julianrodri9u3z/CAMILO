#!/usr/bin/env python3
"""
Cross-platform backend for vision_analyze.py (Windows / Linux / macOS fallback): per-frame PERSON MATTES + FACE/HAND
ZONES with Google MediaPipe. Same output as the Apple Vision backend:
   OUT/matte/m_000001.png (RGBA, alpha = person)   and   OUT/zones.json

Do not call directly: vision_analyze.py picks this backend when it is the right one and runs it with the managed
virtual environment (see vision_setup.py). Needs: mediapipe, numpy, pillow, and the 3 model files in ../models/.

Quality note (measured against Apple Vision on the same frames): MediaPipe's selfie model works at 256x256, so edges
are softer and hair/hand details coarser. Fine for text behind a head and for caption-dodging; slightly less crisp.
"""
import argparse, json, os, subprocess, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
MODELS = os.path.join(os.path.dirname(HERE), "models")


def probe(video):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height,avg_frame_rate,r_frame_rate:stream_tags=rotate:side_data=rotation",
                        "-of", "json", video], capture_output=True, text=True, stdin=subprocess.DEVNULL)
    s = json.loads(r.stdout)["streams"][0]
    n, d = (s.get("avg_frame_rate") or s["r_frame_rate"]).split("/")
    return int(s["width"]), int(s["height"]), float(n) / float(d)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("out")
    ap.add_argument("--matte-width", type=int, default=540)
    ap.add_argument("--start", type=float, default=0)
    ap.add_argument("--dur", type=float, default=0)
    ap.add_argument("--zone-step", type=int, default=3)
    ap.add_argument("--no-matte", action="store_true")
    ap.add_argument("--no-zones", action="store_true")
    ap.add_argument("--no-png", action="store_true", help="compute zones/person boxes only, do not write matte PNGs")
    a = ap.parse_args()

    import mediapipe as mp
    from mediapipe.tasks import python as mpp
    from mediapipe.tasks.python import vision

    w, h, fps = probe(a.video)
    out_w = a.matte_width
    out_h = int(round(out_w * h / w))
    os.makedirs(os.path.join(a.out, "matte"), exist_ok=True)
    # decode at a working resolution (width 512) -- the models resize internally anyway, and it keeps this fast
    work_w = 512
    work_h = int(round(work_w * h / w / 2) * 2)
    cmd = ["ffmpeg", "-v", "error"] + (["-ss", str(a.start)] if a.start else []) + (["-t", str(a.dur)] if a.dur else []) + \
          ["-i", a.video, "-vf", f"scale={work_w}:{work_h}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stdin=subprocess.DEVNULL)

    def base(name):
        return mpp.BaseOptions(model_asset_path=os.path.join(MODELS, name))

    seg = vision.ImageSegmenter.create_from_options(vision.ImageSegmenterOptions(
        base_options=base("selfie_segmenter.tflite"), running_mode=vision.RunningMode.VIDEO, output_confidence_masks=True, output_category_mask=False))
    face = vision.FaceDetector.create_from_options(vision.FaceDetectorOptions(
        base_options=base("face_detector.tflite"), running_mode=vision.RunningMode.VIDEO, min_detection_confidence=0.5))
    hand = vision.HandLandmarker.create_from_options(vision.HandLandmarkerOptions(
        base_options=base("hand_landmarker.task"), running_mode=vision.RunningMode.VIDEO, num_hands=2, min_hand_detection_confidence=0.4))

    frames, idx, frame_bytes = [], 0, work_w * work_h * 3
    while True:
        buf = proc.stdout.read(frame_bytes)
        if len(buf) < frame_bytes:
            break
        idx += 1
        rgb = np.frombuffer(buf, np.uint8).reshape(work_h, work_w, 3)
        ts = int(round((idx - 1) * 1000 / fps))
        img = mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(rgb))
        person = None
        if not a.no_matte:
            res = seg.segment_for_video(img, ts)
            conf = np.squeeze(res.confidence_masks[0].numpy_view()).astype(np.float32)   # HxW confidence of PERSON
            # sharpen the soft edge (smoothstep) before upscaling
            x = np.clip((conf - 0.35) / 0.30, 0, 1)
            x = x * x * (3 - 2 * x)
            if not a.no_png:
                m = Image.fromarray((x * 255).astype(np.uint8)).resize((out_w, out_h), Image.BICUBIC)
                arr = np.zeros((out_h, out_w, 4), np.uint8)
                arr[..., 3] = np.array(m)
                Image.fromarray(arr, "RGBA").save(os.path.join(a.out, "matte", f"m_{idx:06d}.png"), optimize=False)
            ys, xs = np.where(x > 0.5)
            if len(xs):
                person = [float(xs.min()) / work_w, float(ys.min()) / work_h, float(xs.max() - xs.min()) / work_w, float(ys.max() - ys.min()) / work_h]
        if not a.no_zones and (idx % a.zone_step == 1 or a.zone_step <= 1):
            faces, hands = [], []
            fr = face.detect_for_video(img, ts)
            for d in fr.detections:
                b = d.bounding_box
                faces.append([b.origin_x / work_w, b.origin_y / work_h, b.width / work_w, b.height / work_h])
            hr = hand.detect_for_video(img, ts)
            for lm in hr.hand_landmarks:
                xs_ = [p.x for p in lm]
                ys_ = [p.y for p in lm]
                x0, y0, x1, y1 = min(xs_) - 0.03, min(ys_) - 0.03, max(xs_) + 0.03, max(ys_) + 0.03
                hands.append([x0, y0, x1 - x0, y1 - y0])
            frames.append({"i": idx, "t": round(a.start + (idx - 1) / fps, 3), "faces": faces, "hands": hands, "person": person})
        if idx % 120 == 0:
            print(f"frame {idx}", file=sys.stderr)
    doc = {"fps": fps, "w": w, "h": h, "matteW": out_w, "matteH": out_h, "frameCount": idx, "start": a.start, "firstT": a.start, "frames": frames, "backend": "mediapipe"}
    json.dump(doc, open(os.path.join(a.out, "zones.json"), "w"))
    print(f"done: {idx} frames -> {a.out}")


if __name__ == "__main__":
    main()
