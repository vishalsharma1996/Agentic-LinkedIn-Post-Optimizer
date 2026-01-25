from langgraph.graph import StateGraph, START, END

from graph.state import LinkedInPostState

from prompts.intent_classifier import intent_classifier
from prompts.reference_retriever import reference_retriever
from prompts.generator import generate_linkedin_post
from prompts.evaluator import evaluate_linkedin_post
from prompts.optimizer import optimize_linkedin_post
from prompts.summarize_changes import summarize_changes

def active_focus_flattened(state: LinkedInPostState) -> bool:
    """
    Returns True if all active focus factors
    show zero improvement compared to the previous iteration.
    """
    history = state.get("iteration_focus_history", [])
    if len(history) < 2:
        return False

    prev_scores = history[-2]["scores"]
    curr_scores = history[-1]["scores"]

    for factor in state.get("active_focus_factors", []):
        if curr_scores[factor] > prev_scores[factor]:
            return False

    return True

def non_focus_regressed(state: LinkedInPostState) -> bool:
    """
    Returns True if any non-focus dimension
    regressed compared to the previous iteration.
    """
    history = state.get("iteration_focus_history", [])
    if len(history) < 2:
        return False

    prev_scores = state["history"][-2]["scores"]
    curr_scores = state["history"][-1]["scores"]

    focus = set(state.get("frozen_focus_factors", []))

    for dim, curr_val in curr_scores.items():
        if dim not in focus:
            if curr_val < prev_scores[dim]:
                return True

    return False

def active_focus_regressed(state: LinkedInPostState) -> bool:
    """
    Returns True if any active focus factor score
    decreased compared to the previous iteration.
    Applies for iteration >= 2.
    """
    history = state.get("iteration_focus_history", [])
    if len(history) < 2:
        return False

    prev_scores = history[-2]["scores"]
    curr_scores = history[-1]["scores"]

    for factor in state.get("active_focus_factors", []):
        if curr_scores[factor] < prev_scores[factor]:
            return True

    return False


def first_iteration_focus_regressed(state: LinkedInPostState) -> bool:
    """
    Returns True if any frozen focus factor score
    decreased in iteration 1 compared to iteration 0.
    """
    history = state.get("iteration_focus_history", [])
    if len(history) < 2:
        return False

    prev_scores = history[-2]["scores"]
    curr_scores = history[-1]["scores"]

    for factor in state["frozen_focus_factors"]:
        if curr_scores[factor] < prev_scores[factor]:
            return True

    return False

def rollback_to_best(state: LinkedInPostState) -> LinkedInPostState:
    best = state.get("best_iteration")
    if not best:
        return {}
    
    state["run_metrics"]["rollbacks"] += 1

    return {
        "draft_post": best["draft_post"],
        "quality_score": best["quality_score"],
        "scores": best["scores"],
        "active_focus_factors": best["active_focus_factors"],
        "frozen_focus_factors": best["frozen_focus_factors"],
        "iteration_count": best["iteration_count"],
    }


def should_continue(state: LinkedInPostState):
    
    # 🔒 FAIL-SOFT GUARD
    if state.get('__fail_soft__'):
        return 'summarize_changes'
    
    # 0. Early stop: strong generator output
    if state["iteration_count"] == 0 and state["quality_score"] >= 40:
        state["run_metrics"]["stop_reason"] = "Strong_initial_draft"
        return "summarize_changes"

    # 1. First-iteration regression guard
    if state["iteration_count"] == 1:
        if first_iteration_focus_regressed(state):
            state["run_metrics"]["stop_reason"] = "Active_Focus_Regressed_First_Iteration"
            return "summarize_changes"

    # 2. Later regression guard with rollback
    if state["iteration_count"] >= 2:
        if active_focus_regressed(state):
            state["run_metrics"]["stop_reason"] = "Active_Focus_Regressed_At/After_2nd_Iteration"
            # Rollback to best iteration
            return "rollback"

    # 3. Post-focus flattening guard
    if state["iteration_count"] >= 2:
        if active_focus_flattened(state): # Returns True if Active Focus Flattened
            if non_focus_regressed(state): # Returns True if Non Focus Factor Degraded
                state["run_metrics"]["stop_reason"] = "Non_Focus_Regressed"
                return "rollback"


    # 1. Stop if all focus factors have graduated
    if not state.get("active_focus_factors"):
        state["run_metrics"]["stop_reason"] = "focus_graduated"
        return "summarize_changes"

    # 3. Stop if max iterations reached
    if state["iteration_count"] >= state["max_iterations"]:
        state["run_metrics"]["stop_reason"] = "max_iterations_reached"
        return "summarize_changes"

    if state["run_metrics"]["stop_reason"] == "token_budget_exceeded":
        return "summarize_changes"

    # Otherwise, continue optimizing
    return "optimize_linkedin_post"


def build_graph():
    graph = StateGraph(LinkedInPostState)

    graph.add_node("intent_classifier", intent_classifier)
    graph.add_node("reference_retriever", reference_retriever)
    graph.add_node("generate_linkedin_post", generate_linkedin_post)
    graph.add_node("evaluate_linkedin_post", evaluate_linkedin_post)
    graph.add_node("optimize_linkedin_post", optimize_linkedin_post)
    graph.add_node("rollback", rollback_to_best)
    graph.add_node("summarize", summarize_changes)

    graph.add_edge(START, "intent_classifier")
    graph.add_edge("intent_classifier", "reference_retriever")
    graph.add_edge("reference_retriever", "generate_linkedin_post")
    graph.add_edge("generate_linkedin_post", "evaluate_linkedin_post")

    graph.add_conditional_edges(
        "evaluate_linkedin_post",
        should_continue,
        {
            "optimize_linkedin_post": "optimize_linkedin_post",
            "rollback": "rollback",
            "summarize_changes": "summarize",
        },
    )

    graph.add_edge("optimize_linkedin_post", "evaluate_linkedin_post")
    graph.add_edge("rollback", "summarize")
    graph.add_edge("summarize", END)

    return graph


# Production workflow (unchanged behavior)
linkedin_post_workflow = build_graph().compile()
