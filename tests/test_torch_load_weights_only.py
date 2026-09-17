"""Every torch.load call site must pass weights_only=True.

Ported from services/tests/test_model_load_security.py in
Capsize-Games/airunner (GitHub issue #2031) when the four vendor
files it covered (melo/api.py, melo/data_utils.py, openvoice/api.py,
openvoice/se_extractor.py) moved to this repository (issue #2195):
that source-scan stopped running against them once they no longer
existed at the old path. This is a pure source-text scan -- no torch
import needed -- so it runs in the lean install like the original.
"""

from __future__ import annotations

from pathlib import Path

_PACKAGE_ROOT = Path(__file__).resolve().parents[1] / "airunner_tts_vendor"

_TORCH_LOAD_FILES = [
    "melo/api.py",
    "melo/data_utils.py",
    "openvoice/api.py",
    "openvoice/se_extractor.py",
]


def test_all_torch_load_calls_use_weights_only() -> None:
    """Every torch.load call site passes weights_only=True."""
    for relative_path in _TORCH_LOAD_FILES:
        source = (_PACKAGE_ROOT / relative_path).read_text(
            encoding="utf-8"
        )
        # Strip comments so a mention in prose does not count as a call.
        code_lines = [line.split("#", 1)[0] for line in source.splitlines()]
        for line_number, code in enumerate(code_lines, start=1):
            if "torch.load(" not in code:
                continue
            # Find the call block and ensure weights_only=True appears
            # within the same statement (multi-line calls included).
            block_lines = []
            depth = 0
            started = False
            for index in range(line_number - 1, len(code_lines)):
                candidate = code_lines[index]
                block_lines.append(candidate)
                depth += candidate.count("(") - candidate.count(")")
                if not started:
                    started = True
                    if depth <= 0:
                        break
                elif depth <= 0:
                    break
            joined = "\n".join(block_lines)
            assert "weights_only=True" in joined, (
                f"torch.load in {relative_path}:{line_number} "
                "missing weights_only=True"
            )
