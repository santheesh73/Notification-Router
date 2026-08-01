"""Unit tests for MutedGroupRule, OfficeRule, FamilyRule, and PersonalRule."""

from config.settings import DATASET_PATH
from src.builders.context_manager import ContextManager
from src.features.feature_pipeline import FeaturePipeline
from src.loaders.load_data import DataRepository
from src.rules.family_rule import FamilyRule
from src.rules.muted_group_rule import MutedGroupRule
from src.rules.office_rule import OfficeRule
from src.rules.personal_rule import PersonalRule


def test_muted_group_rule() -> None:
    """Test MutedGroupRule mutes muted group messages."""
    repo = DataRepository(dataset_path=DATASET_PATH)
    repo.load_all()
    ctx = ContextManager(repo)
    ctx.build()
    pipeline = FeaturePipeline(ctx)

    msg = {
        "message_id": "M_MUTED_TEST",
        "sender_id": "USR_103",
        "recipient_id": "USR_101",
        "group_id": "GRP_502",  # GRP_502 is muted by USR_101
        "text_content": "General chatter in company announcements.",
    }
    vec = pipeline.process(msg)

    rule = MutedGroupRule()
    res = rule.evaluate(vec, ctx)

    assert res is not None
    assert res.action == "mute"
    assert res.message_type == "muted_group"


def test_office_rule() -> None:
    """Test OfficeRule notifies office group messages."""
    repo = DataRepository(dataset_path=DATASET_PATH)
    repo.load_all()
    ctx = ContextManager(repo)
    ctx.build()
    pipeline = FeaturePipeline(ctx)

    msg = {
        "message_id": "M_OFFICE_TEST",
        "sender_id": "USR_103",
        "group_id": "GRP_501",  # GRP_501 is DevOps Alerts (Office type)
        "text_content": "Urgent project deployment updates released.",
    }
    vec = pipeline.process(msg)

    rule = OfficeRule()
    res = rule.evaluate(vec, ctx)

    assert res is not None
    assert res.action == "notify"
    assert res.message_type in ["office", "business_update"]
