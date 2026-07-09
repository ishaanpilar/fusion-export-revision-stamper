"""Filename template rendering for revision-stamped exports.

No Fusion API dependency here on purpose, so this logic can be unit tested
without a running Fusion session.
"""
import re
import string

DEFAULT_TEMPLATE = "{name}_Rev{revletter}_{date}.{ext}"

_INVALID_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def revision_letter(version_number: int) -> str:
    """Convert a 1-based version number to a spreadsheet-style letter (1->A, 26->Z, 27->AA)."""
    if version_number < 1:
        raise ValueError("version_number must be >= 1")
    letters = string.ascii_uppercase
    n = version_number
    result = ""
    while n > 0:
        n, remainder = divmod(n - 1, 26)
        result = letters[remainder] + result
    return result


def sanitize_filename_part(text: str) -> str:
    """Strip characters that are invalid in Windows/macOS filenames."""
    return _INVALID_CHARS.sub("_", text).strip()


def render_template(template: str, *, name: str, version: int, date: str, ext: str,
                     note: str = "", rev_letter: str = None) -> str:
    """Render a filename from a template string and the known export fields.

    Supported fields: {name} {version} {rev} {revletter} {date} {ext} {note}
    """
    rev_letter = rev_letter if rev_letter is not None else revision_letter(version)
    fields = {
        "name": sanitize_filename_part(name),
        "version": version,
        "rev": version,
        "revletter": rev_letter,
        "date": date,
        "ext": ext.lstrip("."),
        "note": sanitize_filename_part(note),
    }
    try:
        rendered = template.format(**fields)
    except KeyError as exc:
        raise ValueError(f"Unknown template field: {exc}") from exc
    except IndexError as exc:
        raise ValueError("Template must use named fields, e.g. {name}, not positional {}") from exc
    return sanitize_filename_part(rendered)
