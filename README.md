# YouTube Agent Studio

Een klein project waarin meerdere AI-agents samenwerken om een YouTube video-plan te maken om later zelfstandig filmpjes op te kunnen uploaden.

Het project maakt nog geen echte video. De focus ligt nog op gedeelde state, prompts, provider-keuze, tests en een simpele agentic review-loop.

## Waarom 

Ik wilde beter begrijpen hoe je een kleine AI-workflow bouwt zonder een zwaar framework te gebruiken.

## Wat doet het?

Je geeft een onderwerp op, bijvoorbeeld:

```bash
python -m youtube_agent_studio "Informatie over petrodollar"
```

Daarna draaien deze agents:

1. `PlannerAgent` maakt een korte aanpak.
2. `IdeaAgent` maakt een video-idee.
3. `ResearchQuestionAgent` bedenkt researchvragen.
4. `ResearchAgent` maakt research notes.
5. `ScriptAgent` schrijft een script.
6. `ReviewAgent` beoordeelt het script met structured output.
7. De workflow past het script aan of doet extra research als de review dat vraagt.
8. `TitleAgent` en `ThumbnailAgent` maken titels en een thumbnail-brief.

De output wordt opgeslagen als Markdown en optioneel JSON.

## Installatie

### Windows PowerShell

```powershell
python -m venv .venv
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```


## Testen

```bash
pytest
ruff check .
```

## Fake workflow draaien

Fake gebruikt geen API-key is handig om zonder kosten te testen.

```bash
python -m youtube_agent_studio "Informatie over petrodollar"
```

Met meer opties:

```bash
python -m youtube_agent_studio "Informatie over petrodollar" \
  --audience "mbo studenten" \
  --tone "vlot en simpel" \
  --length "ongeveer 4 minuten" \
  --json
```

Extra context meegeven:

```bash
python -m youtube_agent_studio "Informatie over petrodollar \
  --context "Maak het geschikt voor studenten die nog nooit met AI hebben gewerkt."
```

Of via een tekstbestand:

```bash
python -m youtube_agent_studio "Informatie over petrodollar" --context-file examples/input_examples/student_context.txt
```

## OpenAI gebruiken

Installeer de AI-dependencies:

```bash
pip install -e ".[ai,dev]"
```

Maak een `.env` bestand:

```bash
cp .env.example .env
```

Op Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Zet in `.env`:

```env
AI_PROVIDER=openai
OPENAI_API_KEY=jouw_key_hier
OPENAI_MODEL=gpt-4.1-mini
```

Test je key:

```bash
python -m youtube_agent_studio --check-api --provider openai
```

Run met OpenAI:

```bash
python -m youtube_agent_studio "AI tools voor studenten" --provider openai --json
```

## Gemini gebruiken

Zet in `.env`:

```env
AI_PROVIDER=gemini
GEMINI_API_KEY=jouw_key_hier
GEMINI_MODEL=gemini-2.5-flash
```

Daarna:

```bash
python -m youtube_agent_studio --check-api --provider gemini
python -m youtube_agent_studio "AI tools voor studenten" --provider gemini --json
```

## Streamlit demo
Er is een kleine interface

Installeer de UI-dependency:

```bash
pip install -e ".[ui,ai,dev]"
```

Start de app:

```bash
streamlit run streamlit_app.py
```

In de app kun je invullen:

- onderwerp;
- doelgroep;
- toon;
- lengte;
- provider: fake, OpenAI of Gemini;
- max review rondes;
- extra context.

Daarna kun je de output downloaden als Markdown of JSON.

## Config

Standaardinstellingen staan in `config.toml`:

```toml
[model]
provider = "fake"
model = ""

[workflow]
max_review_rounds = 3
save_json = true
save_markdown = true
```



## Projectstructuur

```text
src/youtube_agent_studio/
  agents.py          # losse agents en parsers
  workflow.py        # agentic loop / orchestrator
  state.py           # gedeelde state
  models.py          # structured review models
  llm.py             # fake, OpenAI en Gemini clients
  output.py          # Markdown en JSON export
  settings.py        # config.toml laden
  prompts/           # losse promptbestanden
streamlit_app.py     # simpele demo UI
tests/               # pytest tests
docs/                # ontwerpkeuzes en roadmap
examples/            # voorbeeldinput en voorbeeldoutput
```

## Ontwerpkeuzes

Ik heb bewust geen LangChain, CrewAI of ander groot framework gebruikt. Voor dit project wilde ik juist laten zien hoe de basis werkt:

- een workflow met meerdere agents;
- gedeelde state;
- fake provider voor tests;
- aparte prompts;
- structured review output;
- een kleine feedback-loop.

De review-agent geeft een gestructureerde beslissing terug:

```json
{
  "decision": "needs_script_changes",
  "score": 6,
  "feedback": ["De intro is nog te algemeen"],
  "required_changes": ["Maak de intro concreter"]
}
```

De workflow kan daarna kiezen of hij stopt, het script herschrijft of extra research doet.


## Kwaliteit

Deze checks draaien lokaal en in GitHub Actions:

```bash
pytest
ruff check .
```
