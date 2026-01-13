# Agentic LinkedIn Post Optimizer (LangGraph + FastAPI)

![Architecture](docs/Architecture_Image.png)

This project demonstrates how to turn manual prompt iteration into a deterministic, agentic workflow using LangGraph and FastAPI.

Instead of repeatedly prompting an LLM to rewrite content, the system models writing as a controlled loop with explicit agent roles, clear stopping conditions, and inspectable state.

The focus is systems and control flow, not prompt hacking.

---

## Why this project exists

Most AI content workflows look like this:

Prompt → Rewrite → Rewrite → Rewrite → Accept something mediocre


This repository shows how to replace that pattern with:

1) Explicit agent roles (writer, editor, line editor)

2) Code-enforced acceptance logic

3) Intent-aware generation rules

4) Style as a presentation layer (not a truth layer)

5) Transparent iteration history

6) Repeatable, inspectable behavior


The goal is not “better prompts”, but **better loops**.

What This System Does

At a high level, the system:

1) Classifies intent (Proof of Work vs Tech Thought Leadership)

2) Generates a draft using intent-specific rules

3) Evaluates quality using strict, structured criteria

4) Refines the draft based on evaluator feedback

5) Stops deterministically when quality or iteration limits are reached

Acceptance is enforced in code, not by the model.
---

## Repository Structure

```text
agentic-linkedin-post-optimizer/
│
├── app/
│   ├── __init__.py
│   └── main.py          # FastAPI entrypoint
│
├── graph/
│   ├── __init__.py
│   ├── state.py         # Typed agent state
│   └── workflow.py     # LangGraph control flow
│
├── prompts/
│   ├── __init__.py
│   ├── intent_classifier.py
│   ├── generator.py    # Writer agent
│   ├── evaluator.py    # Editor agent
│   └── optimizer.py    # Line editor agent
│
├── models/
│   ├── __init__.py
│   └── llm_config.py   # Model + temperature configuration
│
├── Dockerfile
├── requirements.txt
├── .dockerignore

```

---

## High-Level Architecture



### Flow Overview

User Input
   ↓
Intent Classifier
   ↓
Communication Style Selection
   ↓
Generator (Writer)
   ↓
Evaluator (Editor)
   ↓
Optimizer (Line Editor)
   ↓
Code-Enforced Stop Logic
   ↓
Final LinkedIn Post


**Agent Roles (Explicit by Design)**

**Generator Agent (Writer)**

Responsibilities:

1) Drafts the initial LinkedIn post

2) Applies intent-specific rules

3) Produces claim-driven content (not format-driven)

**Intent Behavior**

**Proof of Work**

1) Uses only user-provided facts and metrics

2) No invented mechanisms or numbers

3) Allows bounded interpretation (what mattered, what drove results)

4) No forced bullets or point counts

**Tech Thought Leadership**

1) Opinionated, production-grounded reasoning

2) No metrics

3) Structured explanations allowed

**Communication Style (Presentation Only)**

1) ENGINEERING_DIRECT — concise, factual

2) VIRAL_ENGINEER — scroll-stopping, senior POV

3) STORY_DRIVEN — narrative arc, still factual

Style controls how things are said, not what is allowed.

**Evaluator Agent (Editor)**

**Most critical component in the system.**

**Responsibilities**

1) Scores the draft across multiple dimensions

2) Returns structured feedback (JSON)

3) Does not decide acceptance

4) Is intentionally skeptical and hard to impress

**Scoring Dimensions**

1) Hook strength

2) Factual grounding

3) Cause → effect clarity

4) Interpretive judgment

5) Information density

**The evaluator never sees acceptance thresholds.**
**Stopping logic is enforced strictly in code.**

**Optimizer Agent (Line Editor)**

**Responsibilities**

1) Refines the draft using evaluator feedback

2) Increases clarity and density

3) Removes redundancy and abstraction

4) Preserves all factual constraints

**The optimizer is allowed to:**

1) Merge or remove weak claims

2) Reformat structure if it improves clarity

3) Strengthen interpretation without adding facts

**LangGraph Control Logic**

**The LangGraph workflow:**

1) Makes state explicit and typed

2) Prevents infinite loops

3) Tracks iteration history

4) Enforces stopping conditions in code

**The loop terminates when:**

1) Quality score ≥ threshold, or

2) Maximum iteration count is reached

5. **FastAPI Layer**
   - `/optimize` → JSON response (includes history)
   - `/optimize/text` → Plain text, LinkedIn-ready output

---

**Model Configuration & Rationale**

This project intentionally uses different LLMs for different agent roles.
Each agent has a distinct responsibility, and model choice is aligned to that responsibility.

The goal is consistency, control, and cost-awareness, not using a single model everywhere.

**Generator Agent**

**Model: gpt-4.1**
**Temperature: 0.6**

Why this model?

1) Produces realistic, experience-driven engineering narratives

2) Strong at senior-level framing and bounded interpretation

3) Balances creativity with technical grounding

The generator’s job is to draft content that feels like it was written by a senior engineer, not to be perfect.

**Evaluator Agent (Most Critical)**

**Model: gpt-4.1-mini**
**Temperature: 0.0**

Why this model?

1) Less impressed by fluent prose, more literal and skeptical

2) Highly consistent judgment across iterations

3) Strong at identifying abstraction, redundancy, and weak claims

The evaluator does not decide acceptance.
It only scores and critiques — final acceptance is enforced in code.

This separation is intentional and mirrors real production systems.

**Optimizer Agent**

**Model: gpt-4o-mini**
**Temperature: 0.2–0.3**

Why this model?

1) Excellent at constrained rewriting and refinement

2) Low tendency to hallucinate new ideas or facts

3) Significantly cheaper than full-size models

The optimizer improves density, clarity, and precision without altering intent or factual constraints.

**Why Not Use One Model Everywhere?**

Using a single model for all agents often leads to:

1) Self-agreeing evaluation loops

2) Inflated early scores

3) Over-optimization or cosmetic rewrites

4) Poor debuggability and unclear failure modes

By specializing models per role, the system achieves:

1) More stable convergence

2) Clear separation of responsibilities

3) Lower overall cost

4) Meaningful iteration gradients

Summary Table
Agent Role	Model	Temperature	Purpose
Generator	gpt-4.1	0.6	Draft realistic, senior-engineer content
Evaluator	gpt-4.1-mini	0.0	Strict, skeptical scoring & critique
Optimizer	gpt-4o-mini	0.2–0.3	Precise refinement under constraints

## How to Run the Project

You can run this project **locally** or using **Docker**.  
Both approaches expose the same FastAPI endpoints.

---

## Prerequisites

- Python **3.10+**
- An OpenAI API key
- (Optional) Docker

Set your OpenAI API key as an environment variable:

```bash
export OPENAI_API_KEY=sk-xxxx
pip install -r requirements.txt
uvicorn app.main:app --reload

docker build -t agentic-linkedin-post-optimizer .
docker run -p 8000:8000 \
  -e OPENAI_API_KEY=sk-xxxx \
  agentic-linkedin-post-optimizer
```
## FASTAPI EndPoint

![Architecture](docs/s1.png)

## ExampleOutput(## Virality Post)
![Architecture](docs/s2.png)

![Architecture](docs/s3.png)

## ExampleOutput(## Story Driven)
![Architecture](docs/s4.png)





