import os
import json
import streamlit as st

st.set_page_config(page_title="Research Agent Harness", layout="wide", page_icon="🔎")
st.title("🔎 Research Agent Harness")

with st.sidebar:
    st.header("⚙️ Configuration & Limits")
    st.caption("Leave blank to run in free demo mode.")
    openai_key = st.text_input("OpenAI API Key", type="password")
    anthropic_key = st.text_input("Anthropic API Key", type="password")
    tavily_key = st.text_input("Tavily API Key (optional, real web search)", type="password")

    if openai_key:
        os.environ["OPENAI_API_KEY"] = openai_key
    if anthropic_key:
        os.environ["ANTHROPIC_API_KEY"] = anthropic_key
    if tavily_key:
        os.environ["TAVILY_API_KEY"] = tavily_key

    st.markdown("---")
    max_steps = st.slider("Max Agent Loop Steps (Token Guard)", min_value=1, max_value=15, value=6, help="Limits the maximum number of LLM tool iterations to prevent burning API credits.")

from config import load_config
from agent import ResearchAgent

cfg = load_config()
st.sidebar.markdown("---")
st.sidebar.write(f"**LLM mode:** `{cfg.llm_mode.upper()}`")
st.sidebar.write(f"**Search mode:** `{cfg.search_mode.upper()}`")
if cfg.llm_mode == "demo":
    st.sidebar.info("💡 No LLM key set — running in FREE DEMO MODE (scripted planner, real tools).")
if cfg.search_mode == "wikipedia":
    st.sidebar.info("💡 No Tavily key set — using free Wikipedia search.")

question = st.text_area(
    "Research question",
    value="Compare ReAct, Plan-and-Execute, and Reflexion as agent architectures -- which is most suitable for a tool-using coding assistant, and why?",
    height=100,
)

if st.button("🚀 Run Agent", type="primary"):
    try:
        with st.spinner(f"Running agent in {cfg.llm_mode.upper()} mode..."):
            agent = ResearchAgent(cfg, max_steps=max_steps)
            report = agent.run(question)

        st.markdown("### 📄 Research Report")
        st.markdown(report)

        st.markdown("---")
        col1, col2 = st.columns(2)

        mem_dict = agent.memory.to_dict()
        with col1:
            st.markdown("### 🧠 Working Memory Notes")
            notes = mem_dict.get("notes", [])
            if notes:
                for idx, note in enumerate(notes, 1):
                    with st.container(border=True):
                        st.markdown(f"**Note {idx}:** {note.get('fact')}")
                        if note.get("source"):
                            st.caption(f"📍 Source: {note.get('source')}")
            else:
                st.info("No notes saved in working memory.")

            with st.expander("🔍 View Raw Working Memory (JSON)"):
                st.json(mem_dict)

        with col2:
            st.markdown("### 📜 Agent Trajectory Timeline")
            try:
                with open(agent.logger.path) as f:
                    log_data = json.load(f)
                
                events = log_data.get("events", [])
                for ev in events:
                    ev_type = ev.get("type")
                    if ev_type == "tool_call":
                        st.write(f"🛠️ **Tool Executed:** `{ev.get('tool')}`")
                        st.caption(f"Arguments: `{ev.get('args')}`")
                    elif ev_type == "tool_result":
                        st.caption(f"Result Preview: {ev.get('result_preview', '')[:120]}...")
                    elif ev_type == "tool_failure":
                        st.error(f"❌ Tool Failed: `{ev.get('tool')}` - {ev.get('error')}")
                    elif ev_type == "agent_decision":
                        st.write(f"🤖 **Step {ev.get('step')}** ({ev.get('provider')})")

                with st.expander("🔍 View Raw Trajectory Log (JSON)"):
                    st.json(log_data)

                n_calls = sum(1 for e in events if e.get("type") == "tool_call")
                n_failures = sum(1 for e in events if e.get("type") == "tool_failure")
                st.success(f"Execution finished: {len(events)} events, {n_calls} tool calls, {n_failures} failures.")

            except Exception as e:
                st.warning(f"Could not load trajectory log: {e}")

    except Exception as err:
        st.error(f"⚠️ An error occurred while running the agent: {err}")