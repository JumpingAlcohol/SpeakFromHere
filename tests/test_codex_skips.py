from copy import deepcopy
import unittest
from chat_reader import codex_adapter
from chat_reader.paragraphs import ParagraphUnavailable
from probe_fixtures import node, paragraph, snapshot
from skip_fixtures import activity, edited_files


class CodexSkipTests(unittest.TestCase):
    def plan(self, data):
        self.assertTrue(hasattr(codex_adapter, "plan_at_point"), "Skip-aware adapter is missing")
        return codex_adapter.plan_at_point(data)

    def after_footer(self, extra):
        data = snapshot()
        stream = data["tree"]["children"][0]["children"]
        index = next(i for i, item in enumerate(stream) if item["id"] == "footer-a") + 1
        stream[index:index] = extra
        return data

    def test_verified_compaction_status_does_not_veto_body_or_enter_speech(self):
        """The user's post-Copy activity container used to reject the entire reply."""
        plan = self.plan(self.after_footer([activity()]))
        self.assertEqual("Middle with emphasis. Link.\n\nLast.", plan.text)
        self.assertEqual([("code", False), ("system_status", False)],
                         [(item.kind, item.before_start) for item in plan.skipped])

    def test_activity_shape_cannot_hide_an_editor_or_prove_completion(self):
        self.assertTrue(hasattr(codex_adapter, "plan_at_point"), "Activity safety gates are missing")
        for case in ("before-footer", "missing-footer", "protected", "editor", "wrong-class"):
            status = activity()
            data = self.after_footer([status])
            stream = data["tree"]["children"][0]["children"]
            if case == "before-footer":
                stream.remove(status)
                stream.insert(6, status)
            elif case == "missing-footer":
                stream[:] = [item for item in stream if item["id"] != "footer-a"]
            elif case == "protected":
                status["children"][0]["password"] = None
            elif case == "editor":
                status["children"][0]["children"][0]["children"].append(node("hidden", "textbox"))
            else:
                status["children"][0]["children"][0]["class_name"] = "unrecognized"
            with self.subTest(case=case), self.assertRaises(ParagraphUnavailable):
                codex_adapter.plan_at_point(data)

    def test_inspected_file_summary_and_rows_are_one_reported_omission(self):
        """Skipping only the diff header leaves file-row buttons vetoing prose."""
        plan = self.plan(snapshot(extra=edited_files()))
        self.assertEqual("Middle with emphasis. Link.\n\nLast.", plan.text)
        self.assertEqual(["code", "edited_files"], [item.kind for item in plan.skipped])

    def test_orphan_file_row_unknown_tail_or_hidden_marker_still_reject(self):
        self.assertTrue(hasattr(codex_adapter, "plan_at_point"), "File-region validation is missing")
        for case in ("orphan", "unknown", "marker", "protected", "changed-row"):
            files = list(edited_files())
            if case == "orphan":
                files.pop(0)
            elif case == "unknown":
                files.insert(2, node("unknown-button", "button", name="Must not blindly skip"))
            elif case == "marker":
                files[1]["children"].append(node("hidden", "heading", name="ChatGPT said:", css="sr-only"))
            elif case == "protected":
                files[1]["children"][0]["password"] = True
            else:
                files[1]["children"].append(node("expanded-diff", "textbox"))
            with self.subTest(case=case), self.assertRaises(ParagraphUnavailable):
                codex_adapter.plan_at_point(snapshot(extra=files))

    def test_tables_and_inspected_editor_wrappers_skip_without_losing_later_prose(self):
        """Reading opaque descendants leaks editor/table data; rejecting them vetoes later prose."""
        table = node("table", "table", children=(node("table-cell", "cell", name="Never speak table cell"),))
        editor = node("editor", css="group/writing-block-surface", children=(node("editor-text", "textbox", name="Never speak editor"),))
        plan = self.plan(snapshot(extra=(table, editor)))
        self.assertEqual("Middle with emphasis. Link.\n\nLast.", plan.text)
        self.assertEqual(["code", "table", "editor"], [item.kind for item in plan.skipped])

    def test_unknown_protected_or_cross_reply_structures_are_not_blanket_skipped(self):
        self.assertTrue(hasattr(codex_adapter, "plan_at_point"), "Skip ownership guards are missing")
        cases = [node("unknown", name="Unclassified"), node("unwrapped-edit", "textbox"),
                 node("wrong-table", "table"), node("protected-table", "table")]
        cases[2]["control_type"] = 50026
        cases[3]["password"] = True
        for extra in cases:
            with self.subTest(id=extra["id"]), self.assertRaises(ParagraphUnavailable):
                codex_adapter.plan_at_point(snapshot(extra=(extra,)))

    def test_hover_on_a_skipped_block_never_advances_to_the_next_paragraph(self):
        self.assertTrue(hasattr(codex_adapter, "plan_at_point"), "Skip starting-position gate is missing")
        table = node("table", "table", bounds=(10, 85, 100, 10))
        with self.assertRaises(ParagraphUnavailable):
            codex_adapter.plan_at_point(snapshot(point=(15, 86), point_id="table", extra=(table,)))
