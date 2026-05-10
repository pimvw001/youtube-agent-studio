from youtube_agent_studio.models import ReviewIteration
from youtube_agent_studio.state import VideoState


def test_add_research_keeps_old_research() -> None:
    state = VideoState(topic="AI")

    state.add_research("Eerste notes")
    state.add_research("Tweede notes")

    assert "Research ronde 1" in state.research
    assert "Research ronde 2" in state.research
    assert state.research_rounds == 2


def test_review_iteration_in_dict() -> None:
    state = VideoState(topic="AI")
    state.add_review_iteration(
        ReviewIteration(
            round_number=1,
            decision="approved",
            score=8,
            feedback=["Goed genoeg"],
            action="stop: script approved",
        )
    )

    data = state.to_dict()

    assert data["review_iterations"][0]["score"] == 8
    assert data["approved"] is True
