from youtube_agent_studio.agents import (
    IdeaAgent,
    PlannerAgent,
    ResearchAgent,
    ResearchQuestionAgent,
    ReviewAgent,
    ScriptAgent,
    ThumbnailAgent,
    TitleAgent,
)
from youtube_agent_studio.llm import LLMClient
from youtube_agent_studio.models import ReviewIteration
from youtube_agent_studio.state import VideoState


class VideoWorkflow:
    """Een kleine agentic workflow voor een YouTube video-plan.

    De workflow Het idee is :
    - agents delen state;
    - de review-agent mag bepalen wat de volgende stap is;
    - de loop stopt na een maximum aantal rondes.
    """

    def __init__(self, llm: LLMClient, max_review_rounds: int = 3) -> None:
        self.max_review_rounds = max(1, max_review_rounds)
        self.planner_agent = PlannerAgent(llm)
        self.idea_agent = IdeaAgent(llm)
        self.research_question_agent = ResearchQuestionAgent(llm)
        self.research_agent = ResearchAgent(llm)
        self.script_agent = ScriptAgent(llm)
        self.review_agent = ReviewAgent(llm)
        self.title_agent = TitleAgent(llm)
        self.thumbnail_agent = ThumbnailAgent(llm)

    def run(
        self,
        topic: str,
        audience: str = "beginners",
        tone: str = "duidelijk en informeel",
        language: str = "Nederlands",
        length: str = "kort: ongeveer 3 tot 5 minuten",
        context: str = "",
        verbose: bool = True,
    ) -> VideoState:
        topic = topic.strip()
        if not topic:
            raise ValueError("Topic cannot be empty.")

        state = VideoState(
            topic=topic,
            audience=audience.strip() or "beginners",
            tone=tone.strip() or "duidelijk en informeel",
            language=language.strip() or "Nederlands",
            length=length.strip() or "kort: ongeveer 3 tot 5 minuten",
            context=context.strip(),
        )

        self._say(verbose, "1/8 Plan maken...")
        self.planner_agent.run(state)

        self._say(verbose, "2/8 Idee maken...")
        self.idea_agent.run(state)

        self._say(verbose, "3/8 Researchvragen maken...")
        self.research_question_agent.run(state)

        self._say(verbose, "4/8 Eerste research maken...")
        self.research_agent.run(state)

        self._run_agentic_script_loop(state, verbose=verbose)

        self._say(verbose, "7/8 Titels maken...")
        self.title_agent.run(state)

        self._say(verbose, "8/8 Thumbnail-idee maken...")
        self.thumbnail_agent.run(state)

        return state

    def _run_agentic_script_loop(self, state: VideoState, verbose: bool) -> None:
        """Laat review feedback bepalen of research/script nog een ronde nodig heeft."""
        instruction = ""

        for round_number in range(1, self.max_review_rounds + 1):
            self._say(verbose, f"5/8 Script maken of verbeteren... ronde {round_number}")
            self.script_agent.run(state, instruction=instruction)

            self._say(verbose, f"6/8 Script reviewen... ronde {round_number}")
            review = self.review_agent.run(state)

            action = self._decide_next_action(
                decision=review.decision,
                round_number=round_number,
            )
            state.add_review_iteration(
                ReviewIteration(
                    round_number=round_number,
                    decision=review.decision,
                    score=review.score,
                    feedback=review.feedback,
                    action=action,
                )
            )

            if review.decision == "approved":
                state.add_step("Workflow", "loop_finished", "Review-agent keurde het script goed.")
                return

            if round_number == self.max_review_rounds:
                state.add_step("Workflow", "loop_stopped", "Maximum aantal reviewrondes bereikt.")
                return

            feedback_text = "; ".join(review.feedback + review.required_changes)
            if review.decision == "needs_more_research":
                self._say(verbose, "Review vraagt extra research. ResearchAgent draait nog één keer...")
                self.research_agent.run(state, reason=feedback_text or state.feedback)
                instruction = "Verbeter het script met de extra research en review-feedback."
                continue

            if review.decision == "needs_script_changes":
                instruction = feedback_text or state.feedback
                continue

            state.add_step("Workflow", "unknown_decision", f"Onverwachte beslissing: {review.decision}")
            return

    def _decide_next_action(self, decision: str, round_number: int) -> str:
        if decision == "approved":
            return "stop: script approved"
        if round_number == self.max_review_rounds:
            return "stop: max review rounds reached"
        if decision == "needs_more_research":
            return "run research again, then rewrite script"
        if decision == "needs_script_changes":
            return "rewrite script with review feedback"
        return "stop: unknown review decision"

    @staticmethod
    def _say(verbose: bool, message: str) -> None:
        if verbose:
            print(message)
