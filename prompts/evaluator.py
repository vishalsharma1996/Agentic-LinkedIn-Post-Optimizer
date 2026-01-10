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
            content="You are a strict LinkedIn content reviewer. You never rewrite content."
        ),
        HumanMessage(
            content=f"""
                    Review the LinkedIn post below.

                    Post:
                    \"\"\"
                    {state["draft_post"]}
                    \"\"\"

                    Score the post on:
                    1. Hook strength (0–10)
                    2. Clarity (0–10)
                    3. Credibility (0–10)
                    4. Engagement potential (0–10)
                    5. Professional tone (0–10)

                    Be critical. Penalize generic advice and weak hooks.

                    Respond ONLY in structured format.
                    """
                            ),
                        ]

    response = structured_evaluator.invoke(messages)

    return {
        "review_decision": response.review_decision,
        "review_feedback": response.review_feedback,
        "quality_score": response.quality_score,
    }
