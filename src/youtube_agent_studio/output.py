import json
from pathlib import Path

from youtube_agent_studio.state import VideoState


def save_markdown(state: VideoState, output_dir: str = "outputs") -> Path:
    folder = Path(output_dir)
    folder.mkdir(parents=True, exist_ok=True)

    path = unique_path(folder / f"{make_safe_filename(state.topic)}.md")
    path.write_text(to_markdown(state), encoding="utf-8")
    return path


def save_json(state: VideoState, output_dir: str = "outputs") -> Path:
    folder = Path(output_dir)
    folder.mkdir(parents=True, exist_ok=True)

    path = unique_path(folder / f"{make_safe_filename(state.topic)}.json")
    path.write_text(json.dumps(state.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def to_markdown(state: VideoState) -> str:
    titles = "\n".join(f"- {title}" for title in state.titles) or "- Geen titels gemaakt"
    questions = "\n".join(f"- {question}" for question in state.research_questions) or "- Geen researchvragen gemaakt"
    reviews = format_review_iterations(state)
    steps = format_agent_steps(state)

    return f"""# YouTube Video Plan

## Onderwerp
{state.topic}

## Doelgroep
{state.audience}

## Taal
{state.language}

## Toon
{state.tone}

## Lengte
{state.length}

## Extra context
{state.context or "Geen extra context meegegeven."}

## Agent status
- Research rondes: {state.research_rounds}
- Script rondes: {state.script_rounds}
- Review rondes: {state.review_rounds}
- Goedgekeurd door review-agent: {"ja" if state.approved else "nee"}
- Laatste beslissing: {state.final_decision}

## Plan
{state.plan}

## Idee
{state.idea}

## Researchvragen
{questions}

## Research
{state.research}

## Script
{state.script}

## Review loop
{reviews}

## Laatste feedback
{state.feedback}

## Titels
{titles}

## Thumbnail idee
{state.thumbnail_idea}

## Agent log
{steps}
"""


def format_review_iterations(state: VideoState) -> str:
    if not state.review_iterations:
        return "- Geen reviewrondes gelogd"

    blocks: list[str] = []
    for iteration in state.review_iterations:
        feedback = "\n".join(f"  - {item}" for item in iteration.feedback) or "  - Geen feedback"
        blocks.append(
            f"### Review ronde {iteration.round_number}\n"
            f"- Score: {iteration.score}/10\n"
            f"- Beslissing: {iteration.decision}\n"
            f"- Actie: {iteration.action}\n"
            f"- Feedback:\n{feedback}"
        )
    return "\n\n".join(blocks)


def format_agent_steps(state: VideoState) -> str:
    if not state.steps:
        return "- Geen stappen gelogd"

    return "\n".join(
        f"- **{step.agent}** — {step.action}: {step.note}" if step.note else f"- **{step.agent}** — {step.action}"
        for step in state.steps
    )


def make_safe_filename(text: str) -> str:
    safe = "".join(char.lower() if char.isalnum() else "-" for char in text)
    safe = "-".join(part for part in safe.split("-") if part)
    return safe[:60] or "video-plan"


def unique_path(path: Path) -> Path:
    """Voorkomt dat oude output per ongeluk overschreven wordt."""
    if not path.exists():
        return path

    counter = 2
    while True:
        candidate = path.with_name(f"{path.stem}-{counter}{path.suffix}")
        if not candidate.exists():
            return candidate
        counter += 1
