import pytest
from graph.workflow import build_graph

def test_strong_generator_output_skips_optimization(mocker):
   # --------------------------------------------------
   # Mock ALL non-deterministic / LLM-calling nodes
   # --------------------------------------------------
   
    mocker.patch(
        "graph.workflow.intent_classifier",
        lambda state: {**state, "intent": "TECH_THOUGHT_LEADERSHIP"}
    )

    mocker.patch(
        "graph.workflow.reference_retriever",
        lambda state: state
    )

    mocker.patch(
        "graph.workflow.generate_linkedin_post",
        lambda state: {**state, "draft_post": "v0"}
    )

    optimizer_spy = mocker.patch(
        "graph.workflow.optimize_linkedin_post"
    )

    mocker.patch(
        "graph.workflow.summarize_changes",
        lambda state: state
    )

    mocker.patch(
        "graph.workflow.evaluate_linkedin_post",
        return_value={
            "review_decision": "accept",
            "review_feedback": "Strong initial draft",
            "review_feedback_history": ["Strong initial draft"],
            "quality_score": 41,
            "scores": {"hook_strength": 8},
            "frozen_focus_factors": ["hook_strength"],
            "active_focus_factors": [],
            "iteration_focus_history": [],
            "history": [],
            "best_iteration": {
                "iteration": 0,
                "quality_score": 41,
                "draft_post": "v0",
            },
        },
    )

    workflow = build_graph().compile()
    final_state = workflow.invoke({
        "topic": "Test",
        "communication_style": "VIRAL_ENGINEER",
        "iteration_count": 0,
        "max_iterations": 5,
        "draft_post": "",
        "scores": {},
        "quality_score": 0,
        "frozen_focus_factors": [],
        "active_focus_factors": [],
        "focus_graduation_threshold": 8,
        "history": [],
        "review_feedback": "",
        "review_feedback_history": [],
        "iteration_focus_history": [],
        "best_iteration": None,
    })

    best = final_state["best_iteration"] if len(final_state['best_iteration']) else final_state


    assert best["quality_score"] == 41
    assert best["draft_post"] == "v0"
    optimizer_spy.assert_not_called()
