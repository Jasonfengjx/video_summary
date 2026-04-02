# 🎬 视频自动总结笔记工具

一款面向知识型视频的自动化笔记生成工具，实现“输入链接 → 结构化笔记输出”的闭环。适合课程、讲座、教程、评测等长视频内容的快速回顾与复盘。

## ✨ 核心能力

- 🚀 **一键流程**：下载 → 音频抽取 → 转写 → 结构化总结 → 可选关键帧截图。
- 🧠 **结构化笔记**：输出 Markdown，包含概览、要点、洞察、行动建议等板块。
- ⏱️ **时间戳关联**：总结内容引导输出标准时间戳，便于回溯原片段。
- 🧩 **可配置**：通过 config.yaml 控制下载、ASR、LLM、截图与清理策略。
- 📦 **统一产物归档**：按 BV 号组织目录，避免文件冲突。

## 🧱 目录结构
产物统一存放在 downloads/ 下，以 BV 号隔离。

- meta.json：标题、作者、发布时间等元数据
- video.mp4：原视频（可选保留）
- audio.wav：音频中间产物（可选保留）
- transcript.json / transcript.srt：转写结果
- assets/：截图素材
- summary.md：最终笔记

## 🛠️ 依赖

- Python 3.9+
- ffmpeg
- yt-dlp
- Whisper（本地 ASR）
- LLM API（默认对接火山引擎兼容 OpenAI 协议）

## ⚙️ 配置说明
主配置文件在根目录 config.yaml：

- download：下载格式、代理、cookies、重试等
- audio：采样率、声道、输出格式
- asr：引擎、模型、语言、缓存策略
- llm：API 地址、模型名、Prompt 路径
- frames：是否截图、最大数量、格式
- cleanup：是否保留视频/音频

API Key 支持两种方式：

1) 环境变量（默认读取 DASHSCOPE_API_KEY，可在 config.yaml 中改名）
2) 根目录 cmd 文件中的最后一条 api 配置（便于本地测试）

## ▶️ 快速使用

1) 安装依赖：pip install -r requirements.txt
2) 准备 API Key（二选一）：
   - 方式 A：export DASHSCOPE_API_KEY=你的Key
   - 方式 B：在根目录 cmd 文件中配置最后一条 api
3) 运行：python src/main.py
4) 自定义参数（可选）：python src/main.py --url  --language zh --model deepseek-v3.2

说明：

- 未提供链接时会使用内置测试链接
- 支持手动指定链接、语言、模型、是否截图

输出完成后，summary.md 即为最终笔记。

## 🧩 关键帧截图说明

优先使用 ffmpeg 截图；若遇到 AV1 等解码问题，会自动回退到 OpenCV 读取视频帧。若仍失败，可在运行时关闭截图功能。

## 🧭 设计原则

- ✅ 结构化输出，强调可检索与复用
- ✅ 保留核心观点、流程步骤、关键术语
- ✅ 通过时间戳建立“总结 → 原片段”映射
- ❌ 避免无依据的模型幻觉

## 📈 适用场景

- 学习：课程、讲座、公开课
- 复盘：行业分享、产品发布
- 内容创作：灵感提炼、资料归档

## 🗺️ Roadmap

- 多 ASR 后端切换与热词支持
- 批量队列与并发处理
- GUI 或 Web 面板
- 笔记同步到 Notion / Obsidian

---

如需更强的总结风格定制，可直接修改 prompts/summary_prompt.txt。
