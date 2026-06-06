# 第 5 篇：多 GPU 部署 - 张量并行与流水线并行

当单个 GPU 显存不足以容纳大模型时，vLLM 提供了多种并行策略来充分利用多 GPU 资源。

---

## 1. 并行策略选择指南

| 策略 | 适用场景 | 优势 | 缺点 |
|------|----------|------|------|
| **张量并行 (TP)** | 单节点多 GPU | 通信开销小 | 要求 GPU 数量是 2 的幂 |
| **流水线并行 (PP)** | 多节点或不均匀显存 | 支持不均匀划分 | 复杂度较高 |
| **专家并行 (EP)** | MoE 模型 | 专门优化 MoE | 仅适用于 MoE |

---

## 2. 张量并行 (Tensor Parallelism)

### 2.1 单节点多 GPU 部署

```bash
# 2 张 GPU
vllm serve Qwen/Qwen2.5-32B-Instruct \
    --tensor-parallel-size 2 \
    --served-model-name qwen2.5-32b \
    --dtype bfloat16

# 4 张 GPU
vllm serve Qwen/Qwen2.5-72B-Instruct \
    --tensor-parallel-size 4 \
    --served-model-name qwen2.5-72b
```

### 2.2 Python API 使用

```python
from vllm import LLM

llm = LLM(
    model="Qwen/Qwen2.5-32B-Instruct",
    tensor_parallel_size=2,
    distributed_executor_backend="mp"  # 或 "ray"
)
```

---

## 3. 流水线并行 (Pipeline Parallelism)

```bash
# 2 个流水线阶段
vllm serve Qwen/Qwen2.5-72B-Instruct \
    --tensor-parallel-size 4 \
    --pipeline-parallel-size 2
```

---

## 4. 多节点部署（使用 Ray）

### 4.1 启动 Ray 集群

```bash
# 在主节点上
ray start --head --port=6379

# 在工作节点上
ray start --address="主节点IP:6379"
```

### 4.2 启动 vLLM

```bash
vllm serve Qwen/Qwen2.5-72B-Instruct \
    --tensor-parallel-size 4 \
    --pipeline-parallel-size 2 \
    --distributed-executor-backend ray
```

---

## 5. 不同硬件配置的并行方案

| GPU 配置 | 推荐方案 | 最大模型规模 |
|----------|----------|--------------|
| 1×A100 40G | 单卡 | 7B ~ 14B |
| 2×A100 40G | TP=2 | 32B |
| 4×A100 40G | TP=4 | 72B |
| 8×A100 40G | TP=4 + PP=2 | 100B+ |

---

## 下一篇

[第 6 篇：生产级部署 - Docker + Nginx + Prometheus + Grafana](./06_production_deployment.md)
