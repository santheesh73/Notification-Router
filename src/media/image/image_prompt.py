"""Structured Prompts for Vision AI Models."""


class ImagePromptBuilder:
    """Generates structured prompts for Vision AI models (GPT-4.5-VL, Qwen-VL)."""

    @staticmethod
    def build_extraction_prompt(image_description: str = "") -> str:
        """Build standard JSON extraction prompt for Vision model.

        Args:
            image_description: Optional contextual note or metadata.

        Returns:
            Prompt text string requesting structured JSON output.
        """
        return """Analyze the attached image and extract structured information in valid JSON format with keys:
- classification: Choose one of ["Poster", "Meeting Notice", "Invoice", "Receipt", "Business Promotion", "Advertisement", "Scam", "Payment Screenshot", "Exam Notice", "Assignment Notice", "Government Notice", "College Circular", "Bank Message", "Travel Ticket", "Medical Report", "Chat Screenshot", "QR Code", "Document", "Unknown"]
- summary: Brief 1-2 sentence description of image content.
- visible_text: All readable text in image.
- entities: Key keywords or topics.
- dates: List of explicit dates found.
- times: List of times found.
- amounts: Monetary amounts or prices found.
- people: Names of individuals mentioned.
- organizations: Names of companies, schools, or agencies.
- locations: Addresses, venues, or places.
- urgency: One of ["low", "medium", "high", "critical"].
- risk: One of ["low", "medium", "high"].
- confidence: Confidence float between 0.0 and 1.0.
"""
