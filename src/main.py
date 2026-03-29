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
    url = "https://www.bilibili.com/video/BV1bZAczVEuK?t=94.7"
    output_dir = os.path.join(os.path.dirname(__file__), '../downloads')
    video_dir = download_bilibili_video(url, output_dir)
    # 查找下载目录下的mp4文件
    video_files = [f for f in os.listdir(output_dir) if f.endswith('.mp4')]
    if not video_files:
        print("未找到下载的视频文件！")
        return
    video_path = os.path.join(output_dir, video_files[0])
    # 裁剪视频为1分钟以内
    clipped_video_path = os.path.join(output_dir, "clipped_temp.mp4")
    import subprocess
    print("正在裁剪视频为1分钟以内...")
    subprocess.run([
        'ffmpeg',
        '-i', video_path,
        '-t', '60',
        '-c', 'copy',
        '-y',
        clipped_video_path
    ], check=True)
    print(f"裁剪完成: {clipped_video_path}")
    # 提取音频
    audio_path = extract_audio_from_video(clipped_video_path, output_dir)
    # 音频转写（带时间戳，输出srt）
    transcript_srt_path = transcribe_audio_with_timestamp(audio_path, output_dir)
    # 使用Ollama大模型生成结构化笔记
    generate_summary_with_ollama(transcript_srt_path, output_dir, model="qwen3.5:2b")

if __name__ == "__main__":
    main()
