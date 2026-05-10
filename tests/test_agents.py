from youtube_agent_studio.agents import (
    IdeaAgent,
    PlannerAgent,
    ResearchAgent,
    ResearchQuestionAgent,
    ThumbnailAgent,
    clean_title_list,
    parse_review_decision,
    parse_review_result,
)
from youtube_agent_studio.llm import FakeLLMClient
from youtube_agent_studio.state import VideoState


def test_planner_agent_updates_state() -> None:
    state = VideoState(topic="Python leren")
    agent = PlannerAgent(FakeLLMClient())

    agent.run(state)

    assert state.plan != ""
    assert state.steps[-1].agent == "PlannerAgent"


def test_idea_agent_updates_state() -> None:
    state = VideoState(topic="Python leren", plan="Maak het simpel")
    agent = IdeaAgent(FakeLLMClient())

    agent.run(state)

    assert state.idea != ""


def test_research_question_agent_updates_state() -> None:
    state = VideoState(topic="Python leren", plan="Maak het simpel", idea="Beginner video")
    agent = ResearchQuestionAgent(FakeLLMClient())

    agent.run(state)

    assert len(state.research_questions) == 3


def test_research_agent_adds_research() -> None:
    state = VideoState(topic="Python leren", idea="Maak een beginner video")
    agent = ResearchAgent(FakeLLMClient())

    agent.run(state)

    assert state.research_rounds == 1
    assert "Research ronde 1" in state.research


def test_research_agent_can_use_reason() -> None:
    state = VideoState(topic="Python leren", idea="Maak een beginner video")
    agent = ResearchAgent(FakeLLMClient())

    agent.run(state, reason="Extra uitleg over voorbeelden nodig")

    assert state.research_rounds == 1
    assert state.steps[-1].note == "Extra uitleg over voorbeelden nodig"


def test_thumbnail_agent_updates_state() -> None:
    state = VideoState(topic="Python leren", script="Een kort script")
    agent = ThumbnailAgent(FakeLLMClient())

    agent.run(state)

    assert state.thumbnail_idea != ""


def test_clean_title_list_removes_numbers() -> None:
    raw_titles = "1. Eerste titel\n2) Tweede titel\n- Derde titel"

    titles = clean_title_list(raw_titles)

    assert titles == ["Eerste titel", "Tweede titel", "Derde titel"]


def test_parse_review_decision() -> None:
    assert parse_review_decision("DECISION: approved") == "approved"
    assert parse_review_decision("DECISION: needs_more_research") == "needs_more_research"
    assert parse_review_decision("DECISION: needs-script-changes") == "needs_script_changes"
    assert parse_review_decision("er is meer research nodig") == "needs_more_research"


def test_parse_review_result_from_json() -> None:
    result = parse_review_result(
        '{"decision": "needs_script_changes", "score": 6, '
        '"feedback": ["Intro is te algemeen"], "required_changes": ["Maak intro concreter"]}'
    )

    assert result.decision == "needs_script_changes"
    assert result.score == 6
    assert result.feedback == ["Intro is te algemeen"]


def test_parse_review_result_falls_back_to_text() -> None:
    result = parse_review_result("SCORE: 5\nDECISION: needs_more_research\nFEEDBACK: Er mist context")

    assert result.decision == "needs_more_research"
    assert result.score == 5
