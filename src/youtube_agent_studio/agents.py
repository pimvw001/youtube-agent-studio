import json
import re

from pydantic import ValidationError

from youtube_agent_studio.llm import LLMClient
from youtube_agent_studio.models import ReviewResult
from youtube_agent_studio.prompts import load_prompt
from youtube_agent_studio.state import VideoState


class PlannerAgent:
    """Bepaalt eerst globaal hoe de video aangepakt moet worden."""

    name = "PlannerAgent"

    def __init__(self, llm: LLMClient) -> None:
        self.llm = llm

    def run(self, state: VideoState) -> None:
        prompt = load_prompt("planner").format(
            topic=state.topic,
            audience=state.audience,
            tone=state.tone,
            language=state.language,
            length=state.length,
            context=state.context or "Geen extra context.",
        )
        state.plan = self.llm.generate(prompt).strip()
        state.add_step(self.name, "created_plan", "Globale aanpak gemaakt.")


class IdeaAgent:
    name = "IdeaAgent"

    def __init__(self, llm: LLMClient) -> None:
        self.llm = llm

    def run(self, state: VideoState) -> None:
        prompt = load_prompt("idea").format(
            topic=state.topic,
            audience=state.audience,
            tone=state.tone,
            language=state.language,
            length=state.length,
            plan=state.plan,
            context=state.context or "Geen extra context.",
        )
        state.idea = self.llm.generate(prompt).strip()
        state.add_step(self.name, "created_idea", "Video-idee gemaakt.")


class ResearchQuestionAgent:
    """Bedenkt eerst researchvragen voordat de research agent notes maakt."""

    name = "ResearchQuestionAgent"

    def __init__(self, llm: LLMClient) -> None:
        self.llm = llm

    def run(self, state: VideoState) -> None:
        prompt = load_prompt("research_questions").format(
            topic=state.topic,
            plan=state.plan,
            idea=state.idea,
            context=state.context or "Geen extra context.",
        )
        state.research_questions = clean_title_list(self.llm.generate(prompt))[:3]
        state.add_step(self.name, "created_research_questions", "Researchvragen gemaakt.")


class ResearchAgent:
    name = "ResearchAgent"

    def __init__(self, llm: LLMClient) -> None:
        self.llm = llm

    def run(self, state: VideoState, reason: str = "") -> None:
        prompt = load_prompt("research").format(
            topic=state.topic,
            audience=state.audience,
            language=state.language,
            plan=state.plan,
            idea=state.idea,
            research_questions="\n".join(f"- {question}" for question in state.research_questions)
            or "Geen aparte researchvragen.",
            existing_research=state.research or "Nog geen research.",
            extra_context=reason.strip() or state.context or "Geen extra vraag.",
        )
        research = self.llm.generate(prompt)
        state.add_research(research)
        state.add_step(self.name, "added_research", reason or "Researchronde uitgevoerd.")


class ScriptAgent:
    name = "ScriptAgent"

    def __init__(self, llm: LLMClient) -> None:
        self.llm = llm

    def run(self, state: VideoState, instruction: str = "") -> None:
        prompt = load_prompt("script").format(
            topic=state.topic,
            audience=state.audience,
            tone=state.tone,
            language=state.language,
            length=state.length,
            plan=state.plan,
            idea=state.idea,
            research=state.research,
            feedback=instruction.strip() or "Geen feedback, schrijf een eerste versie.",
        )
        state.set_script(self.llm.generate(prompt))
        state.add_step(self.name, "created_or_updated_script", instruction or "Eerste scriptversie.")


class ReviewAgent:
    name = "ReviewAgent"

    def __init__(self, llm: LLMClient) -> None:
        self.llm = llm

    def run(self, state: VideoState) -> ReviewResult:
        prompt = load_prompt("review").format(
            topic=state.topic,
            audience=state.audience,
            tone=state.tone,
            language=state.language,
            length=state.length,
            plan=state.plan,
            idea=state.idea,
            research=state.research,
            script=state.script,
        )
        state.set_feedback(self.llm.generate(prompt))
        result = parse_review_result(state.feedback)
        state.add_step(self.name, "reviewed_script", f"Decision: {result.decision}, score: {result.score}/10")
        return result


class TitleAgent:
    name = "TitleAgent"

    def __init__(self, llm: LLMClient) -> None:
        self.llm = llm

    def run(self, state: VideoState) -> None:
        prompt = load_prompt("titles").format(
            topic=state.topic,
            audience=state.audience,
            language=state.language,
            script=state.script,
        )
        raw_titles = self.llm.generate(prompt)
        state.titles = clean_title_list(raw_titles)
        state.add_step(self.name, "created_titles", f"{len(state.titles)} titels gemaakt.")


class ThumbnailAgent:
    name = "ThumbnailAgent"

    def __init__(self, llm: LLMClient) -> None:
        self.llm = llm

    def run(self, state: VideoState) -> None:
        prompt = load_prompt("thumbnail").format(
            topic=state.topic,
            audience=state.audience,
            language=state.language,
            script=state.script,
            titles="\n".join(state.titles),
        )
        state.thumbnail_idea = self.llm.generate(prompt).strip()
        state.add_step(self.name, "created_thumbnail_brief", "Thumbnail-brief gemaakt.")


def parse_review_result(feedback: str) -> ReviewResult:
    """De prompt vraagt JSON, maar een LLM kan soms extra tekst of oud format teruggeven.
    Daarom is deze parser bewust tolerant.
    """
    json_text = extract_json_object(feedback)
    if json_text:
        try:
            return ReviewResult.model_validate_json(json_text)
        except ValidationError:
            pass

    decision = parse_review_decision(feedback)
    score = parse_review_score(feedback)
    feedback_lines = parse_feedback_lines(feedback)
    return ReviewResult(decision=decision, score=score, feedback=feedback_lines)


def extract_json_object(text: str) -> str | None:
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        return None

   
    candidate = match.group(0)
    try:
        json.loads(candidate)
    except json.JSONDecodeError:
        return None
    return candidate


def parse_review_decision(feedback: str) -> str:
    feedback_lower = feedback.lower()
    match = re.search(r"decision\s*:\s*([a-z_ -]+)", feedback_lower)

    if match:
        decision = match.group(1).strip().replace(" ", "_").replace("-", "_")
        if decision in {"approved", "needs_more_research", "needs_script_changes"}:
            return decision

    if "meer research" in feedback_lower or "extra research" in feedback_lower:
        return "needs_more_research"
    if "aanpassen" in feedback_lower or "verbeter" in feedback_lower:
        return "needs_script_changes"
    return "approved"


def parse_review_score(feedback: str) -> int:
    match = re.search(r"score\D+(\d{1,2})", feedback.lower())
    if not match:
        return 7
    return max(1, min(10, int(match.group(1))))


def parse_feedback_lines(feedback: str) -> list[str]:
    lines: list[str] = []
    for line in feedback.splitlines():
        cleaned = re.sub(r"^\s*(?:[-•]\s*|feedback\s*:\s*)", "", line, flags=re.IGNORECASE).strip()
        if cleaned and not cleaned.lower().startswith(("decision", "score")):
            lines.append(cleaned)
    return lines[:5] or [feedback.strip()]


def clean_title_list(raw_text: str) -> list[str]:
    """Maak van AI-output een simpele lijst met maximaal 5 regels."""
    titles: list[str] = []

    for line in raw_text.splitlines():
        title = re.sub(r"^\s*(?:[-•]\s*|\d+[.)]\s*)", "", line).strip()
        if title and not title.lower().startswith(("titels", "title")):
            titles.append(title)

    return titles[:5]
