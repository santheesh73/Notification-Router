"""Unit tests for UserContextBuilder."""

from config.settings import DATASET_PATH
from src.builders.user_context_builder import UserContextBuilder
from src.loaders.load_data import DataRepository
from src.models.user_profile import UserProfile


def test_user_context_builder() -> None:
    """Test building UserProfile contexts."""
    repo = DataRepository(dataset_path=DATASET_PATH)
    repo.load_all()

    builder = UserContextBuilder(repo)
    profiles = builder.build()

    assert len(profiles) > 0
    test_id = "USR_101" if "USR_101" in profiles else next(iter(profiles.keys()))
    user = profiles[test_id]
    assert isinstance(user, UserProfile)
    assert user.user_id == test_id
    assert isinstance(user.reply_rate, float)
    assert isinstance(user.open_rate, float)
    assert isinstance(user.engagement_score, float)
    assert isinstance(user.muted_groups, list)
