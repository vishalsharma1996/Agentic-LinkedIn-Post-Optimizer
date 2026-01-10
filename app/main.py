from fastapi import FastAPI
from pydantic import BaseModel, Field
from graph.workflow import linkedin_post_workflow

app = FastAPI(
    title="Agentic LinkedIn Post Optimizer",
    description="Automates generate → review → revise loop using LangGraph",
    version="1.0.0",
)


class PostRequest(BaseModel):
    topic: str = Field(..., description="Topic for the LinkedIn post")
    max_iterations: int = Field(3, ge=1, le=5)


class PostResponse(BaseModel):
    final_post: str
    iterations_used: int
    final_score: int
    review_decision: str


@app.post("/optimize", response_model=PostResponse)
def optimize_linkedin_post(request: PostRequest):
    """
    Runs the agentic loop:
    Generate → Review → Revise (until stop condition)
    """

    initial_state = {
        "topic": request.topic,
        "iteration_count": 0,
        "max_iterations": request.max_iterations,
    }

    final_state = linkedin_post_workflow.invoke(initial_state)

    return {
        "final_post": final_state["draft_post"],
        "iterations_used": final_state["iteration_count"],
        "final_score": final_state.get("quality_score", 0),
        "review_decision": final_state.get("review_decision", "unknown"),
    }
