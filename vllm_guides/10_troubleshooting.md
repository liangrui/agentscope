# 第 10 篇：问题排查与最佳实践

在使用 vLLM 过程中可能会遇到各种问题，本文汇总了常见问题和解决方案，以及生产环境中的最佳实践。

---

## 1. 常见问题与解决方案

### 1.1 显存不足 (OOM)

**症状：** `CUDA out of memory` 错误

**解决方案：**
```bash
# 1. 减小 GPU 内存利用率
--gpu-memory-utilization 0.85

# 2. 使用量化
--quantization awq

# 3. 减小最大上下文长度
--max-model-len 4096

# 4. 减小最大批处理大小
--max-num-batched-tokens 4096

# 5. 使用多 GPU 张量并行
--tensor-parallel-size 2
```

### 1.2 预填充阶段慢

**症状：** 长输入时首 Token 延迟高

**解决方案：**
```bash
# 启用分块预填充
--enable-chunked-prefill
--max-num-batched-tokens 4096
```

### 1.3 频繁发生抢占 (Preemption)

**症状：** 日志中出现大量 "Sequence group preempted"

**解决方案：**
```bash
# 1. 增加 KV 缓存空间
--gpu-memory-utilization 0.95

# 2. 减少并发数
--max-num-seqs 128

# 3. 启用前缀缓存（如果适用）
--enable-prefix-caching
```

### 1.4 模型下载失败或慢

**症状：** HuggingFace 下载超时或速度慢

**解决方案：**
```bash
# 使用镜像站
export HF_ENDPOINT=https://hf-mirror.com

# 或使用 huggingface-cli 预先下载
huggingface-cli download Qwen/Qwen2.5-7B-Instruct --local-dir ./model
```

### 1.5 NCCL 错误（多 GPU）

**症状：** 多 GPU 启动时报错

**解决方案：**
```bash
# 设置 NCCL 环境变量
export NCCL_P2P_DISABLE=1
export NCCL_IB_DISABLE=1
export NCCL_SOCKET_IFNAME=eth0
```

---

## 2. 性能调优检查清单

| 项目 | 说明 |
|------|------|
| ✅ 优化级别 | 生产环境使用 `-O2` |
| ✅ Attention Backend | 根据硬件选择 `flash_attn_4` 或 `flash_attn_2` |
| ✅ 性能模式 | 对话场景用 `--performance-mode interactivity` |
| ✅ 前缀缓存 | RAG/多轮对话场景启用 |
| ✅ 量化 | 显存不足时使用 AWQ |

---

## 3. 生产环境最佳实践

### 3.1 版本锁定

```bash
# 安装指定版本，不要使用 latest
pip install vllm==0.18.0
```

### 3.2 健康检查与自动重启

```bash
# 健康检查脚本
#!/bin/bash
if ! curl -f http://localhost:8000/health; then
    echo "vLLM is unhealthy, restarting..."
    systemctl restart vllm
fi
```

### 3.3 日志收集

```bash
# 启动时重定向日志
vllm serve ... 2>&1 | tee -a /var/log/vllm.log
```

---

## 4. 相关资源

- vLLM 官方文档：https://docs.vllm.ai
- GitHub 仓库：https://github.com/vllm-project/vllm
- 性能基准测试：https://github.com/vllm-project/vllm/tree/main/benchmarks

---

## 总结

恭喜你完成了本系列从入门到精通的全部 10 篇指南！现在你应该已经掌握了：

1. ✅ vLLM 的基础安装和使用
2. ✅ OpenAI 兼容 API 服务部署
3. ✅ 各种量化方案的选择
4. ✅ 从 -O0 到 -O3 的性能优化
5. ✅ 多 GPU 并行部署策略
6. ✅ 生产级 Docker/Nginx/监控部署
7. ✅ 投机解码、前缀缓存等高级特性
8. ✅ 多模态模型部署
9. ✅ 原生 Python 编程接口深度使用
10. ✅ 问题排查和最佳实践

祝你在使用 vLLM 的过程中顺利！
