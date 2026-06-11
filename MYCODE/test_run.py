# -*- coding: utf-8 -*-
"""可执行的五阶段 Agent Loop 测试脚本。

使用模拟模型（无需真实 LLM API），直接展示五阶段循环的完整工作流程。
"""
import asyncio
import sys
import os
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agentscope.message import (
    Msg,
    TextBlock,
    ToolCallBlock,
    ToolCallState,
)
from agentscope.model import ChatResponse
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
    mock_results = {
        "AgentScope": (
            "AgentScope 是阿里通义实验室开源的多智能体开发框架，"
            "支持消息驱动、模块化组件设计、分布式部署。"
        ),
        "LangGraph": (
            "LangGraph 是 LangChain 团队推出的图式 Agent 编排框架，"
            "基于状态图构建多步骤 Agent 工作流。"
        ),
    }
    for key, value in mock_results.items():
        if key.lower() in query.lower():
            return f"搜索 '{query}' 的结果：{value}"
    return f"搜索 '{query}' 的结果：未找到相关信息。"


def compare(topic: str, source_a: str, source_b: str) -> str:
    """对比分析两个来源的异同。

    Args:
        topic: 对比主题。
        source_a: 来源A的内容。
        source_b: 来源B的内容。
    """
    return (
        f"【对比分析：{topic}】\n"
        "相同点：都支持多步骤 Agent 工作流编排\n"
        "不同点：AgentScope 基于消息驱动，LangGraph 基于状态图"
    )


# ======================================================================
# 模拟模型 — 不需要真实 API，按预设逻辑返回响应
# ======================================================================
class MockModel:
    """模拟大模型，按预设的多轮对话逻辑返回响应。"""

    def __init__(self) -> None:
        self.call_count = 0
        self.model = "mock-model"
        # 预设每轮的响应
        self._responses = [
            # 第1轮：模型决定同时搜索两个框架
            ChatResponse(
                content=[
                    TextBlock(text="我需要先搜索两个框架的基本信息。"),
                    ToolCallBlock(
                        id="call_1",
                        name="search_web",
                        input='{"query": "AgentScope"}',
                        state=ToolCallState.ALLOWED,
                    ),
                    ToolCallBlock(
                        id="call_2",
                        name="search_web",
                        input='{"query": "LangGraph"}',
                        state=ToolCallState.ALLOWED,
                    ),
                ],
                is_last=True,
            ),
            # 第2轮：模型决定做对比分析
            ChatResponse(
                content=[
                    TextBlock(text="已获取搜索结果，现在进行对比分析。"),
                    ToolCallBlock(
                        id="call_3",
                        name="compare",
                        input='{"topic": "AgentScope vs LangGraph", "source_a": "AgentScope", "source_b": "LangGraph"}',
                        state=ToolCallState.ALLOWED,
                    ),
                ],
                is_last=True,
            ),
            # 第3轮：模型给出最终回答
            ChatResponse(
                content=[
                    TextBlock(
                        text=(
                            "根据调研结果，以下是 AgentScope 和 LangGraph 的对比分析：\n\n"
                            "## 相同点\n"
                            "- 都支持多步骤 Agent 工作流编排\n"
                            "- 都支持工具调用和状态管理\n\n"
                            "## 不同点\n"
                            "- AgentScope 基于消息驱动，LangGraph 基于状态图\n"
                            "- AgentScope 侧重多智能体协作，LangGraph 侧重图式流程控制\n"
                            "- AgentScope 内置分布式支持，LangGraph 依赖外部部署\n\n"
                            "调研完成！"
                        ),
                    ),
                ],
                is_last=True,
            ),
        ]

    async def __call__(self, messages, tools=None, tool_choice=None, **kwargs):
        response = self._responses[self.call_count]
        self.call_count += 1
        return response


# ======================================================================
# 事件打印器
# ======================================================================
PHASE_NAMES = {
    "perceive": "感知",
    "reason": "推理",
    "plan": "规划",
    "act": "行动",
    "observe": "观察",
}

PHASE_ICONS = {
    "perceive": "👁️",
    "reason": "🧠",
    "plan": "📋",
    "act": "🔧",
    "observe": "🔍",
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
        icon = PHASE_ICONS.get(event.phase, "▶")
        phase_cn = PHASE_NAMES.get(event.phase, event.phase)
        print(f"\n  {icon} [第{event.iteration}轮] {phase_cn}({event.phase}) 开始")
        if event.detail:
            print(f"     {event.detail}")

    elif isinstance(event, PhaseEndEvent):
        icon = PHASE_ICONS.get(event.phase, "◀")
        phase_cn = PHASE_NAMES.get(event.phase, event.phase)
        print(f"  {icon} [第{event.iteration}轮] {phase_cn}({event.phase}) 结束")
        if event.summary:
            print(f"     → {event.summary}")

    elif isinstance(event, Msg):
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
    print("=" * 60)
    print("五阶段 Agent Loop 演示（使用模拟模型，无需真实 API）")
    print("=" * 60)

    # 1. 创建模拟模型
    model = MockModel()

    # 2. 注册工具
    toolkit = Toolkit(tools=[
        FunctionTool(search_web),
        FunctionTool(compare),
    ])

    # 3. 创建 AgentLoop
    agent_loop = AgentLoop(
        model=model,
        toolkit=toolkit,
        system_prompt="你是一个技术调研助手，请用中文回答。",
        max_iters=10,
    )

    # 4. 发送调研问题
    user_msg = Msg(
        name="user",
        content=[TextBlock(
            text="帮我调研 AgentScope 和 LangGraph 两个框架的异同。"
        )],
        role="user",
    )

    print("\n👤 用户: 帮我调研 AgentScope 和 LangGraph 两个框架的异同。")

    # 5. 运行循环
    async for event in agent_loop.run(user_msg):
        print_event(event)


if __name__ == "__main__":
    asyncio.run(main())
