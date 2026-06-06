# vLLM 使用指南：从入门到精通

本系列共 10 篇指南，覆盖 vLLM 从基础安装到生产级部署的完整知识体系。

---

## 目录

| 序号 | 标题 | 简介 |
|------|------|------|
| 1 | [vLLM 入门指南：从安装到首次启动](./01_getting_started.md) | 基础安装、你的第一个程序、启动 API 服务 |
| 2 | [OpenAI 兼容 API 服务部署与使用](./02_openai_api.md) | API 服务、函数调用、与现有框架集成 |
| 3 | [模型选择与量化方案](./03_quantization.md) | AWQ、GPTQ、GGUF、FP8 量化方案对比 |
| 4 | [性能优化：从 -O0 到 -O3](./04_performance_optimization.md) | 优化级别、Attention Backend、缓存配置 |
| 5 | [多 GPU 部署：张量并行与流水线并行](./05_multi_gpu.md) | TP、PP、多节点 Ray 部署 |
| 6 | [生产级部署：Docker + Nginx + Prometheus + Grafana](./06_production_deployment.md) | 容器化、监控、高可用 |
| 7 | [高级特性：投机解码与前缀缓存](./07_advanced_features.md) | 投机解码、前缀缓存、分块预填充 |
| 8 | [多模态模型部署](./08_multimodal.md) | Qwen-VL、LLaVA 部署，多图/视频输入 |
| 9 | [vLLM 编程接口深度使用](./09_programming_api.md) | 原生 Python API、批量处理、流式生成 |
| 10 | [问题排查与最佳实践](./10_troubleshooting.md) | 常见问题、性能调优清单 |

---

## 快速开始

```bash
# 推荐使用 uv 安装
curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv vllm-env --python 3.12
source vllm-env/bin/activate
uv pip install vllm==0.18.0

# 启动服务
vllm serve Qwen/Qwen2.5-7B-Instruct -O2
```

---

## 适用版本

本指南基于 vLLM 0.18.0 版本编写，部分特性可能在更早或更晚的版本中有所差异。

---

## 许可证

本系列指南采用 CC BY-SA 4.0 许可证。
