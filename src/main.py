"""
哔哩哔哩视频自动总结笔记工具
主入口脚本
"""
import argparse
import json
import logging
import os
import re
from typing import Optional

from audio_extractor import extract_audio_from_video
from audio_transcriber_srt import transcribe_audio_with_timestamp
from config import load_config, resolve_path
from frame_extractor import extract_frames_from_summary
from logging_utils import setup_logging
from note_generator import generate_summary_with_ollama
from response_utils import fail
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


def main() -> None:
    parser = argparse.ArgumentParser(description="哔哩哔哩视频自动总结笔记工具")
    parser.add_argument("--url", required=False, help="B站视频链接")
    parser.add_argument("--config", default=None, help="配置文件路径")
    parser.add_argument("--p", type=int, default=None, help="多P视频指定分P")
    parser.add_argument("--engine", default=None, help="ASR引擎: whisper/api")
    parser.add_argument("--language", default=None, help="语言: zh/en/ja/auto")
    parser.add_argument("--model", default=None, help="LLM模型名称")
    parser.add_argument("--force", action="store_true", help="强制重新转写与生成")
    parser.add_argument("--no-frames", action="store_true", help="禁用关键帧截取")
    parser.add_argument("--keep-video", action="store_true", help="保留原视频")
    parser.add_argument("--keep-audio", action="store_true", help="保留音频")
    args = parser.parse_args()

    config = load_config(args.config)
    logs_dir = resolve_path(config, config["app"]["logs_dir"])
    setup_logging(logs_dir, config["app"]["log_level"])

    default_url = "https://www.bilibili.com/video/BV18gQBBDEyB?spm_id_from=333.1007.tianma.1-3-3.click"
    url = args.url or default_url
    if not args.url:
        logging.warning("未提供URL，使用默认测试链接")

    bvid = _extract_bvid(url)
    if not bvid:
        logging.error("未能从URL中提取bvid")
        return

    output_root = resolve_path(config, config["app"]["output_root"])
    bvid_dir = os.path.join(output_root, bvid)
    os.makedirs(bvid_dir, exist_ok=True)
    logging.info("开始处理视频: %s", bvid)

    download_config = config["download"].copy()
    if args.p is not None:
        download_config["p_number"] = args.p

    download_result = download_bilibili_video(
        url=url,
        output_dir=bvid_dir,
        output_name="video.%(ext)s",
        format_spec=download_config["format"],
        merge_output_format=download_config["merge_output_format"],
        cookies=resolve_path(config, download_config.get("cookies", ""))
        if download_config.get("cookies")
        else "",
        proxy=download_config.get("proxy", ""),
        retries=download_config.get("retries", 3),
        backoff_seconds=download_config.get("backoff_seconds", 2),
        p_number=download_config.get("p_number"),
    )
    if download_result["status_code"] != 200:
        logging.error(download_result.get("message"))
        return

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
        return

    transcript_json_path = os.path.join(bvid_dir, "transcript.json")
    use_cache = config["asr"].get("use_cache", True)
    cached_transcript = None if args.force or not use_cache else _load_cached_transcript(transcript_json_path)

    if cached_transcript:
        logging.info("检测到缓存转写结果，跳过ASR")
    else:
        asr_config = config["asr"]
        if args.engine:
            asr_config["engine"] = args.engine
        if args.language:
            asr_config["language"] = args.language
        if asr_config["engine"] != "whisper":
            result = fail(400, f"不支持的ASR引擎: {asr_config['engine']}")
        else:
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
            return

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
        return

    if config["frames"]["enabled"] and not args.no_frames:
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

    keep_video = config["cleanup"]["keep_video"] or args.keep_video
    keep_audio = config["cleanup"]["keep_audio"] or args.keep_audio
    if not keep_audio and os.path.exists(audio_result["file_path"]):
        os.remove(audio_result["file_path"])
    if not keep_video and os.path.exists(video_path):
        os.remove(video_path)

    logging.info("全部流程完成，产物目录: %s", bvid_dir)

if __name__ == "__main__":
    main()
