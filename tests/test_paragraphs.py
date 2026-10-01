"""Synthetic replies only: never copy private chats into public test fixtures."""

import importlib.util
import unittest


class ParagraphBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec("chat_reader.paragraphs"),
                             "Bounded paragraph extraction is not implemented")
        from chat_reader import paragraphs
        self.reader = paragraphs

    def reply(self, *, role="assistant", complete=True):
        p = self.reader
        return p.Reply("reply-a", role, (
            p.Block("first", "paragraph", "First paragraph."),
            p.Block("middle", "paragraph", "Middle paragraph."),
            p.Block("code", "code", "print('not spoken')"),
            p.Block("item", "list_item", "A list item."),
            p.Block("last", "paragraph", "Last paragraph."),
        ), complete=complete)

    def test_reads_first_middle_and_last_without_crossing_reply_boundary(self):
        """Reading the whole reply or dropping the final block breaks this test."""
        for start, expected in (
            ("first", "First paragraph.\n\nMiddle paragraph.\n\nA list item.\n\nLast paragraph."),
            ("middle", "Middle paragraph.\n\nA list item.\n\nLast paragraph."),
            ("last", "Last paragraph."),
        ):
            with self.subTest(start=start):
                self.assertEqual(expected, self.reader.text_from_paragraph(self.reply(), start))

    def test_uses_identity_not_the_first_occurrence_of_repeated_text(self):
        """Searching by paragraph text instead of identity starts at the wrong duplicate."""
        p = self.reader
        reply = p.Reply("reply-a", "assistant", (
            p.Block("one", "paragraph", "Same text."),
            p.Block("between", "paragraph", "Do not read this."),
            p.Block("two", "paragraph", "Same text."),
            p.Block("end", "paragraph", "End."),
        ), complete=True)
        self.assertEqual("Same text.\n\nEnd.", p.text_from_paragraph(reply, "two"))

    def test_rejects_a_paragraph_from_another_reply(self):
        """Defaulting to the first paragraph when lookup fails must not read anything."""
        with self.assertRaises(self.reader.ParagraphUnavailable):
            self.reader.text_from_paragraph(self.reply(), "reply-b-paragraph")

    def test_does_not_read_user_messages_or_incomplete_captures(self):
        """Removing role/completeness checks would allow unrelated or partial text."""
        for reply in (self.reply(role="user"), self.reply(complete=False)):
            with self.subTest(reply=reply):
                with self.assertRaises(self.reader.ParagraphUnavailable):
                    self.reader.text_from_paragraph(reply, "middle")

    def test_code_is_not_a_valid_starting_paragraph(self):
        """Automatically advancing from a code hover would hide a bad hit-test."""
        with self.assertRaises(self.reader.ParagraphUnavailable):
            self.reader.text_from_paragraph(self.reply(), "code")

    def test_rejects_duplicate_ids_and_unclassified_blocks(self):
        """Ambiguous identities or unknown structures must fail closed."""
        p = self.reader
        for blocks in (
            (p.Block("a", "paragraph", "One."), p.Block("a", "paragraph", "Two.")),
            (p.Block("a", "paragraph", "One."), p.Block("b", "unknown", "Copy button?")),
        ):
            with self.subTest(blocks=blocks):
                with self.assertRaises(p.ParagraphUnavailable):
                    p.text_from_paragraph(p.Reply("r", "assistant", blocks, complete=True), "a")

    def test_empty_suffix_is_not_sent_to_speech(self):
        p = self.reader
        reply = p.Reply("r", "assistant", (p.Block("a", "paragraph", " \n "),), complete=True)
        with self.assertRaises(p.ParagraphUnavailable):
            p.text_from_paragraph(reply, "a")
