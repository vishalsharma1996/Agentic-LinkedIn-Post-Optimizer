from pydantic import BaseModel, Field
from typing import Literal, Dict, List
from langchain_core.messages import SystemMessage, HumanMessage
from graph.state import LinkedInPostState
from models.llm_config import evaluator_llm
from langsmith import traceable
from graph.costs import charge_cost
from graph.guards import safe_llm_call

@traceable(name='iteration_focus_snapshot')
def log_iteration_focus(snapshot: dict):
    """
    Lightweight LangSmith-only trace.
    This does NOT affect agent state.
    """
    return snapshot


class LinkedInPostReview(BaseModel):
    review_decision: Literal["accept", "revise"]

    hook_strength: int = Field(..., ge=0, le=10)
    factual_grounding: int = Field(..., ge=0, le=10)
    causal_clarity: int = Field(..., ge=0, le=10)
    interpretive_judgment: int = Field(..., ge=0, le=10)
    density: int = Field(..., ge=0, le=10)

    total_score: int = Field(..., ge=0, le=50)
    review_feedback: str


structured_evaluator = evaluator_llm.with_structured_output(
    LinkedInPostReview)


def evaluate_linkedin_post(state: LinkedInPostState) -> LinkedInPostState:
    def _evaluate(state):
        intent = state["intent"]

        messages = [
            SystemMessage(
                content=(
                    "You are a strict evaluator of LinkedIn posts written by senior AI engineers.\n\n"
                    "GENERAL RULES:\n"
                    "- Do NOT score formatting or bullet usage.\n"
                    "- Evaluate clarity, credibility, and density of claims.\n\n"
                    "PROOF_OF_WORK RULES:\n"
                    "- All user-provided metrics MUST appear verbatim.\n"
                    "- No inferred mechanisms allowed.\n"
                    "- Bounded interpretation is REQUIRED for high scores.\n\n"
                    "TECH THOUGHT LEADERSHIP RULES:\n"
                    "- Exactly five conceptual sections expected.\n"
                    "- No metrics allowed.\n"
                )
            ),
            HumanMessage(
            content=f"""
        Review the LinkedIn post below.

        Post:
        \"\"\"
        {state["draft_post"]}
        \"\"\"

        Score the post on the following dimensions (0–10 each):

        1. Hook strength
        2. Factual grounding
        3. Cause → effect clarity
        4. Interpretive judgment
        5. Information density

        Guidelines:
        - Be strict and skeptical.
        - Do NOT reward fluency alone.
        - Penalize abstraction, redundancy, or vague claims.
        - High scores should require exceptional clarity and sharpness.

        Return ONLY the structured scores and feedback.
        """
        )
        ,
        ]

        
        state["run_metrics"]["iterations"] += 1
        charge_cost(state, "evaluator")
        response = structured_evaluator.invoke(messages)
        if state['iteration_count'] == 0:
            state['run_metrics']['initial_score'] = response.total_score

        scores: Dict[str, int] = {
            "hook_strength": response.hook_strength,
            "factual_grounding": response.factual_grounding,
            "causal_clarity": response.causal_clarity,
            "interpretive_judgment": response.interpretive_judgment,
            "density": response.density,
        }

        # ----------------------------
        # Focus factor initialization
        # ----------------------------
        if not state["iteration_count"]:
            frozen_focus_factors = sorted(scores, key=scores.get)[:2]
            active_focus_factors = frozen_focus_factors.copy()
        else:
            frozen_focus_factors = state["frozen_focus_factors"]
            active_focus_factors = state["active_focus_factors"].copy()
        # ----------------------------
        # Graduation logic (no replacement)
        # ----------------------------
        threshold = state["focus_graduation_threshold"]

        active_focus_factors = [
            factor for factor in active_focus_factors
            if scores[factor] < threshold
        ]

        history_entry = {
        "iteration": state["iteration_count"],
        "draft_post": state["draft_post"],
        "scores": scores,
        "total_score": response.total_score,
        "review_feedback": response.review_feedback,
        }

        # ----------------------------
        # Trajectory logging
        # ----------------------------
        iteration_focus_history = [{
            "iteration": state["iteration_count"],
            "frozen_focus_factors": frozen_focus_factors,
            "active_focus_factors": active_focus_factors,
            "scores": {k: scores[k] for k in frozen_focus_factors},
            "intent": state["intent"],
            "communication_style": state["communication_style"],
        }]

        total_score = response.total_score

        if state["iteration_count"] == 0:
            log_iteration_focus({
                "iteration": 0,
                "total_score": total_score,
                "scores": scores,
                "frozen_focus_factors": frozen_focus_factors,
                "active_focus_factors": active_focus_factors,
                "intent": state["intent"],
                "communication_style": state["communication_style"],
            })
        else:
            total_score_delta = {
                k: scores[k] - state["history"][-1]["scores"][k]
                for k in scores
                if k not in frozen_focus_factors
            }

            best = state.get("best_iteration")
            best_delta = (
                total_score - best["quality_score"] if best else None
            )

            best_focus_scores =  {k: best["scores"][k] for k in frozen_focus_factors if best}
            best_iteration_index = (
            best["iteration_count"] if best else None
            )


            log_iteration_focus({
                "iteration": state["iteration_count"],
                "best_iteration_index": best_iteration_index,
                "frozen_focus_factors": frozen_focus_factors,
                "active_focus_factors": active_focus_factors,
                "best_focus_scores" : best_focus_scores if best_focus_scores else None,
                "focus_scores": {k: scores[k] for k in frozen_focus_factors},
                "focus_score_delta": {
                    k: scores[k] - state["iteration_focus_history"][-1]["scores"][k]
                    for k in frozen_focus_factors
                },
                "total_score": total_score,
                "total_score_delta": total_score_delta,
                "best_score_delta": best_delta,
                "intent": state["intent"],
                "communication_style": state["communication_style"],
            })


        # Logging best iteration scores
        current_iteration_snapshot = {
        "draft_post": state["draft_post"],
        "quality_score": response.total_score,
        "review_feedback": response.review_feedback,
        "scores": scores,
        "iteration_count": state["iteration_count"],
        "active_focus_factors": active_focus_factors.copy(),
        "frozen_focus_factors": frozen_focus_factors.copy(),
        }

        best_iteration = state.get("best_iteration")
        if (best_iteration is None or response.total_score > best_iteration['quality_score']):
            best_iteration = current_iteration_snapshot


        return {
            "review_feedback": response.review_feedback,
            "review_feedback_history": [response.review_feedback],
            "quality_score": response.total_score,
            "scores": scores,

            # Focus control
            "frozen_focus_factors": frozen_focus_factors,
            "active_focus_factors": active_focus_factors,

            # Trajectory
            "iteration_focus_history": iteration_focus_history,

            # Pass-through
            "history": state.get("history", []) + [history_entry],

            # Best Iteration
            'best_iteration': best_iteration
        }
    result = safe_llm_call(_evaluate,state,agent_name='evaluator')
    if '__fail_soft__'  in result:
        return result
    return result
