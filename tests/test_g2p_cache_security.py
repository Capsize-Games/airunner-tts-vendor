"""Regression tests for the g2p cache's restricted unpickler.

Ported from services/tests/test_model_load_security.py in
Capsize-Games/airunner (GitHub issue #2031) when
melo/text/language_base.py moved to this repository (issue #2195):
that file's own coverage of ``_load_g2p_cache_safe`` stopped running
once the module it imported by path no longer existed there.

``_SafeG2PUnpickler`` is pure Python, but the module that defines it
also imports torch and transformers at module scope for the tokenizer
``LanguageBase`` itself uses. Rather than requiring those (real) heavy
optional deps just to exercise a pure-Python class, this stubs them
via ``monkeypatch.setitem(sys.modules, ...)`` before a direct
file-path import: monkeypatch restores the real entries (or removes
the stubs) after each test, so this can't leak a fake ``torch``/
``transformers`` into ``sys.modules`` for the genuinely
torch-dependent tests in test_torch_dependent_modules.py to trip
over -- a real bug the original version of this stub technique in the
source repository's own test suite carried (documented there as
"never restores it").
"""

from __future__ import annotations

import builtins
import importlib.util
import pickle
import sys
from pathlib import Path
from types import ModuleType

_LANGUAGE_BASE_PATH = (
    Path(__file__).resolve().parents[1]
    / "airunner_tts_vendor"
    / "melo"
    / "text"
    / "language_base.py"
)


def _load_language_base_pure(monkeypatch) -> ModuleType:
    """Import language_base.py with torch/transformers stubbed out."""
    torch_stub = ModuleType("torch")
    transformers_stub = ModuleType("transformers")
    transformers_stub.AutoTokenizer = object
    transformers_stub.AutoModelForMaskedLM = object
    monkeypatch.setitem(sys.modules, "torch", torch_stub)
    monkeypatch.setitem(sys.modules, "transformers", transformers_stub)

    spec = importlib.util.spec_from_file_location(
        "airunner_tts_vendor.melo.text.language_base_under_test",
        _LANGUAGE_BASE_PATH,
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


class _Malicious:
    """Object whose unpickle would execute arbitrary code."""

    def __reduce__(self):
        return (builtins.eval, ("__import__('os').getcwd()",))


def _write_pickle(path: str, obj) -> None:
    with open(path, "wb") as handle:
        pickle.dump(obj, handle)


def test_safe_g2p_cache_accepts_plain_dict(tmp_path, monkeypatch) -> None:
    load_safe = _load_language_base_pure(monkeypatch)._load_g2p_cache_safe
    cache = str(tmp_path / "cmudict_cache.pickle")
    _write_pickle(cache, {"hello": [["HH", "AH0", "L", "OW1"]]})
    assert load_safe(cache) == {"hello": [["HH", "AH0", "L", "OW1"]]}


def test_safe_g2p_cache_rejects_malicious_object(
    tmp_path, monkeypatch
) -> None:
    load_safe = _load_language_base_pure(monkeypatch)._load_g2p_cache_safe
    cache = str(tmp_path / "cmudict_cache.pickle")
    _write_pickle(cache, _Malicious())
    assert load_safe(cache) is None


def test_safe_g2p_cache_rejects_non_dict(tmp_path, monkeypatch) -> None:
    load_safe = _load_language_base_pure(monkeypatch)._load_g2p_cache_safe
    cache = str(tmp_path / "cmudict_cache.pickle")
    _write_pickle(cache, ["not", "a", "dict"])
    assert load_safe(cache) is None


def test_safe_g2p_cache_rejects_corrupt_file(tmp_path, monkeypatch) -> None:
    load_safe = _load_language_base_pure(monkeypatch)._load_g2p_cache_safe
    cache = str(tmp_path / "cmudict_cache.pickle")
    with open(cache, "wb") as handle:
        handle.write(b"\x00\x01garbage not a pickle")
    assert load_safe(cache) is None


def test_no_bare_pickle_load_in_language_base() -> None:
    """The g2p cache must never be loaded via raw pickle.load."""
    source = _LANGUAGE_BASE_PATH.read_text(encoding="utf-8")
    assert "pickle.load(" not in source
