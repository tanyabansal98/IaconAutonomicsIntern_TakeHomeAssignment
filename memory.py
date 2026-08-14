"""
memory.py

The agent's working memory: a running list of facts it has collected,
each tagged with its source. This is the harness's state-management
layer -- kept deliberately simple (a list of dicts) so it's easy to
inspect and to feed into report synthesis.
"""


class WorkingMemory:
    def __init__(self):
        self.notes: list[dict] = []
        self.searches_done: list[str] = []
        self.sources_read: list[str] = []

    def add_note(self, fact: str, source: str):
        self.notes.append({"fact": fact, "source": source})

    def record_search(self, query: str):
        self.searches_done.append(query)

    def record_source_read(self, url: str):
        self.sources_read.append(url)

    def has_enough_notes(self, minimum: int = 3) -> bool:
        return len(self.notes) >= minimum

    def as_context_block(self) -> str:
        if not self.notes:
            return "(no notes collected yet)"
        lines = []
        for i, n in enumerate(self.notes, 1):
            lines.append(f"{i}. {n['fact']} [source: {n['source']}]")
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "notes": self.notes,
            "searches_done": self.searches_done,
            "sources_read": self.sources_read,
        }