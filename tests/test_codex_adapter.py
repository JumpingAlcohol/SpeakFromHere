import importlib.util
import unittest

from chat_reader.paragraphs import ParagraphUnavailable
from probe_fixtures import footer, marker, node, paragraph, snapshot


class DesktopReplyAdapterTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec("chat_reader.codex_adapter"),
                             "The actual desktop-layout adapter is missing")
        from chat_reader.codex_adapter import text_at_point
        self.read = text_at_point

    def test_middle_paragraph_preserves_inline_spacing_and_stops_before_controls(self):
        """Flattening all UI text or duplicating link names adds buttons/other replies."""
        self.assertEqual("Middle with emphasis. Link.\n\nLast.", self.read(snapshot()))

    def test_first_and_last_paragraph_use_reply_boundaries_and_skip_code(self):
        self.assertEqual("First.\n\nMiddle with emphasis. Link.\n\nLast.",
                         self.read(snapshot(point=(15, 15))))
        data = snapshot(point=(15, 100))
        data["tree"]["children"][0]["children"][7]["offscreen"] = False
        self.assertEqual("Last.", self.read(data))

    def test_duplicate_text_starts_from_the_hovered_identity(self):
        data = snapshot(extra=(paragraph("duplicate", "First.", 87),))
        self.assertEqual("First.\n\nLast.", self.read({**data, "point": [15, 90]}))

    def test_rejects_user_text_controls_code_and_empty_space(self):
        for point in ((15, -25), (15, 125), (15, 70), (250, 45)):
            with self.subTest(point=point), self.assertRaises(ParagraphUnavailable):
                self.read(snapshot(point=point))

    def test_leaf_hit_and_container_hit_both_resolve_the_same_paragraph(self):
        for key in ("root", "middle", "m4-text"):
            with self.subTest(key=key):
                self.assertEqual("Middle with emphasis. Link.\n\nLast.", self.read(snapshot(point_id=key)))

    def test_stale_or_unrelated_hit_id_is_rejected(self):
        for key in ("missing", "other"):
            with self.subTest(key=key), self.assertRaises(ParagraphUnavailable):
                self.read(snapshot(point_id=key))

    def test_missing_copy_footer_never_marks_a_streaming_reply_complete(self):
        data = snapshot()
        stream = data["tree"]["children"][0]["children"]
        stream[:] = [item for item in stream if item["id"] != "footer-a"]
        with self.assertRaises(ParagraphUnavailable):
            self.read(data)

    def test_unclassified_embedded_editor_or_table_is_not_silently_omitted(self):
        for extra in (node("editor", "textbox", name="Private editor", bounds=(10, 85, 100, 10)),
                      node("table", "table", name="Table data")):
            with self.subTest(extra=extra["role"]), self.assertRaises(ParagraphUnavailable):
                self.read(snapshot(extra=(extra,)))

    def test_truncated_capture_and_nonchrome_layout_are_rejected(self):
        for field, value in (("truncated", True), ("schema_version", 2)):
            with self.subTest(field=field), self.assertRaises(ParagraphUnavailable):
                self.read({**snapshot(), field: value})
        data = snapshot()
        data["tree"]["framework"] = "Unknown"
        with self.assertRaises(ParagraphUnavailable):
            self.read(data)

    def test_overlapping_unrelated_paragraphs_are_not_guessed(self):
        with self.assertRaises(ParagraphUnavailable):
            self.read(snapshot(extra=(paragraph("overlap", "Wrong.", 40),)))

    def test_visible_body_heading_cannot_spoof_hidden_reply_marker(self):
        heading = node("body-heading", "heading", name="你说：", css="_Heading_fixture_1",
                       bounds=(10, 85, 100, 10))
        self.assertEqual("Middle with emphasis. Link.\n\n你说：\n\nLast.",
                         self.read(snapshot(extra=(heading,))))

    def test_list_items_are_independent_starts_including_nested_items(self):
        inner = node("nested", "listitem", css="_ListItem_fixture_1", bounds=(20, 88, 80, 5),
                     children=(node("nested-text", "description", name="Nested item."),))
        outer = node("item", "listitem", css="_ListItem_fixture_1", bounds=(10, 85, 100, 10),
                     children=(node("item-text", "description", name="Outer item."),
                               node("nested-list", "list", css="_List_fixture_1", children=(inner,))))
        listing = node("list", "list", css="_List_fixture_1", children=(outer,))
        self.assertEqual("Nested item.\n\nLast.", self.read(snapshot(point=(25, 90), extra=(listing,))))

    def test_english_interface_markers_and_footer_work(self):
        data = snapshot()
        stream = data["tree"]["children"][0]["children"]
        for item in stream:
            if item["role"] == "heading":
                item["name"] = {"你说：": "You said:", "ChatGPT 说：": "ChatGPT said:"}[item["name"]]
            if item["id"].startswith("footer"):
                item["children"][0]["name"] = "Copy"
        self.assertEqual("Middle with emphasis. Link.\n\nLast.", self.read(data))

    def test_body_after_footer_and_duplicate_runtime_ids_are_rejected(self):
        data = snapshot()
        stream = data["tree"]["children"][0]["children"]
        index = next(i for i, item in enumerate(stream) if item["id"] == "footer-a")
        stream.insert(index + 1, paragraph("late", "Uncertain boundary.", 140))
        with self.assertRaises(ParagraphUnavailable):
            self.read(data)
        data = snapshot(extra=(paragraph("first", "Duplicate identity.", 85),))
        with self.assertRaises(ParagraphUnavailable):
            self.read(data)

    def test_inline_file_mention_is_read_once_without_its_decorative_icon(self):
        """Desktop file links are buttons, but their visible label belongs to the paragraph."""
        data = snapshot()
        middle = data["tree"]["children"][0]["children"][5]
        middle["children"] = [node("file-link", "button", name="README.md",
            css="_InlineMentionFocusRing_fixture_1", bounds=(10, 40, 60, 20), children=(
                node("file-icon", "img", css="_Icon_fixture_1"),
                node("file-label", "description", name="README.md"),))]
        try:
            actual = self.read(data)
        except ParagraphUnavailable as error:
            self.fail(f"A known inline file mention should be readable: {error}")
        self.assertEqual("README.md\n\nLast.", actual)
