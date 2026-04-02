"""
笔记生成模块：调用 LLM 对转写文本进行总结，输出为markdown笔记
"""
import json
import os
from typing import Any, Dict, List

import requests

from config import load_api_key_from_cmd, resolve_path
from response_utils import ok, fail


def _load_transcript_text(transcript_path: str) -> str:
    if transcript_path.endswith(".json"):
        with open(transcript_path, "r", encoding="utf-8") as f:
            payload = json.load(f)
        return payload.get("text", "")
    with open(transcript_path, "r", encoding="utf-8") as f:
        return f.read()


def _chunk_text(text: str, max_chars: int, overlap: int) -> List[str]:
    if len(text) <= max_chars:
        return [text]
    chunks: List[str] = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        chunks.append(text[start:end])
        if end == len(text):
            break
        start = max(0, end - overlap)
    return chunks


def _call_llm(api_base_url: str, api_key: str, model: str, messages: List[Dict[str, str]]) -> str:
    url = f"{api_base_url}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {"model": model, "messages": messages}
    response = requests.post(url, headers=headers, json=payload, timeout=120)
    response.raise_for_status()
    result = response.json()
    return result.get("choices", [{}])[0].get("message", {}).get("content", "")


def generate_summary_with_ollama(
    transcript_path: str,
    output_dir: str,
    config: Dict[str, Any],
) -> Dict[str, Any]:
    """
    调用 DashScope（阿里云通义千问）API 对转写文本进行总结，输出为markdown文件
    """
    llm_config = config["llm"]
    api_key = os.getenv(llm_config["api_key_env"], "")
    if not api_key:
        api_key = load_api_key_from_cmd(config["_project_root"]) or ""
    if not api_key:
        return fail(401, f"缺少API Key，请设置环境变量 {llm_config['api_key_env']} 或在 cmd 文件中配置 api")

    transcript = _load_transcript_text(transcript_path)
    if not transcript.strip():
        return fail(400, "转写文本为空，无法生成笔记")

    prompt_path = resolve_path(config, llm_config["prompt_path"])
    with open(prompt_path, "r", encoding="utf-8") as pf:
        prompt_template = pf.read()

    chunk_config = llm_config.get("chunk", {})
    use_chunk = chunk_config.get("enabled", True)
    max_chars = chunk_config.get("max_chars", 12000)
    overlap = chunk_config.get("overlap", 500)

    model = llm_config["model"]
    api_base_url = llm_config["api_base_url"]

    try:
        if use_chunk and len(transcript) > max_chars:
            summaries: List[str] = []
            for idx, chunk in enumerate(_chunk_text(transcript, max_chars, overlap), start=1):
                chunk_prompt = prompt_template.replace("{transcript}", chunk)
                messages = [{"role": "user", "content": chunk_prompt}]
                chunk_summary = _call_llm(api_base_url, api_key, model, messages)
                summaries.append(f"## 分段总结 {idx}\n\n{chunk_summary}")
            merge_prompt = (
                "请基于以下分段总结，合并为一份最终的结构化Markdown笔记，"
                "保持原有结构但去除重复。\n\n" + "\n\n".join(summaries)
            )
            final_messages = [{"role": "user", "content": merge_prompt}]
            summary = _call_llm(api_base_url, api_key, model, final_messages)
        else:
            prompt = prompt_template.replace("{transcript}", transcript)
            messages = [{"role": "user", "content": prompt}]
            summary = _call_llm(api_base_url, api_key, model, messages)
    except Exception as exc:
        return fail(500, f"笔记生成失败: {exc}")

    md_path = os.path.join(output_dir, "summary.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(summary)
    return ok(markdown_content=summary, file_path=md_path)
