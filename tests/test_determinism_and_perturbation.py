"""Phase 11 & 12 Generalization, Perturbation, and Self-Consistency Unit Tests."""

from pathlib import Path

from config.settings import DATASET_PATH
from src.builders.context_manager import ContextManager
from src.features.feature_pipeline import FeaturePipeline
from src.loaders.load_data import DataRepository
from src.rules.rule_engine import NotificationRuleEngine


def test_pipeline_self_consistency() -> None:
    """Phase 12: Verify pipeline self-consistency by running twice and comparing outputs."""
    repo = DataRepository(dataset_path=DATASET_PATH, input_file=Path("dataset/sample_messages.csv"))
    repo.load_all()
    context = ContextManager(repo)
    context.build()

    fp = FeaturePipeline(context)
    engine = NotificationRuleEngine()

    df = repo.get_dataframe("messages")

    run_1 = [engine.route(fp.process(r.to_dict()), context) for _, r in df.iterrows()]
    
    # Re-instantiate pipeline to test determinism
    fp_2 = FeaturePipeline(context)
    engine_2 = NotificationRuleEngine()
    run_2 = [engine_2.route(fp_2.process(r.to_dict()), context) for _, r in df.iterrows()]

    assert len(run_1) == len(run_2)
    for res1, res2 in zip(run_1, run_2, strict=True):
        assert res1.action == res2.action, f"Action mismatch for {res1.message_id}"
        assert res1.message_type == res2.message_type, f"Message type mismatch for {res1.message_id}"
        assert res1.triggered_rule == res2.triggered_rule, f"Rule mismatch for {res1.message_id}"


def test_perturbation_stability() -> None:
    """Phase 11: Verify prediction stability under whitespace and timestamp perturbations."""
    repo = DataRepository(dataset_path=DATASET_PATH, input_file=Path("dataset/sample_messages.csv"))
    repo.load_all()
    context = ContextManager(repo)
    context.build()

    fp = FeaturePipeline(context)
    engine = NotificationRuleEngine()

    sample_msg = {
        "message_id": "M_TEST_PERTURB",
        "sender_user_id": "USR_001",
        "recipient_id": "USR_002",
        "message_text": "  EMERGENCY: Urgent hospital help needed immediately!  ",
        "created_at": "2026-08-01 10:00:00",
    }

    res_orig = engine.route(fp.process(sample_msg), context)

    # Perturbed version (altered timestamp, extra spaces, mixed case)
    sample_msg_perturbed = {
        "message_id": "M_TEST_PERTURB",
        "sender_user_id": "USR_001",
        "recipient_id": "USR_002",
        "message_text": "emergency: URGENT hospital help needed immediately!",
        "created_at": "2026-08-02 18:30:15",
    }

    res_pert = engine.route(fp.process(sample_msg_perturbed), context)

    assert res_orig.action == res_pert.action == "notify"
    assert res_orig.message_type == res_pert.message_type == "urgent"
