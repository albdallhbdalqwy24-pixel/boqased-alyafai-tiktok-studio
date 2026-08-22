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


def eye_centers(face_landmarks, width, height):
    groups = ([33, 133, 159, 145], [362, 263, 386, 374])
    centers = []
    for group in groups:
        points = [face_landmarks.landmark[i] for i in group]
        x = int(sum(p.x for p in points) / len(points) * width)
        y = int(sum(p.y for p in points) / len(points) * height)
        centers.append((x, y))
    return centers


def add_eye_glow(image, centers):
    if not centers:
        return image
    glow = Image.new("RGBA", image.size, (0, 0, 0, 0))
    sharp = Image.new("RGBA", image.size, (0, 0, 0, 0))
    radius = max(3, min(image.size) // 70)
    from PIL import ImageDraw
    gd = ImageDraw.Draw(glow)
    sd = ImageDraw.Draw(sharp)
    for x, y in centers:
        gd.ellipse((x-radius*4, y-radius*4, x+radius*4, y+radius*4), fill=(255, 24, 35, 170))
        sd.ellipse((x-radius, y-radius//2, x+radius, y+radius//2+1), fill=(255, 35, 45, 245))
    glow = glow.filter(ImageFilter.GaussianBlur(radius * 2))
    return Image.alpha_composite(Image.alpha_composite(image, glow), sharp)


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


def process(input_path, output_path, max_side=360):
    width, height, fps, duration = probe(input_path)
    with tempfile.TemporaryDirectory(prefix="videofx_ai_") as work:
        work = Path(work)
        frames = work / "frames"; frames.mkdir()
        rendered = work / "rendered"; rendered.mkdir()
        extract = ["ffmpeg", "-hide_banner", "-y", "-i", str(input_path), "-fps_mode", "passthrough", str(frames / "%08d.png")]
        subprocess.run(extract, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        segmenter = mp.solutions.selfie_segmentation.SelfieSegmentation(model_selection=0)
        face_mesh = mp.solutions.face_mesh.FaceMesh(static_image_mode=False, max_num_faces=1, refine_landmarks=False)
        last_centers = []
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
                # Track facial landmarks every third frame to reduce CPU while keeping the glow stable.
                if idx % 3 == 0 or not last_centers:
                    face_result = face_mesh.process(rgb)
                    if face_result.multi_face_landmarks:
                        last_centers = eye_centers(face_result.multi_face_landmarks[0], work_w, work_h)
                mask = np.clip(result.segmentation_mask, 0.0, 1.0)
                # Keep the subject solid while feathering only the boundary.
                alpha = Image.fromarray(np.uint8(mask * 255), mode="L").filter(ImageFilter.GaussianBlur(0.7))
                silhouette = Image.new("RGBA", (work_w, work_h), (5, 6, 9, 255))
                silhouette.putalpha(alpha)
                fog = make_fog((work_w, work_h), idx)
                composed = Image.alpha_composite(fog, silhouette)
                if last_centers:
                    composed = add_eye_glow(composed, last_centers)
                # Keep working frames small; FFmpeg restores the original dimensions at encode time.
                composed.convert("RGB").save(rendered / f"{idx + 1:08d}.jpg", quality=86, subsampling=2)
            if idx == 0 or (idx + 1) % 5 == 0 or idx + 1 == total_frames:
                print(json.dumps({"stage": "segment", "progress": 5 + int(((idx + 1) / total_frames) * 78)}, ensure_ascii=False), flush=True)
        print(json.dumps({"stage": "encode", "progress": 86}, ensure_ascii=False), flush=True)
        encode = ["ffmpeg", "-hide_banner", "-y", "-framerate", str(fps), "-i", str(rendered / "%08d.jpg"), "-i", str(input_path), "-map", "0:v:0", "-map", "1:a?", "-vf", f"scale={width}:{height}:flags=lanczos", "-c:v", "libx264", "-preset", "fast", "-crf", "19", "-pix_fmt", "yuv420p", "-c:a", "copy", "-map_metadata", "0", "-movflags", "+faststart", "-fps_mode", "passthrough", str(output_path)]
        subprocess.run(encode, check=True)
        segmenter.close()
        face_mesh.close()
    return {"width": width, "height": height, "fps": round(fps, 3), "duration": round(duration, 3)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("output")
    args = parser.parse_args()
    print(json.dumps(process(args.input, args.output), ensure_ascii=False))
