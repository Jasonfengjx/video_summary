"""
笔记生成模块：调用本地Ollama大模型（如qwen3.5:2b）对转写文本进行总结，输出为markdown笔记
"""
import os

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../prompts'))
from api_config import API_BASE_URL, API_KEY, MODEL
import requests

def generate_summary_with_ollama(transcript_path: str, output_dir: str, model: str = None) -> str:
    """
    调用 DashScope（阿里云通义千问）API 对转写文本进行总结，输出为markdown文件，返回md文件路径
    """
    if model is None:
        model = MODEL
    with open(transcript_path, 'r', encoding='utf-8') as f:
        transcript = f.read()
    # 读取prompt模板
    prompt_path = os.path.join(os.path.dirname(__file__), '../prompts/summary_prompt.txt')
    with open(prompt_path, 'r', encoding='utf-8') as pf:
        prompt_template = pf.read()
    prompt = prompt_template.replace('{transcript}', transcript)
    url = f"{API_BASE_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    print(f"正在调用 DashScope ({model}) 生成笔记...")
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    result = response.json()
    summary = result.get("choices", [{}])[0].get("message", {}).get("content", "")
    base_name = os.path.splitext(os.path.basename(transcript_path))[0]
    md_path = os.path.join(output_dir, f"{base_name}_summary.md")
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(summary)
    print(f"笔记生成完成，保存在: {md_path}")
    return md_path
