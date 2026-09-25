from decimal import Decimal

import pytest

from personal_wealth_tracker.config import TrustPolicySettings
from personal_wealth_tracker.models import Authority, Vote
from personal_wealth_tracker.trust_policy import Evidence, RowFacts, decide_authority

POLICY = TrustPolicySettings(
    auto_max_amount=Decimal(1000),
    min_agreement=2,
    min_confidence=0.85,
    never_auto_categories=frozenset({"Rent (monthly)"}),
)
AGREEING_VOTES = (
    Vote(category="Lunch (monthly)", confidence=0.9, source="gemma4:26b"),
    Vote(category="Lunch (monthly)", confidence=0.8, source="gemma4:12b"),
)


@pytest.mark.parametrize(
    ("evidence", "amount", "authority", "reason"),
    [
        (Evidence("rule", "Lunch (monthly)", 0.9), "-50", Authority.auto, "Deterministic rule"),
        (Evidence("rule", "Lunch (monthly)", 0.7), "-50", Authority.review, "below the auto"),
        (Evidence("category_memory", "Lunch (monthly)", 0.97), "-1000", Authority.auto, None),
        (Evidence("historical", "Lunch (monthly)", 0.98), "-1000.01", Authority.review, "cap"),
        (Evidence("local_llm", "Lunch (monthly)", 0.9, AGREEING_VOTES), "1500", Authority.review, "cap"),
        (Evidence("historical", "Rent (monthly)", 0.98), "-50", Authority.review, "never-auto"),
        (Evidence("local_llm", "Rent (monthly)", 0.9, AGREEING_VOTES), "-50", Authority.review, "never-auto"),
        (Evidence("local_llm", "Lunch (monthly)", 0.9, AGREEING_VOTES), "-50", Authority.auto, "2 model"),
        (Evidence("local_llm", "Lunch (monthly)", 0.99, AGREEING_VOTES[:1]), "-50", Authority.review, "1 of 2"),
        (
            Evidence(
                "local_llm",
                "Lunch (monthly)",
                0.9,
                (AGREEING_VOTES[0], Vote(category="Traveling", confidence=0.9, source="gemma4:12b")),
            ),
            "-50",
            Authority.review,
            "1 of 2",
        ),
        (Evidence("unmatched", None, 0.0), "-50", Authority.review, "No category"),
        (Evidence("monthly_review_decision", "Rent (monthly)", 1.0), "-9000", Authority.auto, "Monthly Review Decision"),
        (Evidence("proxy_split_source", None, 1.0), "-9000", Authority.auto, "excluded"),
        (
            Evidence("rule", "Lunch (monthly)", 0.99, provenance="untrusted_imported_transaction"),
            "-50",
            Authority.review,
            "Untrusted",
        ),
        (
            Evidence("monthly_review_decision", "Lunch (monthly)", 1.0, provenance="educated_import_guess"),
            "-50",
            Authority.review,
            "Untrusted",
        ),
    ],
)
def test_trust_policy_decides_authority_from_evidence_row_and_policy(
    evidence, amount, authority, reason
):
    decision = decide_authority(evidence, RowFacts(amount=Decimal(amount)), POLICY)

    assert decision.authority is authority
    if reason is not None:
        assert reason in decision.reason


def test_trust_policy_defaults_match_operator_policy():
    policy = TrustPolicySettings()

    assert policy.auto_max_amount == Decimal(1000)
    assert policy.min_agreement == 2
    assert policy.never_auto_categories == frozenset(
        {
            "Rent (monthly)",
            "Parent B",
            "Parent A",
            "Home insurance (yearly)",
            "Liability insurance (yearly)",
            "Pension A",
            "Pension B",
            "Stock investment plan",
            "Full-time job (net)",
        }
    )
