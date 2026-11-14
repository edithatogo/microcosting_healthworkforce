# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Compatibility imports for the former generic src package.

New integrations import microcosting_healthworkforce. Legacy submodule imports
resolve to the same objects, preserving models and pickle identities. This shim
cannot resolve another package also named src; use the canonical namespace in
shared environments.
"""

import sys
from importlib import import_module
from importlib.abc import InspectLoader, MetaPathFinder
from importlib.util import find_spec, spec_from_loader
from typing import override
lazy from collections.abc import Sequence
lazy from importlib.machinery import ModuleSpec
lazy from types import CodeType, ModuleType

_PREFIX = "microcosting_healthworkforce."


class _LegacyLoader(InspectLoader):
    """Load a legacy spelling as an alias of one canonical Python module."""

    def __init__(self, canonical: str) -> None:
        self.canonical = canonical
        self.canonical_spec: ModuleSpec | None = None

    @override
    def create_module(self, spec: ModuleSpec) -> ModuleType:
        """Preserve module and model identity for either import order."""
        del spec
        module = import_module(self.canonical)
        self.canonical_spec = module.__spec__
        return module

    @override
    def exec_module(self, module: ModuleType) -> None:
        """Restore canonical introspection after importlib creates the alias."""
        module.__spec__ = self.canonical_spec

    @override
    def get_source(self, fullname: str) -> str | None:
        """Support explicit historical python -m src.module commands."""
        del fullname
        spec = find_spec(self.canonical)
        if spec is None or not isinstance(spec.loader, InspectLoader):
            message = "No inspectable canonical workforce module"
            raise ImportError(message)
        return spec.loader.get_source(self.canonical)

    @override
    def get_code(self, fullname: str) -> CodeType | None:
        """Keep legacy module execution separate from importing an alias."""
        del fullname
        spec = find_spec(self.canonical)
        if spec is None or not isinstance(spec.loader, InspectLoader):
            message = "No inspectable canonical workforce module"
            raise ImportError(message)
        return spec.loader.get_code(self.canonical)


class _LegacyFinder(MetaPathFinder):
    """Resolve only children of this compatibility package."""

    @override
    def find_spec(
        self,
        fullname: str,
        path: Sequence[str] | None = None,
        target: ModuleType | None = None,
    ) -> ModuleSpec | None:
        """Leave unrelated imports to the existing Python import machinery."""
        del path, target
        if not fullname.startswith("src.") or fullname.count(".") != 1:
            return None
        canonical = _PREFIX + fullname.removeprefix("src.")
        if find_spec(canonical) is None:
            return None
        return spec_from_loader(fullname, _LegacyLoader(canonical))


sys.meta_path.insert(0, _LegacyFinder())
