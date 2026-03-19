"""Structural text analysis — measures formatting features rather than vocabulary."""

import re


def analyse_structure(text):
    """
    Analyse structural features that distinguish AI model writing styles.

    Returns a dict of structural metrics:
      - bullet_ratio: fraction of lines that are bullet/list items
      - em_dash_rate: em-dashes per 100 words
      - parenthetical_rate: parenthetical asides per 200 words
      - avg_sentence_length: mean words per sentence
      - sentence_length_variance: std dev of sentence lengths
      - heading_density: fraction of lines that are markdown headings
      - paragraph_count: number of substantial lines (>30 chars)
    """
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    sentences = re.split(r'(?<=[.!?])\s+', text)
    sentences = [s for s in sentences if len(s) > 10]
    word_count = len(text.split())

    if word_count < 20:
        return {'prose_ratio': 0, 'em_dash_rate': 0, 'parenthetical_rate': 0,
                'avg_sentence_length': 0, 'sentence_length_variance': 0,
                'bullet_ratio': 0, 'paragraph_count': len(lines)}

    results = {}

    # Prose vs Bullets/Lists
    bullet_lines = sum(1 for l in lines if re.match(r'^[\-\*\•\d]+[\.\)]\s', l))
    results['bullet_ratio'] = bullet_lines / max(len(lines), 1)

    # Em-dashes
    em_dashes = len(re.findall(r'[—–]', text))
    results['em_dash_rate'] = em_dashes / max(word_count / 100, 1)

    # Parenthetical asides
    parens = len(re.findall(r'\([^)]{10,}\)', text))
    results['parenthetical_rate'] = parens / max(word_count / 200, 1)

    # Sentence length variation
    if sentences:
        lengths = [len(s.split()) for s in sentences]
        avg = sum(lengths) / len(lengths)
        variance = sum((l - avg) ** 2 for l in lengths) / len(lengths)
        results['avg_sentence_length'] = avg
        results['sentence_length_variance'] = variance ** 0.5
    else:
        results['avg_sentence_length'] = 0
        results['sentence_length_variance'] = 0

    # Heading usage
    markdown_headings = sum(1 for l in lines if re.match(r'^#{1,6}\s', l))
    results['heading_density'] = markdown_headings / max(len(lines), 1)

    results['paragraph_count'] = len([l for l in lines if len(l) > 30])

    return results
