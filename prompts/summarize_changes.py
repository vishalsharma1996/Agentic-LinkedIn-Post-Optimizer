from pydantic import BaseModel
from langchain_core.messages import SystemMessage, HumanMessage
from graph.state import LinkedInPostState
from models.llm_config import change_summary_llm
from graph.costs import charge_cost
from graph.guards import safe_llm_call


class ChangeSummary(BaseModel):
    summary: str

structured_summary_llm = change_summary_llm.with_structured_output(ChangeSummary)


def summarize_changes(state: LinkedInPostState) -> LinkedInPostState:
    def _summarize(state):
        best = state.get("best_iteration")
        history = state.get("review_feedback_history", [])

        state["run_metrics"]["best_score"] = (
        best["quality_score"] if best else state["quality_score"]
        )
        state["run_metrics"]["final_score"] = state["run_metrics"]["best_score"]

        if not best or len(history) < 1:
            return {"change_summary": None}

        messages = [
            SystemMessage(
                content=(
                    "You summarize editorial changes across iterations.\n"
                    "Do NOT rescore or re-evaluate.\n"
                    "Do NOT introduce new claims.\n"
                    "Only describe what improved, weakened, or stayed the same."
                )
            ),
            HumanMessage(
                content=f"""
            Initial feedback:
            {history[0]}

            Final feedback (best iteration):
            {best['review_feedback']}

            Active Focus dimensions:
            {best["frozen_focus_factors"]}

            Summarize the changes clearly for a user.
            """
                    ),
        ]
        charge_cost(state, "summarizer")
        response = structured_summary_llm.invoke(messages)
        return {"change_summary": response.summary}
    
    result = safe_llm_call(_summarize, state, agent_name='summarizer')
    if '__fail_soft__' in result:
        return {'change_summary':None}
    return result
