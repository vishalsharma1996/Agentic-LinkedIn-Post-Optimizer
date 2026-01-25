import socket
from openai import OpenAIError

LLM_FAILURES = (
    OpenAIError,
    TimeoutError,
    socket.timeout,
)


def safe_llm_call(fn, state: dict, agent_name: str) -> dict:
    """
    Executes an LLM-backed function safely.

    On timeout / API failure:
    - Signals fail-soft termination
    - Preserves best iteration
    - Prevents further optimization
    """
    try:
        return fn(state)
    except LLM_FAILURES as e:
        state["run_metrics"]["stop_reason"] = f"{agent_name}_fail_soft"
        return {
            "__fail_soft__": True,
            "stop_reason": f"{agent_name}_timeout",
            "error": str(e),
        }
