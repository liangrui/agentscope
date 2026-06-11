# -*- coding: utf-8 -*-
"""五阶段 Agent Loop 的事件类型定义。"""
from typing import Literal
from pydantic import BaseModel, Field


class LoopStartEvent(BaseModel):
    """Agent Loop 循环开始事件。"""
    type: Literal["loop_start"] = "loop_start"


class LoopEndEvent(BaseModel):
    """Agent Loop 循环结束事件。"""
    type: Literal["loop_end"] = "loop_end"
    reason: str = ""
    """循环结束的原因。"""


class PhaseStartEvent(BaseModel):
    """阶段开始事件。"""
    type: Literal["phase_start"] = "phase_start"
    phase: Literal["perceive", "reason", "plan", "act", "observe"]
    """当前阶段名称。"""
    iteration: int
    """当前循环迭代次数（从1开始）。"""
    detail: str = ""
    """阶段开始的附加信息。"""


class PhaseEndEvent(BaseModel):
    """阶段结束事件。"""
    type: Literal["phase_end"] = "phase_end"
    phase: Literal["perceive", "reason", "plan", "act", "observe"]
    """当前阶段名称。"""
    iteration: int
    """当前循环迭代次数。"""
    summary: str = ""
    """阶段结束的摘要信息。"""
