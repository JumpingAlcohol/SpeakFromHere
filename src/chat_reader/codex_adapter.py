"""Conservative adapter for the inspected Codex desktop Chromium layout.

No window-wide text is spoken. Hidden speaker headings bound a reply;
paragraph identities and rectangles establish the starting block, and a
reply-level copy toolbar establishes completion. Unknown layouts fail closed.
"""

import math
import re

from chat_reader.paragraphs import Block, ParagraphUnavailable, Reply, text_from_paragraph


def _walk(node, path=()):
    yield node, path
    for index, child in enumerate(node.get("children", ())):
        yield from _walk(child, path + (index,))


def _css(node, prefix):
    return any(token.startswith(prefix) for token in node.get("class_name", "").split())


def _marker(node):
    if (node.get("role") != "heading" or not _css(node, "sr-only")
            or node.get("heading_level") != 80054):
        return None
    label = node.get("name", "").strip().rstrip(":：").strip()
    if label in {"ChatGPT 说", "ChatGPT said"}:
        return "assistant"
    if label in {"你说", "You said"}:
        return "user"
    return "unknown"


def _contains(node, point):
    box = node.get("bounds")
    if (node.get("offscreen") is not False or not box or len(box) != 4
            or not all(isinstance(v, (int, float)) and math.isfinite(v) for v in box)):
        return False
    x, y, width, height = box
    return width > 0 and height > 0 and x <= point[0] < x + width and y <= point[1] < y + height


def _units(node, path):
    """Return recognized body blocks without reading text during hit testing."""
    role = node.get("role")
    if _css(node, "_CodeBlock_"):
        return [(node, path, "code")]
    if _css(node, "_Paragraph_"):
        return [(node, path, "paragraph")]
    if role == "heading" and _marker(node) is None and not _css(node, "sr-only"):
        return [(node, path, "heading")]
    if role == "list" and _css(node, "_List_"):
        result = []
        for index, item in enumerate(node.get("children", ())):
            if item.get("role") != "listitem" or not _css(item, "_ListItem_"):
                raise ParagraphUnavailable("This list uses an unsupported structure. Use Alt + S.")
            item_path = path + (index,)
            result.append((item, item_path, "list_item"))
            for subindex, child in enumerate(item.get("children", ())):
                if child.get("role") == "list":
                    nested = _units(child, item_path + (subindex,))
                    if nested is None:
                        raise ParagraphUnavailable("The nested list cannot be read safely. Use Alt + S.")
                    result.extend(nested)
        return result
    return None


def _inline_text(node):
    if node.get("password") is not False:
        raise ParagraphUnavailable("Protected or unavailable reply text cannot be read.")
    role = node.get("role")
    if role == "list":
        return ""  # Nested items are separate blocks, not repeated inside their parent.
    if role == "img" and _css(node, "_Icon_") and not node.get("name"):
        return ""
    if role not in {"group", "description", "text", "strong", "emphasis", "em", "link",
                    "code", "heading", "listitem"} and not (
                        role == "button" and _css(node, "_InlineMentionFocusRing_")):
        raise ParagraphUnavailable("This paragraph contains an unsupported control. Use Alt + S.")
    children = node.get("children", ())
    if children:
        return "".join(_inline_text(child) for child in children)
    return node.get("name", "")


def _toolbar(node):
    if node.get("role") != "group" or not _css(node, "contents"):
        return False, False
    descendants = [item for item, _ in _walk(node)]
    if (not any(item.get("role") == "button" for item in descendants)
            or any(item.get("role") not in {"group", "button", "img", "description", "text"}
                   for item in descendants)):
        return False, False
    copy = any(item.get("role") == "button" and item.get("name") in {"复制", "Copy"}
               for item in descendants)
    return True, copy


def _reply(header, segment, base_path, offset):
    blocks = []
    completed = False
    for index, node in enumerate(segment):
        units = _units(node, base_path + (offset + index,))
        if units is not None:
            if completed:
                raise ParagraphUnavailable("Reply content appeared after its footer. Try again.")
            for item, _, kind in units:
                text = "" if kind == "code" else _inline_text(item).strip()
                if kind != "code" and not text:
                    raise ParagraphUnavailable("Part of the reply text is unavailable. Use Alt + S.")
                blocks.append(Block(item["id"], kind, text))
            continue
        if node.get("role") == "status" and _css(node, "sr-only"):
            continue
        toolbar, copy = _toolbar(node)
        if toolbar:
            completed = completed or copy
            continue
        if (completed and node.get("role") in {"description", "text"}
                and re.fullmatch(r"\d{1,2}:\d{2}", node.get("name", ""))):
            continue
        raise ParagraphUnavailable("This reply has an unsupported editor, table or layout. Use Alt + S.")
    if not completed:
        raise ParagraphUnavailable("The reply is not confirmed complete. Wait for it to finish or use Alt + S.")
    return Reply(header["id"], "assistant", tuple(blocks), complete=True)


def text_at_point(snapshot):
    """Resolve the physical mouse position to one complete reply's text suffix."""
    root = snapshot.get("tree", {})
    if (snapshot.get("schema_version") != 1 or snapshot.get("truncated") is not False
            or root.get("role") != "document" or root.get("framework") != "Chrome"):
        raise ParagraphUnavailable("The desktop text capture is incomplete or unsupported. Use Alt + S.")
    point = snapshot.get("point", ())
    if len(point) != 2 or not all(isinstance(v, (int, float)) and math.isfinite(v) for v in point):
        raise ParagraphUnavailable("The mouse position is unavailable.")
    rows = list(_walk(root))
    identities = [node.get("id") for node, _ in rows]
    if any(not key for key in identities) or len(set(identities)) != len(identities):
        raise ParagraphUnavailable("The desktop element identities are ambiguous. Try again.")
    paths = {node["id"]: path for node, path in rows}
    hit_path = paths.get(snapshot.get("point_id"))
    if hit_path is None:
        raise ParagraphUnavailable("The pointed element is no longer in the captured layout. Try again.")
    for node, _ in rows:
        if (node.get("role") == "button"
                and node.get("name") in {"停止", "停止生成", "Stop", "Stop generating"}):
            raise ParagraphUnavailable("Wait until the reply finishes generating, then try Alt + E.")
        if _contains(node, point) and not _css(node, "_InlineMentionFocusRing_") and (node.get("role") in {
                "button", "textbox", "combobox", "menu", "menuitem", "dialog", "table"}
                or _css(node, "group/writing-block-surface")):
            raise ParagraphUnavailable("Point at ordinary reply text, not a control or editor. Use Alt + S for other content.")
    candidates = []
    for parent, parent_path in rows:
        children = parent.get("children", ())
        markers = [(index, _marker(child)) for index, child in enumerate(children) if _marker(child)]
        for marker_index, (index, role) in enumerate(markers):
            if role != "assistant":
                continue
            end = markers[marker_index + 1][0] if marker_index + 1 < len(markers) else len(children)
            segment = children[index + 1:end]
            for relative, body_node in enumerate(segment):
                for block, block_path, kind in _units(body_node, parent_path + (index + 1 + relative,)) or ():
                    if (kind != "code" and _contains(block, point)
                            and (hit_path[:len(block_path)] == block_path
                                 or block_path[:len(hit_path)] == hit_path)):
                        candidates.append((block, block_path, children[index], segment, parent_path, index + 1))
    # A nested list item's box lies inside its parent item's box. Prefer the
    # descendant; unrelated overlapping candidates remain ambiguous and fail.
    candidates = [candidate for candidate in candidates if not any(
        len(other[1]) > len(candidate[1]) and other[1][:len(candidate[1])] == candidate[1]
        for other in candidates)]
    if len(candidates) != 1:
        raise ParagraphUnavailable("No unique assistant paragraph is under the mouse. Point at its text and try again.")
    block, _, header, segment, parent_path, offset = candidates[0]
    return text_from_paragraph(_reply(header, segment, parent_path, offset), block["id"])
