#!/usr/bin/env python3
"""Shared defaults for workflow YAML generation and validation."""
from __future__ import annotations

import unicodedata
from typing import Any


DEFAULT_SPLITTYPE = 20
SPLITTYPE_BY_ACTIVITYTYPE: dict[int, int | None] = {
    10: 30,
    20: None,
    30: 20,
    40: 30,
    90: 20,
    100: 30,
}

DEFAULT_IS_CHECKMATERIALSUBMIT = 20

FLOW_START_ICON_X = "0"
FLOW_START_ICON_Y = "204"
FLOW_FIRST_ACTIVITY_ICON_X = 235
FLOW_MAIN_ICON_Y = "180"
FLOW_BRANCH_ICON_Y = "20"
FLOW_MIN_STEP_X = 320
FLOW_GAP_X = 60
FLOW_NODE_MAX_WIDTH = 520
# Backward-compatible alias: dynamic layout uses this as the minimum step.
FLOW_STEP_X = FLOW_MIN_STEP_X
FLOW_END_ICON_Y = "204"
FLOW_BROWSE_ICON_X = "24"
FLOW_BROWSE_ICON_Y = "-34"

# activitytype → handleurl 模式映射（只有 30 和 100 有 handleurl，其他为 None）
HANDLE_URL_ACTIVITY_TYPES: dict[int, str] = {
    30: "add",     # 申请/审批节点用 add 模式
    100: "detail", # 浏览节点用 detail 模式
}

WORKFLOW_RENDERER_PREFIX = "home/vuepagedesigner/renderer"


def _to_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def default_splittype(activitytype: Any) -> int | None:
    """Return the default splittype for an activitytype."""
    atype = _to_int(activitytype)
    if atype is None:
        return DEFAULT_SPLITTYPE
    return SPLITTYPE_BY_ACTIVITYTYPE.get(atype, DEFAULT_SPLITTYPE)


def default_operationvisiablecase(operationtype: Any) -> str:
    """Return the default operationvisiablecase for an operationtype."""
    return "30" if _to_int(operationtype) == 50 else "1020"


def flow_iconx(index: int) -> str:
    """Return minimum x coordinate for the nth non-start flow activity.

    Prefer flow_iconx_sequence() for real workflow generation because it accounts
    for node-name width and keeps wide cards from overlapping.
    """
    return str(FLOW_FIRST_ACTIVITY_ICON_X + index * FLOW_STEP_X)


def _text_display_width(text: Any) -> int:
    """Estimate rendered text width in px for workflow cards."""
    width = 0
    for char in str(text or ""):
        width += 16 if unicodedata.east_asian_width(char) in ("W", "F") else 8
    return width


def estimate_activity_node_width(activitytype: Any, activityname: Any) -> int:
    """Estimate workflow designer card width for layout spacing."""
    atype = _to_int(activitytype)
    text_width = _text_display_width(activityname)
    if atype == 20:
        return 120
    if atype == 90:
        return min(max(240, text_width + 160), FLOW_NODE_MAX_WIDTH)
    if atype == 30:
        return min(max(280, text_width + 190), FLOW_NODE_MAX_WIDTH)
    return min(max(160, text_width + 120), FLOW_NODE_MAX_WIDTH)


def flow_step_after(activitytype: Any, activityname: Any) -> int:
    """Return x-axis step after a flow node, with overlap-safe minimum."""
    return max(FLOW_MIN_STEP_X, estimate_activity_node_width(activitytype, activityname) + FLOW_GAP_X)


def flow_iconx_sequence(nodes: list[tuple[Any, Any]]) -> list[str]:
    """Return dynamic x coordinates for non-start main-flow nodes.

    nodes must be ordered as application/subprocess/approve/.../end and should
    contain (activitytype, activityname) pairs. The first node always starts at
    FLOW_FIRST_ACTIVITY_ICON_X; each following node is moved by the previous
    node's estimated card width plus a safety gap, with a 320px minimum.
    """
    positions: list[str] = []
    x = FLOW_FIRST_ACTIVITY_ICON_X
    for i, (activitytype, activityname) in enumerate(nodes):
        positions.append(str(x))
        if i < len(nodes) - 1:
            x += flow_step_after(activitytype, activityname)
    return positions


def material_page_url(mode: str, pagetag: str) -> str:
    """Build workflowPvMaterial page URL for add/detail modes."""
    if not pagetag:
        return ""
    return f"{WORKFLOW_RENDERER_PREFIX}/{mode}?pagetag={pagetag}"


def build_handle_url(activitytype: int, pagetag: str) -> str | None:
    """根据 activitytype 构建 handleurl。

    - activitytype 30（申请/审批）：用 add 模式
    - activitytype 100（浏览）：用 detail 模式
    - 其他类型（10 开始、20 结束、40 路由、90 子流程）：返回 None
    """
    mode = HANDLE_URL_ACTIVITY_TYPES.get(activitytype)
    if mode is None:
        return None
    if not pagetag:
        return ""
    return f"{WORKFLOW_RENDERER_PREFIX}/{mode}?pagetag={pagetag}"
