"""
音频分离模块：从视频中提取音频
"""
import os
import subprocess
from typing import Any, Dict

from response_utils import ok, fail


def extract_audio_from_video(
    video_path: str,
    output_dir: str,
    output_name: str = "audio.wav",
    sample_rate: int = 16000,
    channels: int = 1,
    codec: str = "pcm_s16le",
) -> Dict[str, Any]:
    """
    使用ffmpeg从视频文件中提取音频，输出为16k/16bit mono WAV
    """
    os.makedirs(output_dir, exist_ok=True)
    audio_path = os.path.join(output_dir, output_name)
    cmd = [
        "ffmpeg",
        "-i",
        video_path,
        "-vn",
        "-ac",
        str(channels),
        "-ar",
        str(sample_rate),
        "-acodec",
        codec,
        "-y",
        audio_path,
    ]
    try:
        subprocess.run(cmd, check=True)
    except Exception as exc:
        return fail(500, f"音频提取失败: {exc}")
    if not os.path.exists(audio_path):
        return fail(500, "音频提取失败: 未找到输出文件")
    return ok(file_path=audio_path)
