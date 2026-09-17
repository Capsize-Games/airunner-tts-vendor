"""Regression tests for the extraction itself (issue #2195).

The whole point of extracting this fork into its own repository was
that it depends on nothing from Capsize-Games/airunner -- confirmed
before extraction by issue #2190's decoupling work and this
repository's own import-boundary checker. These tests pin that here,
independent of whichever host application eventually installs this
package.
"""

from __future__ import annotations

import re
from pathlib import Path

_PACKAGE_ROOT = Path(__file__).resolve().parents[1] / "airunner_tts_vendor"

_APP_IMPORT_PATTERN = re.compile(
    r"^\s*(?:from|import)\s+(airunner\.|airunner_common\.|airunner_services\.)",
    re.MULTILINE,
)


def test_package_imports_nothing_from_the_source_application():
    offenders = []
    for path in _PACKAGE_ROOT.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        match = _APP_IMPORT_PATTERN.search(text)
        if match:
            offenders.append((str(path), match.group(0).strip()))
    assert offenders == []


def test_melo_and_openvoice_subtrees_both_present():
    assert (_PACKAGE_ROOT / "melo" / "LICENSE").is_file()
    assert (_PACKAGE_ROOT / "melo" / "README.md").is_file()
    assert (_PACKAGE_ROOT / "openvoice" / "LICENSE").is_file()
    assert (_PACKAGE_ROOT / "openvoice" / "README.md").is_file()
