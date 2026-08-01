"""HackerRank Orchestrate August 26 Mandatory Compliance Logger."""

from datetime import datetime
import os
import re
from typing import Any

# Sensitive pattern regexes for secret redaction
SECRET_PATTERNS = [
    re.compile(r"gsk_[A-Za-z0-9_]+"),
    re.compile(r"AQ\.[A-Za-z0-9_\-]+"),
    re.compile(r"AIzaSy[A-Za-z0-9_\-]+"),
    re.compile(r"sk-[A-Za-z0-9_]+"),
]


class OrchestrateLogger:
    """Appends compliant session and turn logs to ~/hackerrank_orchestrate_august26/log.txt."""

    def __init__(self) -> None:
        self.log_dir = os.path.join(os.path.expanduser("~"), "hackerrank_orchestrate_august26")
        os.makedirs(self.log_dir, exist_ok=True)
        self.log_path = os.path.join(self.log_dir, "log.txt")

    def _redact_secrets(self, text: str) -> str:
        """Redact API keys, tokens, and secrets from log strings."""
        if not text:
            return ""
        clean_text = str(text)
        for pattern in SECRET_PATTERNS:
            clean_text = pattern.sub("[REDACTED_SECRET]", clean_text)
        return clean_text

    def log_session_start(self, session_name: str = "Notification Router Pipeline Session") -> None:
        """Log SESSION START header with AGREEMENT RECORDED line."""
        now_str = datetime.now().isoformat()
        entry = (
            f"================================================================================\n"
            f"SESSION START: {now_str}\n"
            f"AGREEMENT RECORDED: HackerRank Orchestrate August 2026 Hackathon Terms Accepted\n"
            f"Session: {self._redact_secrets(session_name)}\n"
            f"================================================================================\n"
        )
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(entry)

    def log_turn(
        self,
        turn_num: int,
        user_prompt: str,
        response_summary: str,
        actions: list[str] | str,
        context: str = "",
    ) -> None:
        """Log per-turn interaction block."""
        now_str = datetime.now().isoformat()
        if isinstance(actions, list):
            actions_str = "; ".join(actions)
        else:
            actions_str = str(actions)

        clean_prompt = self._redact_secrets(user_prompt)
        clean_summary = self._redact_secrets(response_summary)
        clean_actions = self._redact_secrets(actions_str)
        clean_context = self._redact_secrets(context)

        entry = (
            f"Turn: {turn_num}\n"
            f"Timestamp: {now_str}\n"
            f"User Prompt: {clean_prompt}\n"
            f"Agent Response Summary: {clean_summary}\n"
            f"Actions: {clean_actions}\n"
            f"Context: {clean_context}\n"
            f"================================================================================\n"
        )
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(entry)
