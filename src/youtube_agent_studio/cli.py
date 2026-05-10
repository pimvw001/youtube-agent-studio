import argparse
import os
from pathlib import Path

from dotenv import load_dotenv

from youtube_agent_studio.llm import make_llm_client
from youtube_agent_studio.output import save_json, save_markdown
from youtube_agent_studio.settings import load_settings
from youtube_agent_studio.workflow import VideoWorkflow

PROVIDERS = ["fake", "gemini", "openai"]


def main() -> None:
    load_dotenv()
    settings = load_settings()

    parser = argparse.ArgumentParser(description="Maak een YouTube video-plan met een kleine agentic workflow.")
    parser.add_argument("topic", nargs="?", help="Onderwerp voor de YouTube video")
    parser.add_argument("--audience", default=settings.audience, help="Voor wie is de video?")
    parser.add_argument("--tone", default=settings.tone, help="Welke toon moet het script hebben?")
    parser.add_argument("--language", default=settings.language, help="Taal voor de output")
    parser.add_argument("--length", default=settings.length, help="Gewenste lengte van de video")
    parser.add_argument("--context", default="", help="Extra context die de agents mogen gebruiken")
    parser.add_argument("--context-file", help="Pad naar een tekstbestand met extra context")
    parser.add_argument(
        "--provider",
        choices=PROVIDERS,
        default=settings.provider,
        help="Welke AI-provider wil je gebruiken?",
    )
    parser.add_argument("--model", default=settings.model or None, help="Modelnaam, bijvoorbeeld gpt-4.1-mini")
    parser.add_argument(
        "--json",
        action="store_true",
        default=settings.save_json,
        help="Sla ook JSON output op",
    )
    parser.add_argument(
        "--no-json",
        action="store_false",
        dest="json",
        help="Sla geen JSON output op",
    )
    parser.add_argument("--output-dir", default="outputs", help="Map waar de output wordt opgeslagen")
    parser.add_argument("--check-api", action="store_true", help="Test alleen of je API-key werkt")
    parser.add_argument("--max-rounds", type=int, default=settings.max_review_rounds, help="Maximaal aantal reviewrondes")
    parser.add_argument(
        "--real-ai",
        action="store_true",
        help="Oude snelle optie: gebruikt AI_PROVIDER uit .env of anders OpenAI",
    )
    args = parser.parse_args()

    provider = args.provider

    # Oude shortcut blijft werken, maar provider is nu de go to optie.
    if args.real_ai and provider == "fake":
        provider = os.getenv("AI_PROVIDER", "openai")

    try:
        llm = make_llm_client(provider=provider, model=args.model)

        if args.check_api:
            answer = llm.generate("Zeg in één korte Nederlandse zin dat de API werkt.")
            print(f"API-test gelukt met provider '{provider}'. Antwoord: {answer}")
            return

        if not args.topic:
            parser.error("Geef een onderwerp op, of gebruik --check-api.")

        context = build_context(args.context, args.context_file)
        print(f"Provider: {provider}")
        workflow = VideoWorkflow(llm, max_review_rounds=args.max_rounds)
        state = workflow.run(
            args.topic,
            audience=args.audience,
            tone=args.tone,
            language=args.language,
            length=args.length,
            context=context,
        )

        markdown_path = save_markdown(state, output_dir=args.output_dir)
        print(f"\nKlaar! Markdown opgeslagen in: {markdown_path}")

        if args.json:
            json_path = save_json(state, output_dir=args.output_dir)
            print(f"JSON opgeslagen in: {json_path}")

    except (RuntimeError, ValueError) as error:
        print(f"Fout: {error}")
        raise SystemExit(1) from error


def build_context(context: str, context_file: str | None) -> str:
    parts = [context.strip()] if context.strip() else []

    if context_file:
        path = Path(context_file)
        if not path.exists():
            raise ValueError(f"Contextbestand niet gevonden: {path}")
        parts.append(path.read_text(encoding="utf-8").strip())

    return "\n\n".join(part for part in parts if part)
