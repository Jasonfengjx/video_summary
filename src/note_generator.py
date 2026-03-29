"""
笔记生成模块：调用本地Ollama大模型（如qwen3.5:2b）对转写文本进行总结，输出为markdown笔记
"""
import os
import requests

def generate_summary_with_ollama(transcript_path: str, output_dir: str, model: str = "qwen3.5:2b") -> str:
    """
    调用本地Ollama API对转写文本进行总结，输出为markdown文件，返回md文件路径
    """
    with open(transcript_path, 'r', encoding='utf-8') as f:
        transcript = f.read()
    prompt = f"""
请将以下视频转写内容进行结构化总结，提炼重点，输出为带有标题和分点的Markdown笔记：

{transcript}
"""
    # Ollama API
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }
    print(f"正在调用Ollama模型({model})生成笔记...")
    response = requests.post(url, json=payload)
    response.raise_for_status()
    result = response.json()
    summary = result.get("response", "")
    base_name = os.path.splitext(os.path.basename(transcript_path))[0]
    md_path = os.path.join(output_dir, f"{base_name}_summary.md")
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(summary)
    print(f"笔记生成完成，保存在: {md_path}")
    return md_path
