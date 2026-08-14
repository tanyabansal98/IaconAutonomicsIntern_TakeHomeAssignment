import re
import time
import os
import requests


class ToolError(Exception):
    pass


def search(query: str, max_results: int = 5, max_retries: int = 3) -> list[dict]:
    if not query or not query.strip():
        raise ToolError("search() called with an empty query")
    tavily_key = os.environ.get("TAVILY_API_KEY")
    if tavily_key:
        return _search_tavily(query, tavily_key, max_results, max_retries)
    return _search_wikipedia(query, max_results, max_retries)


def _search_tavily(query, api_key, max_results, max_retries):
    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.post(
                "https://api.tavily.com/search",
                json={"api_key": api_key, "query": query, "max_results": max_results},
                timeout=10,
            )
            resp.raise_for_status()
            hits = resp.json().get("results", [])
            if hits:
                return [{"title": h.get("title", ""), "url": h.get("url", ""), "snippet": h.get("content", "")[:300]} for h in hits]
            last_error = f"Tavily returned zero results for '{query}'"
        except Exception as e:
            last_error = f"Tavily search failed: {e}"
        if attempt < max_retries:
            time.sleep(2 ** attempt)
    raise ToolError(f"Tavily search failed after {max_retries} attempts: {last_error}")


def _search_wikipedia(query, max_results, max_retries):
    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.get(
                "https://en.wikipedia.org/w/api.php",
                params={"action": "query", "list": "search", "srsearch": query, "srlimit": max_results, "format": "json"},
                headers={"User-Agent": "research-agent-harness/1.0"},
                timeout=8,
            )
            resp.raise_for_status()
            hits = resp.json().get("query", {}).get("search", [])
            if hits:
                return [
                    {"title": h["title"], "url": f"https://en.wikipedia.org/wiki/{h['title'].replace(' ', '_')}", "snippet": re.sub(r"<[^>]+>", "", h.get("snippet", ""))}
                    for h in hits
                ]
            last_error = f"Wikipedia returned zero results for '{query}'"
        except Exception as e:
            last_error = f"Wikipedia search failed: {e}"
        if attempt < max_retries:
            time.sleep(2 ** attempt)
    raise ToolError(f"Wikipedia search failed after {max_retries} attempts: {last_error}")


def read_source(url: str, max_chars: int = 3000) -> str:
    if not url or not url.startswith("http"):
        raise ToolError(f"read_source() got an invalid url: '{url}'")
    if "wikipedia.org/wiki/" in url:
        return _read_wikipedia_extract(url, max_chars)
    return _read_generic_html(url, max_chars)


def _read_wikipedia_extract(url, max_chars):
    title = url.rsplit("/wiki/", 1)[-1]
    try:
        resp = requests.get(
            "https://en.wikipedia.org/w/api.php",
            params={"action": "query", "prop": "extracts", "explaintext": 1, "titles": title.replace("_", " "), "format": "json"},
            headers={"User-Agent": "research-agent-harness/1.0"},
            timeout=8,
        )
        resp.raise_for_status()
        pages = resp.json().get("query", {}).get("pages", {})
    except Exception as e:
        raise ToolError(f"could not fetch Wikipedia extract: {e}")
    for page in pages.values():
        extract = page.get("extract", "").strip()
        if extract:
            return extract[:max_chars]
    raise ToolError(f"Wikipedia extract for '{url}' was empty")


def _read_generic_html(url, max_chars):
    try:
        resp = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0 (research-agent-harness)"})
    except requests.RequestException as e:
        raise ToolError(f"could not fetch '{url}': {e}")
    if resp.status_code != 200:
        raise ToolError(f"'{url}' returned HTTP {resp.status_code}")
    text = re.sub(r"<script[^>]*>.*?</script>", " ", resp.text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style[^>]*>.*?</style>", " ", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        raise ToolError(f"'{url}' returned no readable text content")
    return text[:max_chars]


def save_note(memory, fact: str, source: str) -> str:
    if not fact or not fact.strip():
        raise ToolError("save_note() called with an empty fact")
    memory.add_note(fact.strip(), source)
    return f"Saved note: '{fact[:60]}...'"


def calculate(expression: str) -> float:
    allowed = re.fullmatch(r"[0-9+\-*/().\s]+", expression or "")
    if not allowed:
        raise ToolError(f"calculate() rejected unsafe expression: '{expression}'")
    try:
        return eval(expression, {"__builtins__": {}}, {})
    except Exception as e:
        raise ToolError(f"calculate() could not evaluate '{expression}': {e}")


def write_report(question: str, memory, llm_synthesis: str = "") -> str:
    report = []
    report.append(f"# 📊 Executive Research Report\n")
    report.append(f"**Target Question:** {question}\n")
    
    if llm_synthesis and llm_synthesis.strip():
        report.append("## 💡 Synthesis & Analysis")
        report.append(llm_synthesis.strip())
        report.append("")

    if memory.notes:
        report.append("## 📝 Key Findings & Gathered Evidence")
        for idx, n in enumerate(memory.notes, 1):
            report.append(f"{idx}. **{n['fact']}**")
            if n.get("source"):
                report.append(f"   - *Source:* `{n['source']}`")
        report.append("")
    elif not llm_synthesis:
        raise ToolError("write_report() called with no notes in memory and no synthesis content.")

    report.append("---")
    report.append(f"*Research Stats: Read {len(memory.sources_read)} source(s) across {len(memory.searches_done)} search(es).*")
    return "\n".join(report)