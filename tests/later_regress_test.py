import pytest
from graph.workflow import build_graph


def test_later_regression_triggers_rollback(mocker):
    # --------------------------------------------------
    # Mock ALL non-deterministic / LLM-calling nodes
    # --------------------------------------------------
    mocker.patch(
        "graph.workflow.intent_classifier",
        lambda state: {**state, "intent": "PROOF_OF_WORK"}
    )

    mocker.patch(
        "graph.workflow.reference_retriever",
        lambda state: state
    )

    mocker.patch(
        "graph.workflow.generate_linkedin_post",
        lambda state: {**state, "draft_post": "mock draft"}
    )

    mocker.patch(
        "graph.workflow.optimize_linkedin_post",
        lambda state: {
            **state,
            "draft_post": "optimized draft",
            "iteration_count": state["iteration_count"] + 1,
        }
    )
    
    mocker.patch(
    "graph.workflow.summarize_changes",
    lambda state: state
    )
    # --------------------------------------------------
    # Mock evaluator to simulate improve → regress
    # --------------------------------------------------
    mocker.patch(
        "graph.workflow.evaluate_linkedin_post",
        side_effect=[
            # Iteration 0 (baseline)
            {
                "review_decision": "revise",
                "review_feedback": "Baseline",
                "review_feedback_history": ["Baseline"],
                "quality_score": 25,
                "scores": {"hook_strength": 4},
                "frozen_focus_factors": ["hook_strength"],
                "active_focus_factors": ["hook_strength"],
                "iteration_focus_history": [],
                "history": [],
                "best_iteration": {
                    "iteration": 0,
                    "quality_score": 25,
                    "draft_post": "v0",
                },
            },
            # Iteration 1 (best)
            {
                "review_decision": "revise",
                "review_feedback": "Improved",
                "review_feedback_history": ["Baseline", "Improved"],
                "quality_score": 28,
                "scores": {"hook_strength": 7},
                "frozen_focus_factors": ["hook_strength"],
                "active_focus_factors": ["hook_strength"],
                "iteration_focus_history": [],
                "history": [],
                "best_iteration": {
                    "iteration": 1,
                    "quality_score": 28,
                    "draft_post": "v1",
                },
            },
            # Iteration 2 (regression)
            {
                "review_decision": "revise",
                "review_feedback": "Regression",
                "review_feedback_history": ["Baseline", "Improved", "Regression"],
                "quality_score": 26,
                "scores": {"hook_strength": 5},
                "frozen_focus_factors": ["hook_strength"],
                "active_focus_factors": ["hook_strength"],
                "iteration_focus_history": [],
                "history": [],
                "best_iteration": {
                    "iteration": 1,
                    "quality_score": 28,
                    "draft_post": "v1",
                },

            },
            {
            "quality_score": 28,
            "scores": {"hook_strength": 7},
            "frozen_focus_factors": ["hook_strength"],
            "active_focus_factors": [],
            "review_feedback": "Post-rollback",
            "review_feedback_history": [],
            "iteration_focus_history": [],
            "history": [],
            "best_iteration": {
                "iteration": 1,
                "quality_score": 28,
                "draft_post": "v1",
            },
        }, 
        ],
    )

    # --------------------------------------------------
    # Initial state
    # --------------------------------------------------
    state = {
        "topic": "Test topic",
        "communication_style": "VIRAL_ENGINEER",
        "intent": None,
        "draft_post": "",
        "iteration_count": 0,
        "max_iterations": 5,
        "quality_score": 0,
        "scores": {},
        "frozen_focus_factors": [],
        "active_focus_factors": [],
        "focus_graduation_threshold": 8,
        "history": [],
        "review_feedback": "",
        "review_feedback_history": [],
        "iteration_focus_history": [],
        "best_iteration": None,
    }

    # --------------------------------------------------
    # Execute graph
    # --------------------------------------------------
    
    workflow = build_graph().compile()
    final_state = workflow.invoke(state)
    best = final_state.get('best_iteration')

    # --------------------------------------------------
    # Assertions: rollback to best iteration
    # --------------------------------------------------
    assert best["quality_score"] == 28
    assert best["draft_post"] == "v1"
