import pytest
from graph.workflow import build_graph

def test_global_best_iteration_is_always_returned(mocker):
    # --------------------------------------------------
    # Mock graph nodes (call-site mocking)
    # --------------------------------------------------
    mocker.patch(
        "graph.workflow.intent_classifier",
        lambda s: {**s, "intent": "PROOF_OF_WORK"}
    )
    mocker.patch("graph.workflow.reference_retriever", lambda s: s)
    mocker.patch("graph.workflow.summarize_changes", lambda s: s)

    mocker.patch(
        "graph.workflow.generate_linkedin_post",
        lambda s: {**s, "draft_post": f"v{s['iteration_count']}"}
    )

    mocker.patch(
        "graph.workflow.optimize_linkedin_post",
        lambda s: {
            **s,
            "draft_post": f"v{s['iteration_count'] + 1}",
            "iteration_count": s["iteration_count"] + 1,
        }
    )

    # --------------------------------------------------
    # Evaluator oscillates, but best is iteration 2
    # --------------------------------------------------
    mocker.patch(
        "graph.workflow.evaluate_linkedin_post",
        side_effect=[
            # Iter 0
            {
                "quality_score": 25,
                "scores": {"density": 4},
                "frozen_focus_factors": ["density"],
                "active_focus_factors": ["density"],
                "review_feedback": "Baseline",
                "review_feedback_history": ["Baseline"],
                "iteration_focus_history": [],
                "history": [],
                "best_iteration": {
                    "iteration": 0,
                    "quality_score": 25,
                    "draft_post": "v0",
                },
            },
            # Iter 1 (improves)
            {
                "quality_score": 30,
                "scores": {"density": 6},
                "frozen_focus_factors": ["density"],
                "active_focus_factors": ["density"],
                "review_feedback": "Improved",
                "review_feedback_history": ["Baseline", "Improved"],
                "iteration_focus_history": [],
                "history": [],
                "best_iteration": {
                    "iteration": 1,
                    "quality_score": 30,
                    "draft_post": "v1",
                },
            },
            # Iter 2 (BEST)
            {
                "quality_score": 35,
                "scores": {"density": 8},
                "frozen_focus_factors": ["density"],
                "active_focus_factors": [],
                "review_feedback": "Best",
                "review_feedback_history": ["Baseline", "Improved", "Best"],
                "iteration_focus_history": [],
                "history": [],
                "best_iteration": {
                    "iteration": 2,
                    "quality_score": 35,
                    "draft_post": "v2",
                },
            },
            # Iter 3 (regression)
            {
                "quality_score": 32,
                "scores": {"density": 6},
                "frozen_focus_factors": ["density"],
                "active_focus_factors": [],
                "review_feedback": "Regressed",
                "review_feedback_history": [],
                "iteration_focus_history": [],
                "history": [],
                "best_iteration": {
                    "iteration": 2,
                    "quality_score": 35,
                    "draft_post": "v2",
                },
            },
            # Iter 4 (partial recovery, but not best)
            {
                "quality_score": 33,
                "scores": {"density": 7},
                "frozen_focus_factors": ["density"],
                "active_focus_factors": [],
                "review_feedback": "Recovered",
                "review_feedback_history": [],
                "iteration_focus_history": [],
                "history": [],
                "best_iteration": {
                    "iteration": 2,
                    "quality_score": 35,
                    "draft_post": "v2",
                },
            },
            # Sentinel
            {
                "quality_score": 35,
                "scores": {"density": 8},
                "frozen_focus_factors": ["density"],
                "active_focus_factors": [],
                "review_feedback": "Final",
                "review_feedback_history": [],
                "iteration_focus_history": [],
                "history": [],
                "best_iteration": {
                    "iteration": 2,
                    "quality_score": 35,
                    "draft_post": "v2",
                },
            },
        ],
    )

    # --------------------------------------------------
    # Initial state
    # --------------------------------------------------
    state = {
        "topic": "Test",
        "communication_style": "ENGINEERING_DIRECT",
        "intent": None,
        "draft_post": "",
        "iteration_count": 0,
        "max_iterations": 10,
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
    best = final_state["best_iteration"]

    # --------------------------------------------------
    # Assertion: GLOBAL BEST wins
    # --------------------------------------------------
    assert best["quality_score"] == 35
    assert best["draft_post"] == "v2"
