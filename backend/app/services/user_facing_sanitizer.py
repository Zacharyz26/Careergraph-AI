import re


INTERNAL_MARKER_PATTERN = re.compile(
    r"(?:\(|\[|\{)\s*(?:evidence|source|trace|debug|id)?\s*e\d{2,}\s*(?:\)|\]|\})"
    r"|(?:\(|\[|\{)\s*(?:evidence|source|trace|debug)\s*[:#-]?\s*[^)\]\}]+(?:\)|\]|\})"
    r"|\b(?:evidence|source|trace|debug)\s*(?:id)?\s*[:#-]\s*e?\d{2,}\b"
    r"|\be\d{2,}\b",
    re.IGNORECASE,
)
CITATION_ARTIFACT_PATTERN = re.compile(
    r"\[(?:source|citation|cite|ref|evidence)[^\]]*\]"
    r"|\((?:source|citation|cite|ref|evidence)[^)]*\)"
    r"|\[\d+\]",
    re.IGNORECASE,
)
PLACEHOLDER_PATTERN = re.compile(
    r"\[(?:insert|add|metric|number|details?|placeholder)[^\]]*\]"
    r"|<(?:insert|add|metric|number|details?|placeholder)[^>]*>"
    r"|\b(?:tbd|xx+|x%)\b",
    re.IGNORECASE,
)
WHITESPACE_PATTERN = re.compile(r"\s+")
PUNCTUATION_SPACING_PATTERN = re.compile(r"\s+([,.;:!?])")


def sanitize_user_facing_text(value: str) -> str:
    """Remove internal artifacts from prose intended for users."""

    cleaned = INTERNAL_MARKER_PATTERN.sub("", value)
    cleaned = CITATION_ARTIFACT_PATTERN.sub("", cleaned)
    cleaned = WHITESPACE_PATTERN.sub(" ", cleaned)
    cleaned = PUNCTUATION_SPACING_PATTERN.sub(r"\1", cleaned)
    cleaned = re.sub(r"\(\s*\)", "", cleaned)
    cleaned = re.sub(r"\[\s*\]", "", cleaned)
    return cleaned.strip(" -")


def user_facing_artifact_reasons(value: str) -> list[str]:
    reasons = []
    if INTERNAL_MARKER_PATTERN.search(value):
        reasons.append("contains an internal evidence marker")
    if CITATION_ARTIFACT_PATTERN.search(value):
        reasons.append("contains a citation artifact")
    if PLACEHOLDER_PATTERN.search(value):
        reasons.append("contains placeholder text")
    return reasons


def has_user_facing_artifact(value: str) -> bool:
    return bool(user_facing_artifact_reasons(value))
