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

    def test_unclassified_editor_or_wrong_type_table_is_not_silently_omitted(self):
        # A verified Table is now a disclosed skip; a role-only lookalike is not.
        table = node("table", "table", name="Unverified table")
        table["control_type"] = 50026
        for extra in (node("editor", "textbox", name="Private editor", bounds=(10, 85, 100, 10)), table):
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

    def with_footer_label(self, label):
        """Synthetic copy-footer sibling, matching the inspected timestamp leaf."""
        data = snapshot()
        stream = data["tree"]["children"][0]["children"]
        index = next(i for i, item in enumerate(stream) if item["id"] == "footer-a") + 1
        timestamp = node("localized-time", "description", name=label)
        stream.insert(index, timestamp)
        return data, timestamp

    def test_chinese_weekday_footer_does_not_veto_or_enter_reply_speech(self):
        """Reintroducing the bare-clock gate rejects the user's completed reply."""
        labels = [f"星期{day}{gap}23:43" for day in "一二三四五六日天" for gap in ("", " ")]
        for label in ("0:00", "23:59", *labels):
            with self.subTest(label=label):
                data, _ = self.with_footer_label(label)
                try:
                    actual = self.read(data)
                except ParagraphUnavailable as error:
                    self.fail(f"Verified timestamp leaf must not veto ordinary prose: {error}")
                self.assertEqual("Middle with emphasis. Link.\n\nLast.", actual)

    def test_english_weekday_footer_does_not_veto_or_enter_reply_speech(self):
        """Omitting English weekday support breaks the same bilingual workflow."""
        for day in ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"):
            with self.subTest(day=day):
                data, _ = self.with_footer_label(day + " 23:43")
                for item in data["tree"]["children"][0]["children"]:
                    if item["role"] == "heading":
                        item["name"] = {"你说：": "You said:", "ChatGPT 说：": "ChatGPT said:"}[item["name"]]
                    if item["id"].startswith("footer"):
                        item["children"][0]["name"] = "Copy"
                try:
                    actual = self.read(data)
                except ParagraphUnavailable as error:
                    self.fail(f"English weekday timestamp leaf must preserve prose: {error}")
                self.assertEqual("Middle with emphasis. Link.\n\nLast.", actual)

    def test_timestamp_shape_cannot_hide_protected_text_children_or_controls(self):
        """Skipping by label alone would omit hidden editors or protected content."""
        mutations = ({"password": None}, {"password": True}, {"control_type": 50000},
                     {"role": "button"}, {"role": "group"},
                     {"children": [node("hidden-editor", "textbox", name="Synthetic editor")]})
        for label in ("23:43", "星期四23:43", "Thursday 23:43"):
            for mutation in mutations:
                with self.subTest(label=label, mutation=mutation):
                    data, timestamp = self.with_footer_label(label)
                    timestamp.update(mutation)
                    with self.assertRaises(ParagraphUnavailable):
                        self.read(data)

    def test_date_like_text_before_completion_footer_is_not_skipped(self):
        """Dropping the completed-footer guard could discard unknown body content."""
        for label in ("23:43", "星期四23:43", "Thursday 23:43"):
            with self.subTest(label=label), self.assertRaises(ParagraphUnavailable):
                self.read(snapshot(extra=(node("body-date", "description", name=label),)))

    def test_weekday_timestamp_does_not_prove_reply_completion(self):
        """Treating a clock as completion or body could read an unfinished reply."""
        data, _ = self.with_footer_label("星期四23:43")
        stream = data["tree"]["children"][0]["children"]
        footer_node = next(item for item in stream if item["id"] == "footer-a")
        footer_node["children"][0]["name"] = "Synthetic other action"
        with self.assertRaises(ParagraphUnavailable):
            self.read(data)

    def test_weekday_timestamp_is_not_a_starting_paragraph(self):
        """Offering a metadata node as a paragraph would guess the user's start."""
        data, timestamp = self.with_footer_label("Thursday 23:43")
        timestamp["bounds"] = (10, 140, 100, 10)
        data.update(point=[15, 145], point_id="localized-time")
        with self.assertRaises(ParagraphUnavailable):
            self.read(data)

    def test_malformed_or_uninspected_footer_labels_are_not_guessed(self):
        """Loose matching/ranges would accept arbitrary text as footer decoration."""
        labels = ("24:00", "23:60", "星期四24:00", "星期四23:60", "星期四23:43 extra",
                  "Thursday 23:43 extra", "Yesterday 23:43", "Thu 23:43", "Thursday 11:43 PM",
                  "Thursday\n23:43", "星期四\n23:43")
        for label in labels:
            with self.subTest(label=label):
                data, _ = self.with_footer_label(label)
                with self.assertRaises(ParagraphUnavailable):
                    self.read(data)

    def test_timestamp_text_in_a_supported_paragraph_remains_audible(self):
        """A global timestamp-text filter would delete legitimate prose."""
        self.assertEqual("Middle with emphasis. Link.\n\n星期四23:43\n\nLast.",
                         self.read(snapshot(extra=(paragraph("body-time", "星期四23:43", 85),))))

    def test_valid_timestamp_does_not_make_other_unknown_footer_content_safe(self):
        """Skipping the rest of a footer after its timestamp would hide unknown blocks."""
        data, timestamp = self.with_footer_label("Thursday 23:43")
        stream = data["tree"]["children"][0]["children"]
        stream.insert(stream.index(timestamp) + 1, node("unknown-footer", name="Synthetic unknown content"))
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

    def test_verified_leaf_separator_does_not_veto_or_enter_reply_speech(self):
        for label in ("", "Horizontal divider"):
            divider = node("divider", "separator", name=label, bounds=(10, 85, 100, 1))
            divider.update(control_type=50038, text_pattern=None)
            with self.subTest(label=label):
                try:
                    actual = self.read(snapshot(extra=(divider,)))
                except ParagraphUnavailable as error:
                    self.fail(f"A verified decorative separator must not veto prose: {error}")
                self.assertEqual("Middle with emphasis. Link.\n\nLast.", actual)

    def test_separator_cannot_hide_descendants_or_unknown_protected_text(self):
        mutations = ({"control_type": 50026}, {"password": None}, {"password": True},
                     {"text_pattern": True},
                     {"children": [node("hidden-editor", "textbox", name="Never read this")]})
        for mutation in mutations:
            divider = node("divider", "separator")
            divider.update(control_type=50038, text_pattern=None)
            divider.update(mutation)
            with self.subTest(mutation=mutation), self.assertRaises(ParagraphUnavailable):
                self.read(snapshot(extra=(divider,)))

    def test_pointing_at_separator_itself_never_guesses_a_starting_paragraph(self):
        divider = node("divider", "separator", bounds=(10, 85, 100, 2))
        divider.update(control_type=50038, text_pattern=None)
        with self.assertRaises(ParagraphUnavailable):
            self.read(snapshot(point=(15, 86), point_id="divider", extra=(divider,)))

    def test_finished_earlier_reply_remains_readable_while_later_reply_generates(self):
        data = snapshot()
        transcript = data["tree"]["children"][0]["children"]
        transcript[:] = [item for item in transcript if item["id"] != "footer-b"]
        data["tree"]["children"].append(node("busy", "button", name="Stop generating"))
        try:
            actual = self.read(data)
        except ParagraphUnavailable as error:
            self.fail(f"An independently completed earlier reply should remain readable: {error}")
        self.assertEqual("Middle with emphasis. Link.\n\nLast.", actual)

    def test_latest_reply_still_rejects_with_stale_copy_footer_while_generating(self):
        data = snapshot(point=(15, 165), point_id="other")
        data["tree"]["children"].append(node("busy", "button", name="Stop generating"))
        with self.assertRaises(ParagraphUnavailable):
            self.read(data)

    def test_busy_reply_still_needs_its_own_completion_and_same_parent_successor(self):
        for case in ("missing-footer", "nested-marker", "busy-in-target"):
            data = snapshot(point=(15, 165), point_id="other") if case == "nested-marker" else snapshot()
            transcript = data["tree"]["children"][0]["children"]
            data["tree"]["children"].append(node("busy", "button", name="Stop generating"))
            if case == "missing-footer":
                transcript[:] = [item for item in transcript if item["id"] != "footer-a"]
            elif case == "nested-marker":
                data["tree"]["children"].append(node("unrelated", children=(marker("nested-mark", "ChatGPT said:"),)))
            else:
                transcript.insert(6, node("target-busy", "button", name="Stop generating"))
            with self.subTest(case=case), self.assertRaises(ParagraphUnavailable):
                self.read(data)
