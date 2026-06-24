"""layer_tools — standalone-and-integratable Layer-Tools (Initiative I-5).

Each tool runs against the bare stack (no ALUCA core needed) AND integrates
(Invariant I4). I-5.1 ships the Visual-Library + spec resolver in
`visual_library.py` (also a CLI: `python -m tooling.superversion.layer_tools.visual_library`).
Import submodules directly (not re-exported here, so running a submodule with
`-m` doesn't trigger a runpy double-import warning):

    from tooling.superversion.layer_tools import visual_library
"""
