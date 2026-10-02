import unittest
from chat_reader import paragraphs


class ReadingPlanTests(unittest.TestCase):
    def test_skips_are_visible_even_before_the_start_and_never_enter_speech(self):
        """Dropping omission metadata silently hides blocks; flattening exposes skipped text."""
        self.assertTrue(hasattr(paragraphs, "plan_from_paragraph"), "Reading omissions are not implemented")
        p = paragraphs
        reply = p.Reply("r", "assistant", (
            p.Block("table", "table", "Must never speak table data"),
            p.Block("first", "paragraph", "First."), p.Block("code", "code", "secret_code()"),
            p.Block("middle", "paragraph", "Middle."), p.Block("editor", "editor", "Private editor"),
            p.Block("last", "paragraph", "Last.")), complete=True)
        plan = p.plan_from_paragraph(reply, "middle")
        self.assertEqual("Middle.\n\nLast.", plan.text)
        self.assertEqual([("table", 1, True), ("code", 3, True), ("editor", 5, False)],
                         [(item.kind, item.ordinal, item.before_start) for item in plan.skipped])

    def test_skipped_block_is_not_a_start_or_completion_evidence(self):
        self.assertTrue(hasattr(paragraphs, "plan_from_paragraph"), "Skip-aware boundaries are missing")
        p = paragraphs
        blocks = (p.Block("table", "table", ""), p.Block("body", "paragraph", "Body."))
        for reply, start in ((p.Reply("r", "assistant", blocks, True), "table"),
                             (p.Reply("r", "assistant", blocks, False), "body"),
                             (p.Reply("r", "user", blocks, True), "body")):
            with self.subTest(start=start), self.assertRaises(p.ParagraphUnavailable):
                p.plan_from_paragraph(reply, start)

    def test_worker_payload_rejects_invalid_or_unbounded_omissions(self):
        self.assertTrue(hasattr(paragraphs, "ReadingPlan"), "Worker omission validation is missing")
        valid = {"text": "Body.", "skipped": [{"kind": "table", "ordinal": 2, "before_start": False}]}
        plan = paragraphs.ReadingPlan.from_payload(valid)
        self.assertEqual(valid, plan.to_payload())
        cases = [{"kind": "unknown", "ordinal": 2, "before_start": False},
                 {"kind": [], "ordinal": 2, "before_start": False},
                 {"kind": "table", "ordinal": True, "before_start": False},
                 {"kind": "table", "ordinal": 0, "before_start": False},
                 {"kind": "table", "ordinal": 2, "before_start": "False"},
                 {"kind": "table", "ordinal": 2, "before_start": False, "text": "Hidden content"}]
        for item in cases:
            with self.subTest(item=item), self.assertRaises(ValueError):
                paragraphs.ReadingPlan.from_payload({"text": "Body.", "skipped": [item]})
        for items in ([valid["skipped"][0]] * 2, [valid["skipped"][0]] * 1501):
            with self.assertRaises(ValueError):
                paragraphs.ReadingPlan.from_payload({"text": "Body.", "skipped": items})
