from langchain_core.messages import SystemMessage, HumanMessage
from graph.state import LinkedInPostState
from models.llm_config import optimizer_llm
from graph.costs import charge_cost, ESTIMATED_TOKEN_COSTS
from graph.guards import safe_llm_call


PROOF_OF_WORK_SYSTEM = (
    "You refine proof-of-work posts written by senior AI engineers.\n"
    "STRICT RULES:\n"
    "- Preserve all user-provided metrics verbatim.\n"
    "- Do NOT add new facts or mechanisms.\n"
    "- You MAY strengthen bounded interpretation derived from existing facts.\n"
    "- You MAY remove redundancy or tighten phrasing.\n"
    "- Fewer, denser claims are preferred over padded structure."
)

TECH_THOUGHT_LEADERSHIP_SYSTEM = (
    "You refine tech thought leadership posts.\n"
    "Maintain conceptual clarity.\n"
    "Reduce abstraction without removing explanatory substance."
)


def optimize_linkedin_post(state: LinkedInPostState) -> LinkedInPostState:
    def _optimize(state):
        intent = state["intent"]
        active_focus_factors = state.get("active_focus_factors", [])

        # Anchor to the last evaluated draft (signal-preserving anchor)
        previous_draft = None
        if state.get("history"):
            previous_draft = state["history"][-1]["draft_post"]

        system_prompt = (
            TECH_THOUGHT_LEADERSHIP_SYSTEM
            if intent == "TECH_THOUGHT_LEADERSHIP"
            else PROOF_OF_WORK_SYSTEM
        )

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(
                content=f"""
    You are refining a LinkedIn post through controlled iteration.

    IMPORTANT:
    - The previous version contains textual signals that resulted in higher evaluation scores.
    - Those signals MUST be preserved.
    - Prefer no change over risky change.

    Active focus areas (allowed to improve):
    {active_focus_factors}

    Evaluator feedback:
    {state["review_feedback"]}

    Previous evaluated version (anchor — preserve its strengths):
    \"\"\"
    {previous_draft if previous_draft else "N/A (first iteration)"}
    \"\"\"

    Current draft to revise:
    \"\"\"
    {state["draft_post"]}
    \"\"\"

    INSTRUCTIONS:
    - Improve ONLY the active focus areas.
    - Do NOT weaken or abstract content present in the previous evaluated version.
    - Reduce abstraction by making reasoning and evidence more explicit, not by compressing or implying it.
    - Increase density only by removing repetition, not by collapsing explanations.
    - If uncertain whether a change improves evaluation, leave the text unchanged.
    - Do NOT add new claims, facts, or interpretations.

    Return LinkedIn-ready text only.
    """
            ),
        ]

        
        state["run_metrics"]["optimizer_runs"] += 1
        if state['run_metrics']['token_budget_remaining'] < ESTIMATED_TOKEN_COSTS["optimizer"]:
            state['run_metrics']['stop_reason'] = 'token_budget_exceeded'
            return state
        
        charge_cost(state, 'optimizer')
        response = optimizer_llm.invoke(messages).content
        return {
                "draft_post": response,
                "iteration_count": state["iteration_count"] + 1,
            }
    result = safe_llm_call(_optimize,state,agent_name='optimizer')
    if '__fail_soft__' in result:
        return result
    return result
