# Agent design

Dit document legt kort uit hoe ik over de agents in dit project heb nagedacht.

## Wat is een agent in dit project?

Een agent is hier bewust simpel het heeft een class die één taak heeft, een prompt maakt, een LLM-client aanroept en de gedeelde `VideoState` bijwerkt.

Bijvoorbeeld:

- `IdeaAgent` maakt een video-idee.
- `ResearchAgent` maakt research notes.
- `ScriptAgent` schrijft of verbetert het script.
- `ReviewAgent` beoordeelt het script en bepaalt wat de workflow daarna moet doen.


## State

Alle agents delen één `VideoState` object. Dat is het geheugen van de workflow.

Daarin staat onder andere:

- onderwerp;
- doelgroep;
- plan;
- idee;
- research;
- script;
- review-iterations;
- titels;
- agent-log.

Dit voorkomt dat elke agent losse data teruggeeft die de orchestrator handmatig moet bewaren.

## Agentic loop

De `ReviewAgent` geeft één van drie beslissingen terug:

- `approved` → klaar
- `needs_script_changes` → script herschrijven
- `needs_more_research` → eerst meer research, dan herschrijven

Stopt bij approved of als `max_review_rounds` is bereikt.


## Structured output

De review-agent geeft JSON terug, gevalideerd met Pydantic. Maakt de beslissingen betrouwbaar leesbaar voor de workflow. Er is een fallback-parser voor als een LLM toch rommelige output geeft.

## Providers

`fake` (tests), `openai`, `gemini`. De agents merken het verschil niet. ze gebruiken alleen de `LLMClient` interface.