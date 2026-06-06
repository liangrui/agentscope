# 第 6 篇：生产级部署 - Docker + Nginx + Prometheus + Grafana

在生产环境中部署 vLLM 需要考虑高可用、监控、安全等多个方面。本文将介绍完整的生产部署方案。

---

## 1. Docker 部署

### 1.1 创建 Dockerfile

```dockerfile
FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04

WORKDIR /app

# 安装 Python
RUN apt-get update && apt-get install -y python3.10 python3-pip python3.10-venv git

# 创建虚拟环境
RUN python3.10 -m venv /venv
ENV PATH="/venv/bin:$PATH"

# 安装 vLLM
RUN pip install --no-cache-dir vllm==0.18.0

# 启动命令
CMD ["vllm", "serve", "Qwen/Qwen2.5-7B-Instruct", \
     "--served-model-name", "qwen2.5-7b", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "-O2"]
```

### 1.2 使用官方镜像

```bash
# 拉取官方镜像
docker pull vllm/vllm-openai:latest

# 运行容器
docker run -d --gpus all \
    -p 8000:8000 \
    -v /path/to/models:/models \
    -e HF_ENDPOINT=https://hf-mirror.com \
    vllm/vllm-openai:latest \
    --model /models/Qwen2.5-7B-Instruct \
    --served-model-name qwen2.5-7b
```

### 1.3 Docker Compose 配置

```yaml
version: '3.8'

services:
  vllm:
    image: vllm/vllm-openai:latest
    container_name: vllm-server
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    ports:
      - "8000:8000"
    volumes:
      - ./models:/models
    environment:
      - HF_ENDPOINT=https://hf-mirror.com
    command: >
      --model /models/Qwen2.5-7B-Instruct
      --served-model-name qwen2.5-7b
      -O2
    restart: unless-stopped
```

---

## 2. Nginx 反向代理与负载均衡

### 2.1 基础反向代理配置

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        
        # 流式输出需要的配置
        proxy_buffering off;
        proxy_cache off;
        proxy_set_header Connection '';
        proxy_http_version 1.1;
        chunked_transfer_encoding off;
    }
}
```

### 2.2 添加 SSL（Let's Encrypt）

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_buffering off;
    }
}
```

---

## 3. Prometheus + Grafana 监控

### 3.1 prometheus.yml 配置

```yaml
scrape_configs:
  - job_name: 'vllm'
    static_configs:
      - targets: ['vllm-server:8000']
    metrics_path: '/metrics'
    scrape_interval: 15s
```

### 3.2 Docker Compose 完整监控栈

```yaml
version: '3.8'

services:
  vllm:
    # ... 同前文 ...

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=your-password
    volumes:
      - grafana-storage:/var/lib/grafana

volumes:
  grafana-storage:
```

---

## 4. 使用 systemd 管理服务

### 4.1 创建服务文件 /etc/systemd/system/vllm.service

```ini
[Unit]
Description=vLLM Inference Server
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/project
ExecStart=/path/to/venv/bin/vllm serve Qwen/Qwen2.5-7B-Instruct -O2
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 4.2 启动服务

```bash
sudo systemctl daemon-reload
sudo systemctl enable vllm
sudo systemctl start vllm
sudo systemctl status vllm
```

---

## 下一篇

[第 7 篇：高级特性 - 投机解码与前缀缓存](./07_advanced_features.md)
