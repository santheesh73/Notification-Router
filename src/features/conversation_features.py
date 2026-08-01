"""Conversation Feature Extractor."""

from typing import Any

from src.builders.context_manager import ContextManager
from src.features.base_feature import BaseFeatureExtractor


class ConversationFeatureExtractor(BaseFeatureExtractor):
    """Extracts structural conversation features from message metadata."""

    def extract(
        self,
        message: dict[str, Any],
        context: ContextManager,
    ) -> dict[str, Any]:
        """Extract conversation features.

        Args:
            message: Message record dictionary.
            context: ContextManager instance.

        Returns:
            Dictionary of conversation feature signals.
        """
        sender_id = str(message.get("sender_id", ""))
        group_id = str(message.get("group_id", "")) if str(message.get("group_id", "")) != "nan" and str(message.get("group_id", "")) != "" else None

        # Determine conversation type
        if group_id:
            conv_type = "group"
        elif sender_id.startswith("BUS"):
            conv_type = "business"
        else:
            conv_type = "personal"

        is_personal = conv_type == "personal"
        is_group = conv_type == "group"
        is_business = conv_type == "business"

        # Media & Forwarding signals
        msg_type = str(message.get("message_type", "text")).lower()
        has_media = bool(message.get("has_media", False)) or msg_type in ["image", "voice", "audio", "video", "document"]
        is_forwarded = bool(message.get("is_forwarded", False))
        forward_level = int(message.get("forwarded_count", 1 if is_forwarded else 0))

        return {
            "conversation_type": conv_type,
            "personal": is_personal,
            "group": is_group,
            "business": is_business,
            "is_forwarded": is_forwarded,
            "forward_level": forward_level,
            "media_type": msg_type,
            "has_media": has_media,
        }
