"""
视频下载模块：负责下载B站视频
"""
import subprocess
import os

def download_bilibili_video(url: str, output_dir: str) -> str:
    """
    使用yt-dlp下载B站视频，返回视频文件路径
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    # 输出文件名模板
    output_template = os.path.join(output_dir, '%(title)s.%(ext)s')
    cmd = [
        'yt-dlp',
        '-f', 'bestvideo+bestaudio/best',
        '-o', output_template,
        url
    ]
    print(f"正在下载视频: {url}")
    subprocess.run(cmd, check=True)
    print(f"下载完成，文件保存在: {output_dir}")
    return output_dir
