# Tasks

- [x] Task 1: 创建 MYCODE 目录结构和基础文件
  - [x] SubTask 1.1: 创建 MYCODE/ 目录
  - [x] SubTask 1.2: 创建 MYCODE/__init__.py

- [x] Task 2: 实现五阶段事件类型（MYCODE/events.py）
  - [x] SubTask 2.1: 定义 LoopStartEvent / LoopEndEvent
  - [x] SubTask 2.2: 定义 PhaseStartEvent / PhaseEndEvent（携带阶段名称：perceive / reason / plan / act / observe）

- [x] Task 3: 实现 AgentLoop 核心类（MYCODE/agent_loop.py）
  - [x] SubTask 3.1: 实现 __init__，接收 AgentScope Agent 实例和 max_iters 参数
  - [x] SubTask 3.2: 实现 perceive() 方法 — 组装上下文（system_prompt + summary + context + 工具结果）
  - [x] SubTask 3.3: 实现 reason() 方法 — 调用模型推理，判断输出类型
  - [x] SubTask 3.4: 实现 plan() 方法 — 解析工具调用，规划执行批次（并发/顺序）
  - [x] SubTask 3.5: 实现 act() 方法 — 执行工具调用，收集结果
  - [x] SubTask 3.6: 实现 observe() 方法 — 将工具结果注入上下文
  - [x] SubTask 3.7: 实现 run() 主循环方法 — 串联五阶段，发出事件流，处理循环控制

- [x] Task 4: 实现智能研究助手 Demo（MYCODE/demo_research.py）
  - [x] SubTask 4.1: 配置自部署大模型（OpenAI 兼容 API）
  - [x] SubTask 4.2: 注册工具函数：search_web / read_document / summarize / compare
  - [x] SubTask 4.3: 创建 AgentLoop 实例，发送调研问题
  - [x] SubTask 4.4: 打印每个阶段的执行过程和结果

- [x] Task 5: 实现数据分析助手 Demo（MYCODE/demo_analytics.py）
  - [x] SubTask 5.1: 配置自部署大模型（OpenAI 兼容 API）
  - [x] SubTask 5.2: 注册工具函数：query_database / calculate / generate_chart
  - [x] SubTask 5.3: 创建 AgentLoop 实例，发送数据分析问题
  - [x] SubTask 5.4: 打印每个阶段的执行过程和结果

# Task Dependencies
- [Task 2] depends on [Task 1]
- [Task 3] depends on [Task 1, Task 2]
- [Task 4] depends on [Task 3]
- [Task 5] depends on [Task 3]
