"""Read-only, bounded UIA inspection; not a verified paragraph-reading adapter."""

import time
from chat_reader.windows_context import physical_coordinate_context


class ProbeUnavailable(RuntimeError):
    """Inspection could not obtain a safe, bounded snapshot."""


def capture_probe(client, point, *, max_nodes=1500, max_depth=32,
                  clock=time.monotonic):
    """Inspect the pointed subtree and ancestry without clicking or copying.

    An article is only a scope hint, not proof that it is an assistant reply.
    Captures remain unverified, including when all nodes fit within the limits.
    """
    deadline = clock() + 10
    def check_time():
        if clock() >= deadline:
            raise ProbeUnavailable("Inspection exceeded its time budget.")

    try:
        ancestors = []
        elements = []
        current = client.element_at(point)
        while current is not None and len(ancestors) < 48:
            check_time()
            info = client.describe(current)
            if info["password"] is not False:
                raise ProbeUnavailable(
                    "Password fields cannot be inspected." if info["password"] is True
                    else "The pointed element has unknown password status. Point at ordinary reply text.")
            ancestors.append(info)
            elements.append(current)
            if info["control_type"] == 50032:  # Window; never walk into the desktop.
                break
            current = client.parent(current)
        if not ancestors:
            raise ProbeUnavailable("No element was found under the mouse.")
        if current is not None and len(ancestors) == 48:
            raise ProbeUnavailable("The ancestor path is too deep to inspect safely.")
        scope = next((i for i, info in enumerate(ancestors) if info["role"] == "article"), None)
        hint = "article"
        if scope is None:
            hint = "unclassified"
            scope = next((i for i, info in enumerate(ancestors)
                          if info["control_type"] == 50030), max(0, len(ancestors) - 2))
        count = 0
        truncated = False

        def visit(element, depth):
            nonlocal count, truncated
            check_time()
            info = client.describe(element)
            count += 1
            info["children"] = []
            if info["password"] is not False:
                info["name"] = ""
                truncated = True
                return info
            for child in client.children(element):
                check_time()
                if count >= max_nodes or depth >= max_depth:
                    truncated = True
                    break
                info["children"].append(visit(child, depth + 1))
            return info

        tree = visit(elements[scope], 0)
        return {
            "schema_version": 1, "point": list(point), "point_id": ancestors[0]["id"],
            "ancestors": ancestors, "scope_hint": hint, "tree": tree,
            "node_count": count, "truncated": truncated, "verified_reply": False,
        }
    except ProbeUnavailable:
        raise
    except Exception as error:
        raise ProbeUnavailable("An element disappeared or could not be read. Try again.") from error


class WindowsUIA:
    """Typed Windows UIA COM boundary, lazily loaded for source-only inspection."""

    def __init__(self):
        import comtypes.client
        self.types = comtypes.client.GetModule("UIAutomationCore.dll")
        self.automation = comtypes.client.CreateObject(
            self.types.CUIAutomation, interface=self.types.IUIAutomation)
        self.walker = self.automation.RawViewWalker
        self.cache = self.automation.CreateCacheRequest()
        for property_id in (30003, 30005, 30011, 30012, 30019, 30022, 30024,
                            30002, 30001, 30040, 30101, 30102, 30173):
            self.cache.AddProperty(property_id)

    def element_at(self, point):
        with physical_coordinate_context():
            element = self.automation.ElementFromPoint(self.types.tagPOINT(*point))
        return element if element else None

    def parent(self, element):
        parent = self.walker.GetParentElement(element)
        return parent if parent else None

    def children(self, element):
        child = self.walker.GetFirstChildElement(element)
        while child:
            yield child
            child = self.walker.GetNextSiblingElement(child)

    def describe(self, element):
        with physical_coordinate_context():
            cached = element.BuildUpdatedCache(self.cache)
        def value(property_id, *, ignore_default=True):
            raw = cached.GetCachedPropertyValueEx(property_id, ignore_default)
            if isinstance(raw, (str, int, float, bool, tuple, list)):
                return raw
            return None
        control_type = value(30003)
        role = value(30101) or ""
        password = value(30019)
        password = bool(password) if isinstance(password, (bool, int)) else None
        # Many noneditable web containers omit IsPassword. UIA supplies a default
        # of False when requested. Never apply that default to an unknown edit,
        # combo box, custom control or a web role identifying editable content.
        noneditable_types = {
            50000, 50005, 50006, 50007, 50008, 50009, 50010, 50011,
            50017, 50020, 50021, 50023, 50024, 50026, 50029, 50030,
            50032, 50033, 50034, 50035, 50036, 50038,
        }
        editable_roles = {"textbox", "searchbox", "combobox", "spinbutton"}
        if (password is None and control_type in noneditable_types
                and not editable_roles.intersection(role.lower().split())):
            default = value(30019, ignore_default=False)
            if isinstance(default, (bool, int)):
                password = bool(default)
        runtime_id = element.GetRuntimeId()
        return {
            "id": ".".join(str(part) for part in runtime_id),
            "control_type": control_type, "role": role,
            "automation_id": value(30011) or "", "class_name": value(30012) or "",
            "name": (value(30005) or "") if password is False else "",
            "password": password, "offscreen": value(30022),
            "framework": value(30024), "process_id": value(30002),
            "bounds": value(30001), "text_pattern": value(30040),
            "aria_properties": value(30102) if password is False else None,
            "heading_level": value(30173),
        }
