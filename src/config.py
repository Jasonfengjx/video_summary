import os
from typing import Any, Dict, Optional
import re

import yaml


def _project_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _default_config() -> Dict[str, Any]:
    return {
        "app": {
            "output_root": "downloads",
            "logs_dir": "logs",
            "temp_dir": "temp",
            "log_level": "INFO",
        },
        "download": {
            "format": "bestvideo+bestaudio/best",
            "merge_output_format": "mp4",
            "cookies": "",
            "proxy": "",
            "retries": 3,
            "backoff_seconds": 2,
            "continue": True,
            "p_number": None,
        },
        "audio": {
            "format": "wav",
            "sample_rate": 16000,
            "channels": 1,
            "keep_audio": False,
        },
        "asr": {
            "engine": "whisper",
            "model": "base",
            "language": "auto",
            "save_srt": True,
            "save_json": True,
            "use_cache": True,
        },
        # "llm": {
        #     "provider": "dashscope",
        #     "api_base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        #     "api_key_env": "DASHSCOPE_API_KEY",
        #     "model": "qwen3.5-27b",
        #     "prompt_path": "prompts/summary_prompt.txt",
        #     "chunk": {
        #         "enabled": True,
        #         "max_chars": 12000,
        #         "overlap": 500,
        #     },
        # },
        "llm": {
            "provider": "dashscope",
            "api_base_url": "https://ark.cn-beijing.volces.com/api/coding/v3",
            "api_key_env": "DASHSCOPE_API_KEY",
            "model": "deepseek-v3.2",
            "prompt_path": "prompts/summary_prompt.txt",
            "chunk": {
                "enabled": True,
                "max_chars": 12000,
                "overlap": 500,
            },
        },
        "frames": {
            "enabled": True,
            "max_frames": 8,
            "image_format": "jpg",
            "quality": 2,
        },
        "cleanup": {
            "keep_video": False,
            "keep_audio": False,
        },
    }


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            base[key] = _deep_merge(base[key], value)
        else:
            base[key] = value
    return base


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    config = _default_config()
    root = _project_root()
    candidate_path = config_path or os.path.join(root, "config.yaml")
    if os.path.exists(candidate_path):
        with open(candidate_path, "r", encoding="utf-8") as f:
            loaded = yaml.safe_load(f) or {}
        if not isinstance(loaded, dict):
            raise ValueError("config.yaml 结构不正确，必须是字典")
        config = _deep_merge(config, loaded)
    config["_project_root"] = root
    return config


def resolve_path(config: Dict[str, Any], path_value: str) -> str:
    if not path_value:
        return path_value
    if os.path.isabs(path_value):
        return path_value
    return os.path.abspath(os.path.join(config["_project_root"], path_value))


def load_api_key_from_cmd(project_root: str) -> Optional[str]:
    cmd_path = os.path.join(project_root, "cmd")
    if not os.path.exists(cmd_path):
        return None
    try:
        with open(cmd_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception:
        return None
    matches = re.findall(r"api\s*[:：]\s*(\S+)", content)
    if not matches:
        return None
    return matches[-1]
