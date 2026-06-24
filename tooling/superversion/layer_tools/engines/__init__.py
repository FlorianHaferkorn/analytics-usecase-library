"""engines — gov/eng/arch engine-adapter seam + Beta engines (task I-5.3).

Importing this package registers the three Beta engines (gov, dataarch, dataeng)
on the contract in `base.py`. The real Meridian engines dock here when vendored.
Run via `python -m tooling.superversion.layer_tools.engines.cli`.
"""
from tooling.superversion.layer_tools.engines import (  # noqa: F401 — register on import
    dataarch_engine,
    dataeng_engine,
    gov_engine,
)
from tooling.superversion.layer_tools.engines.base import (
    EngineAdapter,
    EngineContractError,
    EngineFinding,
    EngineReport,
    available,
    get,
    register,
    run,
)

__all__ = [
    "EngineAdapter", "EngineFinding", "EngineReport", "EngineContractError",
    "register", "get", "available", "run",
]
