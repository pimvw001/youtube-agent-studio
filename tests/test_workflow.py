import pytest

from youtube_agent_studio.llm import FakeLLMClient, make_llm_client
from youtube_agent_studio.workflow import VideoWorkflow


def test_workflow_makes_video_plan() -> None:
    workflow = VideoWorkflow(FakeLLMClient())

    state = workflow.run(
        "AI voor studenten",
        audience="mbo studenten",
        tone="vlot",
        context="Gebruik vooral praktische voorbeelden.",
        verbose=False,
    )

    assert state.topic == "AI voor studenten"
    assert state.audience == "mbo studenten"
    assert state.context
    assert state.plan
    assert state.idea
    assert state.research_questions
    assert state.research
    assert state.script
    assert state.titles
    assert state.thumbnail_idea
    assert state.steps


def test_agentic_loop_can_approve_after_second_review() -> None:
    workflow = VideoWorkflow(FakeLLMClient(), max_review_rounds=2)

    state = workflow.run("AI voor studenten", verbose=False)

    assert state.review_rounds == 2
    assert state.approved is True
    assert state.final_decision == "approved"
    assert len(state.review_iterations) == 2
    assert state.review_iterations[0].action == "rewrite script with review feedback"


def test_workflow_rejects_empty_topic() -> None:
    workflow = VideoWorkflow(FakeLLMClient())

    with pytest.raises(ValueError):
        workflow.run("   ", verbose=False)


def test_make_fake_llm_client() -> None:
    client = make_llm_client("fake")

    assert client.generate("test")


def test_unknown_provider_raises_error() -> None:
    with pytest.raises(RuntimeError):
        make_llm_client("unknown")
