"""Unit tests for BusinessContextBuilder."""

from config.settings import DATASET_PATH
from src.builders.business_context_builder import BusinessContextBuilder
from src.loaders.load_data import DataRepository
from src.models.business_profile import BusinessProfile


def test_business_context_builder() -> None:
    """Test building BusinessProfile contexts."""
    repo = DataRepository(dataset_path=DATASET_PATH)
    repo.load_all()

    builder = BusinessContextBuilder(repo)
    profiles = builder.build()

    assert len(profiles) > 0
    test_id = "BUS_301" if "BUS_301" in profiles else next(iter(profiles.keys()))
    bus = profiles[test_id]
    assert isinstance(bus, BusinessProfile)
    assert bus.business_id == test_id
    assert bus.trust_score >= 0.0
