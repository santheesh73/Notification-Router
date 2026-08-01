"""Unit tests for HistoryContextBuilder."""

from config.settings import DATASET_PATH
from src.builders.history_context_builder import HistoryContextBuilder
from src.loaders.load_data import DataRepository
from src.models.history_profile import HistoryProfile


def test_history_context_builder() -> None:
    """Test building HistoryProfile contexts and O(1) indices."""
    repo = DataRepository(dataset_path=DATASET_PATH)
    repo.load_all()

    builder = HistoryContextBuilder(repo)
    profiles = builder.build()

    assert len(profiles) > 0
    test_id = "MSG_001" if "MSG_001" in profiles else next(iter(profiles.keys()))
    hist = profiles[test_id]
    assert isinstance(hist, HistoryProfile)
    assert hist.message_id == test_id

    # Test O(1) indices
    u_hist = builder.get_user_history("u_001")
    assert isinstance(u_hist, list)

    s_hist = builder.get_sender_history("u_002")
    assert isinstance(s_hist, list)
