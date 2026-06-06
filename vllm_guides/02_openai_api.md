# 第 2 篇：OpenAI 兼容 API 服务部署与使用

vLLM 的一大优势是提供完全兼容 OpenAI API 的接口，这意味着你可以直接替换现有代码中的 `base_url`，而无需做太多修改。

---

## 1. 启动 API 服务器

### 1.1 基础启动命令

```bash
vllm serve Qwen/Qwen2.5-7B-Instruct \
    --served-model-name qwen2.5-7b \
    --host 0.0.0.0 \
    --port 8000
```

### 1.2 使用 --performance-mode（推荐）

vLLM 0.18+ 提供了性能模式预设，无需手动调参：

| 模式 | 用途 | 优化方向 |
|------|------|----------|
| `balanced`（默认） | 混合流量 | 延迟/吞吐量均衡 |
| `interactivity` | 实时对话 | 最小化 TTFT（首 Token 延迟） |
| `throughput` | 批处理 | 最大化 tokens/s |

```bash
# 聊天机器人场景
vllm serve Qwen/Qwen2.5-7B-Instruct \
    --served-model-name qwen2.5-7b \
    --performance-mode interactivity

# 批量文档处理
vllm serve Qwen/Qwen2.5-7B-Instruct \
    --served-model-name qwen2.5-7b \
    --performance-mode throughput
```

---

## 2. API 使用指南

### 2.1 使用 OpenAI Python 库

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="dummy"
)

# 聊天补全
response = client.chat.completions.create(
    model="qwen2.5-7b",
    messages=[
        {"role": "system", "content": "你是一个友好的AI助手"},
        {"role": "user", "content": "你好！"},
    ],
    temperature=0.7,
    max_tokens=512,
    stream=True  # 流式输出
)

# 处理流式响应
for chunk in response:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

### 2.2 原生 HTTP 请求（使用 curl）

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{
        "model": "qwen2.5-7b",
        "messages": [
            {"role": "user", "content": "什么是 AI？"}
        ],
        "temperature": 0.7,
        "max_tokens": 256,
        "stream": true
    }'
```

### 2.3 多模型服务（路由模式）

vLLM 可以同时服务多个模型，通过 API 路由：

```python
from vllm.entrypoints.openai.api_server import run_server

# 命令行方式
vllm serve \
    --model Qwen/Qwen2.5-7B-Instruct \
    --model Qwen/Qwen2.5-14B-Instruct \
    --served-model-name qwen2.5-7b,qwen2.5-14b
```

---

## 3. 高级 API 特性

### 3.1 函数调用（Function Calling）

```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8000/v1", api_key="dummy")

# 定义工具
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "获取城市天气",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "城市名称"}
                },
                "required": ["city"]
            }
        }
    }
]

# 发送请求
response = client.chat.completions.create(
    model="qwen2.5-7b",
    messages=[{"role": "user", "content": "北京今天天气怎么样？"}],
    tools=tools,
    tool_choice="auto"
)
```

### 3.2 结构化输出（JSON Schema）

```python
from pydantic import BaseModel

class Response(BaseModel):
    answer: str
    confidence: float
    sources: list[str]

response = client.chat.completions.create(
    model="qwen2.5-7b",
    messages=[{"role": "user", "content": "简单介绍 Python"}],
    response_format={"type": "json_object"}
)
```

---

## 4. 与现有项目集成

### 4.1 LangChain 集成

```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    base_url="http://localhost:8000/v1",
    model="qwen2.5-7b",
    api_key="dummy"
)

result = llm.invoke("你好！")
print(result.content)
```

### 4.2 LlamaIndex 集成

```python
from llama_index.llms.openai import OpenAI

llm = OpenAI(
    base_url="http://localhost:8000/v1",
    model="qwen2.5-7b",
    api_key="dummy"
)

response = llm.complete("介绍一下 vLLM")
print(response)
```

---

## 5. API 端点参考

vLLM 实现了以下 OpenAI 兼容端点：

| 端点 | 功能 |
|------|------|
| `/v1/chat/completions` | 聊天补全 |
| `/v1/completions` | 文本补全（旧版） |
| `/v1/models` | 列出可用模型 |
| `/v1/embeddings` | 生成嵌入向量（需要嵌入模型） |
| `/health` | 健康检查 |
| `/metrics` | Prometheus 指标 |

---

## 下一篇

[第 3 篇：模型选择与量化方案](./03_quantization.md)
