"""Feature Engineering Pipeline & Orchestrator."""

from dataclasses import asdict, dataclass, field
from typing import Any

import pandas as pd
from tabulate import tabulate

from src.builders.context_manager import ContextManager
from src.features.business_features import BusinessFeatureExtractor
from src.features.conversation_features import ConversationFeatureExtractor
from src.features.feature_vector import FeatureVector
from src.features.group_features import GroupFeatureExtractor
from src.features.safety_features import SafetyFeatureExtractor
from src.features.sender_features import SenderFeatureExtractor
from src.features.temporal_features import TemporalFeatureExtractor
from src.features.text_features import TextFeatureExtractor
from src.features.user_features import UserFeatureExtractor
from src.utils.logger import logger


@dataclass
class FeatureValidationReport:
    """Dataclass holding validation report for feature vectors."""

    missing_message_ids: list[str] = field(default_factory=list)
    invalid_timestamps: list[str] = field(default_factory=list)
    unknown_conv_types: list[str] = field(default_factory=list)
    invalid_forward_counts: list[str] = field(default_factory=list)
    broken_user_refs: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        """Return True if no critical vector validation errors are found."""
        return (
            len(self.missing_message_ids) == 0
            and len(self.invalid_timestamps) == 0
            and len(self.unknown_conv_types) == 0
            and len(self.invalid_forward_counts) == 0
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert report to dictionary."""
        return asdict(self)


class FeaturePipeline:
    """Orchestrates feature extraction sub-modules to produce FeatureVector instances."""

    def __init__(self, context: ContextManager) -> None:
        """Initialize FeaturePipeline with ContextManager dependency.

        Args:
            context: ContextManager instance.
        """
        self.context: ContextManager = context

        # Instantiate sub-extractors
        self.text_extractor = TextFeatureExtractor()
        self.conv_extractor = ConversationFeatureExtractor()
        self.sender_extractor = SenderFeatureExtractor()
        self.user_extractor = UserFeatureExtractor()
        self.group_extractor = GroupFeatureExtractor()
        self.business_extractor = BusinessFeatureExtractor()
        self.temporal_extractor = TemporalFeatureExtractor()
        self.safety_extractor = SafetyFeatureExtractor()

    def process(self, message: dict[str, Any] | pd.Series) -> FeatureVector:
        """Process a single incoming message and produce a FeatureVector.

        Args:
            message: Message record dictionary or pandas Series.

        Returns:
            Constructed FeatureVector instance.
        """
        msg_dict = message.to_dict() if isinstance(message, pd.Series) else dict(message)

        # Basic metadata extraction
        msg_id = str(msg_dict.get("message_id", "MSG_UNKNOWN"))
        user_id = str(msg_dict.get("recipient_id", msg_dict.get("user_id", "USR_UNKNOWN")))
        sender_id = str(msg_dict.get("sender_id", "USR_UNKNOWN"))
        group_id = str(msg_dict.get("group_id", "")) if str(msg_dict.get("group_id", "")) != "nan" and str(msg_dict.get("group_id", "")) != "" else None
        business_id = sender_id if sender_id.startswith("BUS") else None
        timestamp = str(msg_dict.get("timestamp", "")) or None
        media_type = str(msg_dict.get("message_type", "text")).lower()
        forwarded_count = int(msg_dict.get("forwarded_count", 1 if msg_dict.get("is_forwarded") else 0))

        # Extract raw message text for text-based classification
        raw_text = str(msg_dict.get("message_text", "") or msg_dict.get("text_content", "") or "")
        if raw_text.lower() == "nan":
            raw_text = ""

        # 1. Run Extractors
        text_feats = self.text_extractor.extract(msg_dict, self.context)
        conv_feats = self.conv_extractor.extract(msg_dict, self.context)
        sender_feats = self.sender_extractor.extract(msg_dict, self.context)
        user_feats = self.user_extractor.extract(msg_dict, self.context)
        group_feats = self.group_extractor.extract(msg_dict, self.context)
        biz_feats = self.business_extractor.extract(msg_dict, self.context)
        temp_feats = self.temporal_extractor.extract(msg_dict, self.context)
        safety_feats = self.safety_extractor.extract(msg_dict, self.context)

        # 2. Merge Feature Dictionaries
        merged_kwargs = {
            "message_id": msg_id,
            "user_id": user_id,
            "sender_id": sender_id,
            "group_id": group_id,
            "business_id": business_id,
            "timestamp": timestamp,
            "media_type": media_type,
            "forwarded_count": forwarded_count,
            "message_text": raw_text,
            **text_feats,
            **conv_feats,
            **sender_feats,
            **user_feats,
            **group_feats,
            **biz_feats,
            **temp_feats,
            **safety_feats,
        }

        # 3. Construct FeatureVector
        vector = FeatureVector(**merged_kwargs)
        return vector

    def process_dataset(self, messages_df: pd.DataFrame) -> list[FeatureVector]:
        """Process a dataframe of messages into a list of FeatureVectors.

        Args:
            messages_df: pandas DataFrame containing messages.

        Returns:
            List of FeatureVector objects.
        """
        logger.info(f"Extracting FeatureVectors for {len(messages_df)} messages...")
        vectors: list[FeatureVector] = []
        for _, row in messages_df.iterrows():
            vec = self.process(row)
            vectors.append(vec)
        logger.success(f"Successfully generated {len(vectors)} FeatureVectors.")
        return vectors

    def validate(self, vectors: list[FeatureVector]) -> FeatureValidationReport:
        """Validate extracted FeatureVectors for integrity and broken references.

        Args:
            vectors: List of FeatureVectors.

        Returns:
            FeatureValidationReport object.
        """
        report = FeatureValidationReport()

        for vec in vectors:
            if not vec.message_id or vec.message_id == "MSG_UNKNOWN":
                report.missing_message_ids.append(vec.message_id)

            if vec.conversation_type not in ["personal", "group", "business"]:
                report.unknown_conv_types.append(f"{vec.message_id}: {vec.conversation_type}")

            if vec.forwarded_count < 0:
                report.invalid_forward_counts.append(f"{vec.message_id}: {vec.forwarded_count}")

            # Check user reference exists in context
            if vec.user_id and vec.user_id != "USR_UNKNOWN" and not self.context.get_user(vec.user_id):
                report.broken_user_refs.append(f"{vec.message_id}: user '{vec.user_id}' missing in context")

        logger.info(f"Feature vectors validation completed. Is valid: {report.is_valid}")
        return report

    def summary(self, vectors: list[FeatureVector]) -> str:
        """Generate statistical summary report across extracted feature vectors.

        Args:
            vectors: List of FeatureVectors.

        Returns:
            Formatted ASCII summary table string.
        """
        if not vectors:
            return "No FeatureVectors available for summary."

        total_v = len(vectors)
        avg_len = sum(v.message_length for v in vectors) / total_v
        avg_forwarded = sum(v.forwarded_count for v in vectors) / total_v

        # Distributions
        personal_cnt = sum(1 for v in vectors if v.personal)
        group_cnt = sum(1 for v in vectors if v.group)
        biz_cnt = sum(1 for v in vectors if v.business)

        # Media distribution
        media_dist: dict[str, int] = {}
        for v in vectors:
            m_t = v.media_type or "unknown"
            media_dist[m_t] = media_dist.get(m_t, 0) + 1

        # Safety keywords count
        scam_cnt = sum(1 for v in vectors if v.contains_scam_keyword or v.risk_score > 0.0)

        rows = [
            ["Total Feature Vectors", total_v],
            ["Average Message Length", f"{avg_len:.1f} chars"],
            ["Average Forwarded Count", f"{avg_forwarded:.2f}"],
            ["Personal Messages", f"{personal_cnt} ({personal_cnt / total_v * 100:.1f}%)"],
            ["Group Messages", f"{group_cnt} ({group_cnt / total_v * 100:.1f}%)"],
            ["Business Messages", f"{biz_cnt} ({biz_cnt / total_v * 100:.1f}%)"],
            ["Media Distribution", ", ".join([f"{k}:{v}" for k, v in media_dist.items()])],
            ["Safety Risk Flags", scam_cnt],
        ]

        return tabulate(rows, headers=["Feature Metric", "Statistical Value"], tablefmt="grid")
