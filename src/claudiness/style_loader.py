"""Load and discover .style fingerprint files."""

import json
import os
from pathlib import Path


def _bundled_styles_dir():
    """Return the path to the bundled styles directory."""
    return Path(__file__).parent / "styles"


def _user_styles_dir():
    """Return the user config styles directory."""
    config_home = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
    return Path(config_home) / "claudiness" / "styles"


def _project_styles_dir():
    """Return the project-local styles directory."""
    return Path.cwd() / ".claudiness" / "styles"


def load_style(path):
    """Load a single .style file and return its parsed dict."""
    with open(path, 'r', encoding='utf-8') as f:
        style = json.load(f)
    style['_path'] = str(path)
    return style


def discover_styles(style_dirs=None, model_filter=None):
    """
    Discover and load all .style files from standard locations.

    Search order (later overrides earlier if same model+date):
      1. Bundled styles (package)
      2. User config (~/.config/claudiness/styles/)
      3. Project local (./.claudiness/styles/)
      4. Extra dirs from style_dirs parameter

    Args:
        style_dirs: Additional directories to search for .style files.
        model_filter: If set, only return styles whose 'model' or 'family'
                      matches this string (case-insensitive).

    Returns:
        List of parsed style dicts, deduplicated by model+date (latest wins).
    """
    search_dirs = [
        _bundled_styles_dir(),
        _user_styles_dir(),
        _project_styles_dir(),
    ]
    if style_dirs:
        for d in style_dirs:
            search_dirs.append(Path(d))

    # Collect all .style files, later dirs override earlier for same key
    styles_by_key = {}
    for d in search_dirs:
        if not d.is_dir():
            continue
        for f in sorted(d.glob("*.style")):
            try:
                style = load_style(f)
                key = (style.get('model', ''), style.get('date', ''))
                styles_by_key[key] = style
            except (json.JSONDecodeError, OSError):
                continue

    styles = list(styles_by_key.values())

    if model_filter:
        model_filter_lower = model_filter.lower()
        styles = [
            s for s in styles
            if s.get('model', '').lower() == model_filter_lower
            or s.get('family', '').lower() == model_filter_lower
        ]

    return styles


def list_models(style_dirs=None):
    """Return summary info for all discovered styles."""
    styles = discover_styles(style_dirs=style_dirs)
    summaries = []
    for s in styles:
        summaries.append({
            'model': s.get('model', 'unknown'),
            'family': s.get('family', 'unknown'),
            'display_name': s.get('display_name', s.get('model', 'unknown')),
            'date': s.get('date', 'unknown'),
            'categories': len(s.get('categories', {})),
            'path': s.get('_path', ''),
        })
    return summaries
