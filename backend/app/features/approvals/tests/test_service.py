from app.features.approvals.schemas import Action, ApprovalPolicy, ApprovalRule, Condition
from app.features.approvals.service import evaluate, holds, matching, policy_problems


def rule(id: str, action: Action, *conditions: Condition, enabled: bool = True) -> ApprovalRule:
    return ApprovalRule(
        id=id, action=action, reason=f"because {id}", when=list(conditions), enabled=enabled
    )


SENSITIVE = Condition(fact="files_changed", op="matches_any", value=["package.json", ".env*"])
SMALL = Condition(fact="files_count", op="lte", value=3)


def test_no_match_uses_the_default() -> None:
    verdict = evaluate(
        ApprovalPolicy(rules=[rule("sensitive", Action.ASK, SENSITIVE)]),
        {"files_changed": ["calc.py"]},
    )

    assert (verdict.action, verdict.rule_ids) == (Action.ASK, [])
    assert verdict.reasons == ["Every release needs your approval."]


def test_strictest_matching_action_wins_with_every_reason() -> None:
    policy = ApprovalPolicy(
        default=Action.APPROVE,
        rules=[
            rule("small", Action.APPROVE, SMALL),
            rule("sensitive", Action.ASK, SENSITIVE),
            rule("big_spend", Action.ASK, Condition(fact="tokens", op="gt", value=100)),
        ],
    )
    facts = {"files_changed": ["src/.env.local"], "files_count": 1, "tokens": 500}

    verdict = evaluate(policy, facts)

    assert verdict.action == Action.ASK  # the approve rule matched too, but ask is stricter
    assert verdict.rule_ids == ["sensitive", "big_spend"]
    assert verdict.reasons == ["because sensitive", "because big_spend"]


def test_reject_beats_everything_and_disabled_rules_are_ignored() -> None:
    policy = ApprovalPolicy(
        rules=[
            rule("never", Action.REJECT, Condition(fact="amount", op="gt", value=2000)),
            rule("off", Action.REJECT, enabled=False),
            rule("always", Action.APPROVE),
        ]
    )

    assert evaluate(policy, {"amount": 2500}).action == Action.REJECT
    assert evaluate(policy, {"amount": 100}).rule_ids == ["always"]


def test_conditions_are_safe_on_missing_or_odd_facts() -> None:
    gt = Condition(fact="tokens", op="gt", value=10)

    assert not holds(gt, {})
    assert not holds(gt, {"tokens": "lots"})  # wrong type never matches
    assert holds(Condition(fact="tests_passed", op="eq", value=True), {"tests_passed": True})


def test_patterns_match_full_paths_or_file_names() -> None:
    assert matching(
        ["a/b/package.json", "src/app.py", "migrations/001.sql"],
        [
            "package.json",
            "migrations/*",
        ],
    ) == ["a/b/package.json", "migrations/001.sql"]


def test_policy_problems_name_unknown_facts_and_duplicates() -> None:
    policy = ApprovalPolicy(
        rules=[
            rule("a", Action.ASK, Condition(fact="refund_amount", op="gt", value=1)),
            rule("a", Action.ASK, Condition(fact="tokens", op="matches_any", value=5)),
        ]
    )

    problems = policy_problems(policy, frozenset({"tokens"}))

    assert any("unknown facts refund_amount" in p for p in problems)
    assert any("matches_any needs a list" in p for p in problems)
    assert any("duplicate approval rules: a" in p for p in problems)
