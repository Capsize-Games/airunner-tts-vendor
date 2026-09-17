# airunner-tts-vendor

Vendored [MeloTTS](https://github.com/myshell-ai/MeloTTS) and
[OpenVoice](https://github.com/myshell-ai/OpenVoice) forks used by the
TTS pipeline in
[Capsize-Games/airunner](https://github.com/Capsize-Games/airunner)
(AI Runner). This is third-party code, kept in its own repository
rather than a subdirectory of `airunner-services` specifically so its
licensing and upstream provenance stay physically separate from that
GPL-3.0 distribution's own code, and so upstream diffs stay legible.

## Licensing

Both `melo/` and `openvoice/` are separately MIT-licensed by their
respective upstream projects. See `melo/LICENSE` and
`openvoice/LICENSE` for the exact upstream copyright notices; neither
this package as a whole nor Capsize LLC's own integration changes
relicense either subtree. This repository does not carry a top-level
`LICENSE` file that would override either subtree's own.

## Provenance

Extracted from `Capsize-Games/airunner` at commit `b57cb8e3d`
(2026-09-17), as issue
[#2195](https://github.com/Capsize-Games/airunner/issues/2195), part
of the repository-split tracker
[#2185](https://github.com/Capsize-Games/airunner/issues/2185).
History for the moved files is preserved (`git filter-repo`).

Each subtree's own README documents its upstream project and
whichever pin information issue
[#2190](https://github.com/Capsize-Games/airunner/issues/2190) could
establish for it -- see `melo/README.md` and `openvoice/README.md`.
Neither README names an exact upstream commit; both were vendored
from the upstream project's `main` branch at the time of integration
(issue #2051 in the source repository) without recording the specific
commit. That is a real gap, not an oversight being papered over here:
if an exact upstream fork point is ever needed (for issue #2113 in
the source repository, the dependency/model license inventory, or for
comparing against a specific upstream release), it is not currently
determinable from this repository's history and would need to be
reconstructed by diffing against the upstream projects directly.

## Local modifications

Both forks were decoupled from the application they used to live
beside (issue [#2190](https://github.com/Capsize-Games/airunner/issues/2190),
before this extraction): no import here reaches into `airunner`,
`airunner_common`, or `airunner_services`. Where the fork previously
needed something app-specific (a language enum, a model storage path,
a cache directory, the application's GPU-memory-clearing helper), it
now either defines its own equivalent (`melo/language.py`,
`openvoice/language.py`) or exposes an injectable resolver/hook that
the host process registers at startup
(`set_tts_model_root_resolver`, `set_tts_model_base_resolver`,
`set_cache_base_resolver`, `set_memory_cleanup_hook` in
`melo/runtime_support.py` and `melo/api.py`) -- see each subtree's own
README for the full list.

**Do not reformat, restyle, or lint-fix the vendored code.** The value
of keeping it in its own repository is that upstream diffs stay
readable; a formatting pass defeats that on day one.

## Install

The base install has no torch dependency at all -- `melo/api.py` and
`openvoice/api.py` need torch to *import*, but installing this
package does not require it, since torch needs an explicit
`--index-url` for your platform (CPU vs a specific CUDA version):

```bash
pip install -e .
pip install "airunner-tts-vendor[ml]" \
  --index-url https://download.pytorch.org/whl/cu129   # GPU
pip install "airunner-tts-vendor[ml]" \
  --index-url https://download.pytorch.org/whl/cpu     # CPU
# Plus, per language:
pip install -e ".[zh]"   # Chinese (MeloTTS/OpenVoice)
pip install -e ".[jp]"   # Japanese
pip install -e ".[kr]"   # Korean
pip install -e ".[tw]"   # Taiwanese Hokkien (g2pkk)
pip install -e ".[gruut]"  # German/Spanish/French phonemization support
```

No dependency on `airunner`, `airunner-common`, or `airunner-services`
-- this package installs and imports standalone. `airunner-services`
depends on the published version of this package; see
`runtimes/openvoice_model_manager.py` and
`runtimes/openvoice_runtime_helpers.py` in that repository for its
public surface (`melo.api`, `melo.runtime_support`, `openvoice.api`,
`openvoice.se_extractor`, `openvoice.mel_processing`) and the resolver
registration that reconnects it to the application after installing
this package.

## Testing

This fork has no tests of its own in the source repository; the TTS
synthesis tests that exercise it (`test_tts_synthesize_functional.py`,
`test_model_load_security.py`) stay in `airunner-services`, since they
need the full daemon and a real GPU/model to run meaningfully. CI here
is therefore limited to import-level sanity checks: that both
subtrees import cleanly with no application dependency present, and
that the language-enum/resolver integration points this repository
exposes behave as documented. Full synthesis coverage (and the
[bobross.wav](https://github.com/Capsize-Games/airunner/blob/master/services/src/airunner_services/assets/reference_speakers/bobross.wav)
reference-speaker fixture it uses) stays in `airunner-services` as an
integration test against this published package.
