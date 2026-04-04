"""
哔哩哔哩视频自动总结笔记工具
主入口脚本
"""
import argparse
import json
import logging
import os
import re
from typing import Any, Dict, Optional

from audio_extractor import extract_audio_from_video
from audio_transcriber_srt import transcribe_audio_with_timestamp
from config import load_config, resolve_path
from frame_extractor import extract_frames_from_summary
from logging_utils import setup_logging
from note_generator import generate_summary_with_ollama
from playlist_fetcher import get_playlist_videos
from response_utils import fail, ok
from video_downloader import download_bilibili_video


def _extract_bvid(url: str) -> Optional[str]:
    match = re.search(r"/video/(BV[\w\d]+)", url)
    return match.group(1) if match else None


def _load_cached_transcript(transcript_json_path: str) -> Optional[dict]:
    if not os.path.exists(transcript_json_path):
        return None
    try:
        with open(transcript_json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _process_single_video(
    video_url: str,
    output_root: str,
    config: Dict[str, Any],
    args: argparse.Namespace,
) -> Dict[str, Any]:
    """
    处理单个视频的完整流程
    
    Returns:
        Dict: 包含处理结果和文件路径
    """
    bvid = _extract_bvid(video_url)
    if not bvid:
        return fail(500, "未能从URL中提取bvid")

    bvid_dir = os.path.join(output_root, bvid)
    os.makedirs(bvid_dir, exist_ok=True)
    logging.info("开始处理视频: %s", bvid)

    transcript_json_path = os.path.join(bvid_dir, "transcript.json")
    summary_md_path = os.path.join(bvid_dir, "summary.md")
    use_cache = config["asr"].get("use_cache", True)
    cached_transcript = None if args.force or not use_cache else _load_cached_transcript(transcript_json_path)
    summary_exists = os.path.exists(summary_md_path)

    if cached_transcript and summary_exists and not args.force:
        logging.info("检测到已完成的转写和总结，跳过下载和ASR: %s", bvid)
        return ok(
            bvid=bvid,
            output_dir=bvid_dir,
            summary_path=summary_md_path,
            skipped=True,
        )

    download_config = config["download"].copy()
    if args.p is not None:
        download_config["p_number"] = args.p

    cookies = resolve_path(config, download_config.get("cookies", "")) if download_config.get("cookies") else ""
    proxy = download_config.get("proxy", "")

    video_path = os.path.join(bvid_dir, "video.mp4")
    audio_result = None

    if cached_transcript and os.path.exists(os.path.join(bvid_dir, "audio.wav")):
        logging.info("检测到缓存音频，跳过下载")
        audio_result = ok(file_path=os.path.join(bvid_dir, "audio.wav"))
    else:
        download_result = download_bilibili_video(
            url=video_url,
            output_dir=bvid_dir,
            output_name="video.%(ext)s",
            format_spec=download_config["format"],
            merge_output_format=download_config["merge_output_format"],
            cookies=cookies,
            proxy=proxy,
            retries=download_config.get("retries", 3),
            backoff_seconds=download_config.get("backoff_seconds", 2),
            p_number=download_config.get("p_number"),
        )
        if download_result["status_code"] != 200:
            logging.error(download_result.get("message"))
            return download_result

        video_path = download_result["file_path"]
        audio_config = config["audio"]
        audio_result = extract_audio_from_video(
            video_path=video_path,
            output_dir=bvid_dir,
            output_name="audio.wav",
            sample_rate=audio_config["sample_rate"],
            channels=audio_config["channels"],
        )
        if audio_result["status_code"] != 200:
            logging.error(audio_result.get("message"))
            return audio_result

    if cached_transcript:
        logging.info("检测到缓存转写结果，跳过ASR")
    else:
        asr_config = config["asr"]
        if args.engine:
            asr_config["engine"] = args.engine
        if args.language:
            asr_config["language"] = args.language
        if asr_config["engine"] != "whisper":
            return fail(400, f"不支持的ASR引擎: {asr_config['engine']}")

        result = transcribe_audio_with_timestamp(
            audio_path=audio_result["file_path"],
            output_dir=bvid_dir,
            model_size=asr_config["model"],
            language=asr_config["language"],
            save_srt=asr_config["save_srt"],
            save_json=asr_config["save_json"],
        )
        if result["status_code"] != 200:
            logging.error(result.get("message"))
            return result

    if summary_exists and not args.force:
        logging.info("检测到已有总结，跳过LLM生成")
        summary_result = ok(
            markdown_content="",
            file_path=summary_md_path,
        )
    else:
        summary_config = config
        if args.model:
            summary_config = json.loads(json.dumps(config))
            summary_config["llm"]["model"] = args.model
        logging.info("使用LLM模型: %s", summary_config["llm"]["model"])

        summary_result = generate_summary_with_ollama(
            transcript_path=transcript_json_path,
            output_dir=bvid_dir,
            config=summary_config,
        )
        if summary_result["status_code"] != 200:
            logging.error(summary_result.get("message"))
            return summary_result

    if config["frames"]["enabled"] and not args.no_frames and not args.force:
        assets_dir = os.path.join(bvid_dir, "assets")
        try:
            extract_frames_from_summary(
                video_path=video_path,
                summary_text=summary_result["markdown_content"],
                assets_dir=assets_dir,
                max_frames=config["frames"]["max_frames"],
                image_format=config["frames"]["image_format"],
                quality=config["frames"]["quality"],
            )
        except Exception as exc:
            logging.warning("关键帧截取失败: %s", exc)

    if audio_result and audio_result.get("file_path"):
        keep_audio = config["cleanup"]["keep_audio"] or args.keep_audio
        if not keep_audio and os.path.exists(audio_result["file_path"]):
            os.remove(audio_result["file_path"])
    
    keep_video = config["cleanup"]["keep_video"] or args.keep_video
    if not keep_video and os.path.exists(video_path):
        os.remove(video_path)

    logging.info("视频处理完成: %s", bvid)
    return ok(
        bvid=bvid,
        output_dir=bvid_dir,
        summary_path=summary_md_path,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="哔哩哔哩视频自动总结笔记工具")
    parser.add_argument("--url", required=False, help="B站视频链接")
    parser.add_argument("--playlist", required=False, help="B站系列/合集/频道链接")
    parser.add_argument("--config", default=None, help="配置文件路径")
    parser.add_argument("--p", type=int, default=None, help="多P视频指定分P")
    parser.add_argument("--engine", default=None, help="ASR引擎: whisper/api")
    parser.add_argument("--language", default=None, help="语言: zh/en/ja/auto")
    parser.add_argument("--model", default=None, help="LLM模型名称")
    parser.add_argument("--force", action="store_true", help="强制重新转写与生成")
    parser.add_argument("--no-frames", action="store_true", help="禁用关键帧截取")
    parser.add_argument("--keep-video", action="store_true", help="保留原视频")
    parser.add_argument("--keep-audio", action="store_true", help="保留音频")
    parser.add_argument("--output-root", default=None, help="产物输出根目录")
    args = parser.parse_args()

    config = load_config(args.config)
    logs_dir = resolve_path(config, config["app"]["logs_dir"])
    setup_logging(logs_dir, config["app"]["log_level"])

    default_url = "https://www.bilibili.com/video/BV1TTDTBbEo1?t=49.8"
    url = args.url or default_url
    if not args.url and not args.playlist:
        logging.warning("未提供URL，使用默认测试链接")

    output_root = args.output_root or resolve_path(config, config["app"]["output_root"])

    if args.playlist:
        logging.info("开始处理系列视频: %s", args.playlist)
        playlist_result = get_playlist_videos(
            url=args.playlist,
            cookies=resolve_path(config, config["download"].get("cookies", "")) if config["download"].get("cookies") else "",
            proxy=config["download"].get("proxy", ""),
        )
        if playlist_result["status_code"] != 200:
            logging.error(playlist_result.get("message"))
            return

        playlist_title = playlist_result.get("playlist_title", "unknown")
        videos = playlist_result.get("videos", [])
        logging.info("获取到 %d 个视频: %s", len(videos), playlist_title)

        playlist_id = playlist_result.get("playlist_id", "unknown")
        series_dir = os.path.join(output_root, f"series_{playlist_id}")
        os.makedirs(series_dir, exist_ok=True)

        playlist_urls_path = os.path.join(output_root, f"{playlist_id}_playlist.txt")
        with open(playlist_urls_path, "w", encoding="utf-8") as f:
            for video in videos:
                f.write(f"{video.get('id', '')}\t{video.get('title', '')}\t{video.get('url', '')}\n")
        logging.info("视频列表已保存到: %s", playlist_urls_path)

        results = []
        for idx, video in enumerate(videos, start=1):
            video_url = video.get("url", "")
            if not video_url:
                logging.warning("视频 %d 缺少URL，跳过", idx)
                continue

            logging.info("处理进度: %d/%d - %s", idx, len(videos), video.get("title", ""))
            result = _process_single_video(
                video_url=video_url,
                output_root=series_dir,
                config=config,
                args=args,
            )
            results.append({
                "index": idx,
                "bvid": video.get("id", ""),
                "title": video.get("title", ""),
                "status": "success" if result.get("status_code") == 200 else "failed",
                "message": result.get("message", ""),
                "summary_path": result.get("summary_path", ""),
            })

        summary_index_path = os.path.join(series_dir, "_index.md")
        with open(summary_index_path, "w", encoding="utf-8") as f:
            f.write(f"# {playlist_title}\n\n")
            f.write(f"共 {len(videos)} 个视频，成功 {sum(1 for r in results if r['status'] == 'success')} 个\n\n")
            f.write("## 视频列表\n\n")
            for r in results:
                status_icon = "✓" if r["status"] == "success" else "✗"
                f.write(f"- {status_icon} [{r['title']}]({r['bvid']}/summary.md)\n")

        logging.info("系列视频处理完成，结果目录: %s", series_dir)
    else:
        result = _process_single_video(
            video_url=url,
            output_root=output_root,
            config=config,
            args=args,
        )
        if result["status_code"] != 200:
            logging.error(result.get("message"))
            return
        logging.info("全部流程完成，产物目录: %s", result.get("output_dir", ""))

if __name__ == "__main__":
    main()
