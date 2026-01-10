from typing import TypedDict, Literal, List, Dict, Any

class LinkedInPostState(TypedDict):
    topic: str
    draft_post: str
    review_decision: Literal["accept", "revise"]
    review_feedback: str
    quality_score: int
    iteration_count: int
    max_iterations: int
    history: List[Dict[str, Any]]
