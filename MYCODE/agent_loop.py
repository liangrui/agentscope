# -*- coding: utf-8 -*-
"""五阶段 Agent Loop 核心实现。

将 Agent 的运行循环显式拆分为五个阶段：
  Perceive（感知）→ Reason（推理）→ Plan（规划）→ Act（行动）→ Observe（观察）

基于 AgentScope 的 Model、Toolkit、Msg 等核心组件构建。
"""
import asyncio
import json
import uuid
from copy import deepcopy
from typing import AsyncGenerator, Any

from agentscope.model import ChatModelBase, ChatResponse
from agentscope.message import (
    Msg,
    UserMsg,
    AssistantMsg,
    SystemMsg,
    TextBlock,
    ToolCallBlock,
    ToolResultBlock,
    ToolResultState,
)
from agentscope.tool import Toolkit, ToolChoice
from agentscope.state import AgentState

from .events import LoopStartEvent, LoopEndEvent, PhaseStartEvent, PhaseEndEvent


class ToolCallBatch:
    """工具调用批次，用于 Plan 阶段的执行规划。"""

    def __init__(
        self,
        tool_calls: list[ToolCallBlock],
        batch_type: Literal["concurrent", "sequential"] = "concurrent",
    ) -> None:
        self.tool_calls = tool_calls
        self.type = batch_type


# 为了类型提示，从 typing 导入 Literal
from typing import Literal


class AgentLoop:
    """五阶段 Agent Loop。

    将 Agent 的运行循环显式拆分为五个阶段，每个阶段有明确的职责和可观测的事件：

    - Perceive（感知）：接收输入，组装上下文
    - Reason（推理）：模型读上下文，决定下一步做什么
    - Plan（规划）：解析工具调用，规划执行批次
    - Act（行动）：执行工具调用，改变外部世界状态
    - Observe（观察）：获取行动结果，注入上下文，进入下一轮循环
    """

    def __init__(
        self,
        model: ChatModelBase,
        toolkit: Toolkit,
        system_prompt: str,
        max_iters: int = 20,
    ) -> None:
        """初始化 AgentLoop。

        Args:
            model: AgentScope 的聊天模型实例。
            toolkit: AgentScope 的工具集实例。
            system_prompt: 系统提示词。
            max_iters: 最大循环迭代次数，默认 20。
        """
        self.model = model
        self.toolkit = toolkit
        self.system_prompt = system_prompt
        self.max_iters = max_iters

        # 对话上下文
        self.context: list[Msg] = []

    # ==================================================================
    # Phase 1: Perceive — 感知
    # ==================================================================
    async def perceive(self) -> list[Msg]:
        """感知阶段：组装上下文。

        将系统提示词、对话历史组装为模型可用的消息列表。

        Returns:
            组装好的消息列表。
        """
        messages: list[Msg] = []

        # 系统提示词
        messages.append(
            SystemMsg(
                name="system",
                content=[TextBlock(text=self.system_prompt)],
            ),
        )

        # 对话历史
        messages.extend(self.context)

        return messages

    # ==================================================================
    # Phase 2: Reason — 推理
    # ==================================================================
    async def reason(
        self,
        messages: list[Msg],
        tools: list[dict] | None = None,
    ) -> ChatResponse:
        """推理阶段：调用模型，获取响应。

        Args:
            messages: 感知阶段组装的消息列表。
            tools: 可用工具的 JSON Schema 列表。

        Returns:
            模型的完整响应。
        """
        # 调用模型
        res = await self.model(
            messages=messages,
            tools=tools,
            tool_choice=ToolChoice(mode="auto") if tools else None,
        )

        # 处理流式响应：收集所有 chunk 得到完整响应
        if hasattr(res, "__aiter__"):
            completed_response = None
            async for chunk in res:
                if chunk.is_last:
                    completed_response = chunk
            if completed_response is None:
                raise RuntimeError("模型未返回完整响应")
            res = completed_response

        return res

    # ==================================================================
    # Phase 3: Plan — 规划
    # ==================================================================
    async def plan(
        self,
        response: ChatResponse,
    ) -> list[ToolCallBatch]:
        """规划阶段：解析工具调用，规划执行批次。

        从模型响应中提取工具调用，并根据工具的并发安全性
        规划为并发执行批次或顺序执行批次。

        Args:
            response: 推理阶段的模型响应。

        Returns:
            工具调用批次列表。如果没有工具调用，返回空列表。
        """
        # 提取工具调用
        tool_calls = [
            block
            for block in response.content
            if isinstance(block, ToolCallBlock)
        ]

        if not tool_calls:
            return []

        # 对工具调用进行批次规划
        batches: list[ToolCallBatch] = []
        for tool_call in tool_calls:
            tool = await self.toolkit.get_tool(tool_call.name)

            # 并发安全或未注册的工具归入并发批次
            if tool is None or tool.is_concurrency_safe:
                if batches and batches[-1].type == "concurrent":
                    batches[-1].tool_calls.append(tool_call)
                else:
                    batches.append(
                        ToolCallBatch(
                            tool_calls=[tool_call],
                            batch_type="concurrent",
                        ),
                    )
            else:
                # 非并发安全的工具归入顺序批次
                if batches and batches[-1].type == "sequential":
                    batches[-1].tool_calls.append(tool_call)
                else:
                    batches.append(
                        ToolCallBatch(
                            tool_calls=[tool_call],
                            batch_type="sequential",
                        ),
                    )

        return batches

    # ==================================================================
    # Phase 4: Act — 行动
    # ==================================================================
    async def act(
        self,
        batches: list[ToolCallBatch],
        state: AgentState,
    ) -> list[tuple[ToolCallBlock, list[TextBlock], ToolResultState]]:
        """行动阶段：执行工具调用。

        按照 Plan 阶段的规划执行工具调用，支持顺序和并发两种模式。

        Args:
            batches: Plan 阶段规划的工具调用批次。
            state: Agent 状态，用于工具调用时的状态注入。

        Returns:
            工具调用结果列表，每项为 (tool_call, result_blocks, state)。
        """
        results: list[tuple[ToolCallBlock, list[TextBlock], ToolResultState]] = []

        for batch in batches:
            if batch.type == "concurrent":
                # 并发执行
                batch_results = await self._execute_concurrent(
                    batch.tool_calls, state,
                )
                results.extend(batch_results)
            else:
                # 顺序执行
                batch_results = await self._execute_sequential(
                    batch.tool_calls, state,
                )
                results.extend(batch_results)

        return results

    async def _execute_sequential(
        self,
        tool_calls: list[ToolCallBlock],
        state: AgentState,
    ) -> list[tuple[ToolCallBlock, list[TextBlock], ToolResultState]]:
        """顺序执行工具调用。"""
        results = []
        for tool_call in tool_calls:
            result = await self._execute_single_tool(tool_call, state)
            results.append(result)
        return results

    async def _execute_concurrent(
        self,
        tool_calls: list[ToolCallBlock],
        state: AgentState,
    ) -> list[tuple[ToolCallBlock, list[TextBlock], ToolResultState]]:
        """并发执行工具调用。"""
        tasks = [
            self._execute_single_tool(tc, state) for tc in tool_calls
        ]
        return await asyncio.gather(*tasks)

    async def _execute_single_tool(
        self,
        tool_call: ToolCallBlock,
        state: AgentState,
    ) -> tuple[ToolCallBlock, list[TextBlock], ToolResultState]:
        """执行单个工具调用，返回结果。"""
        try:
            result_blocks: list[TextBlock] = []
            result_state = ToolResultState.SUCCESS

            async for chunk in self.toolkit.call_tool(tool_call, state):
                from agentscope.tool import ToolChunk, ToolResponse

                if isinstance(chunk, ToolChunk):
                    for block in chunk.content:
                        if isinstance(block, TextBlock):
                            result_blocks.append(block)
                    if chunk.state == ToolResultState.ERROR:
                        result_state = ToolResultState.ERROR
                elif isinstance(chunk, ToolResponse):
                    for block in chunk.content:
                        if isinstance(block, TextBlock):
                            result_blocks.append(block)
                    if chunk.state in (
                        ToolResultState.ERROR,
                        ToolResultState.DENIED,
                        ToolResultState.INTERRUPTED,
                    ):
                        result_state = chunk.state

            return (tool_call, result_blocks, result_state)

        except Exception as e:
            return (
                tool_call,
                [TextBlock(text=f"工具执行出错: {e}")],
                ToolResultState.ERROR,
            )

    # ==================================================================
    # Phase 5: Observe — 观察
    # ==================================================================
    async def observe(
        self,
        response: ChatResponse,
        tool_results: list[tuple[ToolCallBlock, list[TextBlock], ToolResultState]],
    ) -> None:
        """观察阶段：将工具执行结果注入上下文。

        将模型的 assistant 消息（含工具调用）和工具结果消息
        追加到上下文中，供下一轮 Perceive 使用。

        Args:
            response: 推理阶段的模型响应。
            tool_results: 行动阶段的工具执行结果。
        """
        # 将 assistant 的响应（含工具调用）加入上下文
        assistant_msg = AssistantMsg(
            id=uuid.uuid4().hex,
            name="assistant",
            content=list(response.content),
        )
        self.context.append(assistant_msg)

        # 将工具结果加入上下文
        tool_result_blocks = []
        for tool_call, result_blocks, result_state in tool_results:
            tool_result_blocks.append(
                ToolResultBlock(
                    id=tool_call.id,
                    name=tool_call.name,
                    output="".join(b.text for b in result_blocks),
                    state=result_state,
                ),
            )

        if tool_result_blocks:
            tool_msg = Msg(
                id=uuid.uuid4().hex,
                name="tool",
                content=tool_result_blocks,
                role="assistant",
            )
            self.context.append(tool_msg)

    # ==================================================================
    # 主循环
    # ==================================================================
    async def run(
        self,
        user_msg: Msg,
    ) -> AsyncGenerator[
        LoopStartEvent
        | LoopEndEvent
        | PhaseStartEvent
        | PhaseEndEvent
        | Msg,
        None,
    ]:
        """运行五阶段 Agent Loop。

        串联 Perceive → Reason → Plan → Act → Observe 五个阶段，
        在每个阶段的入口和出口发出可观测事件，直到模型给出最终回答
        或达到最大迭代次数。

        Args:
            user_msg: 用户输入消息。

        Yields:
            LoopStartEvent / LoopEndEvent / PhaseStartEvent / PhaseEndEvent / Msg
        """
        # 将用户消息加入上下文
        self.context.append(user_msg)

        # 发出循环开始事件
        yield LoopStartEvent()

        iteration = 0

        while iteration < self.max_iters:
            iteration += 1

            # ===========================================================
            # Phase 1: Perceive — 感知
            # ===========================================================
            yield PhaseStartEvent(
                phase="perceive",
                iteration=iteration,
                detail=f"组装上下文，当前上下文消息数: {len(self.context)}",
            )

            messages = await self.perceive()

            yield PhaseEndEvent(
                phase="perceive",
                iteration=iteration,
                summary=f"已组装 {len(messages)} 条消息供模型使用",
            )

            # ===========================================================
            # Phase 2: Reason — 推理
            # ===========================================================
            yield PhaseStartEvent(
                phase="reason",
                iteration=iteration,
                detail="调用大模型进行推理",
            )

            # 获取工具 schema
            tools = await self.toolkit.get_tool_schemas()

            response = await self.reason(messages, tools=tools if tools else None)

            # 判断模型输出类型
            has_tool_calls = any(
                isinstance(block, ToolCallBlock)
                for block in response.content
            )

            # 提取文本内容用于摘要
            text_content = "".join(
                block.text
                for block in response.content
                if isinstance(block, TextBlock)
            )

            if has_tool_calls:
                tool_names = [
                    block.name
                    for block in response.content
                    if isinstance(block, ToolCallBlock)
                ]
                yield PhaseEndEvent(
                    phase="reason",
                    iteration=iteration,
                    summary=f"模型决定调用工具: {', '.join(tool_names)}",
                )
            else:
                yield PhaseEndEvent(
                    phase="reason",
                    iteration=iteration,
                    summary=f"模型直接回答: {text_content[:100]}",
                )

            # 如果没有工具调用，直接返回最终回答
            if not has_tool_calls:
                # 将最终回答加入上下文
                final_msg = AssistantMsg(
                    id=uuid.uuid4().hex,
                    name="assistant",
                    content=list(response.content),
                )
                self.context.append(final_msg)

                yield LoopEndEvent(reason="模型已给出最终回答")
                yield final_msg
                return

            # ===========================================================
            # Phase 3: Plan — 规划
            # ===========================================================
            yield PhaseStartEvent(
                phase="plan",
                iteration=iteration,
                detail="解析工具调用，规划执行批次",
            )

            batches = await self.plan(response)

            batch_info = ", ".join(
                f"[{b.type}: {len(b.tool_calls)}个工具]"
                for b in batches
            )

            yield PhaseEndEvent(
                phase="plan",
                iteration=iteration,
                summary=f"规划完成: {batch_info}",
            )

            # ===========================================================
            # Phase 4: Act — 行动
            # ===========================================================
            yield PhaseStartEvent(
                phase="act",
                iteration=iteration,
                detail=f"执行 {sum(len(b.tool_calls) for b in batches)} 个工具调用",
            )

            state = AgentState()
            tool_results = await self.act(batches, state)

            # 构建行动摘要
            act_summary_parts = []
            for tool_call, result_blocks, result_state in tool_results:
                result_text = "".join(b.text for b in result_blocks)
                act_summary_parts.append(
                    f"{tool_call.name}: {result_text[:80]}"
                )

            yield PhaseEndEvent(
                phase="act",
                iteration=iteration,
                summary="; ".join(act_summary_parts),
            )

            # ===========================================================
            # Phase 5: Observe — 观察
            # ===========================================================
            yield PhaseStartEvent(
                phase="observe",
                iteration=iteration,
                detail="将工具结果注入上下文",
            )

            await self.observe(response, tool_results)

            yield PhaseEndEvent(
                phase="observe",
                iteration=iteration,
                summary=f"已注入 {len(tool_results)} 个工具结果到上下文，准备下一轮循环",
            )

        # 达到最大迭代次数
        yield LoopEndEvent(reason=f"已达到最大推理-行动循环次数 ({self.max_iters})")

        max_iter_msg = AssistantMsg(
            id=uuid.uuid4().hex,
            name="assistant",
            content=[TextBlock(
                text="已达到最大推理-行动循环次数，任务可能未完成。"
            )],
        )
        yield max_iter_msg
