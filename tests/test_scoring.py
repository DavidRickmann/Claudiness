"""Tests for the claudiness scoring engine."""

import json
import sys
import os
import unittest

# Allow running tests without pip install
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from claudiness.scoring import score_text, score_text_all_models
from claudiness.structural import analyse_structure
from claudiness.patterns import count_pattern_matches, count_line_start_matches, find_specific_matches
from claudiness.style_loader import discover_styles, load_style


# Sample texts for testing
CLAUDE_LIKE_TEXT = """
That's a great question. I think it's worth noting that this topic is quite nuanced,
and there are compelling arguments on both sides. From my understanding, the situation
is more complex than it might initially appear.

On the other hand, I'd argue that there are legitimate reasons to consider the
alternative perspective. It's important to acknowledge that reasonable people can
disagree on this, and the truth is probably somewhere in between.

I should be transparent about the fact that I'm not an expert in this particular area,
so please consult a professional for specific advice. That said, I think the fundamental
tension here is between practicality and principle — and that's genuinely a tricky
balance to strike.

Having said that, the broader picture suggests that a thoughtful approach — one that
grapples with the subtle complexities rather than oversimplifying — is worthwhile.
"""

CHATGPT_LIKE_TEXT = """
Let's dive into this fascinating topic! In today's fast-paced digital landscape,
understanding this concept is absolutely essential. The transformative power of
this technology cannot be overstated.

Here are the key takeaways:
- First, leverage robust cutting-edge solutions
- Second, harness the power of seamless integration
- Third, unlock the full potential of your workflow

This is truly a game-changer that paves the way for unprecedented innovation.
The holistic approach to this challenge is commendable, and it plays a pivotal
role in the ever-evolving landscape of modern technology.

Moreover, these actionable tips will help you master the art of productivity
and embark on a journey toward excellence. It's a testament to the vibrant
community that supports this endeavor.
"""

SHORT_TEXT = "Hello world, this is a test."


class TestPatterns(unittest.TestCase):
    """Test pattern matching helpers."""

    def test_count_pattern_matches_basic(self):
        text = "It's worth noting that this is nuanced. It's worth noting again."
        patterns = [r"\bit'?s worth (?:noting|mentioning)\b"]
        self.assertEqual(count_pattern_matches(text, patterns), 2)

    def test_count_pattern_matches_empty(self):
        self.assertEqual(count_pattern_matches("hello world", [r"\bnuanced\b"]), 0)

    def test_count_line_start_matches(self):
        text = "Great question! Let me explain.\nAbsolutely, that makes sense."
        patterns = [r"^great question\b", r"^absolutely"]
        self.assertEqual(count_line_start_matches(text, patterns), 2)

    def test_find_specific_matches(self):
        text = "This is nuanced and also quite nuanced indeed."
        patterns = [r"\bnuanced\b"]
        matches = find_specific_matches(text, patterns)
        self.assertEqual(len(matches), 2)
        self.assertEqual(matches[0], "nuanced")


class TestStructural(unittest.TestCase):
    """Test structural analysis."""

    def test_short_text_defaults(self):
        result = analyse_structure("Too short.")
        self.assertEqual(result['bullet_ratio'], 0)

    def test_bullet_detection(self):
        text = "1. Item one\n2. Item two\n3. Item three\nA normal paragraph here."
        result = analyse_structure(text + " " + "word " * 30)
        self.assertGreater(result['bullet_ratio'], 0)

    def test_em_dash_detection(self):
        text = ("This is a sentence — with an em-dash — that should be detected. " +
                "word " * 30)
        result = analyse_structure(text)
        self.assertGreater(result['em_dash_rate'], 0)


class TestScoring(unittest.TestCase):
    """Test the generic scoring engine."""

    def test_short_text_returns_zero(self):
        styles = discover_styles()
        self.assertTrue(len(styles) > 0, "No styles found")
        result = score_text(SHORT_TEXT, styles[0])
        self.assertEqual(result['score'], 0)
        self.assertIn('note', result)

    def test_claude_text_scores_high_for_claude(self):
        styles = discover_styles(model_filter='claude')
        self.assertEqual(len(styles), 1)
        result = score_text(CLAUDE_LIKE_TEXT, styles[0])
        self.assertGreater(result['score'], 40,
                           f"Expected Claude-like text to score >40, got {result['score']}")

    def test_chatgpt_text_scores_high_for_chatgpt(self):
        styles = discover_styles(model_filter='chatgpt')
        self.assertEqual(len(styles), 1)
        result = score_text(CHATGPT_LIKE_TEXT, styles[0])
        self.assertGreater(result['score'], 40,
                           f"Expected ChatGPT-like text to score >40, got {result['score']}")

    def test_claude_text_scores_low_for_chatgpt(self):
        styles = discover_styles(model_filter='chatgpt')
        self.assertEqual(len(styles), 1)
        result = score_text(CLAUDE_LIKE_TEXT, styles[0])
        self.assertLess(result['score'], 30,
                        f"Expected Claude text to score <30 for ChatGPT, got {result['score']}")

    def test_score_text_all_models(self):
        styles = discover_styles()
        results = score_text_all_models(CLAUDE_LIKE_TEXT, styles)
        self.assertEqual(len(results), len(styles))
        # Results should be sorted by score descending
        scores = [r['score'] for r in results]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_result_has_required_fields(self):
        styles = discover_styles(model_filter='claude')
        result = score_text(CLAUDE_LIKE_TEXT, styles[0])
        self.assertIn('score', result)
        self.assertIn('label', result)
        self.assertIn('breakdown', result)
        self.assertIn('details', result)
        self.assertIn('word_count', result)
        self.assertIn('model', result)
        self.assertIn('display_name', result)


class TestStyleLoader(unittest.TestCase):
    """Test style file loading and discovery."""

    def test_discover_bundled_styles(self):
        styles = discover_styles()
        self.assertGreaterEqual(len(styles), 3, "Expected at least 3 bundled styles")

    def test_filter_by_model(self):
        styles = discover_styles(model_filter='claude')
        self.assertEqual(len(styles), 1)
        self.assertEqual(styles[0]['model'], 'claude')

    def test_filter_by_family(self):
        styles = discover_styles(model_filter='chatgpt')
        self.assertEqual(len(styles), 1)

    def test_style_has_required_fields(self):
        styles = discover_styles()
        for s in styles:
            self.assertIn('model', s)
            self.assertIn('categories', s)
            self.assertIn('labels', s)

    def test_nonexistent_model_returns_empty(self):
        styles = discover_styles(model_filter='nonexistent_model')
        self.assertEqual(len(styles), 0)


class TestCLI(unittest.TestCase):
    """Test CLI preprocessing."""

    def test_preprocess_model_shorthand(self):
        from claudiness.cli import _preprocess_argv
        result = _preprocess_argv(['-claude', 'file.txt'])
        self.assertEqual(result, ['--model', 'claude', 'file.txt'])

    def test_preprocess_preserves_known_flags(self):
        from claudiness.cli import _preprocess_argv
        result = _preprocess_argv(['-v', '-j', 'file.txt'])
        self.assertEqual(result, ['-v', '-j', 'file.txt'])

    def test_preprocess_preserves_long_flags(self):
        from claudiness.cli import _preprocess_argv
        result = _preprocess_argv(['--verbose', '--model', 'claude'])
        self.assertEqual(result, ['--verbose', '--model', 'claude'])


if __name__ == '__main__':
    unittest.main()
