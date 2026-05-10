from pathlib import Path

PROMPT_DIR = Path(__file__).parent / "prompts"


def load_prompt(name: str) -> str:
    """Laad een prompt uit de prompts-map."""
    path = PROMPT_DIR / f"{name}.txt"
    if not path.exists():
        raise FileNotFoundError(f"Prompt not found: {path}")
    return path.read_text(encoding="utf-8")
