import unittest

from chat_reader.codex_adapter import plan_at_point
from chat_reader.paragraphs import ParagraphUnavailable
from probe_fixtures import marker, node, paragraph, snapshot
from skip_fixtures import table_widget, standalone_reply_controls


class TableWidgetTests(unittest.TestCase):
    def plan(self, data):
        try:
            return plan_at_point(data)
        except ParagraphUnavailable as error:
            self.fail(f"Expected bounded prose, but the reply was vetoed: {error}")

    def test_widget_grid_is_one_disclosed_omission_and_keeps_both_prose_sides(self):
        """Missing the widget boundary vetoes prose or leaks cell/action text."""
        for style in ("fixture", "changedhash"):
            for point, hit, expected, before in (
                ((15, 45), "middle", "Middle with emphasis. Link.\n\nLast.", False),
                ((15, 96), "last", "Last.", True),
            ):
                data = snapshot(point=point, point_id=hit, extra=(table_widget(style=style),))
                data["tree"]["children"][0]["children"][8]["offscreen"] = False
                plan = self.plan(data)
                self.assertEqual(expected, plan.text)
                self.assertEqual([("code", 3, before), ("table", 4, before)],
                                 [(item.kind, item.ordinal, item.before_start) for item in plan.skipped])

    def test_widget_cannot_hide_unverified_content_or_cross_reply_boundaries(self):
        """Weakening shape/protection/process guards would silently omit unsafe data."""
        for case in ("outer-class", "outer-type", "grid-role", "grid-type", "missing-grid", "extra-prose",
                     "protected", "foreign-process", "document", "marker", "tool-text", "tool-input"):
            widget = table_widget()
            grid, tools = widget["children"]
            if case == "outer-class": widget["class_name"] = "group/app-widget"
            elif case == "outer-type": widget["control_type"] = 50004
            elif case == "grid-role": grid["role"] = "group"
            elif case == "grid-type": grid["control_type"] = 50026
            elif case == "missing-grid": widget["children"].pop(0)
            elif case == "extra-prose": widget["children"].append(paragraph("hidden-body", "Do not omit me.", 250))
            elif case == "protected": grid["children"][0]["children"][0]["password"] = None
            elif case == "foreign-process": grid["process_id"] = 456
            elif case == "document": grid["children"].append(node("nested", "document"))
            elif case == "marker": grid["children"].append(marker("hidden-turn", "You said:"))
            elif case == "tool-text": tools["children"].append(paragraph("tool-body", "Do not omit me.", 250))
            elif case == "tool-input": tools["children"][0]["children"].append(node("tool-edit", "textbox"))
            with self.subTest(case=case), self.assertRaises(ParagraphUnavailable):
                plan_at_point(snapshot(extra=(widget,)))

    def test_pointing_inside_widget_never_reads_cells_or_jumps_to_following_prose(self):
        """Treating cell paragraphs as starts would narrate omitted table content."""
        widget = table_widget()
        widget["children"][0]["children"][1]["children"][0]["children"] = [paragraph("cell-paragraph", "Omitted cell.", 80)]
        for hit in ("table-widget", "table-widget-grid", "table-widget-1-0", "cell-paragraph", "table-widget-action-0"):
            with self.subTest(hit=hit), self.assertRaises(ParagraphUnavailable):
                plan_at_point(snapshot(point=(15, 82), point_id=hit, extra=(widget,)))

    def test_known_standalone_footer_controls_do_not_veto_or_enter_speech(self):
        """Post-Copy Regenerate/More leaves used to reject this completed reply."""
        for language in ("zh", "en"):
            data = snapshot()
            stream = data["tree"]["children"][0]["children"]
            where = next(i for i, item in enumerate(stream) if item["id"] == "footer-a") + 1
            stream[where:where] = standalone_reply_controls(language)
            self.assertEqual("Middle with emphasis. Link.\n\nLast.", self.plan(data).text)

    def test_standalone_controls_need_copy_leaf_shape_label_and_style(self):
        """Arbitrary body/unknown buttons cannot be completion evidence or silent skips."""
        for case in ("before-copy", "missing-copy", "protected", "foreign-process", "children", "label", "type", "style", "more-style"):
            data = snapshot()
            stream = data["tree"]["children"][0]["children"]
            controls = standalone_reply_controls()
            where = next(i for i, item in enumerate(stream) if item["id"] == "footer-a")
            if case == "before-copy": stream[where:where] = controls
            else: stream[where+1:where+1] = controls
            if case == "missing-copy": stream[:] = [item for item in stream if item["id"] != "footer-a"]
            elif case == "protected": controls[0]["password"] = True
            elif case == "foreign-process": controls[0]["process_id"] = 456
            elif case == "children": controls[0]["children"].append(node("hidden-editor", "textbox"))
            elif case == "label": controls[0]["name"] = "Unknown action"
            elif case == "type": controls[0]["control_type"] = 50004
            elif case == "style": controls[0]["class_name"] = "outline-hidden cursor-interaction"
            elif case == "more-style": controls[1]["class_name"] = "outline-hidden cursor-interaction"
            with self.subTest(case=case), self.assertRaises(ParagraphUnavailable):
                plan_at_point(data)

    def test_real_topology_combines_widget_and_standalone_footer_without_crossing_turn(self):
        """Fixing only the table or only the footer leaves the user's refusal intact."""
        data = snapshot(extra=(table_widget(),))
        stream = data["tree"]["children"][0]["children"]
        where = next(i for i, item in enumerate(stream) if item["id"] == "footer-a") + 1
        stream[where:where] = standalone_reply_controls()
        plan = self.plan(data)
        self.assertEqual("Middle with emphasis. Link.\n\nLast.", plan.text)
        self.assertEqual(["code", "table"], [item.kind for item in plan.skipped])
