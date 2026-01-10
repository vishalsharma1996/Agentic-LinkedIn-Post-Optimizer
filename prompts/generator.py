from langchain_core.messages import SystemMessage, HumanMessage
from graph.state import LinkedInPostState
from models.llm_config import generator_llm

def generate_linkedin_post(state: LinkedInPostState) -> LinkedInPostState:
    messages = [
        SystemMessage(
            content="You write high-quality, professional LinkedIn posts that feel human and insightful."
        ),
        HumanMessage(
            content=f"""
Write a concise LinkedIn post on the following topic:

Topic:
{state["topic"]}

Rules:
- First line must be a strong hook.
- Professional, conversational tone.
- No emojis.
- No hashtags.
- No hype or buzzwords.
- 5–8 short lines max.
- Simple, clear English.
"""
        ),
    ]

    response = generator_llm.invoke(messages).content

    return {
        "draft_post": response
    }
