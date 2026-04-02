import os
import re
import subprocess
from typing import List


def _parse_timestamps(markdown_text: str) -> List[float]:
    timestamps: List[float] = []

    # 支持 HH:MM:SS / MM:SS
    pattern = re.compile(r"(?<!\d)(\d{1,2}):(\d{2})(?::(\d{2}))?")
    for match in pattern.finditer(markdown_text):
        parts = match.groups()
        if parts[2] is None:
            minutes = int(parts[0])
            seconds = int(parts[1])
            total = minutes * 60 + seconds
        else:
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = int(parts[2])
            total = hours * 3600 + minutes * 60 + seconds
        if total not in timestamps:
            timestamps.append(float(total))
    return timestamps


def extract_frames_from_summary(
    video_path: str,
    summary_text: str,
    assets_dir: str,
    max_frames: int = 8,
    image_format: str = "jpg",
    quality: int = 2,
) -> List[str]:
    if not os.path.exists(video_path):
        return []
    os.makedirs(assets_dir, exist_ok=True)
    timestamps = _parse_timestamps(summary_text)[:max_frames]
    output_paths: List[str] = []

    ffmpeg_failed = False
    for idx, ts in enumerate(timestamps, start=1):
        output_path = os.path.join(assets_dir, f"frame_{idx:03d}.{image_format}")
        cmd = [
            "ffmpeg",
            "-ss",
            str(ts),
            "-i",
            video_path,
            "-frames:v",
            "1",
            "-q:v",
            str(quality),
            "-y",
            output_path,
        ]
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            output_paths.append(output_path)
        except Exception:
            ffmpeg_failed = True
            break

    if not ffmpeg_failed:
        return output_paths

    output_paths = []
    try:
        import cv2
    except Exception:
        return output_paths

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return output_paths

    for idx, ts in enumerate(timestamps, start=1):
        cap.set(cv2.CAP_PROP_POS_MSEC, ts * 1000)
        ok, frame = cap.read()
        if not ok:
            continue
        output_path = os.path.join(assets_dir, f"frame_{idx:03d}.{image_format}")
        cv2.imwrite(output_path, frame)
        output_paths.append(output_path)
    cap.release()
    return output_paths
