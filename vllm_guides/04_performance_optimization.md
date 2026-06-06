# 第 4 篇：性能优化 - 从 -O0 到 -O3

vLLM 0.17+ 提供了全新的优化级别系统，让你可以快速在启动时间和推理性能之间找到平衡。

---

## 1. 优化级别详解

| 级别 | 启动时间 | 优化内容 | 适用场景 |
|------|----------|----------|----------|
| `-O0` | 最快 | 无优化、无 CUDA Graph | 开发调试 |
| `-O1` | 快 | 基础融合、分段 CUDA Graph | 快速原型 |
| `-O2` | 中等 | 高级融合、全量 CUDA Graph | **生产推荐** |
| `-O3` | 最慢 | 实验性激进优化 | 追求极致性能 |

### 1.1 使用方式

```bash
# 生产环境推荐 -O2
vllm serve Qwen/Qwen2.5-7B-Instruct -O2

# 或通过环境变量
VLLM_OPTIMIZATION_LEVEL=2 vllm serve ...
```

---

## 2. Attention Backend 选择

| Backend | 硬件要求 | 特性 |
|---------|----------|------|
| `flash_attn_4` | H100/H200/RTX 40xx | 最快 |
| `flash_attn_2` | A100/RTX 30xx+ | 稳定可靠 |
| `xformers` | 通用 | 兼容性好 |
| `sdpa` | PyTorch 原生 | 无额外依赖 |

```bash
# 显式指定
vllm serve ... --attention-backend flash_attn_4

# 环境变量
export VLLM_ATTENTION_BACKEND=FLASH_ATTN_4
```

---

## 3. 调度策略与并发控制

### 3.1 关键参数

```bash
vllm serve Qwen/Qwen2.5-7B-Instruct \
    --max-num-seqs 256 \          # 最大并发序列数
    --max-num-batched-tokens 8192 \ # 最大批处理 Token 数
    --scheduling-policy fcfs  # 调度策略：fcfs/lifo
```

### 3.2 调度策略对比

| 策略 | 说明 | 适用场景 |
|------|------|----------|
| `fcfs` | 先来先服务（默认） | 公平性重要 |
| `lifo` | 后来先服务 | 追求吞吐量 |

---

## 4. 显存优化技巧

### 4.1 增加 GPU 内存利用率

```bash
# 安全值通常在 0.9-0.95 之间
vllm serve ... --gpu-memory-utilization 0.92
```

### 4.2 启用前缀缓存（Prefix Caching）

```bash
vllm serve ... --enable-prefix-caching
```

适合 RAG、多轮对话等有重复前缀的场景。

---

## 5. 性能监控与调试

### 5.1 查看 Prometheus 指标

```bash
# 访问指标端点
curl http://localhost:8000/metrics
```

关键指标：
- `vllm:num_requests_running` - 正在运行的请求数
- `vllm:gpu_cache_usage_percentage` - KV Cache 使用率
- `vllm:avg_generation_throughput_tokens_per_second` - 平均生成吞吐量

---

## 下一篇

[第 5 篇：多 GPU 部署 - 张量并行与流水线并行](./05_multi_gpu.md)
