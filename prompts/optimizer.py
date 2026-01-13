from langchain_core.messages import SystemMessage, HumanMessage
from graph.state import LinkedInPostState
from models.llm_config import optimizer_llm


PROOF_OF_WORK_SYSTEM = (
    "You refine proof-of-work posts written by senior AI engineers.\n"
    "STRICT RULES:\n"
    "- Preserve all user-provided metrics verbatim.\n"
    "- Do NOT add new facts or mechanisms.\n"
    "- You MAY strengthen bounded interpretation derived from existing facts.\n"
    "- You MAY remove bullets, merge claims, or reformat structure.\n"
    "- Fewer, denser claims are preferred over padded structure."
)

TECH_THOUGHT_LEADERSHIP_SYSTEM = (
    "You refine tech thought leadership posts.\n"
    "Maintain structured sections.\n"
    "Reduce abstraction and improve clarity."
)


def optimize_linkedin_post(state: LinkedInPostState) -> LinkedInPostState:
    intent = state["intent"]

    system_prompt = (
        TECH_THOUGHT_LEADERSHIP_SYSTEM
        if intent == "TECH_THOUGHT_LEADERSHIP"
        else PROOF_OF_WORK_SYSTEM
    )

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(
            content=f"""
Revise the post below.

Feedback:
{state["review_feedback"]}

Draft:
\"\"\"
{state["draft_post"]}
\"\"\"

GOAL:
- Increase density
- Remove filler
- Strengthen senior POV
- Preserve factual integrity

Return LinkedIn-ready text.
"""
        ),
    ]

    response = optimizer_llm.invoke(messages).content

    return {
        "draft_post": response,
        "iteration_count": state["iteration_count"] + 1,
    }
