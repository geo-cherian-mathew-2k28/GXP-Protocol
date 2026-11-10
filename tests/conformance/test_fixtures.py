from __future__ import annotations

import json
import unittest
from pathlib import Path

from gxp.validation import validate_envelope


class FixtureConformanceTests(unittest.TestCase):
    def test_valid_position_fixture(self) -> None:
        fixture_path = Path(__file__).parents[1] / "fixtures" / "valid-busroot-position.json"
        validate_envelope(json.loads(fixture_path.read_text(encoding="utf-8")))

