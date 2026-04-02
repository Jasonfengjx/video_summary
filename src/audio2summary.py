"""
音频到总结链路测试脚本
用法：python audio2summary.py <音频文件路径>
"""
import os
import sys
from audio_transcriber_srt import transcribe_audio_with_timestamp
from note_generator import generate_summary_with_ollama

def main():
    if len(sys.argv) < 2:
        print("用法: python audio2summary.py <音频文件路径>")
        return
    audio_path = sys.argv[1]
    output_dir = os.path.dirname(audio_path)
    ext = os.path.splitext(audio_path)[1].lower()
    if ext == '.srt':
        # 直接用已有SRT做总结
        print(f"直接用SRT做总结: {audio_path}")
        generate_summary_with_ollama(audio_path, output_dir)
        print("全部完成！")
        return
    elif ext in ['.mp3', '.wav', '.m4a', '.aac', '.flac', '.ogg']:
        print(f"转写音频: {audio_path}")
        transcript_srt_path = transcribe_audio_with_timestamp(audio_path, output_dir)
        print(f"SRT转写完成: {transcript_srt_path}")
        print("调用大模型生成结构化笔记...")
        generate_summary_with_ollama(transcript_srt_path, output_dir)
        print("全部完成！")
        return
    else:
        print(f"不支持的文件类型: {audio_path}")
        return

if __name__ == "__main__":
    main()

# python src/audio2summary.py /Users/feng/Desktop/projects/bilibili_summary/downloads/Claude_Code_源码分析与复刻实现_transcript.srt