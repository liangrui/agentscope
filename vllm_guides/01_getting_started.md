# vLLM 入门指南：从安装到首次启动

vLLM 是一个高性能的大语言模型推理服务框架，以其出色的吞吐量和低延迟著称。本指南将带你从零基础开始，完成 vLLM 的安装、配置和首次启动。

---

## 1. 系统要求

在开始安装 vLLM 之前，确保你的系统满足以下基本要求：

| 要求项 | 详细说明 |
|--------|----------|
| 操作系统 | Linux（推荐 Ubuntu 22.04+），macOS 或 Windows（WSL2） |
| Python 版本 | 3.10 - 3.12（推荐 3.12） |
| GPU 要求 | NVIDIA CUDA 11.8+ 或 AMD ROCm 6.0+（GPU 不是强制要求，但性能会受影响） |
| 内存 | 16GB+（取决于模型大小） |
| 硬盘空间 | 至少 20GB（用于存放模型文件） |

---

## 2. 安装步骤

### 2.1 推荐使用 uv 进行安装（最快）

```bash
# 1. 安装 uv（如果尚未安装）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. 创建并激活虚拟环境
uv venv vllm-env --python 3.12
source vllm-env/bin/activate

# 3. 安装 vLLM（会自动安装 PyTorch 和 CUDA 依赖）
uv pip install vllm==0.18.0

# 4. 验证安装
python -c "import vllm; print(f'vLLM 版本: {vllm.__version__}')"
```

### 2.2 标准 pip 安装方式

```bash
# 创建并激活虚拟环境
python -m venv vllm-env
source vllm-env/bin/activate

# 安装 vLLM
pip install vllm==0.18.0
```

---

## 3. 你的第一个 vLLM 程序

我们将使用 Python API 来运行一个简单的文本生成任务：

```python
from vllm import LLM, SamplingParams

def main():
    # 1. 初始化模型（使用小模型进行测试）
    llm = LLM(
        model="Qwen/Qwen2.5-7B-Instruct",
        dtype="bfloat16",  # 使用 bfloat16 降低内存使用
        gpu_memory_utilization=0.9,  # 使用 90% 的 GPU 内存
    )

    # 2. 设置采样参数
    sampling_params = SamplingParams(
        temperature=0.7,
        top_p=0.9,
        max_tokens=512,
    )

    # 3. 生成文本
    prompts = [
        "什么是 vLLM？",
        "写一首关于 AI 的诗",
    ]

    outputs = llm.generate(prompts, sampling_params)

    # 4. 输出结果
    for output in outputs:
        prompt = output.prompt
        generated_text = output.outputs[0].text
        print(f"\n用户: {prompt}")
        print(f"\nAI: {generated_text}")
        print("=" * 60)

if __name__ == "__main__":
    main()
```

将上述代码保存为 `simple_demo.py` 并运行：

```bash
python simple_demo.py
```

---

## 4. 首次启动 API 服务器

vLLM 最常用的方式是作为 OpenAI 兼容的 API 服务器运行。

### 4.1 单 GPU 启动命令

```bash
vllm serve Qwen/Qwen2.5-7B-Instruct \
    --served-model-name qwen2.5-7b \
    --dtype bfloat16 \
    --max-model-len 8192 \
    --gpu-memory-utilization 0.9
```

### 4.2 测试 API 服务

服务启动后（默认监听在 `http://localhost:8000`），使用以下 Python 代码测试：

```python
from openai import OpenAI

# 连接到本地 vLLM 服务器
client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="dummy",  # vLLM 不需要真实 API key
)

# 发送请求
completion = client.chat.completions.create(
    model="qwen2.5-7b",
    messages=[
        {"role": "user", "content": "你好，vLLM！"},
    ],
    temperature=0.7,
    max_tokens=256,
)

print(completion.choices[0].message.content)
```

---

## 5. 常用启动参数速查表

| 参数名 | 说明 | 示例 |
|--------|------|------|
| `--model` | 模型名称或路径 | `Qwen/Qwen2.5-7B-Instruct` |
| `--served-model-name` | API 中显示的模型名 | `qwen2.5-7b` |
| `--dtype` | 数据类型（可选：float16, bfloat16, float32） | `bfloat16` |
| `--max-model-len` | 最大上下文长度 | `8192` |
| `--gpu-memory-utilization` | GPU 内存利用率（0.0 ~ 1.0） | `0.9` |
| `--tensor-parallel-size` | 张量并行大小（多 GPU 部署用） | `2` |
| `--host` | 服务绑定地址 | `0.0.0.0` |
| `--port` | 服务端口 | `8000` |
| `--quantization` | 量化方案（可选：awq, gptq, gguf） | `awq` |

---

## 6. 常见问题排查

### 6.1 显存不足（Out of Memory）

如果遇到显存不足错误，可以：
1. 减小 `gpu-memory-utilization`
2. 使用更小的模型
3. 启用量化
4. 减少 `max-model-len`

### 6.2 模型下载缓慢

可以使用国内镜像：
```bash
export HF_ENDPOINT=https://hf-mirror.com
vllm serve ...
```

---

## 下一篇

[第 2 篇：OpenAI 兼容 API 服务部署与使用](./02_openai_api.md)
