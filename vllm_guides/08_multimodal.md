# 第 8 篇：多模态模型部署

vLLM 提供了完善的多模态（视觉-语言）模型支持，可以高效处理图像+文本的多模态任务。

---

## 1. 支持的多模态模型

| 模型系列 | 示例 | 特点 |
|----------|------|------|
| Qwen-VL | Qwen/Qwen2-VL-7B-Instruct | 中文能力强、功能全面 |
| LLaVA | liuhaotian/llava-v1.6-vicuna-7b | 开源生态好 |
| InternVL | OpenGVLab/InternVL2-8B | 视觉理解强 |
| Pixtral | mistralai/Pixtral-12B-2409 | 多语言支持好 |

---

## 2. 部署 Qwen2-VL

### 2.1 基础启动命令

```bash
vllm serve Qwen/Qwen2-VL-7B-Instruct \
    --served-model-name qwen2-vl-7b \
    --max-model-len 8192 \
    --gpu-memory-utilization 0.9
```

### 2.2 多图像输入

```python
from openai import OpenAI
import base64

client = OpenAI(base_url="http://localhost:8000/v1", api_key="dummy")

def encode_image(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

img1 = encode_image("image1.jpg")
img2 = encode_image("image2.jpg")

response = client.chat.completions.create(
    model="qwen2-vl-7b",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "对比这两张图"},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img1}"}},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img2}"}}
        ]
    }]
)
```

---

## 3. 多模态缓存优化

```bash
vllm serve Qwen/Qwen2-VL-7B-Instruct \
    --enable-multimodal-cache
```

---

## 4. 视频输入处理

对于视频输入，可以采样关键帧，然后多图输入：

```python
import cv2

def sample_frames(video_path, num_frames=8):
    cap = cv2.VideoCapture(video_path)
    frames = []
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    interval = max(1, total // num_frames)
    for i in range(0, total, interval):
        cap.set(cv2.CAP_PROP_POS_FRAMES, i)
        ret, frame = cap.read()
        if ret:
            _, buffer = cv2.imencode('.jpg', frame)
            frames.append(base64.b64encode(buffer).decode())
    cap.release()
    return frames

# 使用采样的帧
frames = sample_frames("video.mp4")
content = [{"type": "text", "text": "描述这个视频"}]
for frame in frames:
    content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{frame}"}})
```

---

## 下一篇

[第 9 篇：vLLM 编程接口深度使用](./09_programming_api.md)
