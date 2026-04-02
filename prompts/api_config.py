# 百炼云大模型API调用配置
API_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
API_KEY = "sk-ea6e1bd229624f5084786e810a186aa7"
MODEL = "qwen3.5-27b"

'''
curl -X POST "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions" \
  -H "Authorization: Bearer sk-ea6e1bd229624f5084786e810a186aa7" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3.5-27b",
    "messages": [
      {"role": "user", "content": "你是谁？"}
    ]
  }'
'''