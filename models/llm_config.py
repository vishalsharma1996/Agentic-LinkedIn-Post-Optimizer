from langchain_openai import ChatOpenAI

# Intent Classifier LLM (Consistent Output)
intent_classifier_llm = ChatOpenAI(
    model="gpt-4.1-mini",
    temperature=0.0,
)

# Writer — strong POV, fluent, confident
generator_llm = ChatOpenAI(
    model="gpt-4.1",
    temperature=0.6,
)

# Editor — harsher, less impressed by fluency
evaluator_llm = ChatOpenAI(
    model="gpt-4.1-mini",
    temperature=0.0,
)

# Line editor — surgical rewrites only
optimizer_llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.2,
)
