# 第 3 篇：模型选择与量化方案

选择合适的模型和量化方案是发挥 vLLM 性能的关键。本文将介绍常见的量化方案和如何根据硬件选择最佳配置。

---

## 1. 常见量化方案对比

| 方案 | 描述 | 显存节省 | 性能损失 | 适用场景 |
|------|------|----------|----------|----------|
| **无量化 (BF16/FP16)** | 原始精度 | 0% | 0% | 追求精度、显存充足 |
| **AWQ** | 激活感知权重量化 | 75% | < 1% | 生产环境、兼顾精度和速度 |
| **GPTQ** | 梯度后量化 | 75% | ~1-2% | 开源生态好、量化模型多 |
| **GGUF** | llama.cpp 量化格式 | 50-80% | 低 | CPU 推理或兼容 llama.cpp |
| **FP8** | 8 位浮点数 | 50% | 极低 | H100/Blackwell 硬件原生支持 |

---

## 2. AWQ 量化使用

### 2.1 使用预量化模型

```bash
# 从 Hugging Face 下载 AWQ 量化模型并启动
vllm serve Qwen/Qwen2.5-7B-Instruct-AWQ \
    --served-model-name qwen2.5-7b-awq \
    --quantization awq \
    --dtype half
```

### 2.2 自定义量化模型

```python
from vllm.model_executor.layers.quantization.awq import AWQConfig

# 或使用 AutoAWQ 进行量化
# 安装: pip install autoawq
```

---

## 3. GPTQ 量化使用

```bash
vllm serve TheBloke/Qwen2.5-7B-Instruct-GPTQ \
    --served-model-name qwen2.5-7b-gptq \
    --quantization gptq \
    --dtype float16
```

---

## 4. 不同硬件的推荐配置

### 4.1 消费级显卡（RTX 3090/4090）

| 显存 | 推荐模型配置 | 量化方案 | 上下文长度 |
|------|--------------|----------|------------|
| 24GB | Qwen2.5-7B | AWQ/GPTQ | 8192 |
| 24GB | Qwen2.5-14B | AWQ/GPTQ | 4096 |

启动示例：
```bash
vllm serve Qwen/Qwen2.5-7B-Instruct-AWQ \
    --served-model-name qwen2.5-7b \
    --quantization awq \
    --max-model-len 8192 \
    --gpu-memory-utilization 0.9
```

### 4.2 数据中心显卡（A100/H100）

| 显存 | 推荐模型配置 | 量化方案 | 上下文长度 |
|------|--------------|----------|------------|
| 40GB (A100) | Qwen2.5-32B | BF16 | 8192 |
| 80GB (A100/H100) | Qwen2.5-72B | BF16/FP8 | 8192 |

H100 推荐配置（启用 FP8）：
```bash
vllm serve Qwen/Qwen2.5-72B-Instruct \
    --served-model-name qwen2.5-72b \
    --dtype fp8_e5m2
```

---

## 5. 如何选择模型

| 应用场景 | 推荐模型规模 | 特点 |
|----------|--------------|------|
| 实时对话、客服 | 7B ~ 14B | 低延迟，快速响应 |
| 文档问答、RAG | 14B ~ 32B | 平衡速度和理解能力 |
| 复杂推理、代码 | 32B ~ 72B | 更强的逻辑能力 |
| 批量处理 | 任意 | 吞吐量优先 |

---

## 下一篇

[第 4 篇：性能优化 - 从 -O0 到 -O3](./04_performance_optimization.md)
