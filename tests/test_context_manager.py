"""Unit tests for ContextManager."""

from config.settings import DATASET_PATH
from src.builders.context_manager import ContextManager, ContextValidationReport
from src.loaders.load_data import DataRepository
from src.models.user_profile import UserProfile


def test_context_manager_build_and_get() -> None:
    """Test ContextManager build, caching, and retrieval."""
    repo = DataRepository(dataset_path=DATASET_PATH)
    repo.load_all()

    ctx = ContextManager(repo)
    ctx.build()

    u_id = "USR_101" if ctx.get_user("USR_101") else next(iter(ctx.user_builder._cache.keys()))
    user = ctx.get_user(u_id)
    assert user is not None
    assert isinstance(user, UserProfile)

    g_id = "GRP_501" if ctx.get_group("GRP_501") else next(iter(ctx.group_builder._cache.keys()))
    group = ctx.get_group(g_id)
    assert group is not None

    b_id = "BUS_301" if ctx.get_business("BUS_301") else next(iter(ctx.business_builder._cache.keys()))
    biz = ctx.get_business(b_id)
    assert biz is not None

    h_id = "MSG_001" if ctx.get_history("MSG_001") else next(iter(ctx.history_builder._cache.keys()))
    msg = ctx.get_history(h_id)
    assert msg is not None


def test_context_manager_validation() -> None:
    """Test context manager validation report."""
    repo = DataRepository(dataset_path=DATASET_PATH)
    repo.load_all()

    ctx = ContextManager(repo)
    ctx.build()

    report = ctx.validate()
    assert isinstance(report, ContextValidationReport)
    assert report.is_valid is True


def test_context_manager_summary() -> None:
    """Test context manager summary report string."""
    repo = DataRepository(dataset_path=DATASET_PATH)
    repo.load_all()

    ctx = ContextManager(repo)
    ctx.build()

    summary_str = ctx.summary()
    assert isinstance(summary_str, str)
    assert "Users Loaded" in summary_str
    assert "Average Engagement" in summary_str
