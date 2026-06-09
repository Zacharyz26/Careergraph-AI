from pathlib import Path

ALLOWED_RESUME_EXTENSIONS = {".pdf", ".docx"}


def is_supported_resume(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_RESUME_EXTENSIONS


def safe_filename(filename: str) -> str:
    return Path(filename).name.replace("\x00", "")
