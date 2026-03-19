"""Generic scoring engine — scores text against any .style definition."""

import re

from claudiness.patterns import count_pattern_matches, count_line_start_matches
from claudiness.structural import analyse_structure


def _evaluate_structural_rules(structure, rules):
    """Evaluate structural threshold rules against computed structure metrics."""
    score = 0
    for rule in rules:
        feature = rule['feature']
        value = structure.get(feature, 0)
        for threshold in rule.get('thresholds', []):
            matched = True
            if 'min' in threshold and value < threshold['min']:
                matched = False
            if 'max' in threshold and value > threshold['max']:
                matched = False
            if matched:
                score += threshold['points']
                break  # First matching threshold wins per rule
    return score


def score_text(text, style, structure=None):
    """
    Score text against a single style definition.

    Args:
        text: The text to analyse.
        style: A parsed .style dict.
        structure: Pre-computed structure analysis (optional, computed if None).

    Returns:
        Dict with score, label, breakdown, details, word_count.
    """
    word_count = len(text.split())
    scoring_cfg = style.get('scoring', {})
    min_words = scoring_cfg.get('min_word_count', 30)
    norm_base = scoring_cfg.get('normalization_base', 500)

    if word_count < min_words:
        return {
            'model': style.get('model', 'unknown'),
            'display_name': style.get('display_name', style.get('model', 'unknown')),
            'score': 0,
            'label': style.get('labels', [{}])[-1].get('label', 'Unknown'),
            'breakdown': {},
            'details': {},
            'word_count': word_count,
            'note': f'Text too short for meaningful analysis (< {min_words} words)',
        }

    norm = norm_base / max(word_count, 1)
    breakdown = {}
    details = {}

    # --- Score each category ---
    for key, cat in style.get('categories', {}).items():
        patterns = cat.get('patterns', [])
        match_mode = cat.get('match_mode', 'anywhere')
        weight = cat.get('weight', 10)
        multiplier = cat.get('multiplier', 1)
        direction = cat.get('direction', 'positive')

        if match_mode == 'line_start':
            match_count = count_line_start_matches(text, patterns)
        else:
            match_count = count_pattern_matches(text, patterns)

        norm_count = match_count * norm
        raw_points = min(norm_count * multiplier, weight)

        if direction == 'negative':
            breakdown[key] = -raw_points
            details[key] = {
                'matches': match_count,
                'per_500_words': round(norm_count, 1),
                'penalty': round(raw_points, 1),
            }
        else:
            breakdown[key] = raw_points
            details[key] = {
                'matches': match_count,
                'per_500_words': round(norm_count, 1),
                'max_points': weight,
                'points': round(raw_points, 1),
            }

    # --- Structural analysis ---
    structural_cfg = style.get('structural', {})
    if structural_cfg.get('enabled', False):
        if structure is None:
            structure = analyse_structure(text)
        struct_weight = structural_cfg.get('weight', 15)
        struct_score = _evaluate_structural_rules(
            structure, structural_cfg.get('rules', [])
        )
        breakdown['structure'] = min(struct_score, struct_weight)
        details['structure'] = {
            'bullet_ratio': round(structure.get('bullet_ratio', 0), 3),
            'em_dash_rate': round(structure.get('em_dash_rate', 0), 2),
            'parenthetical_rate': round(structure.get('parenthetical_rate', 0), 2),
            'avg_sentence_length': round(structure.get('avg_sentence_length', 0), 1),
            'sentence_length_std_dev': round(structure.get('sentence_length_variance', 0), 1),
            'max_points': struct_weight,
            'points': round(breakdown['structure'], 1),
        }

    # --- Bonuses ---
    bonuses_cfg = style.get('bonuses', {})
    conv_cfg = bonuses_cfg.get('conversational_tone', {})
    if conv_cfg.get('enabled', False):
        first_person = len(re.findall(r'\bI\b', text))
        second_person = len(re.findall(r'\byou(?:r|\'re|\'ve|\'ll)?\b', text, re.IGNORECASE))
        conv_norm = (first_person + second_person) * norm
        conv_bonus = min(conv_norm * conv_cfg.get('multiplier', 0.3),
                         conv_cfg.get('weight', 10))
        breakdown['conversational_bonus'] = conv_bonus
        details['conversational_bonus'] = {
            'first_person_count': first_person,
            'second_person_count': second_person,
            'per_500_words': round(conv_norm, 1),
            'bonus': round(conv_bonus, 1),
        }

    # --- Final score ---
    raw_score = sum(breakdown.values())
    final_score = max(0, min(100, raw_score))

    # Determine label
    label = style.get('labels', [{}])[-1].get('label', 'Unknown')
    for entry in style.get('labels', []):
        if final_score >= entry.get('min', 0):
            label = entry['label']
            break

    return {
        'model': style.get('model', 'unknown'),
        'display_name': style.get('display_name', style.get('model', 'unknown')),
        'score': round(final_score, 1),
        'label': label,
        'word_count': word_count,
        'breakdown': {k: round(v, 1) for k, v in breakdown.items()},
        'details': details,
    }


def score_text_all_models(text, styles):
    """
    Score text against all provided style definitions.

    Computes structural analysis once and shares it across all scorers.

    Args:
        text: The text to analyse.
        styles: List of parsed .style dicts.

    Returns:
        List of result dicts, sorted by score descending.
    """
    structure = analyse_structure(text)
    results = []
    for style in styles:
        result = score_text(text, style, structure=structure)
        results.append(result)
    results.sort(key=lambda r: r['score'], reverse=True)
    return results
