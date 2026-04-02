"""
音频转写模块（带时间戳）：将音频文件转为带时间戳的文本
"""
import json
import os
from typing import Any, Dict

import whisper

from response_utils import ok, fail


def transcribe_audio_with_timestamp(
    audio_path: str,
    output_dir: str,
    model_size: str = "base",
    language: str = "auto",
    save_srt: bool = True,
    save_json: bool = True,
) -> Dict[str, Any]:
    """
    使用whisper Python API转写音频，输出为SRT字幕与JSON
    """
    os.makedirs(output_dir, exist_ok=True)
    srt_path = os.path.join(output_dir, "transcript.srt")
    json_path = os.path.join(output_dir, "transcript.json")

    try:
        model = whisper.load_model(model_size)
        whisper_language = None if language == "auto" else language
        result = model.transcribe(audio_path, language=whisper_language)
    except Exception as exc:
        return fail(500, f"音频转写失败: {exc}")

    segments = [
        {
            "start": segment["start"],
            "end": segment["end"],
            "text": segment["text"].strip(),
        }
        for segment in result.get("segments", [])
    ]
    full_text = "\n".join(segment["text"] for segment in segments)

    if save_srt:
        def format_time(t: float) -> str:
            h = int(t // 3600)
            m = int((t % 3600) // 60)
            s = int(t % 60)
            ms = int((t - int(t)) * 1000)
            return f"{h:02}:{m:02}:{s:02},{ms:03}"

        with open(srt_path, "w", encoding="utf-8") as f:
            for i, segment in enumerate(segments):
                f.write(
                    f"{i+1}\n"
                    f"{format_time(segment['start'])} --> {format_time(segment['end'])}\n"
                    f"{segment['text']}\n\n"
                )

    if save_json:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "text": full_text,
                    "segments": segments,
                    "language": result.get("language"),
                },
                f,
                ensure_ascii=False,
                indent=2,
            )

    return ok(text=full_text, segments=segments, srt_path=srt_path, json_path=json_path)
