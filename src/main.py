"""
哔哩哔哩视频自动总结笔记工具
主入口脚本
"""
import os
import sys

from video_downloader import download_bilibili_video

from audio_extractor import extract_audio_from_video
from audio_transcriber import transcribe_audio

from audio_transcriber_srt import transcribe_audio_with_timestamp
from note_generator import generate_summary_with_ollama

def main():
    print("欢迎使用哔哩哔哩视频自动总结笔记工具！")
    # 直接写死B站视频链接
    url = "https://www.bilibili.com/video/BV1kQXsBuEiV?t=1.1"
    output_root = os.path.join(os.path.dirname(__file__), '../downloads')
    import re
    m = re.search(r'/video/(BV[\w\d]+)', url)
    if not m:
        print("未能从URL中提取bvid！")
        return
    bvid = m.group(1)
    bvid_dir = os.path.join(output_root, bvid)
    if not os.path.exists(bvid_dir):
        os.makedirs(bvid_dir)
    # 下载视频到bvid目录
    download_bilibili_video(url, bvid_dir)
    # 查找bvid目录下最新的mp4文件
    mp4_files = [f for f in os.listdir(bvid_dir) if f.endswith('.mp4')]
    if not mp4_files:
        print("未找到下载的视频文件！")
        return
    mp4_files_full = [os.path.join(bvid_dir, f) for f in mp4_files]
    video_path = max(mp4_files_full, key=os.path.getmtime)
    print(f"后续处理文件: {video_path}")
    # 命名中间产物
    audio_path = os.path.join(bvid_dir, "audio.mp3")
    transcript_srt_path = os.path.join(bvid_dir, "transcript.srt")
    summary_md_path = os.path.join(bvid_dir, "summary.md")
    # 提取音频（强制输出audio.mp3）
    extract_audio_from_video(video_path, bvid_dir, output_name="audio.mp3")
    # whisper转写
    from audio_transcriber_srt import whisper
    model = whisper.load_model("base")
    result = model.transcribe(audio_path, language="zh")
    with open(transcript_srt_path, 'w', encoding='utf-8') as f:
        for i, segment in enumerate(result["segments"]):
            start = segment["start"]
            end = segment["end"]
            text = segment["text"].strip()
            def format_time(t):
                h = int(t // 3600)
                m = int((t % 3600) // 60)
                s = int(t % 60)
                ms = int((t - int(t)) * 1000)
                return f"{h:02}:{m:02}:{s:02},{ms:03}"
            f.write(f"{i+1}\n{format_time(start)} --> {format_time(end)}\n{text}\n\n")
    # 生成结构化笔记（输出到bvid目录）
    generate_summary_with_ollama(transcript_srt_path, bvid_dir)

if __name__ == "__main__":
    main()
