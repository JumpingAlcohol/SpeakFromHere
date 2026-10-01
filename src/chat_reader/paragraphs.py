"""Bounded extraction, independent of Windows and the speech engine.

A platform adapter must establish reply ownership and completeness before
constructing a Reply with complete=True. A window's text is not a reply.
"""

from dataclasses import dataclass


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


def text_from_paragraph(reply: Reply, paragraph_id: str) -> str:
    """Return a verified assistant reply's suffix, never a whole conversation."""
    if reply.role != "assistant" or not reply.complete:
        raise ParagraphUnavailable("A complete assistant reply has not been verified.")
    readable = {"paragraph", "list_item", "heading"}
    ids = [block.id for block in reply.blocks]
    if len(set(ids)) != len(ids) or any(not key for key in ids):
        raise ParagraphUnavailable("Paragraph identities are ambiguous.")
    if any(block.kind not in readable | {"code"} for block in reply.blocks):
        raise ParagraphUnavailable("This reply contains an unclassified structure.")
    if paragraph_id not in ids:
        raise ParagraphUnavailable("The paragraph does not belong to this reply.")
    start = ids.index(paragraph_id)
    if reply.blocks[start].kind not in readable:
        raise ParagraphUnavailable("Point at a text paragraph, not a code block.")
    text = "\n\n".join(block.text.strip() for block in reply.blocks[start:]
                       if block.kind in readable and block.text.strip())
    if not text:
        raise ParagraphUnavailable("There is no readable text at this position.")
    return text
