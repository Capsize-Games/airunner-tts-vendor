"""Regression tests for the g2p cache's restricted unpickler.

Ported from services/tests/test_model_load_security.py in
Capsize-Games/airunner (GitHub issue #2031) when
melo/text/language_base.py moved to this repository (issue #2195):
that file's own coverage of ``_load_g2p_cache_safe`` stopped running
once the module it imported by path no longer existed there. The
underlying fix stays the same -- the g2p cache is never loaded via
raw ``pickle.load``; a restricted unpickler that only permits
primitive container types rejects everything else and falls back to
regeneration.

The source-scan test needs no import and runs in the lean install;
language_base.py itself imports torch and transformers at module
scope (for the tokenizer it also uses), so the behavioral tests are
guarded with importorskip for both, matching the "ml" extra split.
"""

from __future__ import annotations

import builtins
import pickle
from pathlib import Path

import pytest

_LANGUAGE_BASE_PATH = (
    Path(__file__).resolve().parents[1]
    / "airunner_tts_vendor"
    / "melo"
    / "text"
    / "language_base.py"
)


class _Malicious:
    """Object whose unpickle would execute arbitrary code."""

    def __reduce__(self):
        return (builtins.eval, ("__import__('os').getcwd()",))


def _write_pickle(path: str, obj) -> None:
    with open(path, "wb") as handle:
        pickle.dump(obj, handle)


@pytest.fixture
def load_g2p_cache_safe():
    pytest.importorskip("torch")
    pytest.importorskip("transformers")
    from airunner_tts_vendor.melo.text.language_base import (
        _load_g2p_cache_safe,
    )

    return _load_g2p_cache_safe


def test_safe_g2p_cache_accepts_plain_dict(
    tmp_path, load_g2p_cache_safe
) -> None:
    cache = str(tmp_path / "cmudict_cache.pickle")
    _write_pickle(cache, {"hello": [["HH", "AH0", "L", "OW1"]]})
    assert load_g2p_cache_safe(cache) == {
        "hello": [["HH", "AH0", "L", "OW1"]]
    }


def test_safe_g2p_cache_rejects_malicious_object(
    tmp_path, load_g2p_cache_safe
) -> None:
    cache = str(tmp_path / "cmudict_cache.pickle")
    _write_pickle(cache, _Malicious())
    assert load_g2p_cache_safe(cache) is None


def test_safe_g2p_cache_rejects_non_dict(
    tmp_path, load_g2p_cache_safe
) -> None:
    cache = str(tmp_path / "cmudict_cache.pickle")
    _write_pickle(cache, ["not", "a", "dict"])
    assert load_g2p_cache_safe(cache) is None


def test_safe_g2p_cache_rejects_corrupt_file(
    tmp_path, load_g2p_cache_safe
) -> None:
    cache = str(tmp_path / "cmudict_cache.pickle")
    with open(cache, "wb") as handle:
        handle.write(b"\x00\x01garbage not a pickle")
    assert load_g2p_cache_safe(cache) is None


def test_no_bare_pickle_load_in_language_base() -> None:
    """The g2p cache must never be loaded via raw pickle.load."""
    source = _LANGUAGE_BASE_PATH.read_text(encoding="utf-8")
    assert "pickle.load(" not in source
