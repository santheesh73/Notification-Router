"""Synthetic Generalization Test Suite for Promotion Utility Score & Action Routing (Step 9)."""

import pytest
from src.features.feature_vector import FeatureVector
from src.rules.promotion_rule import PromotionRule
from src.builders.context_manager import ContextManager
from unittest.mock import MagicMock


@pytest.fixture
def mock_context():
    return MagicMock(spec=ContextManager)


def test_trusted_business_promotion_digest(mock_context):
    """Verified business + past orders + price deal -> Digest (High Utility)."""
    vec = FeatureVector(
        message_id="syn_promo_001",
        user_id="u_syn_101",
        sender_id="b_syn_001",
        conversation_type="business",
        message_text="Exclusive summer offer: Ladakh tour package at Rs 15,000 per person.",
        verified=True,
        trusted_business=True,
        orders=3,
        contains_offer=True,
        dismiss_rate=0.10,
    )
    rule = PromotionRule()
    res = rule.evaluate(vec, mock_context)

    assert res is not None
    assert res.action == "digest"
    assert res.message_type == "promotion"
    assert res.confidence >= 0.75


def test_unknown_business_unsolicited_spam_mute(mock_context):
    """Unknown business + zero orders + high dismiss + try50 coupon -> Mute (Low Utility)."""
    vec = FeatureVector(
        message_id="syn_promo_002",
        user_id="u_syn_102",
        sender_id="b_syn_999",
        conversation_type="business",
        message_text="Get 50% OFF now! Use code TRY50 click here for instant discount.",
        verified=False,
        trusted_business=False,
        orders=0,
        contains_coupon=True,
        dismiss_rate=0.85,
        report_history=1,
    )
    rule = PromotionRule()
    res = rule.evaluate(vec, mock_context)

    assert res is not None
    assert res.action == "mute"
    assert res.message_type == "promotion"


def test_duplicate_broadcast_promotion_mute(mock_context):
    """High duplicate probability + forwarded count -> Mute (Fatigue Penalty)."""
    vec = FeatureVector(
        message_id="syn_promo_003",
        user_id="u_syn_103",
        sender_id="u_syn_888",
        conversation_type="group",
        message_text="Selling cycle helmet medium size. Contact if interested.",
        forwarded_count=3,
        duplicate_probability=1.0,
        contains_offer=True,
    )
    rule = PromotionRule()
    res = rule.evaluate(vec, mock_context)

    assert res is not None
    assert res.action == "mute"
    assert res.message_type == "promotion"


def test_community_item_selling_digest(mock_context):
    """Community group selling item + first occurrence -> Digest (Useful Info)."""
    vec = FeatureVector(
        message_id="syn_promo_004",
        user_id="u_syn_104",
        sender_id="u_syn_555",
        conversation_type="group",
        message_text="Selling brand new kurta set, size M. Unopened box.",
        forwarded_count=0,
        duplicate_probability=0.0,
        contains_offer=True,
    )
    rule = PromotionRule()
    res = rule.evaluate(vec, mock_context)

    assert res is not None
    assert res.action == "digest"
    assert res.message_type == "promotion"
