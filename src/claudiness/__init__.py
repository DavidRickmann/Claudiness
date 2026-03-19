"""Claudiness - Multi-model AI writing style detector."""

from claudiness.scoring import score_text, score_text_all_models
from claudiness.style_loader import load_style, discover_styles
from claudiness.structural import analyse_structure
from claudiness.patterns import count_pattern_matches, count_line_start_matches, find_specific_matches
