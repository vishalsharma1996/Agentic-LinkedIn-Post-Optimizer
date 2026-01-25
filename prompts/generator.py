from langchain_core.messages import SystemMessage, HumanMessage
from graph.state import LinkedInPostState
from models.llm_config import generator_llm
from graph.guards import safe_llm_call


# ---------- INTENT RULES ----------

TECH_THOUGHT_LEADERSHIP_SYSTEM = (
    "You are a senior AI engineer writing in public.\n"
    "You explain systems the way experienced engineers do.\n"
    "Exactly FIVE structured sections are required.\n"
    "You may include ONE commonly observed production failure pattern.\n"
    "Do NOT use metrics or numbers.\n"
)

PROOF_OF_WORK_SYSTEM = (
    "You are a senior AI engineer sharing proof-of-work.\n"
    "STRICT RULES:\n"
    "- Use ONLY facts, mechanisms, and metrics explicitly provided by the user.\n"
    "- You MUST include all user-provided metrics verbatim.\n"
    "- Do NOT infer or invent architectures, tools, or techniques.\n"
    "- You MAY add bounded interpretation derived from the given facts\n"
    "  (e.g., what mattered most, what actually drove the gains).\n"
    "- DO NOT force bullets or points.\n"
    "- Structure should emerge naturally from the claims.\n"
)


# ---------- STYLE OVERLAYS ----------

STYLE_PROMPTS = {
    "ENGINEERING_DIRECT": (
        "Write clearly and concisely.\n"
        "Prioritize accuracy and signal over persuasion.\n"
        "No hype. No drama."
    ),
    "VIRAL_ENGINEER": (
        "Write like a senior engineer who has seen systems fail in production.\n"
        "Use a strong, scroll-stopping opening.\n"
        "Be opinionated but never exaggerate facts.\n"
        "Make the reader pause and think."
    ),
    "STORY_DRIVEN": (
        "Use a narrative arc: before → tension → insight → outcome.\n"
        "Keep it factual, but human.\n"
        "Do NOT add any facts beyond what is provided."
    ),
}


def generate_linkedin_post(state: LinkedInPostState) -> LinkedInPostState:
    def _generate(state):
        intent = state["intent"]
        style = state["communication_style"]

        intent_prompt = (
            TECH_THOUGHT_LEADERSHIP_SYSTEM
            if intent == "TECH_THOUGHT_LEADERSHIP"
            else PROOF_OF_WORK_SYSTEM
        )

        style_prompt = STYLE_PROMPTS[style]

        messages = [
            SystemMessage(content=intent_prompt),
            SystemMessage(content=style_prompt),
            HumanMessage(
                content=f"""
    Write a LinkedIn post based ONLY on the information below.

    Topic:
    {state["topic"]}

    IMPORTANT:
    - For PROOF_OF_WORK: focus on claims, not formatting.
    - For TECH_THOUGHT_LEADERSHIP: use clear structured sections.
    - Plain text only.
    """
            ),
        ]
        
        response = generator_llm.invoke(messages).content
        return {"draft_post": response}
    result = safe_llm_call(_generate,state,agent_name='generator')
    if '__fail_soft__' in result:
        return result
    return result
