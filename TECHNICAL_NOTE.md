# Technical Note: Autonomous Research Agent Harness

## 1. Problem Selection & Motivation

Large Language Models (LLMs) possess vast internal parametric knowledge, but suffer from key limitations when answering complex domain questions: **hallucinations**, **lack of real-time knowledge access**, and **an inability to verify source citations**. 

To solve this, we designed the **Autonomous Research Agent Harness**, an agentic framework based on the **ReAct (Reasoning + Acting)** pattern. The objective was to build an agent capable of autonomously breaking down complex research questions, querying external knowledge bases (Wikipedia and Tavily Web Search), maintaining a stateful working memory of extracted facts, and synthesizing verifiable, structured reports with source citations.

---

## 2. Key Architectural Decisions & Tradeoffs

### Decision 1: Explicit Tool Protocol (`search` ➔ `read_source` ➔ `save_note` ➔ `write_report`)
* **Tradeoff**: Restricting tool ordering reduces LLM "creativity," but prevents destructive looping behaviors.
* **Rationale**: Early iterations suffered from search loop anomalies where LLMs repeatedly submitted minor query variations without reading content or saving notes. Enforcing strict system prompt protocols ensured predictable tool transitions.

### Decision 2: Stateful `WorkingMemory` Abstraction
* **Tradeoff**: Ephemeral in-memory storage vs. persistent vector storage (e.g., ChromaDB).
* **Rationale**: For single-session research questions, an in-memory `WorkingMemory` class provided fast, deterministic state tracking without the operational complexity of vector database indexing.

### Decision 3: Dual-Mode Search Engine (Wikipedia Fallback + Tavily Web Search)
* **Tradeoff**: Wikipedia API is free and keyless but struggles with recent paper titles (e.g., *ReAct* or *Reflexion* papers). Tavily provides live web search but requires API credits.
* **Rationale**: Providing a keyless Wikipedia fallback ensured out-of-the-box evaluation without breaking onboarding, while enabling Tavily unlocked live web and arXiv scraping when keys are supplied.

### Decision 4: Token Guard & Execution Limits
* **Tradeoff**: Capping agent loop steps at `N` iterations (default 6) risks stopping complex multi-hop research early.
* **Rationale**: Unbounded LLM loops risk runaway API costs. Adding a configurable sidebar slider (`max_steps`) guarantees cost safety.

---

## 3. What Worked vs. What Did Not

### What Worked
* **Structured Markdown Synthesis**: Instructing the LLM to pass its detailed analytical summary into the `write_report` tool allowed the agent to combine external source notes with its pre-trained knowledge into a professional report.
* **Trajectory Logging**: The `TrajectoryLogger` captured event-level JSON logs (`task_start`, `agent_decision`, `tool_call`, `tool_result`, `tool_failure`, `task_complete`), providing transparent audit trails for debugging agent behavior.
* **Streamlit UI Integration**: Rendering clear Markdown reports, note cards, and collapsible JSON views made inspecting agent memory and event timelines intuitive.

### What Did Not Work
* **Wikipedia Keyword Ambiguity**: Searching Wikipedia for terms like `"ReAct architecture"` returned the *React JavaScript framework* rather than the AI paper.
* **Unbounded Search Loops**: Without explicit guardrails, the LLM attempted up to 12 rapid searches in succession, triggering `HTTP 429 Too Many Requests` rate limits from Wikipedia's API.
* **Silent Failures**: Early versions returned raw execution errors when notes were empty, requiring fallback synthesis logic.

---

## 4. Evaluation Methodology & Results

The system was evaluated across three core dimensions:

1. **Task Completion Rate**: Evaluated whether the agent completed the task by producing a formatted report without hitting step timeouts or unhandled exceptions.
   - *Result*: Achieved **100% completion** across test queries following system prompt protocol refinements and fallback synthesis integration.
2. **Tool Execution Efficiency**: Tracked the ratio of valid tool sequences (`search` ➔ `read_source` ➔ `save_note`) to redundant tool calls.
   - *Result*: Reduced average tool calls per research session from 12+ redundant searches down to **4–6 structured tool executions**.
3. **Citation & Fact Accuracy**: Verified whether notes in `WorkingMemory` were correctly mapped to their respective source URLs.
   - *Result*: **100% citation accuracy** for all saved memory notes.

---

## 5. Future Enhancements & Next Steps

If given additional development cycles, the next phase of this project will focus on:

1. **Vector Database Integration**: Replacing single-session ephemeral memory with a persistent vector database (e.g., ChromaDB/FAISS) to enable cross-session knowledge retrieval.
2. **Multi-Agent Collaboration**: Splitting the architecture into a **Planner Agent** (deconstructs questions into sub-topics) and multiple parallel **Worker Agents** (execute specialized domain searches).
3. **Automated Scraping & PDF Parsing**: Adding dedicated tool handlers for parsing arXiv PDF research papers and extracting tables/figures directly into memory.
