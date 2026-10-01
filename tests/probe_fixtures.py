"""Hand-written synthetic fixtures matching the inspected desktop layout."""


def node(key, role="group", *, name="", css="", bounds=None, children=(), offscreen=False):
    control_type = {"document": 50030, "description": 50020, "heading": 50020,
                    "strong": 50020, "code": 50020, "link": 50005,
                    "button": 50000, "textbox": 50004, "list": 50008,
                    "listitem": 50007, "status": 50017, "table": 50036}.get(role, 50026)
    return {"id": key, "role": role, "control_type": control_type, "name": name,
            "class_name": css, "bounds": bounds, "offscreen": offscreen,
            "password": False, "framework": "Chrome", "process_id": 123,
            "automation_id": "RootWebArea" if role == "document" else "",
            "text_pattern": False, "aria_properties": "",
            "heading_level": 80054 if role == "heading" else 80050,
            "children": list(children)}


def marker(key, label):
    return node(key, "heading", name=label, css="sr-only m-0 select-none")


def paragraph(key, text, y, *, offscreen=False):
    return node(key, css="_Paragraph_fixture_1", bounds=(10, y, 100, 20),
                offscreen=offscreen, children=(node(key + "-text", "description", name=text),))


def footer(key, y):
    return node(key, css="contents", children=(
        node(key + "-button", "button", name="复制", bounds=(10, y, 20, 20)),))


def snapshot(*, point=(15, 45), point_id="root", extra=()):
    middle = node("middle", css="_Paragraph_fixture_1", bounds=(10, 40, 100, 20), children=(
        node("m1", "description", name="Middle "),
        node("m2", "strong", children=(node("m2-text", "description", name="with emphasis"),)),
        node("m3", "description", name=". "),
        node("m4", "link", name="Link.", children=(node("m4-text", "description", name="Link."),)),
    ))
    transcript = node("transcript", css="relative shrink-0", children=(
        marker("user-a", "你说："),
        node("bubble", css="bg-user-message", children=(paragraph("question", "Do not speak the question.", -30),)),
        marker("assistant-a", "ChatGPT 说："), node("status", "status", css="sr-only"),
        paragraph("first", "First.", 10), middle,
        node("code", css="_CodeBlock_fixture_1", bounds=(10, 65, 100, 20), children=(
            node("code-content", "code", children=(node("code-text", "description", name="secret_code()"),)),)),
        *extra,
        paragraph("last", "Last.", 95, offscreen=True), footer("footer-a", 120),
        node("time", "description", name="1:26"),
        marker("user-b", "你说："), node("bubble-b", css="bg-user-message"),
        marker("assistant-b", "ChatGPT 说："), paragraph("other", "Do not speak another reply.", 160),
        footer("footer-b", 185),
    ))
    tree = node("root", "document", bounds=(0, 0, 400, 300), children=(transcript,))
    return {"schema_version": 1, "point": list(point), "point_id": point_id,
            "ancestors": [], "scope_hint": "unclassified", "tree": tree,
            "node_count": 40, "truncated": False, "verified_reply": False}
