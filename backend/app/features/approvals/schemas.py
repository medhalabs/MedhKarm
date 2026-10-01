"""Approval rules: when a gate needs the founder, and why.

A gate (e.g. the release) always exists in the workflow. Its policy decides what happens
there: ask the founder, approve on its own, or stop. Rules look at the gate's facts
(files changed, tokens used, ...), which each workflow provides.
"""

from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field


class Action(StrEnum):
    ASK = "ask"  # pause for the founder
    APPROVE = "approve"  # go ahead without asking
    REJECT = "reject"  # stop without asking


# Strictest first: when several rules match, the strictest action wins.
STRICTNESS = (Action.REJECT, Action.ASK, Action.APPROVE)

Operator = Literal["eq", "ne", "gt", "gte", "lt", "lte", "matches_any"]


class Condition(BaseModel):
    fact: str  # e.g. "files_changed", "tokens"
    op: Operator
    value: Any  # a number, text, true/false, or for matches_any a list of patterns ("*.env")


class ApprovalRule(BaseModel):
    id: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    action: Action
    reason: str = Field(min_length=1)  # shown to the founder: "It changes package.json"
    when: list[Condition] = Field(default_factory=list)  # all must hold; empty = always
    enabled: bool = True


class ApprovalPolicy(BaseModel):
    default: Action = Action.ASK  # when no rule matches
    default_reason: str = "Every release needs your approval."
    rules: list[ApprovalRule] = Field(default_factory=list)


class Verdict(BaseModel):
    action: Action
    rule_ids: list[str]  # the matching rules behind the action; empty = the default
    reasons: list[str]  # plain sentences for the founder
