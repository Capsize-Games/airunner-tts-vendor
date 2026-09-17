"""Import checks for the modules that hard-require torch.

melo/api.py and openvoice/api.py (and se_extractor.py) are real
inference code and import torch at module level, unlike
language.py/runtime_support.py (see test_language_and_resolvers.py).
Guarded with importorskip rather than assumed available, matching the
pattern services/tests/test_model_load_security.py already uses in
the source repository for the same reason.
"""

from __future__ import annotations

import pytest

pytest.importorskip("torch")


def test_melo_api_imports():
    from airunner_tts_vendor.melo import api

    assert hasattr(api, "TTS")
    assert hasattr(api, "set_memory_cleanup_hook")


def test_openvoice_api_imports():
    from airunner_tts_vendor.openvoice import api

    assert hasattr(api, "ToneColorConverter")


def test_openvoice_se_extractor_imports():
    from airunner_tts_vendor.openvoice import se_extractor

    assert hasattr(se_extractor, "get_se")
    assert se_extractor.logger.name == (
        "airunner_tts_vendor.openvoice.se_extractor"
    )


def test_memory_cleanup_hook_is_injectable():
    from airunner_tts_vendor.melo import api

    calls = []
    api.set_memory_cleanup_hook(lambda: calls.append(1))
    api._memory_cleanup_hook()
    assert calls == [1]
