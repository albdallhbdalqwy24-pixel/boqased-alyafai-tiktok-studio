# -*- coding: utf-8 -*-
"""AI human segmentation + generated white fog background.

The input video is never used as a background layer in the final composition:
rembg creates a person alpha mask, the person is rendered black, and a new
procedural light fog background is generated for every frame.
"""
import argparse
import json
import math
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import mediapipe as mp
from PIL import Image, ImageFilter


def probe(path):
    cmd = ["ffprobe", "-v", "error", "-show_entries", "stream=width,height,avg_frame_rate,duration:format=duration", "-of", "json", str(path)]
    data = json.loads(subprocess.check_output(cmd, text=True))
    stream = next(s for s in data["streams"] if s.get("width"))
    rate = stream.get("avg_frame_rate", "0/0")
    a, b = rate.split("/")
    fps = float(a) / float(b) if float(b) else 30.0
    duration = float(stream.get("duration") or data.get("format", {}).get("duration") or 0)
    return int(stream["width"]), int(stream["height"]), fps, duration


def make_fog(size, frame_index):
    w, h = size
    # Generated light fog: white/pearl base, soft moving gray clouds, no source frame.
    base = Image.new("RGB", (w, h), (246, 247, 249))
    fog = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    step = max(32, min(w, h) // 8)
    for i in range(9):
        x = int((w * (i + 0.5) / 9 + math.sin(frame_index * 0.025 + i) * w * 0.12) % (w + step)) - step // 2
        y = int(h * (0.12 + ((i * 0.173) % 0.78)))
        layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        blob = Image.new("RGBA", (step * 3, step * 2), (100, 106, 116, 22))
        blob = blob.filter(ImageFilter.GaussianBlur(max(10, step // 2)))
        layer.paste(blob, (x, y), blob)
        fog = Image.alpha_composite(fog, layer)
    return Image.alpha_composite(base.convert("RGBA"), fog)


def process(input_path, output_path, max_side=960):
    width, height, fps, duration = probe(input_path)
    with tempfile.TemporaryDirectory(prefix="videofx_ai_") as work:
        work = Path(work)
        frames = work / "frames"; frames.mkdir()
        rendered = work / "rendered"; rendered.mkdir()
        extract = ["ffmpeg", "-hide_banner", "-y", "-i", str(input_path), "-fps_mode", "passthrough", str(frames / "%08d.png")]
        subprocess.run(extract, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        segmenter = mp.solutions.selfie_segmentation.SelfieSegmentation(model_selection=1)
        scale = min(1.0, max_side / max(width, height))
        work_w = max(2, int(width * scale) // 2 * 2)
        work_h = max(2, int(height * scale) // 2 * 2)
        frame_paths = sorted(frames.glob("*.png"))
        total_frames = max(1, len(frame_paths))
        for idx, frame_path in enumerate(frame_paths):
            with Image.open(frame_path).convert("RGB") as frame:
                small = frame.resize((work_w, work_h), Image.Resampling.LANCZOS)
                rgb = np.asarray(small, dtype=np.uint8)
                result = segmenter.process(rgb)
                mask = np.clip(result.segmentation_mask, 0.0, 1.0)
                # Keep the subject solid while feathering only the boundary.
                alpha = Image.fromarray(np.uint8(mask * 255), mode="L").filter(ImageFilter.GaussianBlur(0.7))
                silhouette = Image.new("RGBA", (work_w, work_h), (5, 6, 9, 255))
                silhouette.putalpha(alpha)
                fog = make_fog((work_w, work_h), idx)
                composed = Image.alpha_composite(fog, silhouette)
                if (work_w, work_h) != (width, height):
                    composed = composed.resize((width, height), Image.Resampling.LANCZOS)
                composed.convert("RGB").save(rendered / f"{idx + 1:08d}.jpg", quality=94, subsampling=0)
            if idx == 0 or (idx + 1) % 5 == 0 or idx + 1 == total_frames:
                print(json.dumps({"stage": "segment", "progress": 5 + int(((idx + 1) / total_frames) * 78)}, ensure_ascii=False), flush=True)
        print(json.dumps({"stage": "encode", "progress": 86}, ensure_ascii=False), flush=True)
        encode = ["ffmpeg", "-hide_banner", "-y", "-framerate", str(fps), "-i", str(rendered / "%08d.jpg"), "-i", str(input_path), "-map", "0:v:0", "-map", "1:a?", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "copy", "-map_metadata", "0", "-movflags", "+faststart", "-fps_mode", "passthrough", str(output_path)]
        subprocess.run(encode, check=True)
        segmenter.close()
    return {"width": width, "height": height, "fps": round(fps, 3), "duration": round(duration, 3)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("output")
    args = parser.parse_args()
    print(json.dumps(process(args.input, args.output), ensure_ascii=False))
