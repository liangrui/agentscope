# -*- coding: utf-8 -*-
"""Hello AgentScope! - 使用自部署大模型 + 工具调用的示例。"""
import asyncio

from agentscope.agent import Agent
from agentscope.message import Msg, TextBlock
from agentscope.model import OpenAIChatModel
from agentscope.credential import OpenAICredential
from agentscope.tool import Toolkit, FunctionTool


# ================================================================
# 定义工具函数
# ================================================================
def get_greeting(name: str) -> str:
    """根据名字生成问候语。

    Args:
        name: 要问候的对象名字。
    """
    return f"Hello {name}！欢迎来到 AgentScope 的世界！"


def get_current_time() -> str:
    """获取当前时间。"""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


async def main() -> None:
    # ================================================================
    # 1. 配置自部署大模型
    #    通过 OpenAICredential 的 base_url 指向你自己的模型服务地址，
    #    只需兼容 OpenAI Chat Completions API 即可。
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
        FunctionTool(get_greeting),
        FunctionTool(get_current_time),
    ])

    # ================================================================
    # 3. 创建 Agent（传入 toolkit，Agent 会自动处理工具调用循环）
    # ================================================================
    agent = Agent(
        name="assistant",
        system_prompt="你是一个友好的AI助手，请用中文回答问题。你可以使用工具来获取信息。",
        model=model,
        toolkit=toolkit,
    )

    # ================================================================
    # 4. 发送消息并流式获取回复
    # ================================================================
    user_msg = Msg(
        name="user",
        content=[TextBlock(text="请帮我向 AgentScope 说 Hello，并告诉我现在几点了？")],
        role="user",
    )

    print("用户: 请帮我向 AgentScope 说 Hello，并告诉我现在几点了？")
    print("助手: ", end="", flush=True)

    async for event in agent.reply_stream(user_msg):
        # 流式输出文本内容
        if hasattr(event, "delta") and event.delta:
            print(event.delta, end="", flush=True)

    print()  # 换行


if __name__ == "__main__":
    asyncio.run(main())
