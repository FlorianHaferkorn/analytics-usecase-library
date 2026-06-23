"""Superversion target (stack) adapters (ADR-0006).

The contract lives in `base`; re-exported here so callers can
`from tooling.superversion.targets import register, render, TargetAdapter`.
Concrete adapters (TMDL I-3.2, PBIR I-3.3) register into `base.REGISTRY`.
"""
from tooling.superversion.targets.base import (
    REGISTRY,
    TargetAdapter,
    TargetContractError,
    TargetEmitter,
    available,
    get,
    register,
    render,
)

__all__ = [
    "TargetEmitter", "TargetAdapter", "TargetContractError",
    "REGISTRY", "register", "get", "available", "render",
]
