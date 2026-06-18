from app.schemas.common import PreferredLanguage


def language_name(language: PreferredLanguage) -> str:
    return "Chinese" if language == "zh" else "English"


def advisor_language_instruction(language: PreferredLanguage) -> str:
    if language == "zh":
        return (
            "Language preference: write user-facing explanations, summaries, "
            "career direction names, gaps, and next actions in Simplified Chinese. "
            "Keep schema field names and enum values unchanged. Preserve resume "
            "evidence excerpts in their source language. Keep resume-ready rewrites "
            "in the same language as the source resume text unless the source text "
            "is already Chinese. Keep technical skill, tool, framework, and model "
            "names such as Python, C/C++, ComfyUI, LoRA, and Stable Diffusion in "
            "their original or commonly used form."
        )
    return (
        "Language preference: write user-facing explanations, summaries, career "
        "direction names, gaps, and next actions in English. Keep schema field names "
        "and enum values unchanged. Preserve resume evidence excerpts in their "
        "source language. Keep resume-ready rewrites in the same language as the "
        "source resume text. Keep technical skill, tool, framework, and model names "
        "in their original or commonly used form."
    )
