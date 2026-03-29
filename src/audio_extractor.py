"""
音频分离模块：从视频中提取音频
"""
import os
import subprocess

def extract_audio_from_video(video_path: str, output_dir: str) -> str:
    """
    使用ffmpeg从视频文件中提取音频，输出为mp3文件，返回音频文件路径
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    base_name = os.path.splitext(os.path.basename(video_path))[0]
    audio_path = os.path.join(output_dir, f"{base_name}.mp3")
    cmd = [
        'ffmpeg',
        '-i', video_path,
        '-vn',
        '-acodec', 'mp3',
        '-y',
        audio_path
    ]
    print(f"正在提取音频: {video_path}")
    subprocess.run(cmd, check=True)
    print(f"音频提取完成，文件保存在: {audio_path}")
    return audio_path
