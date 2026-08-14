# 🔎 Autonomous Research Agent Harness

An autonomous, tool-using AI research agent harness equipped with stateful working memory, dynamic search capabilities (Wikipedia & Tavily), rate-limiting safety guards, trajectory logging, and a Streamlit web interface.

---

## 🌟 Highlights & Key Features

- **🤖 Multi-Provider LLM Support**: Seamless integration with **OpenAI (`gpt-4o-mini`)**, **Anthropic (`claude-3-5-haiku`)**, or a **Free Scripted Demo Mode** (no API key required).
- **🔎 Dynamic Dual-Mode Search**: 
  - **Wikipedia API**: Free search fallback out-of-the-box (no API keys required).
  - **Tavily Web Search API**: Live web search capabilities when an API key is provided.
- **🧠 Stateful Working Memory**: Accumulates notes, facts, and source citations throughout the research trajectory before synthesizing the final output.
- **🛡️ Token Guard & Rate Limit Protection**:
  - Interactive **Max Agent Loop Steps** slider to cap tool iterations and prevent burning LLM API tokens.
  - Retries with exponential backoff for handling `HTTP 429 Too Many Requests`.
- **📜 Trajectory Logging**: Full event-level JSON trajectory tracking (`task_start`, `agent_decision`, `tool_call`, `tool_result`, `tool_failure`, `task_complete`).
- **🎨 Interactive Streamlit UI**: User-friendly dashboard featuring Markdown reports, visual note cards, step-by-step event timelines, and expandable raw JSON inspection.

---

## 📁 Repository Structure

```
research_agent/
├── app.py              # Entry point forwarding to main.py
├── main.py             # Streamlit application dashboard & UI layout
├── agent.py            # Core ReAct ResearchAgent execution engine & system prompt
├── tools.py            # Tool implementations (search, read_source, save_note, calculate, write_report)
├── memory.py           # WorkingMemory data structures & state management
├── config.py           # Configuration loader & provider detection
├── logger.py           # TrajectoryLogger for persisting JSON run logs
├── run_logs/           # Directory where trajectory JSON run logs are stored
├── requirements.txt    # Project dependencies
└── README.md           # Documentation
```

---

## 🛠️ Installation & Setup

### 1. Prerequisites
- Python 3.10+ installed on your system.

### 2. Virtual Environment Setup

Clone or navigate into the repository directory:

```bash
cd research_agent
```

Create and activate a Python virtual environment:

```bash
# Create virtual environment
python3 -m venv venv

# Activate on macOS/Linux
source venv/bin/activate

# Activate on Windows Command Prompt
# venv\Scripts\activate
```

### 3. Install Dependencies

Install all required Python packages:

```bash
pip install -r requirements.txt
```

---

## 🚀 Running the Web Application

Launch the Streamlit dashboard using your virtual environment:

```bash
./venv/bin/streamlit run main.py
```
*(Or simply `streamlit run main.py` if your virtual environment is actively sourced)*

Open your browser and navigate to:
**`http://localhost:8501`**

---

## ⚙️ Configuration & Operating Modes

### 1. Free Demo Mode (Default)
- **No API Keys Needed**: Leave all API key fields blank in the sidebar.
- **Planner**: Uses a deterministic scripted planner to formulate queries, scrape text, store notes, and synthesize a structured report.
- **Search Provider**: Queries free Wikipedia API.

### 2. OpenAI Mode
- Enter your **OpenAI API Key** in the sidebar.
- Uses **`gpt-4o-mini`** for function calling and step-by-step ReAct reasoning.

### 3. Anthropic Mode
- Enter your **Anthropic API Key** in the sidebar.
- Uses **`claude-3-5-haiku-20241022`** for tool calls and analytical synthesis.

### 4. Real Web Search Mode (Optional)
- Enter a **Tavily API Key** in the sidebar.
- Automatically upgrades search tool from Wikipedia API to live web search using Tavily.

---

## 📊 System Architecture & Tool Workflow

```
┌─────────────────┐
│ User Research   │
│    Question     │
└────────┬────────┘
         │
         ▼
┌───────────────────────────────────────────────────────────┐
│                    ResearchAgent Engine                   │
│                                                           │
│  1. LLM Evaluates State & Chooses Tool                    │
│  2. Executes Tool via Function Calling                    │
│  3. Logs Event to TrajectoryLogger                        │
└──────┬──────────────────────┬──────────────────────┬──────┘
       │                      │                      │
       ▼                      ▼                      ▼
┌──────────────┐      ┌──────────────┐       ┌──────────────┐
│    search    │      │ read_source  │       │  save_note   │
│ (Wiki/Tavily)│      │(HTML Cleaner)│       │(Fact+Source) │
└──────┬───────┘      └──────┬───────┘       └──────┬───────┘
       │                     │                      │
       └─────────────────────┼──────────────────────┘
                             │
                             ▼
                  ┌────────────────────┐
                  │   WorkingMemory    │
                  └──────────┬─────────┘
                             │
                             ▼
                  ┌────────────────────┐
                  │    write_report    │
                  │ (Markdown Report)  │
                  └────────────────────┘
```

### Available Tools Defined in `tools.py`:
1. **`search(query)`**: Performs Wikipedia or Tavily web searches.
2. **`read_source(url)`**: Downloads and extracts clean readable text from HTML/Wikipedia extracts.
3. **`save_note(fact, source)`**: Saves an extracted fact and citation into `WorkingMemory`.
4. **`calculate(expression)`**: Evaluates basic mathematical expressions safely.
5. **`write_report(summary)`**: Compiles stored notes and LLM synthesis into an executive Markdown report.

---

## 🛡️ Safety Guards & Robustness

1. **Token Guard Slider**:
   - Limit the maximum tool iteration steps (1-15 steps, default 6) via the Streamlit sidebar to control LLM token expenditure.
2. **Rate Limit Handling**:
   - `tools.py` implements exponential backoff retries to gracefully handle `HTTP 429 Too Many Requests` status codes.
3. **Fallback Knowledge Synthesis**:
   - If search results are sparse or off-topic, the LLM falls back to synthesizing an analytical answer using pre-trained expert knowledge while noting search constraints.

---

## 📜 Trajectory Logging

Every run automatically generates a unique run ID and saves a JSON log in `run_logs/run_<id>.json`.

Each log includes:
- `task_start`: Question and mode.
- `agent_decision`: Current step number and LLM provider.
- `tool_call`: Tool name and arguments.
- `tool_result` / `tool_failure`: Tool outputs or exception messages.
- `task_complete`: Preview of generated report.

---

## 📄 License

Distributed under the MIT License.
