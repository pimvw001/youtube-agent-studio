import json
import os

import streamlit as st
from dotenv import load_dotenv

from youtube_agent_studio.llm import make_llm_client
from youtube_agent_studio.output import to_markdown
from youtube_agent_studio.settings import load_settings
from youtube_agent_studio.workflow import VideoWorkflow


def default_model_for_provider(provider_name: str) -> str:
    if provider_name == "openai":
        return os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    if provider_name == "gemini":
        return os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    return ""


load_dotenv()
settings = load_settings()

st.set_page_config(page_title="YouTube Agent Studio", page_icon="🎬", layout="wide")

st.title("🎬 YouTube Agent Studio")
st.write(
    "Klein agentic hobbyproject dat een YouTube video-plan maakt met meerdere agents, "
    "gedeelde state en een review-loop."
)

with st.sidebar:
    st.header("Instellingen")
    provider = st.selectbox(
        "AI provider",
        ["fake", "openai", "gemini"],
        index=["fake", "openai", "gemini"].index(settings.provider)
        if settings.provider in ["fake", "openai", "gemini"]
        else 0,
    )
    model = st.text_input("Model", value=settings.model or default_model_for_provider(provider))
    max_rounds = st.slider("Max review rondes", min_value=1, max_value=5, value=settings.max_review_rounds)

    st.caption("Tip: zet je API-key in `.env`. De app slaat geen API-keys op.")
    if provider == "openai" and not os.getenv("OPENAI_API_KEY"):
        st.warning("OPENAI_API_KEY staat nog niet in je .env bestand.")
    if provider == "gemini" and not (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")):
        st.warning("GEMINI_API_KEY staat nog niet in je .env bestand.")

topic = st.text_input("Onderwerp", value="AI tools voor studenten")
col1, col2 = st.columns(2)
with col1:
    audience = st.text_input("Doelgroep", value=settings.audience)
    language = st.text_input("Taal", value=settings.language)
with col2:
    tone = st.text_input("Toon", value=settings.tone)
    length = st.text_input("Lengte", value=settings.length)

context = st.text_area(
    "Extra context (optioneel)",
    placeholder="Plak hier eigen notities, doelgroepinformatie of eisen voor de video.",
    height=120,
)

if st.button("Generate video plan", type="primary"):
    if not topic.strip():
        st.error("Vul eerst een onderwerp in.")
    else:
        try:
            with st.spinner("Agents zijn bezig..."):
                llm = make_llm_client(provider=provider, model=model or None)
                workflow = VideoWorkflow(llm, max_review_rounds=max_rounds)
                state = workflow.run(
                    topic,
                    audience=audience,
                    tone=tone,
                    language=language,
                    length=length,
                    context=context,
                    verbose=False,
                )
                st.session_state["latest_state"] = state
        except RuntimeError as error:
            st.error(str(error))

state = st.session_state.get("latest_state")
if state:
    st.success(f"Plan gemaakt. Review status: {state.final_decision}")

    tab_overview, tab_script, tab_review, tab_export = st.tabs(
        ["Overzicht", "Script", "Review-loop", "Export"]
    )

    with tab_overview:
        st.subheader("Plan")
        st.write(state.plan)
        st.subheader("Idee")
        st.write(state.idea)
        st.subheader("Researchvragen")
        st.write(state.research_questions)
        st.subheader("Research")
        st.write(state.research)
        st.subheader("Titels")
        st.write(state.titles)
        st.subheader("Thumbnail")
        st.write(state.thumbnail_idea)

    with tab_script:
        st.markdown(state.script)

    with tab_review:
        for iteration in state.review_iterations:
            with st.expander(f"Review ronde {iteration.round_number}: {iteration.decision}", expanded=True):
                st.write(f"Score: {iteration.score}/10")
                st.write(f"Actie: {iteration.action}")
                st.write(iteration.feedback)

    with tab_export:
        markdown = to_markdown(state)
        json_data = json.dumps(state.to_dict(), indent=2, ensure_ascii=False)
        st.download_button("Download Markdown", markdown, file_name="video_plan.md")
        st.download_button("Download JSON", json_data, file_name="video_plan.json", mime="application/json")
        st.code(markdown[:4000], language="markdown")
