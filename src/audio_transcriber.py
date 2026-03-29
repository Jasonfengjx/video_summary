"""
音频转写模块：将音频文件转为文本
"""
import os
import subprocess

def transcribe_audio(audio_path: str, output_dir: str) -> str:
    """
    使用whisper命令行工具转写音频，输出为txt文件，返回文本文件路径
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    base_name = os.path.splitext(os.path.basename(audio_path))[0]
    text_path = os.path.join(output_dir, f"{base_name}_transcript.txt")
    cmd = [
        'whisper',
        audio_path,
        '--model', 'base',
        '--language', 'zh',
        '--output_format', 'txt',
        '--output_dir', output_dir
    ]
    print(f"正在转写音频: {audio_path}")
    subprocess.run(cmd, check=True)
    print(f"转写完成，文件保存在: {text_path}")
    return text_path
