import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from lib import naming


def test_revision_letter_basic():
    assert naming.revision_letter(1) == "A"
    assert naming.revision_letter(26) == "Z"
    assert naming.revision_letter(27) == "AA"
    assert naming.revision_letter(52) == "AZ"


def test_revision_letter_rejects_non_positive():
    with pytest.raises(ValueError):
        naming.revision_letter(0)


def test_render_template_default():
    filename = naming.render_template(
        naming.DEFAULT_TEMPLATE,
        name="bracket_final",
        version=7,
        date="20260709",
        ext="step",
    )
    assert filename == "bracket_final_RevG_20260709.step"


def test_render_template_sanitizes_invalid_characters():
    filename = naming.render_template(
        "{name}.{ext}",
        name='bracket/final:v2?',
        version=1,
        date="20260709",
        ext="stl",
    )
    assert "/" not in filename
    assert ":" not in filename
    assert "?" not in filename


def test_render_template_supports_note_and_version_fields():
    filename = naming.render_template(
        "{name}_v{version}_{note}.{ext}",
        name="bracket",
        version=3,
        date="20260709",
        ext="step",
        note="for acme corp",
    )
    assert filename == "bracket_v3_for acme corp.step"


def test_render_template_unknown_field_raises():
    with pytest.raises(ValueError):
        naming.render_template(
            "{name}_{bogus}.{ext}",
            name="bracket",
            version=1,
            date="20260709",
            ext="step",
        )
