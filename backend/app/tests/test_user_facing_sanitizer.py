from app.services.user_facing_sanitizer import (
    sanitize_user_facing_text,
    user_facing_artifact_reasons,
)


def test_sanitizer_removes_internal_markers_and_citation_artifacts() -> None:
    text = "Lead with project evidence (E018) [source: parser] [1]."

    assert sanitize_user_facing_text(text) == "Lead with project evidence."
    assert user_facing_artifact_reasons(text) == [
        "contains an internal evidence marker",
        "contains a citation artifact",
    ]


def test_sanitizer_flags_placeholders_without_rewriting_claims() -> None:
    text = "Improved process by [insert metric] using documented evidence."

    assert "contains placeholder text" in user_facing_artifact_reasons(text)
    assert "Improved process by" in sanitize_user_facing_text(text)
