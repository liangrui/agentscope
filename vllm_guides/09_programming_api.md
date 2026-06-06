# 第 9 篇：vLLM 编程接口深度使用

除了 OpenAI 兼容 API，vLLM 还提供了强大的原生 Python 接口，可以实现更精细的控制和集成。

---

## 1. 基础 LLM 类使用

### 1.1 批量生成

```python
from vllm import LLM, SamplingParams

llm = LLM(
    model="Qwen/Qwen2.5-7B-Instruct",
    dtype="bfloat16",
    tensor_parallel_size=1
)

prompts = [
    "你好，世界！",
    "写一首关于秋天的诗",
    "什么是机器学习？"
]

sampling_params = SamplingParams(
    temperature=0.7,
    top_p=0.9,
    max_tokens=512,
    n=2  # 每个提示生成 2 个结果
)

outputs = llm.generate(prompts, sampling_params)

for output in outputs:
    prompt = output.prompt
    generated = [o.text for o in output.outputs]
    print(f"Prompt: {prompt}")
    for i, text in enumerate(generated):
        print(f"Response {i+1}: {text}")
    print("=" * 60)
```

---

## 2. 流式生成

```python
from vllm import LLM, SamplingParams
from vllm.outputs import RequestOutput

llm = LLM("Qwen/Qwen2.5-7B-Instruct")

sampling_params = SamplingParams(max_tokens=256)

for output in llm.generate(
    "写一个 Python 快速排序的函数",
    sampling_params,
    stream=True
):
    print(output.outputs[0].text, end="", flush=True)
```

---

## 3. 自定义停止条件

```python
sampling_params = SamplingParams(
    stop=["\n", "总结："],  # 遇到这些字符串停止
    stop_token_ids=[1234],  # 或遇到特定 token ID 停止
    include_stop_str_in_output=False
)
```

---

## 4. Logits 处理与引导

```python
from vllm import LogitsProcessor

class MyLogitsProcessor(LogitsProcessor):
    def __call__(self, input_ids, logits):
        # 自定义 logits 处理逻辑
        logits[0, 1234] = -float('inf')  # 禁用某个 token
        return logits

sampling_params = SamplingParams(
    logits_processors=[MyLogitsProcessor()]
)
```

---

## 5. 使用 AsyncLLMEngine 构建高性能服务

```python
import asyncio
from vllm import AsyncLLMEngine, SamplingParams

engine = AsyncLLMEngine.from_engine_args(
    model="Qwen/Qwen2.5-7B-Instruct",
    dtype="bfloat16"
)

async def generate_text(prompt, request_id):
    sampling_params = SamplingParams(max_tokens=256)
    async for output in engine.generate(prompt, sampling_params, request_id):
        print(output.outputs[0].text, end="", flush=True)

async def main():
    await asyncio.gather(
        generate_text("你好！", "req1"),
        generate_text("写首诗", "req2")
    )

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 下一篇

[第 10 篇：问题排查与最佳实践](./10_troubleshooting.md)
