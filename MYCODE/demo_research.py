# -*- coding: utf-8 -*-
"""智能研究助手 Demo — 展示五阶段 Agent Loop 的完整工作流程。

场景：技术调研助手，需要多步工具调用来完成调研任务。
工具：search_web / read_document / summarize / compare
"""
import asyncio
import sys
import os

# 将项目根目录加入 sys.path，确保可以导入 agentscope 和 MYCODE
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agentscope.model import OpenAIChatModel
from agentscope.credential import OpenAICredential
from agentscope.message import Msg, TextBlock
from agentscope.tool import Toolkit, FunctionTool

from MYCODE.agent_loop import AgentLoop
from MYCODE.events import (
    LoopStartEvent,
    LoopEndEvent,
    PhaseStartEvent,
    PhaseEndEvent,
)


# ======================================================================
# 模拟工具函数
# ======================================================================
def search_web(query: str) -> str:
    """搜索网络，返回搜索结果摘要。

    Args:
        query: 搜索关键词。
    """
    # 模拟搜索结果
    mock_results = {
        "AgentScope": (
            "AgentScope 是阿里通义实验室开源的多智能体开发框架，"
            "支持消息驱动、模块化组件设计、分布式部署。"
            "核心特性包括：消息交换机制、智能体构建与任务编排、"
            "可插拔模型接口（支持17+ LLM API提供商）。"
        ),
        "LangGraph": (
            "LangGraph 是 LangChain 团队推出的图式 Agent 编排框架，"
            "基于状态图（StateGraph）构建多步骤 Agent 工作流。"
            "核心特性包括：图式状态管理、条件边、循环控制、"
            "人机交互节点、持久化检查点。"
        ),
    }
    # 尝试匹配关键词
    for key, value in mock_results.items():
        if key.lower() in query.lower():
            return f"搜索 '{query}' 的结果：\n{value}"
    return f"搜索 '{query}' 的结果：未找到相关信息。"


def read_document(doc_name: str) -> str:
    """读取文档，返回文档内容摘要。

    Args:
        doc_name: 文档名称。
    """
    mock_docs = {
        "AgentScope架构文档": (
            "AgentScope 采用三层架构：\n"
            "1. 核心框架层：消息驱动的通信中枢，基于 msghub 模块\n"
            "2. 服务层：模型接口、记忆系统、工具调用\n"
            "3. 部署层：分布式运行时、监控与追踪\n"
            "支持 ReAct、Plan-then-Execute 等多种 Agent 模式。"
        ),
        "LangGraph架构文档": (
            "LangGraph 核心概念：\n"
            "1. StateGraph：基于 TypedDict 的状态定义\n"
            "2. Node：状态处理函数\n"
            "3. Edge：条件路由和循环控制\n"
            "4. Checkpoint：持久化状态快照\n"
            "支持流式输出、人机交互、子图嵌套。"
        ),
    }
    for key, value in mock_docs.items():
        if key in doc_name or doc_name in key:
            return f"文档 '{doc_name}' 的内容：\n{value}"
    return f"文档 '{doc_name}' 未找到。"


def summarize(text: str) -> str:
    """对文本进行摘要，返回关键要点。

    Args:
        text: 需要摘要的文本。
    """
    # 模拟摘要
    return (
        f"【摘要】{text[:60]}...\n"
        "关键要点：\n"
        "1. 框架定位清晰，面向多智能体协作\n"
        "2. 核心架构基于消息驱动/状态图\n"
        "3. 支持工具调用和分布式部署"
    )


def compare(topic: str, source_a: str, source_b: str) -> str:
    """对比分析两个来源的异同。

    Args:
        topic: 对比主题。
        source_a: 来源A的内容。
        source_b: 来源B的内容。
    """
    return (
        f"【对比分析：{topic}】\n"
        "相同点：\n"
        " - 都支持多步骤 Agent 工作流编排\n"
        " - 都支持工具调用和状态管理\n"
        " - 都支持人机交互\n"
        "不同点：\n"
        f" - AgentScope 基于消息驱动，LangGraph 基于状态图\n"
        f" - AgentScope 侧重多智能体协作，LangGraph 侧重图式流程控制\n"
        f" - AgentScope 内置分布式支持，LangGraph 依赖外部部署"
    )


# ======================================================================
# 阶段事件打印器
# ======================================================================
# 阶段名称的中文映射
PHASE_NAMES = {
    "perceive": "感知",
    "reason": "推理",
    "plan": "规划",
    "act": "行动",
    "observe": "观察",
}


def print_event(event) -> None:
    """打印循环事件。"""
    if isinstance(event, LoopStartEvent):
        print("\n" + "=" * 60)
        print("🔄 Agent Loop 循环开始")
        print("=" * 60)

    elif isinstance(event, LoopEndEvent):
        print("\n" + "=" * 60)
        print(f"🏁 Agent Loop 循环结束（原因: {event.reason}）")
        print("=" * 60)

    elif isinstance(event, PhaseStartEvent):
        phase_cn = PHASE_NAMES.get(event.phase, event.phase)
        print(f"\n{'─' * 40}")
        print(f"▶ [{event.iteration}] {phase_cn}({event.phase}) 阶段开始")
        if event.detail:
            print(f"  {event.detail}")

    elif isinstance(event, PhaseEndEvent):
        phase_cn = PHASE_NAMES.get(event.phase, event.phase)
        print(f"◀ [{event.iteration}] {phase_cn}({event.phase}) 阶段结束")
        if event.summary:
            print(f"  {event.summary}")

    elif isinstance(event, Msg):
        # 最终回答
        text_parts = []
        for block in event.content if hasattr(event, "content") else []:
            if hasattr(block, "text"):
                text_parts.append(block.text)
        if text_parts:
            print(f"\n💬 最终回答:\n{''.join(text_parts)}")


# ======================================================================
# 主函数
# ======================================================================
async def main() -> None:
    # 1. 配置自部署大模型
    model = OpenAIChatModel(
        credential=OpenAICredential(
            api_key="your-api-key",              # 替换为你的 API Key
            base_url="http://localhost:8000/v1",  # 替换为你的模型服务地址
        ),
        model="your-model-name",                 # 替换为你的模型名称
        stream=False,
    )

    # 2. 注册工具
    toolkit = Toolkit(tools=[
        FunctionTool(search_web),
        FunctionTool(read_document),
        FunctionTool(summarize),
        FunctionTool(compare),
    ])

    # 3. 创建 AgentLoop
    agent_loop = AgentLoop(
        model=model,
        toolkit=toolkit,
        system_prompt=(
            "你是一个技术调研助手。当用户提出调研需求时，"
            "请按以下步骤工作：\n"
            "1. 先用 search_web 搜索相关信息\n"
            "2. 再用 read_document 读取详细文档\n"
            "3. 如有需要，用 summarize 摘要关键内容\n"
            "4. 最后用 compare 做对比分析\n"
            "请用中文回答。"
        ),
        max_iters=10,
    )

    # 4. 发送调研问题
    user_msg = Msg(
        name="user",
        content=[TextBlock(
            text="帮我调研 AgentScope 和 LangGraph 两个框架的异同，"
                 "先搜索它们的基本信息，再读取相关文档，最后做一个对比分析。"
        )],
        role="user",
    )

    print("👤 用户: 帮我调研 AgentScope 和 LangGraph 两个框架的异同，"
          "先搜索它们的基本信息，再读取相关文档，最后做一个对比分析。")

    # 5. 运行循环，打印事件
    async for event in agent_loop.run(user_msg):
        print_event(event)


if __name__ == "__main__":
    asyncio.run(main())
