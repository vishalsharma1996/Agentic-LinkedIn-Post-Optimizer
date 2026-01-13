from fastapi import FastAPI
from pydantic import BaseModel, Field
from fastapi.responses import PlainTextResponse
from typing import Dict, Any, Literal

from graph.workflow import linkedin_post_workflow


app = FastAPI(
    title="Agentic LinkedIn Post Optimizer",
    description=(
        "Automates intent-aware, style-controlled, "
        "proof-of-work-safe LinkedIn post optimization using LangGraph"
    ),
    version="1.1.0",
)


# ---------- API SCHEMAS ----------

class PostRequest(BaseModel):
    topic: str = Field(..., description="User-provided content or claim")
    max_iterations: int = Field(3, ge=1, le=8)

    communication_style: Literal[
        "ENGINEERING_DIRECT",
        "VIRAL_ENGINEER",
        "STORY_DRIVEN",
    ] = Field(
        "ENGINEERING_DIRECT",
        description="Controls how the post is framed, not what facts are allowed",
    )


class PostResponse(BaseModel):
    final_post: str
    iterations_used: int
    final_score: int
    review_decision: str


# ---------- STATE INITIALIZATION ----------

def build_initial_state(request: PostRequest) -> Dict[str, Any]:
    """
    Explicitly initialize all fields used by the agent graph.
    Intent, references, and content will be populated by graph nodes.
    """
    return {
        # User input
        "topic": request.topic,
        "communication_style": request.communication_style,

        # Control flow
        "iteration_count": 0,
        "max_iterations": request.max_iterations,

        # To be filled by graph nodes
        "intent": None,
        "references": [],
        "draft_post": "",
        "review_decision": "revise",
        "review_feedback": "",
        "quality_score": 0,

        # Diagnostics
        "history": [],
    }


# ---------- ENDPOINTS ----------

@app.post("/optimize", response_model=PostResponse)
def optimize_linkedin_post(request: PostRequest):
    """
    Runs the full agentic loop:
    Intent classification → (optional references) →
    Generate → Evaluate → Optimize (until stop condition)
    """

    initial_state = build_initial_state(request)
    final_state = linkedin_post_workflow.invoke(initial_state)

    return {
        "final_post": final_state["draft_post"],
        "iterations_used": final_state["iteration_count"],
        "final_score": final_state.get("quality_score", 0),
        "review_decision": final_state.get("review_decision", "unknown"),
    }


@app.post("/optimize/text", response_class=PlainTextResponse)
def optimize_linkedin_post_text(request: PostRequest):
    """
    Returns only the final LinkedIn post text,
    formatted exactly as it should be published.
    """

    initial_state = build_initial_state(request)
    final_state = linkedin_post_workflow.invoke(initial_state)

    return final_state["draft_post"]
