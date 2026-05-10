import os
import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass
class AppSettings:
    provider: str = "fake"
    model: str = ""
    max_review_rounds: int = 3
    save_json: bool = True
    save_markdown: bool = True
    audience: str = "beginners"
    tone: str = "duidelijk en informeel"
    language: str = "Nederlands"
    length: str = "kort: ongeveer 3 tot 5 minuten"


def load_settings(config_path: str | Path = "config.toml") -> AppSettings:
    """Laad de projectinstellingen uit config.toml en .env.

    """
    settings = AppSettings()
    path = Path(config_path)

    if path.exists():
        data = tomllib.loads(path.read_text(encoding="utf-8"))
        model_config = data.get("model", {})
        workflow_config = data.get("workflow", {})
        defaults = data.get("video_defaults", {})

        settings.provider = str(model_config.get("provider", settings.provider))
        settings.model = str(model_config.get("model", settings.model))
        settings.max_review_rounds = int(workflow_config.get("max_review_rounds", settings.max_review_rounds))
        settings.save_json = bool(workflow_config.get("save_json", settings.save_json))
        settings.save_markdown = bool(workflow_config.get("save_markdown", settings.save_markdown))
        settings.audience = str(defaults.get("audience", settings.audience))
        settings.tone = str(defaults.get("tone", settings.tone))
        settings.language = str(defaults.get("language", settings.language))
        settings.length = str(defaults.get("length", settings.length))

    settings.provider = os.getenv("AI_PROVIDER", settings.provider)
    settings.model = os.getenv("AI_MODEL", settings.model)
    settings.max_review_rounds = int(os.getenv("MAX_REVIEW_ROUNDS", settings.max_review_rounds))
    return settings
