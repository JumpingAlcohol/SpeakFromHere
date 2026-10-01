"""Exercise our bounded capture against a controlled Windows UIA boundary."""

import importlib.util
import unittest


class Element:
    def __init__(self, key, *, role="", control_type=50026, name="", password=False,
                 children=()):
        self.key = key
        self.role = role
        self.control_type = control_type
        self.name = name
        self.password = password
        self.children = list(children)
        self.parent = None
        for child in self.children:
            child.parent = self


class UIA:
    """Only the COM boundary is substituted; traversal/limits stay real."""
    def __init__(self, target):
        self.target = target

    def element_at(self, point):
        if point != (100, 200):
            raise AssertionError("The capture must use the requested screen position")
        return self.target

    def parent(self, element):
        return element.parent

    def children(self, element):
        yield from element.children

    def describe(self, element):
        return {
            "id": element.key, "role": element.role, "control_type": element.control_type,
            "name": "" if element.password else element.name,
            "password": element.password,
        }


class CachedProperties:
    """COM returns a reserved object for unsupported properties in no-default mode."""
    unsupported = object()

    def __init__(self, *, control_type=50026, role="group", password=None):
        self.values = {
            30003: control_type, 30005: "Synthetic container", 30011: "container",
            30012: "", 30019: password, 30022: False, 30024: "Chrome",
            30002: 123, 30001: (0.0, 0.0, 400.0, 200.0), 30040: False,
            30101: role, 30102: "", 30173: 0,
        }
        self.name_reads = 0

    def GetCachedPropertyValueEx(self, key, ignore_default):
        if key == 30005:
            self.name_reads += 1
        value = self.values[key]
        if value is None:
            return self.unsupported if ignore_default else False
        return value


class NativeElement:
    def __init__(self, properties):
        self.properties = properties

    def BuildUpdatedCache(self, cache):
        return self.properties

    def GetRuntimeId(self):
        return (42, 11)


class CachedStatusTests(unittest.TestCase):
    def test_unsupported_password_status_does_not_abort_a_noneditable_container(self):
        """Requiring every structural element to implement IsPassword causes the user's exact failure."""
        from chat_reader.uia_probe import ProbeUnavailable, WindowsUIA
        uia = WindowsUIA.__new__(WindowsUIA)
        uia.cache = object()
        try:
            info = uia.describe(NativeElement(CachedProperties()))
        except ProbeUnavailable as error:
            self.fail(f"A noneditable container must remain inspectable: {error}")
        self.assertEqual("42.11", info["id"])
        self.assertEqual(50026, info["control_type"])
        self.assertFalse(info["password"])

    def describe(self, properties):
        from chat_reader.uia_probe import WindowsUIA
        uia = WindowsUIA.__new__(WindowsUIA)
        uia.cache = object()
        return uia.describe(NativeElement(properties))

    def test_unknown_password_status_in_an_edit_is_redacted_without_reading_its_name(self):
        """Defaulting an unknown editable field to non-password would expose its name."""
        properties = CachedProperties(control_type=50004, role="textbox")
        try:
            info = self.describe(properties)
        except self.probe_error() as error:
            self.fail(f"An unknown edit should be redacted, not abort the entire tree: {error}")
        self.assertIsNone(info["password"])
        self.assertEqual("", info["name"])
        self.assertIsNone(info["aria_properties"])
        self.assertEqual(0, properties.name_reads)

    def probe_error(self):
        from chat_reader.uia_probe import ProbeUnavailable
        return ProbeUnavailable

    def test_textbox_role_on_a_group_cannot_use_the_noneditable_default(self):
        """Trusting control type alone misclassifies custom web input controls."""
        properties = CachedProperties(role="textbox")
        try:
            info = self.describe(properties)
        except self.probe_error() as error:
            self.fail(f"The custom input should be redacted: {error}")
        self.assertIsNone(info["password"])
        self.assertEqual("", info["name"])
        self.assertEqual(0, properties.name_reads)

    def test_reported_password_is_never_defaulted_to_unprotected(self):
        properties = CachedProperties(control_type=50004, role="textbox", password=True)
        info = self.describe(properties)
        self.assertTrue(info["password"])
        self.assertEqual("", info["name"])
        self.assertIsNone(info["aria_properties"])
        self.assertEqual(0, properties.name_reads)

    def test_explicitly_nonpassword_edit_preserves_ordinary_text(self):
        properties = CachedProperties(control_type=50004, role="textbox", password=False)
        info = self.describe(properties)
        self.assertFalse(info["password"])
        self.assertEqual("Synthetic container", info["name"])


class ProbeTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec("chat_reader.uia_probe"),
                             "Read-only paragraph inspection is not implemented")
        from chat_reader import uia_probe
        self.probe = uia_probe

    def test_captures_nearest_article_and_includes_offscreen_remainder(self):
        """Capturing only the hovered leaf loses the remainder; capturing its parent leaks the next reply."""
        target = Element("middle", role="paragraph", name="Middle.")
        article = Element("reply-a", role="article", children=(
            Element("first", role="paragraph", name="First."), target,
            Element("offscreen", role="paragraph", name="Last."),
        ))
        other = Element("reply-b", role="article", name="Other reply.")
        Element("document", control_type=50030, children=(article, other))
        result = self.probe.capture_probe(UIA(target), (100, 200))
        self.assertEqual("middle", result["point_id"])
        self.assertEqual("reply-a", result["tree"]["id"])
        self.assertEqual(["first", "middle", "offscreen"],
                         [node["id"] for node in result["tree"]["children"]])
        self.assertFalse(result["truncated"])
        self.assertFalse(result["verified_reply"], "An article alone does not prove assistant ownership")

    def test_node_limit_marks_capture_incomplete_instead_of_silently_losing_text(self):
        target = Element("p", role="paragraph")
        Element("article", role="article", children=(target, Element("rest")))
        result = self.probe.capture_probe(UIA(target), (100, 200), max_nodes=2)
        self.assertTrue(result["truncated"])
        self.assertEqual(2, result["node_count"])

    def test_depth_limit_marks_capture_incomplete(self):
        target = Element("p", role="paragraph")
        Element("article", role="article", children=(Element("wrapper", children=(target,)),))
        result = self.probe.capture_probe(UIA(target), (100, 200), max_depth=1)
        self.assertTrue(result["truncated"])

    def test_password_target_is_rejected_without_capturing_its_siblings(self):
        target = Element("secret", control_type=50004, password=True, name="Private.")
        Element("dialog", children=(target, Element("sibling", name="Private too.")))
        with self.assertRaises(self.probe.ProbeUnavailable):
            self.probe.capture_probe(UIA(target), (100, 200))

    def test_password_descendants_are_redacted(self):
        target = Element("p", role="paragraph")
        Element("article", role="article", children=(target,
            Element("secret", password=True, name="Private.", children=(Element("hidden"),))))
        result = self.probe.capture_probe(UIA(target), (100, 200))
        secret = result["tree"]["children"][1]
        self.assertEqual("", secret["name"])
        self.assertEqual([], secret["children"])
        self.assertTrue(result["truncated"])

    def test_unknown_password_descendant_is_redacted_without_losing_other_nodes(self):
        target = Element("p", role="paragraph", name="Readable paragraph.")
        Element("article", role="article", children=(target,
            Element("unknown", password=None, name="Must not be stored.",
                    children=(Element("hidden"),)), Element("last", name="Last paragraph.")))
        result = self.probe.capture_probe(UIA(target), (100, 200))
        unknown = result["tree"]["children"][1]
        self.assertEqual("", unknown["name"])
        self.assertEqual([], unknown["children"])
        self.assertEqual("Last paragraph.", result["tree"]["children"][2]["name"])
        self.assertTrue(result["truncated"])

    def test_unknown_password_target_is_not_inspected(self):
        target = Element("unknown", control_type=50004, password=None, name="Private.")
        with self.assertRaises(self.probe.ProbeUnavailable):
            self.probe.capture_probe(UIA(target), (100, 200))

    def test_unknown_structure_is_inspected_but_never_declared_a_verified_reply(self):
        target = Element("p", role="paragraph")
        Element("document", control_type=50030, children=(target,))
        result = self.probe.capture_probe(UIA(target), (100, 200))
        self.assertEqual("document", result["tree"]["id"])
        self.assertFalse(result["verified_reply"])

    def test_disappearing_element_causes_failure_not_a_partial_success(self):
        target = Element("p", role="paragraph")
        uia = UIA(target)
        def removed(element):
            raise OSError("Element no longer available")
        uia.describe = removed
        with self.assertRaises(self.probe.ProbeUnavailable):
            self.probe.capture_probe(uia, (100, 200))

    def test_time_budget_stops_traversal(self):
        target = Element("p", role="paragraph")
        Element("article", role="article", children=(target,))
        ticks = iter((0, 0, 0, 11, 11, 11, 11))
        with self.assertRaises(self.probe.ProbeUnavailable):
            self.probe.capture_probe(UIA(target), (100, 200), clock=lambda: next(ticks))
