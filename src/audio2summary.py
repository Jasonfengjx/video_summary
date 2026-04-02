"""
音频到总结链路测试脚本
用法：python audio2summary.py <音频文件路径>
"""
import os
import sys

from audio_transcriber_srt import transcribe_audio_with_timestamp
from config import load_config
from note_generator import generate_summary_with_ollama


def main():
    if len(sys.argv) < 2:
        print("用法: python audio2summary.py <音频文件路径>")
        return
    audio_path = sys.argv[1]
    output_dir = os.path.dirname(audio_path)
    config = load_config()
    ext = os.path.splitext(audio_path)[1].lower()
    if ext == ".srt":
        print(f"直接用SRT做总结: {audio_path}")
        result = generate_summary_with_ollama(audio_path, output_dir, config)
        print(result)
        return
    if ext in [".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg"]:
        print(f"转写音频: {audio_path}")
        asr = config["asr"]
        transcript_result = transcribe_audio_with_timestamp(
            audio_path,
            output_dir,
            model_size=asr["model"],
            language=asr["language"],
            save_srt=asr["save_srt"],
            save_json=asr["save_json"],
        )
        if transcript_result["status_code"] != 200:
            print(transcript_result)
            return
        print("调用大模型生成结构化笔记...")
        result = generate_summary_with_ollama(transcript_result["json_path"], output_dir, config)
        print(result)
        return
    print(f"不支持的文件类型: {audio_path}")


if __name__ == "__main__":
    main()

# python src/audio2summary.py /Users/feng/Desktop/projects/bilibili_summary/downloads/Claude_Code_源码分析与复刻实现_transcript.srt