import re
import unittest

from humanizer import analyze, rule_rewrite
from humanizer.textutil import split_sentences

SAMPLE = (
    "In today's digital age, artificial intelligence plays a crucial role in shaping modern "
    "education. It is important to note that these tools delve into vast datasets to provide "
    "personalized learning. Moreover, educators leverage a myriad of platforms to foster "
    "engagement — a trend noted by Smith et al. (2020). Furthermore, the technology "
    "underscores the need for robust policy. Additionally, it doesn't replace teachers. "
    "As one study put it, \"teachers leverage a crucial human element\" (Jones, 2019). "
    "In conclusion, this multifaceted landscape of innovation is a testament to progress."
)


class AnalyzeTests(unittest.TestCase):
    def test_formulaic_text_scores_high(self):
        rep = analyze(SAMPLE)
        self.assertGreater(rep.score, 40)
        self.assertGreaterEqual(rep.transition_openers, 4)
        self.assertEqual(rep.em_dashes, 1)
        self.assertEqual(rep.contractions, 1)
        self.assertTrue(rep.issues())

    def test_plain_text_scores_low(self):
        plain = (
            "The survey was sent to 412 teachers in March. Just over half replied. Those who did "
            "were, on average, older than the sampled population and more likely to work in rural "
            "schools, which limits how far the results can be generalised. We return to this "
            "limitation below. Response rates did not differ by subject taught."
        )
        self.assertLess(analyze(plain).score, 15)

    def test_quoted_phrases_not_counted(self):
        rep = analyze('The author writes that "we delve into a multifaceted tapestry" here.')
        self.assertEqual(rep.stock_phrases, [])

    def test_empty(self):
        self.assertEqual(analyze("").score, 0)


class RewriteTests(unittest.TestCase):
    def setUp(self):
        self.out = rule_rewrite(SAMPLE, seed=0)

    def test_score_drops(self):
        self.assertLess(analyze(self.out).score, analyze(SAMPLE).score / 2)

    def test_citations_and_quotes_preserved(self):
        self.assertIn("(2020)", self.out)
        self.assertIn("(Jones, 2019)", self.out)
        self.assertIn('"teachers leverage a crucial human element"', self.out)

    def test_academic_register(self):
        self.assertNotIn("doesn't", self.out)
        self.assertIn("does not", self.out)
        self.assertNotIn("—", self.out)

    def test_stock_phrases_removed(self):
        body = self.out.replace('"teachers leverage a crucial human element"', "")
        for phrase in ("delve", "crucial role", "myriad", "leverage", "important to note", "testament"):
            self.assertNotIn(phrase, body.lower())

    def test_sentences_stay_capitalised_and_tidy(self):
        for s in split_sentences(self.out):
            self.assertFalse(s[0].islower(), s)
        self.assertNotRegex(self.out, r"\s[,.;:]")
        self.assertNotIn("  ", self.out)

    def test_deleted_opener_capitalises_next_word(self):
        for seed in range(5):
            out = rule_rewrite(SAMPLE, seed=seed)
            self.assertRegex(out, r"(?:\. These|; these) tools (?:examine|analyse) ")
            self.assertNotRegex(out, r"tools (?:examines|analyses)\b")
            self.assertNotRegex(out, r"[.!?] [a-z]")

    def test_subject_verb_agreement(self):
        out = rule_rewrite("Teachers play a vital role in learning. The school plays a key role in it.", seed=1)
        self.assertRegex(out, r"Teachers (?:are central to|contribute to|matter for) learning")
        self.assertRegex(out, r"school (?:is central to|contributes to|matters for) it")

    def test_deterministic_and_seeded(self):
        self.assertEqual(self.out, rule_rewrite(SAMPLE, seed=0))
        self.assertTrue(any(rule_rewrite(SAMPLE, seed=s) != self.out for s in range(1, 6)))

    def test_article_agreement(self):
        out = rule_rewrite("This is a crucial step and an intricate one.", seed=0)
        self.assertNotRegex(out, r"\ba (?:important|essential)\b")
        self.assertNotRegex(out, r"\ban (?:complex|detailed|necessary)\b")
        out = rule_rewrite("They conducted a comprehensive review.", seed=3)
        self.assertRegex(out, r"\ba (?:thorough|full|detailed) review")

    def test_headings_and_paragraphs_kept(self):
        text = "A Crucial Heading\n\nIt is important to note that results vary.\n\nSecond paragraph here."
        out = rule_rewrite(text, seed=0)
        self.assertEqual(out.split("\n\n")[0], "A Crucial Heading")
        self.assertEqual(len(out.split("\n\n")), 3)
        self.assertTrue(out.split("\n\n")[1].startswith("Results vary."))

    def test_plain_text_untouched(self):
        plain = "The sample comprised 40 adults. Two withdrew before testing."
        self.assertEqual(rule_rewrite(plain, seed=0), plain)

    def test_abbreviations_do_not_split(self):
        s = split_sentences("Smith et al. (2020) found this. See Fig. 2 for details, e.g. Table 1.")
        self.assertEqual(len(s), 2)


if __name__ == "__main__":
    unittest.main()
