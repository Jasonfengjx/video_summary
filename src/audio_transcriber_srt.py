"""
音频转写模块（带时间戳）：将音频文件转为带时间戳的文本
"""
import os
import whisper

def transcribe_audio_with_timestamp(audio_path: str, output_dir: str) -> str:
    """
    使用whisper Python API转写音频，输出为srt字幕文件，返回srt文件路径
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    base_name = os.path.splitext(os.path.basename(audio_path))[0]
    srt_path = os.path.join(output_dir, f"{base_name}_transcript.srt")
    print(f"正在用whisper转写音频（带时间戳）: {audio_path}")
    model = whisper.load_model("base")
    result = model.transcribe(audio_path, language="zh")
    # 保存为srt字幕文件
    with open(srt_path, 'w', encoding='utf-8') as f:
        for i, segment in enumerate(result["segments"]):
            start = segment["start"]
            end = segment["end"]
            text = segment["text"].strip()
            # SRT时间格式
            def format_time(t):
                h = int(t // 3600)
                m = int((t % 3600) // 60)
                s = int(t % 60)
                ms = int((t - int(t)) * 1000)
                return f"{h:02}:{m:02}:{s:02},{ms:03}"
            f.write(f"{i+1}\n{format_time(start)} --> {format_time(end)}\n{text}\n\n")
    print(f"转写完成，SRT字幕保存在: {srt_path}")
    return srt_path
