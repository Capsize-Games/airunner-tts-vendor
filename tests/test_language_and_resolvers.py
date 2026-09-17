"""Import-level sanity checks that don't need torch installed.

melo/api.py and openvoice/api.py hard-require torch at module level
(real inference code), so a lean CI install without a torch wheel
cannot import them -- see test_torch_dependent_modules.py for those,
guarded with importorskip. This file covers the pure-Python pieces:
the language enums and the path/logging/memory resolver hooks added
when this fork was decoupled from the application (issue #2190).
"""

from __future__ import annotations

from airunner_tts_vendor.melo.language import Language as MeloLanguage
from airunner_tts_vendor.melo import runtime_support
from airunner_tts_vendor.openvoice.language import (
    Language as OpenVoiceLanguage,
)

_EXPECTED_MEMBERS = {
    "AUTO": "Automatic",
    "EN": "EN",
    "ES": "ES",
    "FR": "FR",
    "ZH": "ZH",
    "ZH_MIX_EN": "ZH_MIX_EN",
    "JP": "JP",
    "KR": "KR",
    "SP": "SP",
}


def test_melo_language_enum_members():
    members = {m.name: m.value for m in MeloLanguage}
    assert members == _EXPECTED_MEMBERS


def test_openvoice_language_enum_members():
    members = {m.name: m.value for m in OpenVoiceLanguage}
    assert members == _EXPECTED_MEMBERS


def test_tts_model_root_resolver_chain(monkeypatch, tmp_path):
    monkeypatch.delenv("AIRUNNER_TTS_MODEL_PATH", raising=False)
    runtime_support.set_tts_model_root_resolver(lambda: None)
    runtime_support.set_tts_model_base_resolver(lambda: None)
    runtime_support.set_cache_base_resolver(lambda: None)

    # No resolver returns a value -> the package's own default, not an
    # application path (there is no application here).
    default_root = runtime_support.resolve_tts_model_root()
    assert default_root == runtime_support._default_tts_model_root()

    # A host process (e.g. airunner-services) registering its own
    # resolvers is the actual integration point.
    runtime_support.set_tts_model_base_resolver(lambda: str(tmp_path))
    resolved = runtime_support.resolve_tts_model_root()
    assert resolved == str(tmp_path / "text" / "models" / "tts")
