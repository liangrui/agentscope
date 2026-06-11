# -*- coding: utf-8 -*-
"""数据分析助手 Demo — 展示五阶段 Agent Loop 的完整工作流程。

场景：数据分析助手，需要多步计算和查询来完成分析任务。
工具：query_database / calculate / generate_chart
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
def query_database(sql: str) -> str:
    """查询数据库，返回查询结果。

    Args:
        sql: SQL 查询语句。
    """
    # 模拟数据库查询结果
    if "华东" in sql and "销售" in sql:
        return (
            "查询结果（华东区上季度销售数据）：\n"
            "| 月份   | 销售额(万元) | 订单数 |\n"
            "|--------|-------------|--------|\n"
            "| 1月    | 1,250       | 340    |\n"
            "| 2月    | 1,180       | 310    |\n"
            "| 3月    | 1,420       | 385    |\n"
            "合计: 3,850万元，1,035笔订单\n"
            "去年同期: 3,200万元"
        )
    elif "华东" in sql:
        return "查询结果：华东区数据已返回。"
    else:
        return f"查询结果：执行 SQL '{sql}' 完成，返回0条记录。"


def calculate(expression: str) -> str:
    """执行数学计算。

    Args:
        expression: 数学表达式，如 "3850 / 3200 * 100"。
    """
    try:
        # 安全地执行简单数学表达式
        # 只允许数字和基本运算符
        allowed_chars = set("0123456789+-*/.() ")
        if not all(c in allowed_chars for c in expression):
            return f"计算失败：表达式包含不允许的字符 '{expression}'"
        result = eval(expression)
        return f"计算结果: {expression} = {result:.2f}"
    except Exception as e:
        return f"计算失败: {e}"


def generate_chart(data: str, chart_type: str) -> str:
    """生成图表，返回图表描述。

    Args:
        data: 图表数据描述。
        chart_type: 图表类型（如 bar, line, pie）。
    """
    chart_names = {
        "bar": "柱状图",
        "line": "折线图",
        "pie": "饼图",
    }
    chart_cn = chart_names.get(chart_type, chart_type)
    return (
        f"【{chart_cn}已生成】\n"
        f"数据: {data[:80]}...\n"
        f"图表类型: {chart_cn}\n"
        "图表展示：华东区上季度月度销售额趋势\n"
        "  ████ 1月: 1,250万\n"
        "  ███  2月: 1,180万\n"
        "  █████ 3月: 1,420万"
    )


# ======================================================================
# 阶段事件打印器
# ======================================================================
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
        FunctionTool(query_database),
        FunctionTool(calculate),
        FunctionTool(generate_chart),
    ])

    # 3. 创建 AgentLoop
    agent_loop = AgentLoop(
        model=model,
        toolkit=toolkit,
        system_prompt=(
            "你是一个数据分析助手。当用户提出分析需求时，"
            "请按以下步骤工作：\n"
            "1. 先用 query_database 查询所需数据\n"
            "2. 再用 calculate 进行计算\n"
            "3. 最后用 generate_chart 生成图表\n"
            "请用中文回答，给出清晰的分析结论。"
        ),
        max_iters=10,
    )

    # 4. 发送数据分析问题
    user_msg = Msg(
        name="user",
        content=[TextBlock(
            text="查询华东区上季度的销售数据，计算同比增长率，并生成柱状图。"
        )],
        role="user",
    )

    print("👤 用户: 查询华东区上季度的销售数据，计算同比增长率，并生成柱状图。")

    # 5. 运行循环，打印事件
    async for event in agent_loop.run(user_msg):
        print_event(event)


if __name__ == "__main__":
    asyncio.run(main())
