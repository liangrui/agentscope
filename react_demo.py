# -*- coding: utf-8 -*-
"""ReAct 模式 Demo - 使用自部署大模型，展示 Reasoning-Acting 循环。

Agent 内置 ReAct 循环：
  Reasoning -> 模型思考并决定是否调用工具
  Acting    -> 执行工具调用，将结果返回给模型
  循环往复，直到模型给出最终回答或达到最大迭代次数。
"""
import asyncio

from agentscope.agent import Agent, ReActConfig
from agentscope.message import Msg, TextBlock
from agentscope.model import OpenAIChatModel
from agentscope.credential import OpenAICredential
from agentscope.tool import Toolkit, FunctionTool
from agentscope.event import (
    TextBlockDeltaEvent,
    ThinkingBlockDeltaEvent,
    ToolCallStartEvent,
    ToolCallEndEvent,
    ToolResultStartEvent,
    ToolResultTextDeltaEvent,
    ToolResultEndEvent,
    ReplyStartEvent,
    ReplyEndEvent,
)


# ================================================================
# 定义工具函数 - 模拟一个简单的数学计算助手
# ================================================================
def add(a: float, b: float) -> str:
    """计算两个数的和。

    Args:
        a: 第一个数。
        b: 第二个数。
    """
    result = a + b
    return f"{a} + {b} = {result}"


def multiply(a: float, b: float) -> str:
    """计算两个数的乘积。

    Args:
        a: 第一个数。
        b: 第二个数。
    """
    result = a * b
    return f"{a} × {b} = {result}"


def power(base: float, exponent: float) -> str:
    """计算一个数的幂次方。

    Args:
        base: 底数。
        exponent: 指数。
    """
    result = base ** exponent
    return f"{base}^{exponent} = {result}"


async def main() -> None:
    # ================================================================
    # 1. 配置自部署大模型
    # ================================================================
    model = OpenAIChatModel(
        credential=OpenAICredential(
            api_key="your-api-key",              # 替换为你的 API Key
            base_url="http://localhost:8000/v1",  # 替换为你的模型服务地址
        ),
        model="your-model-name",                 # 替换为你的模型名称
        stream=True,
    )

    # ================================================================
    # 2. 注册工具到 Toolkit
    # ================================================================
    toolkit = Toolkit(tools=[
        FunctionTool(add),
        FunctionTool(multiply),
        FunctionTool(power),
    ])

    # ================================================================
    # 3. 创建 ReAct Agent
    #    - toolkit: 注册的工具，Agent 会自动进入 ReAct 循环
    #    - react_config: 控制循环行为，如最大迭代次数
    # ================================================================
    agent = Agent(
        name="math_assistant",
        system_prompt=(
            "你是一个数学计算助手。"
            "当遇到计算问题时，请使用提供的工具逐步计算。"
            "每次只做一步计算，然后根据结果决定下一步。"
        ),
        model=model,
        toolkit=toolkit,
        react_config=ReActConfig(
            max_iters=10,  # 最大推理-行动循环次数
        ),
    )

    # ================================================================
    # 4. 发送问题，流式观察 ReAct 循环过程
    # ================================================================
    user_msg = Msg(
        name="user",
        content=[TextBlock(text="请计算 (3 + 5) × 2^3 的结果，需要分步计算。")],
        role="user",
    )

    print("=" * 60)
    print("用户: 请计算 (3 + 5) × 2^3 的结果，需要分步计算。")
    print("=" * 60)

    current_tool = None
    tool_result_text = ""

    async for event in agent.reply_stream(user_msg):

        # --- 回复开始 ---
        if isinstance(event, ReplyStartEvent):
            print("\n🤖 [ReAct 循环开始]")

        # --- 思考过程（如果模型支持 thinking） ---
        elif isinstance(event, ThinkingBlockDeltaEvent):
            print(event.delta, end="", flush=True)

        # --- 模型生成的文本 ---
        elif isinstance(event, TextBlockDeltaEvent):
            print(event.delta, end="", flush=True)

        # --- 工具调用开始 ---
        elif isinstance(event, ToolCallStartEvent):
            current_tool = event.tool_call_name
            print(f"\n🔧 [Acting] 调用工具: {event.tool_call_name}")

        # --- 工具调用结束 ---
        elif isinstance(event, ToolCallEndEvent):
            pass

        # --- 工具结果开始 ---
        elif isinstance(event, ToolResultStartEvent):
            tool_result_text = ""

        # --- 工具结果内容 ---
        elif isinstance(event, ToolResultTextDeltaEvent):
            tool_result_text += event.delta

        # --- 工具结果结束 ---
        elif isinstance(event, ToolResultEndEvent):
            print(f"   [结果] {tool_result_text}")
            print("🧠 [Reasoning] 模型根据结果继续推理...")
            current_tool = None
            tool_result_text = ""

        # --- 回复结束 ---
        elif isinstance(event, ReplyEndEvent):
            print("\n🏁 [ReAct 循环结束]")

    print()


if __name__ == "__main__":
    asyncio.run(main())
