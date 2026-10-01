"""Evaluates an approval policy against a gate's facts. Pure: no I/O, the same answer every time.

Every enabled rule whose conditions all hold "matches". The strictest matching action wins
(reject, then ask, then approve), so an approve rule can never wave through something another
rule says needs the founder. With no match, the policy's default applies.
"""

from fnmatch import fnmatch
from pathlib import PurePosixPath
from typing import Any

from app.features.approvals.schemas import (
    STRICTNESS,
    ApprovalPolicy,
    Condition,
    Verdict,
)


def evaluate(policy: ApprovalPolicy, facts: dict[str, Any]) -> Verdict:
    matched = [
        rule
        for rule in policy.rules
        if rule.enabled and all(holds(condition, facts) for condition in rule.when)
    ]
    for action in STRICTNESS:
        winners = [rule for rule in matched if rule.action == action]
        if winners:
            return Verdict(
                action=action,
                rule_ids=[rule.id for rule in winners],
                reasons=[rule.reason for rule in winners],
            )
    return Verdict(action=policy.default, rule_ids=[], reasons=[policy.default_reason])


def holds(condition: Condition, facts: dict[str, Any]) -> bool:
    """A missing fact or a value of the wrong type never matches."""
    if condition.fact not in facts:
        return False
    actual, expected = facts[condition.fact], condition.value
    try:
        match condition.op:
            case "eq":
                return bool(actual == expected)
            case "ne":
                return bool(actual != expected)
            case "gt":
                return bool(actual > expected)
            case "gte":
                return bool(actual >= expected)
            case "lt":
                return bool(actual < expected)
            case "lte":
                return bool(actual <= expected)
            case "matches_any":
                return bool(matching(actual, expected))
    except TypeError:
        return False
    return False


def matching(values: Any, patterns: Any) -> list[str]:
    """The values (e.g. file paths) matching any pattern, by full path or file name."""
    items = [values] if isinstance(values, str) else list(values)
    globs = [patterns] if isinstance(patterns, str) else list(patterns)
    return [
        str(item)
        for item in items
        if any(fnmatch(str(item), g) or fnmatch(PurePosixPath(str(item)).name, g) for g in globs)
    ]


def policy_problems(policy: ApprovalPolicy, known_facts: frozenset[str]) -> list[str]:
    """Rules that name facts the workflow doesn't provide (checked when a template loads)."""
    problems = []
    for rule in policy.rules:
        unknown = sorted({c.fact for c in rule.when} - known_facts)
        if unknown:
            problems.append(f"approval rule {rule.id}: unknown facts {', '.join(unknown)}")
        for condition in rule.when:
            if condition.op == "matches_any" and not isinstance(condition.value, (str, list)):
                problems.append(f"approval rule {rule.id}: matches_any needs a list of patterns")
    ids = [rule.id for rule in policy.rules]
    duplicates = sorted({i for i in ids if ids.count(i) > 1})
    if duplicates:
        problems.append(f"duplicate approval rules: {', '.join(duplicates)}")
    return problems
