# Agentic LinkedIn Post Optimizer (LangGraph + FastAPI)

This project demonstrates how to turn **manual prompt iteration** into a **deterministic, agentic workflow** using LangGraph and FastAPI.

Instead of repeatedly prompting an LLM to rewrite content, the system:
1. Generates a LinkedIn post
2. Evaluates it using strict, structured criteria
3. Iteratively refines it until it meets a quality threshold or hits a max iteration limit

The focus is **systems and control flow**, not prompt hacking.

---

## Why this project exists

Most AI content workflows look like this:

> Prompt → Rewrite → Rewrite → Rewrite → Accept something mediocre

This repository shows how to replace that loop with:
- Explicit agent roles
- Code-enforced acceptance logic
- Transparent iteration history
- Repeatable, inspectable behavior

The goal is not “better prompts”, but **better loops**.

---

## Repository Structure
```text
agentic-linkedin-post-optimizer/
│
├── app/
│ ├── init.py
│ └── main.py # FastAPI entrypoint
│
├── graph/
│ ├── init.py
│ ├── state.py # Typed agent state
│ └── workflow.py # LangGraph control flow
│
├── prompts/
│ ├── init.py
│ ├── generator.py # Post generation agent
│ ├── evaluator.py # Structured evaluation agent
│ └── optimizer.py # Iterative refinement agent
│
├── models/
│ ├── init.py
│ └── llm_config.py # Model + temperature configuration
│
├── Dockerfile
├── requirements.txt
├── .dockerignore
```

---

## High-Level Architecture



### Flow Overview

1. **Generator Agent**
   - Produces an initial LinkedIn post from a topic
   - Enforces structure: opening line + numbered points

2. **Evaluator Agent**
   - Scores the post on structure, density, and engineering credibility
   - Returns structured feedback (JSON)
   - Does **not** decide acceptance

3. **Optimizer Agent**
   - Refines the post using evaluator feedback
   - Increases information density without bloating length

4. **LangGraph Control Logic**
   - Loops until:
     - Quality score ≥ threshold, or
     - Max iterations reached
   - Prevents infinite loops
   - Keeps state explicit and inspectable

5. **FastAPI Layer**
   - `/optimize` → JSON response (includes history)
   - `/optimize/text` → Plain text, LinkedIn-ready output

---

