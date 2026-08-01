"""Unit tests for GroupContextBuilder."""

from config.settings import DATASET_PATH
from src.builders.group_context_builder import GroupContextBuilder
from src.loaders.load_data import DataRepository
from src.models.group_profile import GroupProfile


def test_group_context_builder() -> None:
    """Test building GroupProfile contexts."""
    repo = DataRepository(dataset_path=DATASET_PATH)
    repo.load_all()

    builder = GroupContextBuilder(repo)
    profiles = builder.build()

    assert len(profiles) > 0
    test_id = "GRP_501" if "GRP_501" in profiles else next(iter(profiles.keys()))
    group = profiles[test_id]
    assert isinstance(group, GroupProfile)
    assert group.group_id == test_id
    assert group.member_count > 0
    assert group.importance_score >= 0.0
