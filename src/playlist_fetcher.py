"""
视频列表获取模块：负责从B站获取系列视频/频道的视频列表
"""
import logging
import os
from typing import Any, Dict, List, Optional

from yt_dlp import YoutubeDL

from response_utils import ok, fail


def _fetch_playlist_with_details(url: str, cookies: str = "", proxy: str = "") -> Optional[Dict[str, Any]]:  # type: ignore[type-arg]
    """
    获取播放列表的详细信息（包含完整标题）
    """
    ydl_opts: dict[str, Any] = {
        "extract_flat": False,
        "skip_download": True,
        "quiet": True,
        "no_warnings": True,
        "playlistend": 5,
    }
    if cookies:
        ydl_opts["cookiefile"] = cookies
    if proxy:
        ydl_opts["proxy"] = proxy

    try:
        with YoutubeDL(ydl_opts) as ydl:  # type: ignore[arg-type]
            info = ydl.extract_info(url, download=False)
            if info and "entries" in info:
                entries: list = info["entries"]
                if entries:
                    for entry in entries[:3]:
                        if entry and entry.get("title"):
                            return info
            return None
    except Exception:
        return None


def get_playlist_videos(url: str, cookies: str = "", proxy: str = "") -> Dict[str, Any]:  # type: ignore[type-arg]
    """
    获取播放列表/频道中的所有视频信息
    
    Args:
        url: 播放列表/频道/合集URL
        cookies: cookies文件路径（可选，用于会员内容）
        proxy: 代理地址（可选）
    
    Returns:
        Dict: 包含视频列表和元数据
    """
    ydl_opts: dict[str, Any] = {
        "extract_flat": True,
        "skip_download": True,
        "quiet": True,
        "no_warnings": True,
    }
    if cookies:
        ydl_opts["cookiefile"] = cookies
    if proxy:
        ydl_opts["proxy"] = proxy

    try:
        with YoutubeDL(ydl_opts) as ydl:  # type: ignore[arg-type]
            info = ydl.extract_info(url, download=False)
    except Exception as exc:
        logging.error("获取视频列表失败: %s", exc)
        return fail(500, f"获取视频列表失败: {exc}")

    if not info:
        return fail(404, "未找到视频列表")

    videos: list[dict[str, Any]] = []
    entries = info.get("entries", [])

    if not entries:
        return fail(404, "视频列表为空")

    for entry in entries:
        if entry:
            video_url = entry.get("url") or entry.get("webpage_url", "")
            title = entry.get("title", "")

            if not title:
                title = entry.get("id", "")

            videos.append({
                "id": entry.get("id", ""),
                "title": title,
                "url": video_url,
                "duration": entry.get("duration"),
                "upload_date": entry.get("upload_date"),
            })

    playlist_title = info.get("title", "")
    playlist_id = info.get("id", "")

    logging.info("获取到视频列表: %s, 共 %d 个视频", playlist_title, len(videos))

    return ok(
        playlist_title=playlist_title,
        playlist_id=playlist_id,
        videos=videos,
        total=len(videos),
    )


def get_video_info(url: str, cookies: str = "", proxy: str = "") -> Dict[str, Any]:  # type: ignore[type-arg]
    """
    获取单个视频的详细信息
    
    Args:
        url: 视频URL
        cookies: cookies文件路径（可选）
        proxy: 代理地址（可选）
    
    Returns:
        Dict: 视频详细信息
    """
    ydl_opts: dict[str, Any] = {
        "skip_download": True,
        "quiet": True,
        "no_warnings": True,
    }
    if cookies:
        ydl_opts["cookiefile"] = cookies
    if proxy:
        ydl_opts["proxy"] = proxy

    try:
        with YoutubeDL(ydl_opts) as ydl:  # type: ignore[arg-type]
            info = ydl.extract_info(url, download=False)
    except Exception as exc:
        logging.error("获取视频信息失败: %s", exc)
        return fail(500, f"获取视频信息失败: {exc}")

    if not info:
        return fail(404, "未找到视频")

    if "entries" in info and info["entries"]:
        info = info["entries"][0]

    return ok(
        id=info.get("id", ""),
        title=info.get("title", ""),
        url=info.get("webpage_url", ""),
        duration=info.get("duration"),
        uploader=info.get("uploader", ""),
        upload_date=info.get("upload_date"),
        description=info.get("description", ""),
    )
