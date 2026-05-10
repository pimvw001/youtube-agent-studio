import os
from typing import Protocol


class LLMClient(Protocol):
    def generate(self, prompt: str) -> str:
        """Return text for a prompt."""


class FakeLLMClient:
    """Fake AI client, zodat de workflow te testen is zonder API-key of kosten."""

    def __init__(self) -> None:
        self.review_calls = 0

    def generate(self, prompt: str) -> str:
        prompt_lower = prompt.lower()
        topic = _extract_prompt_field(prompt, "Onderwerp") or "dit onderwerp"

        if "thumbnail agent" in prompt_lower or "thumbnail" in prompt_lower:
            return (
                f"Thumbnail idee: een persoon die duidelijk met {topic} bezig is, met simpele iconen eromheen.\n"
                f"Tekst op thumbnail: {topic[:35]}\n"
                "Sfeer: helder, praktisch en niet te druk."
            )

        if "titels" in prompt_lower or "title agent" in prompt_lower:
            return (
                f"1. {topic}: simpel uitgelegd\n"
                f"2. 3 praktische tips over {topic}\n"
                f"3. Zo begin je met {topic}"
            )

        if "review agent" in prompt_lower:
            self.review_calls += 1
            if self.review_calls == 1:
                return (
                    '{"decision": "needs_script_changes", "score": 6, '
                    '"feedback": ["De intro mag actiever en er mist een concreet voorbeeld."], '
                    '"required_changes": ["Maak de intro sterker", "Voeg één voorbeeld toe"]}'
                )
            return (
                '{"decision": "approved", "score": 8, '
                '"feedback": ["Het script is duidelijk genoeg voor een eerste versie."], '
                '"required_changes": []}'
            )

        if "script agent" in prompt_lower:
            return (
                f"Intro: Je wilt beginnen met {topic}, maar je weet misschien niet waar je moet starten. "
                "In deze video laat ik drie simpele stappen zien die je meteen kunt gebruiken. "
                f"Bijvoorbeeld: je kiest één klein probleem binnen {topic} en maakt daar een duidelijke eerste stap van.\n\n"
                f"Punt 1: Leg kort uit waarom {topic} relevant is voor de kijker.\n"
                "Punt 2: Geef een concreet voorbeeld dat de kijker direct kan toepassen.\n"
                "Punt 3: Sluit af met een simpele checklist of volgende stap.\n\n"
                f"Afsluiting: {topic} hoeft niet ingewikkeld te zijn. Begin klein, test wat werkt en blijf kritisch."
            )

        if "research-question agent" in prompt_lower:
            return (
                f"1. Wat is het belangrijkste probleem rond {topic}?\n"
                f"2. Welk voorbeeld maakt {topic} concreet voor beginners?\n"
                "3. Welke valkuil moet de kijker vermijden?"
            )

        if "research agent" in prompt_lower:
            return (
                f"- Begin met een herkenbaar probleem rond {topic}.\n"
                "- Houd de uitleg praktisch en vermijd lange theorie.\n"
                "- Geef één voorbeeld dat de kijker meteen begrijpt.\n"
                "- Benoem ook kort een valkuil of iets waar de kijker op moet letten."
            )

        if "idea agent" in prompt_lower:
            return (
                f"Een korte video over {topic} met 3 praktische tips en één herkenbaar voorbeeld. "
                "Dit past bij beginners omdat het niet te technisch wordt."
            )

        if "planner agent" in prompt_lower:
            return (
                f"Doel: laten zien hoe {topic} praktisch en begrijpelijk wordt.\n"
                f"Kijkersvraag: hoe begin ik met {topic} zonder dat het te ingewikkeld wordt?\n"
                "Let op: houd het simpel, geef voorbeelden en benoem één belangrijke valkuil."
            )

        return "Fake antwoord van de AI-client."


def _extract_prompt_field(prompt: str, field_name: str) -> str:
    marker = f"{field_name}:"
    if marker not in prompt:
        return ""
    after_marker = prompt.split(marker, 1)[1].strip()
    return after_marker.splitlines()[0].strip()


class GeminiLLMClient:
    """Kleine Gemini-wrapper voor Google AI Studio."""

    def __init__(self, model: str | None = None) -> None:
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError(
                "Gemini provider gekozen, maar GEMINI_API_KEY mist. "
                "Zet deze in je .env bestand of gebruik --provider fake."
            )

        try:
            from google import genai
        except ImportError as error:
            raise RuntimeError("Google GenAI package mist. Run: pip install -e '.[ai]'") from error

        self.model = model or os.getenv("GEMINI_MODEL") or os.getenv("AI_MODEL") or "gemini-2.5-flash"
        self.client = genai.Client(api_key=api_key)

    def generate(self, prompt: str) -> str:
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
            )
        except Exception as error:  # pragma: no cover - afhankelijk van externe API
            raise RuntimeError(f"Gemini request mislukt: {error}") from error

        text = response.text or ""
        return text.strip()


class OpenAILLMClient:
    """Kleine OpenAI-wrapper."""

    def __init__(self, model: str | None = None) -> None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "OpenAI provider gekozen, maar OPENAI_API_KEY mist. "
                "Zet deze in je .env bestand of gebruik --provider fake."
            )

        try:
            from openai import OpenAI
        except ImportError as error:
            raise RuntimeError("OpenAI package mist. Run: pip install -e '.[ai]'") from error

        self.model = model or os.getenv("OPENAI_MODEL") or os.getenv("AI_MODEL") or "gpt-4.1-mini"
        self.client = OpenAI(api_key=api_key)

    def generate(self, prompt: str) -> str:
        try:
            response = self.client.responses.create(
                model=self.model,
                input=prompt,
            )
        except Exception as error:  # pragma: no cover - afhankelijk van externe API
            raise RuntimeError(f"OpenAI request mislukt: {error}") from error

        return response.output_text.strip()


def make_llm_client(provider: str = "fake", model: str | None = None) -> LLMClient:
    """Maak de juiste LLM-client op basis van providernaam."""
    provider = provider.lower().strip()

    if provider == "fake":
        return FakeLLMClient()

    if provider == "gemini":
        return GeminiLLMClient(model=model)

    if provider == "openai":
        return OpenAILLMClient(model=model)

    raise RuntimeError(f"Onbekende AI-provider: {provider}. Kies uit: fake, gemini, openai.")
