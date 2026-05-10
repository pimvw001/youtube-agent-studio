from pathlib import Path

from youtube_agent_studio.settings import load_settings


def test_load_settings_from_config(tmp_path: Path) -> None:
    config = tmp_path / "config.toml"
    config.write_text(
        """
[model]
provider = "openai"
model = "gpt-4.1-mini"

[workflow]
max_review_rounds = 4
save_json = true
save_markdown = true

[video_defaults]
audience = "studenten"
tone = "praktisch"
language = "Nederlands"
length = "kort"
""",
        encoding="utf-8",
    )

    settings = load_settings(config)

    assert settings.provider == "openai"
    assert settings.max_review_rounds == 4
    assert settings.audience == "studenten"
