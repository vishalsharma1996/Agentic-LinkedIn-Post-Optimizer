from langchain_core.messages import SystemMessage, HumanMessage
from graph.state import LinkedInPostState
from models.llm_config import optimizer_llm

def optimize_linkedin_post(state: LinkedInPostState) -> LinkedInPostState:
    messages = [
        SystemMessage(
            content="You improve LinkedIn posts strictly using reviewer feedback."
        ),
        HumanMessage(
            content=f"""
Revise the LinkedIn post using the feedback below.

Feedback:
{state["review_feedback"]}

Current Draft:
\"\"\"
{state["draft_post"]}
\"\"\"

Rules:
- Preserve original intent.
- Strengthen the hook.
- Improve clarity and flow.
- No emojis.
- No hashtags.
- Output ONLY the revised post.
"""
        ),
    ]

    response = optimizer_llm.invoke(messages).content

    return {
        "draft_post": response,
        "iteration_count": state["iteration_count"] + 1,
    }
