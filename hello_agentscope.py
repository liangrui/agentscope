# -*- coding: utf-8 -*-
"""Hello AgentScope! - 使用自部署大模型的简单示例。"""
import asyncio

from agentscope.agent import Agent
from agentscope.message import Msg, TextBlock
from agentscope.model import OpenAIChatModel
from agentscope.credential import OpenAICredential
from agentscope.formatter import OpenAIChatFormatter


async def main() -> None:
    # ================================================================
    # 1. 配置自部署大模型
    #    通过 OpenAICredential 的 base_url 指向你自己的模型服务地址，
    #    只需兼容 OpenAI Chat Completions API 即可。
    # ================================================================
    model = OpenAIChatModel(
        credential=OpenAICredential(
            api_key="your-api-key",          # 替换为你的 API Key
            base_url="http://localhost:8000/v1",  # 替换为你的模型服务地址
        ),
        model="your-model-name",             # 替换为你的模型名称
        stream=True,
    )

    # ================================================================
    # 2. 创建 Agent
    # ================================================================
    agent = Agent(
        name="assistant",
        system_prompt="你是一个友好的AI助手，请用中文回答问题。",
        model=model,
    )

    # ================================================================
    # 3. 发送消息并流式获取回复
    # ================================================================
    user_msg = Msg(
        name="user",
        content=[TextBlock(text="你好，请对我说 Hello AgentScope！")],
        role="user",
    )

    print("用户: 你好，请对我说 Hello AgentScope！")
    print("助手: ", end="", flush=True)

    async for event in agent.reply_stream(user_msg):
        # 流式输出文本内容
        if hasattr(event, "delta") and event.delta:
            print(event.delta, end="", flush=True)

    print()  # 换行


if __name__ == "__main__":
    asyncio.run(main())
