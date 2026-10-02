"""Conservative adapter for the inspected Codex desktop Chromium layout.

No window-wide text is spoken. Hidden speaker headings bound a reply;
paragraph identities and rectangles establish the starting block, and a
reply-level copy toolbar establishes completion. Unknown layouts fail closed.
"""

import math
import re

from chat_reader.paragraphs import Block, ParagraphUnavailable, Reply, READABLE_KINDS, plan_from_paragraph


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
    if role == "table" and node.get("control_type") == 50036:
        _opaque_boundary(node)
        return [(node, path, "table")]
    if _table_widget(node):
        _opaque_boundary(node)
        return [(node, path, "table")]
    if role == "group" and "group/writing-block-surface" in node.get("class_name", "").split():
        _opaque_boundary(node)
        return [(node, path, "editor")]
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


def _table_widget(node):
    """Inspected table widget: typed grid plus its bounded two-action overlay.

    CSS module hashes vary between builds; names and cell text are irrelevant.
    Never flatten the wrapper or search for an arbitrary nested table.
    """
    if (node.get("role") != "group" or node.get("control_type") != 50026
            or "group/app-widget" not in node.get("class_name", "").split()
            or not _css(node, "_TableContainer_") or len(node.get("children", ())) != 2):
        return False
    grid, tools = node["children"]
    if (grid.get("role") not in {"grid", "table"} or grid.get("control_type") != 50036
            or not _css(grid, "_Table_") or tools.get("role") != "group"
            or tools.get("control_type") != 50026
            or not {"group-hover/app-widget:pointer-events-auto", "group-hover/app-widget:opacity-100"}
                <= set(tools.get("class_name", "").split())
            or len(tools.get("children", ())) != 2):
        return False
    for wrapper in tools["children"]:
        if (wrapper.get("role") != "group" or wrapper.get("control_type") != 50026
                or "contents" not in wrapper.get("class_name", "").split()
                or len(wrapper.get("children", ())) != 1):
            return False
        button = wrapper["children"][0]
        if (button.get("role") != "button" or button.get("control_type") != 50000
                or button.get("children")
                or not {"no-drag", "cursor-interaction"} <= set(button.get("class_name", "").split())):
            return False
    return True


def _opaque_boundary(node):
    """Omit only a known block, never concealed reply markers or a nested document."""
    for item, _ in _walk(node):
        if (item.get("password") is not False or item.get("process_id") != node.get("process_id")
                or item.get("control_type") in {50030, 50032} or _marker(item) is not None):
            raise ParagraphUnavailable("A skipped block has unsafe or ambiguous boundaries. Use Alt + S.")


def _simple_activity(node):
    """Inspected post-footer activity status: three groups and one Text leaf."""
    for css in ("outline-none", "text-size-chat", "group/activity-header"):
        if (node.get("role") != "group" or node.get("control_type") != 50026
                or node.get("password") is not False
                or css not in node.get("class_name", "").split()
                or len(node.get("children", ())) != 1):
            return False
        node = node["children"][0]
    return (node.get("role") in {"description", "text"} and node.get("control_type") == 50020
            and node.get("password") is False and not node.get("children"))


def _file_region_end(segment, start):
    """Inspected collapsed summary + contiguous file buttons; never generic buttons."""
    header = segment[start]
    if (header.get("role") != "group" or header.get("control_type") != 50026
            or "group/turn-diff-header" not in header.get("class_name", "").split()):
        return None
    _opaque_boundary(header)
    children = header.get("children", ())
    if ([item.get("role") for item in children] != ["button", "img", "description", "group", "button", "button"]
            or "turn-diff-default-subtitle" not in children[3].get("class_name", "").split()
            or any(item.get("role") not in {"group", "button", "img", "description", "text"}
                   for item, _ in _walk(header))):
        raise ParagraphUnavailable("The edited-files summary changed structure. Use Alt + S.")
    end, rows = start + 1, 0
    while end < len(segment):
        item = segment[end]
        css = item.get("class_name", "").split()
        if (item.get("role") != "button" or item.get("control_type") != 50000
                or "py-[var(--turn-diff-row-padding-y)]" not in css or "text-size-chat" not in css):
            break
        _opaque_boundary(item)
        descendants = item.get("children", ())
        is_row = "group-last/turn-diff-file-row:rounded-b-lg" in css
        roles = [child.get("role") for child in descendants]
        if is_row:
            valid = roles == ["description", "description", "description"]
        else:
            valid = rows > 0 and "rounded-b-lg" in css and roles == ["description", "img"]
        if not valid or any(child.get("children") for child in descendants):
            raise ParagraphUnavailable("The edited-files rows changed structure. Use Alt + S.")
        end += 1
        if not is_row:
            break
        rows += 1
    if not rows:
        raise ParagraphUnavailable("The edited-files region has no verified rows. Use Alt + S.")
    return end


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


def _standalone_footer_control(node):
    """Known leaf controls only after this reply's independently verified Copy."""
    if (node.get("role") != "button" or node.get("control_type") != 50000
            or node.get("password") is not False or node.get("children")):
        return False
    css = set(node.get("class_name", "").split())
    if not {"outline-hidden", "cursor-interaction"} <= css:
        return False
    if node.get("name") in {"重新生成回复", "Regenerate response"}:
        return {"no-drag", "electron:rounded-md", "electron:p-1", "text-tertiary"} <= css
    return node.get("name") in {"更多操作", "More actions"} and _css(node, "_Button_")


def _reply(header, segment, base_path, offset):
    blocks = []
    completed = False
    file_end = -1
    for index, node in enumerate(segment):
        if index < file_end:
            continue
        end = _file_region_end(segment, index)
        if end is not None:
            if completed:
                raise ParagraphUnavailable("Reply content appeared after its footer. Try again.")
            blocks.append(Block(node["id"], "edited_files", ""))
            file_end = end
            continue
        units = _units(node, base_path + (offset + index,))
        if units is not None:
            if completed:
                raise ParagraphUnavailable("Reply content appeared after its footer. Try again.")
            for item, _, kind in units:
                text = _inline_text(item).strip() if kind in READABLE_KINDS else ""
                if kind in READABLE_KINDS and not text:
                    raise ParagraphUnavailable("Part of the reply text is unavailable. Use Alt + S.")
                blocks.append(Block(item["id"], kind, text))
            continue
        if node.get("role") == "status" and _css(node, "sr-only"):
            continue
        if (node.get("role") == "separator" and node.get("control_type") == 50038
                and node.get("password") is False and not node.get("children")
                and node.get("text_pattern") in (None, False)):
            # Verified leaf decoration, not a body block or starting position.
            # Never descend into an alleged separator containing hidden content.
            continue
        toolbar, copy = _toolbar(node)
        if toolbar:
            completed = completed or copy
            continue
        if (completed and node.get("process_id") == header.get("process_id")
                and _standalone_footer_control(node)):
            continue
        if completed and _simple_activity(node):
            _opaque_boundary(node)
            blocks.append(Block(node["id"], "system_status", ""))
            continue
        if (completed and node.get("role") in {"description", "text"}
                and node.get("control_type") == 50020 and node.get("password") is False
                and not node.get("children")
                and re.fullmatch(
                    r"(?:(?:星期[一二三四五六日天] *)|"
                    r"(?:(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday) +))?"
                    r"(?:[01]?[0-9]|2[0-3]):[0-5][0-9]", node.get("name", ""))):
            # Same-reply completion metadata only, never arbitrary body text or
            # a container that could conceal protected/editor descendants.
            continue
        raise ParagraphUnavailable("This reply has an unsupported editor, table or layout. Use Alt + S.")
    if not completed:
        raise ParagraphUnavailable("The reply is not confirmed complete. Wait for it to finish or use Alt + S.")
    return Reply(header["id"], "assistant", tuple(blocks), complete=True)


def plan_at_point(snapshot):
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
    busy_ids = {node["id"] for node, _ in rows if node.get("role") == "button"
                and node.get("name") in {"停止", "停止生成", "Stop", "Stop generating"}}
    for node, _ in rows:
        if _contains(node, point) and not _css(node, "_InlineMentionFocusRing_") and (node.get("role") in {
                "button", "textbox", "combobox", "menu", "menuitem", "dialog", "table", "grid"}
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
                    if (kind in READABLE_KINDS and _contains(block, point)
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
    if busy_ids:
        parent = root
        for index in parent_path:
            parent = parent["children"][index]
        # A global composer Stop button may belong to a newer reply. Allow an
        # earlier reply only with a later assistant marker in this same bounded
        # transcript AND its own completion footer (validated by _reply below).
        later_assistant = any(_marker(node) == "assistant"
                              for node in parent["children"][offset + len(segment):])
        target_busy = any(item["id"] in busy_ids for node in segment for item, _ in _walk(node))
        if not later_assistant or target_busy:
            raise ParagraphUnavailable("Wait until the reply finishes generating, then try Alt + E.")
    return plan_from_paragraph(_reply(header, segment, parent_path, offset), block["id"])


def text_at_point(snapshot):
    """Legacy text-only API; runtime consumes the omission-aware plan."""
    return plan_at_point(snapshot).text
