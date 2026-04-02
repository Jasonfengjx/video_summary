"""
视频下载模块：负责下载B站视频
"""
import json
import os
from typing import Any, Dict, Optional

from yt_dlp import YoutubeDL

from response_utils import ok, fail


def download_bilibili_video(
    url: str,
    output_dir: str,
    output_name: str = "video.%(ext)s",
    format_spec: str = "bestvideo+bestaudio/best",
    merge_output_format: str = "mp4",
    cookies: str = "",
    proxy: str = "",
    retries: int = 3,
    backoff_seconds: int = 2,
    p_number: Optional[int] = None,
) -> Dict[str, Any]:
    """
    使用yt-dlp下载B站视频，返回标准化结果
    """
    os.makedirs(output_dir, exist_ok=True)

    ydl_opts: Dict[str, Any] = {
        "format": format_spec,
        "outtmpl": os.path.join(output_dir, output_name),
        "merge_output_format": merge_output_format,
        "retries": retries,
        "fragment_retries": retries,
        "continuedl": True,
        "noplaylist": False,
    }
    if cookies:
        ydl_opts["cookiefile"] = cookies
    if proxy:
        ydl_opts["proxy"] = proxy
    if p_number:
        ydl_opts["playlist_items"] = str(p_number)

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
    except Exception as exc:
        return fail(500, f"视频下载失败: {exc}")

    if "entries" in info and info["entries"]:
        info = info["entries"][0]

    video_path = os.path.join(output_dir, f"video.{merge_output_format}")
    meta_path = os.path.join(output_dir, "meta.json")
    try:
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "id": info.get("id"),
                    "title": info.get("title"),
                    "duration": info.get("duration"),
                    "uploader": info.get("uploader"),
                    "upload_date": info.get("upload_date"),
                    "webpage_url": info.get("webpage_url"),
                },
                f,
                ensure_ascii=False,
                indent=2,
            )
    except Exception as exc:
        return fail(500, f"元数据写入失败: {exc}")

    if not os.path.exists(video_path):
        return fail(500, "未找到下载的视频文件")

    return ok(
        bvid=info.get("id"),
        file_path=video_path,
        meta_path=meta_path,
        title=info.get("title"),
        duration=info.get("duration"),
    )
