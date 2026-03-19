"""Pattern matching helpers for regex-based text analysis."""

import re
from collections import Counter


def count_pattern_matches(text, patterns):
    """Count total matches for a list of regex patterns."""
    count = 0
    text_lower = text.lower()
    for pattern in patterns:
        count += len(re.findall(pattern, text_lower, re.IGNORECASE))
    return count


def count_line_start_matches(text, patterns):
    """Count matches that occur at the start of paragraphs/sentences."""
    count = 0
    paragraphs = text.split('\n')
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        for pattern in patterns:
            if re.match(pattern, para, re.IGNORECASE):
                count += 1
                break
        sentences = re.split(r'(?<=[.!?])\s+', para)
        for sent in sentences[1:]:
            for pattern in patterns:
                if re.match(pattern, sent.strip(), re.IGNORECASE):
                    count += 1
                    break
    return count


def find_specific_matches(text, patterns):
    """Return the actual matched strings for diagnostic purposes."""
    matches = []
    text_lower = text.lower()
    for pattern in patterns:
        found = re.findall(pattern, text_lower, re.IGNORECASE)
        if found:
            matches.extend(found)
    return matches
