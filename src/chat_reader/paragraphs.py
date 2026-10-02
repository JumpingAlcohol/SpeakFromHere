"""Bounded extraction, independent of Windows and the speech engine.

A platform adapter must establish reply ownership and completeness before
constructing a Reply with complete=True. A window's text is not a reply.
"""

from dataclasses import dataclass

READABLE_KINDS = frozenset({"paragraph", "list_item", "heading"})
SKIPPED_KINDS = frozenset({"code", "table", "editor", "edited_files", "system_status"})


class ParagraphUnavailable(ValueError):
    """The requested start or reply boundary has not been established safely."""


@dataclass(frozen=True)
class Block:
    id: str
    kind: str
    text: str


@dataclass(frozen=True)
class Reply:
    id: str
    role: str
    blocks: tuple[Block, ...]
    complete: bool = False


@dataclass(frozen=True)
class SkippedBlock:
    kind: str
    ordinal: int
    before_start: bool


@dataclass(frozen=True)
class ReadingPlan:
    text: str
    skipped: tuple[SkippedBlock, ...] = ()

    def to_payload(self):
        return {"text": self.text, "skipped": [
            {"kind": item.kind, "ordinal": item.ordinal, "before_start": item.before_start}
            for item in self.skipped]}

    @classmethod
    def from_payload(cls, data):
        text, items = data.get("text"), data.get("skipped", [])
        if not isinstance(text, str) or not text.strip() or not isinstance(items, list) or len(items) > 1500:
            raise ValueError("Invalid reading plan")
        skipped = []
        previous = 0
        for item in items:
            if (not isinstance(item, dict) or set(item) != {"kind", "ordinal", "before_start"}
                    or not isinstance(item.get("kind"), str)
                    or item.get("kind") not in SKIPPED_KINDS
                    or type(item.get("ordinal")) is not int
                    or not previous < item["ordinal"] <= 1500
                    or type(item.get("before_start")) is not bool):
                raise ValueError("Invalid skipped block")
            skipped.append(SkippedBlock(**item))
            previous = item["ordinal"]
        return cls(text, tuple(skipped))


def plan_from_paragraph(reply: Reply, paragraph_id: str) -> ReadingPlan:
    """Return a verified assistant reply's suffix, never a whole conversation."""
    if reply.role != "assistant" or not reply.complete:
        raise ParagraphUnavailable("A complete assistant reply has not been verified.")
    readable = READABLE_KINDS
    ids = [block.id for block in reply.blocks]
    if len(set(ids)) != len(ids) or any(not key for key in ids):
        raise ParagraphUnavailable("Paragraph identities are ambiguous.")
    if any(block.kind not in readable | SKIPPED_KINDS for block in reply.blocks):
        raise ParagraphUnavailable("This reply contains an unclassified structure.")
    if paragraph_id not in ids:
        raise ParagraphUnavailable("The paragraph does not belong to this reply.")
    start = ids.index(paragraph_id)
    if reply.blocks[start].kind not in readable:
        raise ParagraphUnavailable("Point at a text paragraph, not a skipped block. Use Alt + S.")
    text = "\n\n".join(block.text.strip() for block in reply.blocks[start:]
                       if block.kind in readable and block.text.strip())
    if not text:
        raise ParagraphUnavailable("There is no readable text at this position.")
    skipped = tuple(SkippedBlock(block.kind, index + 1, index < start)
                    for index, block in enumerate(reply.blocks) if block.kind in SKIPPED_KINDS)
    return ReadingPlan(text, skipped)


def text_from_paragraph(reply: Reply, paragraph_id: str) -> str:
    """Legacy text-only API; playback uses the plan so omissions are disclosed."""
    return plan_from_paragraph(reply, paragraph_id).text
