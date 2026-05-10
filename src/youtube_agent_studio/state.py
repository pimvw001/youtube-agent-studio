from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime

from youtube_agent_studio.models import ReviewIteration


@dataclass
class AgentStep:
    """Kleine logregel zodat ik later kunt zien wat de agents gedaan hebben."""

    agent: str
    action: str
    note: str = ""


@dataclass
class VideoState:
    """Gedeeld geheugen van de workflow.

    Alle agents lezen uit en schrijven naar dit object. 
    
    """

    topic: str
    audience: str = "beginners"
    tone: str = "duidelijk en informeel"
    language: str = "Nederlands"
    length: str = "kort: ongeveer 3 tot 5 minuten"
    context: str = ""

    plan: str = ""
    idea: str = ""
    research_questions: list[str] = field(default_factory=list)
    research: str = ""
    script: str = ""
    feedback: str = ""
    titles: list[str] = field(default_factory=list)
    thumbnail_idea: str = ""

    research_rounds: int = 0
    script_rounds: int = 0
    review_rounds: int = 0
    approved: bool = False
    final_decision: str = "not_started"

    review_iterations: list[ReviewIteration] = field(default_factory=list)
    steps: list[AgentStep] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def add_step(self, agent: str, action: str, note: str = "") -> None:
        self.steps.append(AgentStep(agent=agent, action=action, note=note.strip()))

    def add_research(self, text: str) -> None:
        """Voeg research toe zonder oude research kwijt te raken."""
        text = text.strip()
        if not text:
            return

        self.research_rounds += 1
        header = f"Research ronde {self.research_rounds}:"

        if self.research:
            self.research += f"\n\n{header}\n{text}"
        else:
            self.research = f"{header}\n{text}"

    def set_script(self, text: str) -> None:
        self.script_rounds += 1
        self.script = text.strip()

    def set_feedback(self, text: str) -> None:
        self.review_rounds += 1
        self.feedback = text.strip()

    def add_review_iteration(self, iteration: ReviewIteration) -> None:
        self.review_iterations.append(iteration)
        self.final_decision = iteration.decision
        self.approved = iteration.decision == "approved"

    def to_dict(self) -> dict:
        data = asdict(self)
        data["review_iterations"] = [iteration.model_dump() for iteration in self.review_iterations]
        return data
