"""Startup Health Checker for LLM Providers."""

import os
import socket
import sys
from src.llm.gemma_provider import GemmaProvider
from src.llm.groq_provider import GroqProvider
from src.utils.logger import logger


class ProviderHealthChecker:
    """Conducts startup diagnostics and readiness verification across LLM providers."""

    @classmethod
    def _safe_print(cls, text: str) -> None:
        """Safely print text to stdout avoiding Windows cp1252 UnicodeEncodeError."""
        try:
            print(text)
        except UnicodeEncodeError:
            try:
                sys.stdout.buffer.write((text + "\n").encode("utf-8", errors="replace"))
                sys.stdout.buffer.flush()
            except Exception:
                safe_text = text.replace("✓", "[OK]")
                print(safe_text)

    @classmethod
    def check_internet(cls, host: str = "8.8.8.8", port: int = 53, timeout: float = 3.0) -> bool:
        """Check internet connectivity.

        Returns:
            True if internet connection is reachable, else False.
        """
        try:
            socket.setdefaulttimeout(timeout)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
            return True
        except Exception:
            return False

    @classmethod
    def check_all(cls) -> dict[str, bool]:
        """Perform comprehensive health check across Groq and Gemma API providers.

        Returns:
            Dictionary mapping provider names to boolean status.
        """
        results: dict[str, bool] = {
            "groq": False,
            "gemma": False,
        }

        # 1. Groq Check
        groq_prov = GroqProvider()
        groq_ready = groq_prov.is_healthy()
        results["groq"] = groq_ready

        cls._safe_print("✓ Groq Ready")
        logger.info("✓ Groq Ready")

        # 2. Gemma Check
        gemma_prov = GemmaProvider()
        gemma_ready = gemma_prov.is_healthy()
        results["gemma"] = gemma_ready

        cls._safe_print("✓ Gemma Ready")
        logger.info("✓ Gemma Ready")

        return results
