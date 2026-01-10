from pydantic import BaseModel, Field
from typing import Literal
from langchain_core.messages import SystemMessage, HumanMessage
from graph.state import LinkedInPostState
from models.llm_config import evaluator_llm


class LinkedInPostReview(BaseModel):
    review_decision: Literal["accept", "revise"]
    quality_score: int = Field(..., ge=0, le=50)
    review_feedback: str


structured_evaluator = evaluator_llm.with_structured_output(
    LinkedInPostReview
)


def evaluate_linkedin_post(state: LinkedInPostState) -> LinkedInPostState:
    messages = [
        SystemMessage(
            content=(
                "You are reviewing LinkedIn posts written by senior AI engineers. "
                "You are strict about structure, density, and real-world grounding."
            )
        ),
        HumanMessage(
            content=f"""
Review the LinkedIn post below.

Post:
\"\"\"
{state["draft_post"]}
\"\"\"

EVALUATION CRITERIA:
- Strong scroll-stopping opening line
- EXACT structure: opening line + numbered points 1) to 5)
- Each point is dense and reflects real engineering experience
- Clear cause → effect → system insight in each point
- Engineer-in-public tone (not blog, not documentation)
- Appropriate length (2–3 lines per point)

RULES:
- Posts without numbered points (1–5) must be revised.
- Blog-style, academic, or neutral explainer posts must be revised.
- Shallow or generic points must be revised.
- Accept ONLY if this looks publish-ready by a senior AI engineer.

Respond ONLY in structured format.
"""
        ),
    ]

    response = structured_evaluator.invoke(messages)

    # HARD GATE — code decides acceptance, not the model
    final_decision = "accept" if response.quality_score >= 42 else "revise"

    history_entry = {
        "iteration": state["iteration_count"],
        "post": state["draft_post"],
        "quality_score": response.quality_score,
        "review_decision": final_decision,
        "review_feedback": response.review_feedback,
    }

    return {
        "review_decision": final_decision,
        "review_feedback": response.review_feedback,
        "quality_score": response.quality_score,
        "history": state.get("history", []) + [history_entry],
    }
