import json
import uuid

from config import AgentConfig
from memory import WorkingMemory
from logger import TrajectoryLogger
import tools


MAX_STEPS = 8

TOOL_SPECS = [
    {"name": "search", "description": "Search the web for information on a topic.",
     "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}},
    {"name": "read_source", "description": "Fetch and read the full text content of a URL.",
     "parameters": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}},
    {"name": "save_note", "description": "Save a fact you learned into working memory, with its source URL.",
     "parameters": {"type": "object", "properties": {"fact": {"type": "string"}, "source": {"type": "string"}}, "required": ["fact", "source"]}},
    {"name": "calculate", "description": "Evaluate a basic arithmetic expression.",
     "parameters": {"type": "object", "properties": {"expression": {"type": "string"}}, "required": ["expression"]}},
    {"name": "write_report", "description": "Call when you are ready to produce the final report. Pass your detailed analysis in the summary parameter.",
     "parameters": {"type": "object", "properties": {"summary": {"type": "string", "description": "Detailed analysis and synthesis answering the question."}}, "required": []}},
]


SYSTEM_PROMPT = (
    "You are an expert AI research agent. Your goal is to systematically research and answer questions.\n\n"
    "CRITICAL PROTOCOL:\n"
    "1. Never execute more than 1 search query per step.\n"
    "2. Immediately after performing a search, you MUST call `read_source` on a relevant URL returned from the search.\n"
    "3. After calling `read_source`, you MUST call `save_note` to store key facts in working memory.\n"
    "4. If Wikipedia search yields weak or unrelated results (e.g. React.js software instead of ReAct AI agent architecture), do NOT loop search. Immediately call `write_report` and synthesize a comprehensive answer using your pre-trained expert LLM knowledge while noting search limitations."
)




class ResearchAgent:
    def __init__(self, cfg: AgentConfig, max_steps: int = 6):
        self.cfg = cfg
        self.max_steps = max_steps
        self.memory = WorkingMemory()
        run_id = f"run_{uuid.uuid4().hex[:8]}"
        self.logger = TrajectoryLogger(run_id)

    def run(self, question: str) -> str:
        self.logger.log_event("task_start", question=question, mode=self.cfg.llm_mode)
        try:
            if self.cfg.llm_mode == "demo":
                report = self._run_demo_mode(question)
            elif self.cfg.llm_mode == "openai":
                report = self._run_openai_mode(question)
            elif self.cfg.llm_mode == "anthropic":
                report = self._run_anthropic_mode(question)
            else:
                report = self._run_demo_mode(question)
            self.logger.log_event("task_complete", report_preview=report[:200])
            return report
        except Exception as e:
            self.logger.log_event("task_failed", reason=str(e))
            return f"❌ Agent execution failed: {str(e)}"


    def _execute_tool(self, tool_name: str, tool_args: dict) -> str:
        self.logger.log_event("tool_call", tool=tool_name, args=str(tool_args))
        try:
            if tool_name == "search":
                result = tools.search(tool_args["query"])
                self.memory.record_search(tool_args["query"])
                out = json.dumps(result)
            elif tool_name == "read_source":
                result = tools.read_source(tool_args["url"])
                self.memory.record_source_read(tool_args["url"])
                out = result
            elif tool_name == "save_note":
                out = tools.save_note(self.memory, tool_args["fact"], tool_args["source"])
            elif tool_name == "calculate":
                out = str(tools.calculate(tool_args["expression"]))
            elif tool_name == "write_report":
                out = "__WRITE_REPORT__"
            else:
                out = f"ERROR: unknown tool '{tool_name}'"
            self.logger.log_event("tool_result", tool=tool_name, result_preview=str(out)[:200])
            return out
        except tools.ToolError as e:
            self.logger.log_event("tool_failure", tool=tool_name, error=str(e))
            return f"ERROR: {e}"

    def _run_demo_mode(self, question: str) -> str:
        queries = self._derive_queries_demo(question)
        for query in queries:
            self._demo_search_and_note(query)
        return self._finish_demo(question)

    def _derive_queries_demo(self, question: str) -> list[str]:
        head = question.split("--")[0].split(":")[0]
        fragments = [f.strip() for f in head.split(",") if f.strip()]
        cleaned = []
        for f in fragments:
            words = f.split()
            if words and words[0].lower() == "and":
                words = words[1:]
            f = " ".join(words).strip()
            if f.lower().startswith("compare "):
                f = f[len("compare "):]
            if len(f) > 2:
                cleaned.append(f)
        if len(cleaned) < 2:
            return [question]
        return list(dict.fromkeys(cleaned))[:3]

    def _demo_search_and_note(self, query: str):
        raw = self._execute_tool("search", {"query": query})
        if raw.startswith("ERROR"):
            return
        results = json.loads(raw)
        top = results[0]
        content = self._execute_tool("read_source", {"url": top["url"]})
        if content.startswith("ERROR"):
            self._execute_tool("save_note", {"fact": f"(source unreadable, using snippet) {top['title']}: {top['snippet']}", "source": top["url"]})
            return
        excerpt = content[:280].rsplit(" ", 1)[0] + "..."
        self._execute_tool("save_note", {"fact": f"[{top['title']}] {excerpt}", "source": top["url"]})

    def _finish_demo(self, question: str) -> str:
        try:
            return tools.write_report(question, self.memory)
        except tools.ToolError as e:
            self.logger.log_event("task_failed", reason=str(e))
            return f"Could not produce a report: {e}"

    def _run_openai_mode(self, question: str) -> str:
        from openai import OpenAI
        client = OpenAI()
        openai_tools = [{"type": "function", "function": {"name": t["name"], "description": t["description"], "parameters": t["parameters"]}} for t in TOOL_SPECS]
        messages = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": question}]

        for step in range(self.max_steps):
            self.logger.log_event("agent_decision", step=step, provider="openai")
            resp = client.chat.completions.create(model="gpt-4o-mini", messages=messages, tools=openai_tools, tool_choice="auto")
            msg = resp.choices[0].message
            messages.append(msg.model_dump(exclude_unset=True))
            if not msg.tool_calls:
                return msg.content or self._finish_demo(question)
            for tc in msg.tool_calls:
                tool_name = tc.function.name
                try:
                    tool_args = json.loads(tc.function.arguments or "{}")
                except json.JSONDecodeError:
                    tool_args = {}
                if tool_name == "write_report":
                    synthesis = tool_args.get("summary", "")
                    return tools.write_report(question, self.memory, llm_synthesis=synthesis)
                result = self._execute_tool(tool_name, tool_args)
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})

        self.logger.log_event("task_failed", reason="max steps reached")
        return tools.write_report(question, self.memory, llm_synthesis="Completed maximum research iterations.")


    def _run_anthropic_mode(self, question: str) -> str:
        import anthropic
        client = anthropic.Anthropic()
        anthropic_tools = [{"name": t["name"], "description": t["description"], "input_schema": t["parameters"]} for t in TOOL_SPECS]
        messages = [{"role": "user", "content": question}]

        for step in range(self.max_steps):

            self.logger.log_event("agent_decision", step=step, provider="anthropic")
            resp = client.messages.create(model="claude-3-5-haiku-20241022", max_tokens=1024, system=SYSTEM_PROMPT, messages=messages, tools=anthropic_tools)
            messages.append({"role": "assistant", "content": resp.content})
            tool_uses = [b for b in resp.content if b.type == "tool_use"]
            if not tool_uses:
                text_blocks = [b.text for b in resp.content if b.type == "text"]
                return "\n".join(text_blocks) or self._finish_demo(question)
            tool_results = []
            for tu in tool_uses:
                if tu.name == "write_report":
                    return tools.write_report(question, self.memory) if self.memory.notes else "No notes were gathered; unable to produce a report."
                result = self._execute_tool(tu.name, tu.input)
                tool_results.append({"type": "tool_result", "tool_use_id": tu.id, "content": result})
            messages.append({"role": "user", "content": tool_results})

        self.logger.log_event("task_failed", reason="max steps reached")
        return self._finish_demo(question)