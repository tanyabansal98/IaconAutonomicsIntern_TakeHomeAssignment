# AI Usage Documentation

**Tools used:** Claude (Anthropic) for pair-programming the entire build; OpenAI `gpt-4o-mini` and Anthropic `claude-3-5-haiku` as the two optional LLM backends the agent itself uses at runtime.

**What for:** Claude wrote all source files (config, tools, agent loop, Streamlit UI) and docs, iterated with me file-by-file. The LLM APIs power the agent's tool-selection reasoning when a key is supplied; without one, a scripted demo planner runs instead.

**Verification:** I ran every file myself and fixed real bugs together with Claude by reading actual error tracebacks and trajectory logs — a rate-limited search backend, an HTML-scraping bug, a query-parsing bug, an SDK version conflict, and a runaway search loop that never saved notes.

**Limitation:** Free Wikipedia search has weak coverage of niche AI terms (e.g. "ReAct" matches React.js); resolved only with an optional Tavily key.
