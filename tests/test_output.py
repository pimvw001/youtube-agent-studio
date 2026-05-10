from youtube_agent_studio.llm import FakeLLMClient
from youtube_agent_studio.output import make_safe_filename, save_json, save_markdown, to_markdown
from youtube_agent_studio.workflow import VideoWorkflow


def test_make_safe_filename() -> None:
    assert make_safe_filename("AI tools voor studenten!") == "ai-tools-voor-studenten"


def test_markdown_contains_review_loop() -> None:
    workflow = VideoWorkflow(FakeLLMClient(), max_review_rounds=2)
    state = workflow.run("AI tools voor studenten", verbose=False)

    markdown = to_markdown(state)

    assert "## Review loop" in markdown
    assert "Review ronde 1" in markdown
    assert "## Researchvragen" in markdown


def test_save_markdown_and_json(tmp_path) -> None:
    workflow = VideoWorkflow(FakeLLMClient())
    state = workflow.run("AI tools voor studenten", verbose=False)

    markdown_path = save_markdown(state, output_dir=str(tmp_path))
    json_path = save_json(state, output_dir=str(tmp_path))

    assert markdown_path.exists()
    assert json_path.exists()
