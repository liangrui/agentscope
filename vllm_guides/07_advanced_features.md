# 第 7 篇：高级特性 - 投机解码与前缀缓存

vLLM 内置了多种高级特性，可以显著提升特定场景下的性能。

---

## 1. 投机解码（Speculative Decoding）

投机解码使用一个小的"草稿"模型快速生成 Token，然后由目标模型并行验证，从而加速推理。

### 1.1 启用投机解码

```bash
vllm serve Qwen/Qwen2.5-72B-Instruct \
    --served-model-name qwen2.5-72b \
    --speculative-model Qwen/Qwen2.5-1.8B-Instruct \
    --num-speculative-tokens 5
```

### 1.2 关键参数

| 参数 | 说明 | 推荐值 |
|------|------|--------|
| `--speculative-model` | 草稿模型路径 | 目标模型的 ~1/10 大小 |
| `--num-speculative-tokens` | 每次投机生成的 Token 数 | 3-10 |

---

## 2. 前缀缓存（Prefix Caching）

对于 RAG、多轮对话等有大量重复前缀的场景，前缀缓存可以大幅减少重复计算。

### 2.1 启用前缀缓存

```bash
vllm serve Qwen/Qwen2.5-7B-Instruct \
    --enable-prefix-caching \
    --prefix-cache-size 4096
```

### 2.2 适用场景

- RAG 系统（通常有相同的系统提示词）
- 多轮对话（上下文重复）
- 批量相似任务

---

## 3. Chunked Prefill

对于超长上下文，分块预填充可以平衡内存使用和延迟。

```bash
vllm serve Qwen/Qwen2.5-7B-Instruct \
    --enable-chunked-prefill \
    --max-num-batched-tokens 4096
```

---

## 4. 多模态模型支持

vLLM 支持视觉-语言模型，如 Qwen-VL、Llava 等。

```bash
vllm serve Qwen/Qwen2-VL-7B-Instruct \
    --served-model-name qwen2-vl-7b \
    --max-model-len 8192
```

使用示例（OpenAI API 格式）：
```python
import base64
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8000/v1", api_key="dummy")

# 读取图片并编码
with open("image.jpg", "rb") as f:
    img_base64 = base64.b64encode(f.read()).decode()

response = client.chat.completions.create(
    model="qwen2-vl-7b",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "这张图片里有什么？"},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"}}
        ]
    }]
)
```

---

## 下一篇

[第 8 篇：多模态模型部署](./08_multimodal.md)
