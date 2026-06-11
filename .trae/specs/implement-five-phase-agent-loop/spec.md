# 五阶段 Agent Loop 实现 Spec

## Why
AgentScope 内置的 Agent 类已经实现了 ReAct 循环（Reasoning-Acting），但用户希望基于 AgentScope 显式地实现一个完整的五阶段 Agent Loop（感知-推理-规划-行动-观察），使得每个阶段的职责清晰可见、可观测、可定制，便于理解和调试 Agent 的运行过程。

## What Changes
- 在 `MYCODE/` 目录下创建五阶段 Agent Loop 的完整实现
- 创建 `AgentLoop` 类，显式拆分五个阶段：Perceive / Reason / Plan / Act / Observe
- 利用 AgentScope 的 `Agent`、`Toolkit`、`FunctionTool`、`Msg`、`AgentState` 等核心组件作为底层支撑
- 通过 Middleware 机制将五阶段逻辑注入 Agent 的 ReAct 循环，使每个阶段可观测
- 提供一个可运行的 Demo 脚本，展示五阶段循环的完整工作流程

## Impact
- Affected specs: 无既有 spec 受影响（全新代码）
- Affected code: 仅新增 `MYCODE/` 目录下的文件，不修改 AgentScope 源码

## ADDED Requirements

### Requirement: 五阶段 AgentLoop 类
系统 SHALL 提供 `AgentLoop` 类，将 Agent 的运行循环显式拆分为五个阶段，每个阶段有明确的输入/输出和可观测的事件。

#### Scenario: 完整五阶段循环
- **WHEN** 用户向 AgentLoop 发送消息
- **THEN** AgentLoop 按顺序执行 Perceive → Reason → Plan → Act → Observe 五个阶段，并在每个阶段开始和结束时发出可观测的事件

#### Scenario: 无需工具调用的简单回答
- **WHEN** 模型推理后决定直接回答，无需调用工具
- **THEN** 跳过 Plan/Act/Observe 阶段，直接返回回答

#### Scenario: 多轮工具调用
- **WHEN** 模型推理后决定调用工具，且工具结果需要进一步处理
- **THEN** 执行完整五阶段循环，Observe 阶段结束后回到 Perceive 阶段，直到模型给出最终回答或达到最大迭代次数

### Requirement: Perceive 阶段 - 感知
系统 SHALL 在 Perceive 阶段完成以下工作：
- 接收用户输入消息
- 组装上下文：包括系统提示词、对话历史、压缩摘要、工具结果
- 将组装好的上下文传递给 Reason 阶段

#### Scenario: 上下文组装
- **WHEN** 进入 Perceive 阶段
- **THEN** 将 system_prompt + summary + context + 工具结果 组装为完整的消息列表，供模型使用

### Requirement: Reason 阶段 - 推理
系统 SHALL 在 Reason 阶段完成以下工作：
- 将 Perceive 阶段组装的上下文发送给大模型
- 接收模型的输出（文本回复或工具调用决策）
- 判断模型输出类型：直接回答 or 需要调用工具

#### Scenario: 模型决定直接回答
- **WHEN** 模型输出中不包含工具调用
- **THEN** 将模型回复作为最终回答返回，循环结束

#### Scenario: 模型决定调用工具
- **WHEN** 模型输出中包含工具调用
- **THEN** 进入 Plan 阶段

### Requirement: Plan 阶段 - 规划
系统 SHALL 在 Plan 阶段完成以下工作：
- 解析模型输出的工具调用列表
- 对工具调用进行批次规划：哪些可以并发执行，哪些必须顺序执行
- 将规划结果传递给 Act 阶段

#### Scenario: 并发工具调用规划
- **WHEN** 多个工具调用均为并发安全的（is_concurrency_safe=True）
- **THEN** 将这些工具调用规划为并发执行批次

#### Scenario: 顺序工具调用规划
- **WHEN** 存在非并发安全的工具调用
- **THEN** 将其规划为顺序执行批次

### Requirement: Act 阶段 - 行动
系统 SHALL 在 Act 阶段完成以下工作：
- 按照 Plan 阶段的规划执行工具调用
- 支持顺序执行和并发执行两种模式
- 收集每个工具调用的执行结果

#### Scenario: 工具执行成功
- **WHEN** 工具调用执行成功
- **THEN** 收集工具返回结果，进入 Observe 阶段

#### Scenario: 工具执行失败
- **WHEN** 工具调用执行失败
- **THEN** 将错误信息作为工具结果，进入 Observe 阶段

### Requirement: Observe 阶段 - 观察
系统 SHALL 在 Observe 阶段完成以下工作：
- 将工具执行结果注入上下文
- 更新 Agent 状态
- 回到 Perceive 阶段，开始下一轮循环

#### Scenario: 结果注入上下文
- **WHEN** 工具执行结果返回
- **THEN** 将结果以 ToolResultBlock 的形式追加到上下文中，然后回到 Perceive 阶段

### Requirement: 循环控制
系统 SHALL 提供循环控制机制：
- 最大迭代次数限制（默认 20）
- 达到最大迭代次数时，返回当前状态和提示信息

#### Scenario: 达到最大迭代次数
- **WHEN** 循环次数达到 max_iters
- **THEN** 停止循环，返回提示信息"已达到最大推理-行动循环次数"

### Requirement: 阶段可观测性
系统 SHALL 在每个阶段的入口和出口发出事件，便于外部观测和调试：
- `LoopStartEvent` — 整个循环开始
- `PhaseStartEvent` — 某阶段开始（携带阶段名称）
- `PhaseEndEvent` — 某阶段结束（携带阶段名称和摘要信息）
- `LoopEndEvent` — 整个循环结束

#### Scenario: 事件流输出
- **WHEN** AgentLoop 运行
- **THEN** 按顺序发出 LoopStart → PhaseStart(Perceive) → PhaseEnd(Perceive) → PhaseStart(Reason) → ... → LoopEnd 事件流

### Requirement: Demo 脚本
系统 SHALL 提供一个可运行的 Demo 脚本，展示五阶段 Agent Loop 的完整工作流程，包含两个贴近实际的场景：

#### 场景一：智能研究助手
模拟一个"技术调研助手"，需要多步工具调用来完成调研任务：
- 工具集：
  - `search_web(query)` — 模拟网络搜索，返回搜索结果摘要
  - `read_document(doc_name)` — 模拟读取文档，返回文档内容摘要
  - `summarize(text)` — 模拟文本摘要，返回关键要点
  - `compare(topic, source_a, source_b)` — 模拟对比分析，返回对比结论
- 问题示例："帮我调研 AgentScope 和 LangGraph 两个框架的异同，先搜索它们的基本信息，再读取相关文档，最后做一个对比分析"
- 预期循环流程：
  1. Perceive: 接收调研请求
  2. Reason: 模型决定先搜索两个框架
  3. Plan: 规划并发执行两次 search_web
  4. Act: 执行搜索
  5. Observe: 获取搜索结果
  6. Perceive: 组装搜索结果
  7. Reason: 模型决定读取文档
  8. Plan/Act/Observe: 读取文档
  9. Perceive: 组装文档内容
  10. Reason: 模型决定做对比分析
  11. Plan/Act/Observe: 执行对比
  12. Perceive: 组装对比结果
  13. Reason: 模型给出最终调研报告

#### 场景二：数据分析助手
模拟一个"数据分析助手"，需要多步计算和查询：
- 工具集：
  - `query_database(sql)` — 模拟数据库查询，返回查询结果
  - `calculate(expression)` — 执行数学计算
  - `generate_chart(data, chart_type)` — 模拟生成图表，返回图表描述
- 问题示例："查询华东区上季度的销售数据，计算同比增长率，并生成柱状图"
- 预期循环流程：
  1. 查询数据库 → 2. 计算增长率 → 3. 生成图表 → 4. 给出分析结论

#### Scenario: Demo 运行
- **WHEN** 运行 Demo 脚本
- **THEN** 可以清晰看到五阶段循环的执行过程，包括每个阶段的输入输出，且两个场景均可独立运行
