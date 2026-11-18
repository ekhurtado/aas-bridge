"""Load an AASX package with the installed basyx and print baseline metrics.

Run as ``python -m aas_bridge.engine._loaders.baseline_loader <package>``. It is
executed only after the gate installed the source dialect (``==2.0.1``); the
module must work against both basyx 2.0.1 and 2.2.x, so it avoids APIs that only
exist in one of them.

A load of 0 objects is a gate failure: it is exactly the silent-empty-store
failure mode this tool exists to expose (`.ai/ECOSYSTEM_COMPATIBILITY.md` §4.2).
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import sys
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any

from basyx.aas import model
from basyx.aas.adapter.aasx import AASXReader, DictSupplementaryFileContainer

METRIC_KEYS = (
    "basyx_version",
    "total",
    "counts",
    "ids_sha256",
    "semantic_ids_sha256",
)


def installed_basyx_version() -> str:
    """Return the installed distribution version (basyx exposes no top-level ``__version__``)."""
    return importlib.metadata.version("basyx-python-sdk")


def new_object_store() -> model.AbstractObjectStore:
    """Create an object store that exists in every supported basyx version."""
    if hasattr(model, "DictIdentifiableStore"):
        return model.DictIdentifiableStore()
    return model.DictObjectStore()


def load_store(package: Path) -> model.AbstractObjectStore:
    """Load an AASX package with ``failsafe=False`` so dialect errors surface."""
    object_store = new_object_store()
    file_store = DictSupplementaryFileContainer()
    with AASXReader(package, failsafe=False) as reader:
        reader.read_into(object_store, file_store)
    return object_store


def metrics_from_store(object_store: model.AbstractObjectStore) -> dict[str, Any]:
    """Return the deterministic load metrics used by the evidence gate."""
    objects = list(object_store)
    counts = {"aas": 0, "submodels": 0, "concept_descriptions": 0}
    identifiers: list[str] = []
    semantic_ids: list[str] = []
    for obj in objects:
        identifiers.append(obj.id)
        if isinstance(obj, model.AssetAdministrationShell):
            counts["aas"] += 1
        elif isinstance(obj, model.Submodel):
            counts["submodels"] += 1
            if obj.semantic_id is not None:
                semantic_ids.append(_reference_key(obj.semantic_id))
            for element in _iter_elements(obj.submodel_element):
                if element.semantic_id is not None:
                    semantic_ids.append(_reference_key(element.semantic_id))
        elif isinstance(obj, model.ConceptDescription):
            counts["concept_descriptions"] += 1
        else:
            raise TypeError(
                f"Unexpected object type {type(obj).__name__} in the basyx object store"
            )
    return {
        "basyx_version": installed_basyx_version(),
        "total": len(objects),
        "counts": counts,
        "ids_sha256": _sha256_lines(identifiers),
        "semantic_ids_sha256": _sha256_lines(semantic_ids),
    }


def _iter_elements(elements: Iterable[model.SubmodelElement]) -> Iterable[model.SubmodelElement]:
    for element in elements:
        yield element
        if isinstance(element, (model.SubmodelElementCollection, model.SubmodelElementList)):
            yield from _iter_elements(element.value or ())
        elif isinstance(element, model.Entity):
            yield from _iter_elements(element.statement or ())
        elif isinstance(element, model.AnnotatedRelationshipElement):
            yield from _iter_elements(getattr(element, "annotation", ()) or ())
        elif isinstance(element, model.Operation):
            for attribute in ("input_variable", "output_variable", "in_output_variable"):
                for variable in getattr(element, attribute, ()) or ():
                    value = getattr(variable, "value", variable)
                    if isinstance(value, model.SubmodelElement):
                        yield from _iter_elements([value])


def _reference_key(reference: model.Reference) -> str:
    return "|".join(f"{key.type.name}:{key.value}" for key in reference.key)


def _sha256_lines(values: list[str]) -> str:
    payload = "\n".join(sorted(values)).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="baseline_loader",
        description="Load an AASX package with the installed basyx and print load metrics.",
    )
    parser.add_argument("package", type=Path, help="AASX package to load")
    args = parser.parse_args(argv)

    try:
        version = installed_basyx_version()
    except Exception as exc:  # subprocess boundary: report, never swallow
        print(f"baseline_loader: cannot read the basyx version ({exc})", file=sys.stderr)
        return 2

    try:
        metrics = metrics_from_store(load_store(args.package))
    except Exception as exc:  # subprocess boundary: report, never swallow
        print(
            f"baseline_loader: failed to load {args.package} with basyx {version}: {exc}. "
            "Check that the file matches the dialect of the installed basyx.",
            file=sys.stderr,
        )
        return 2

    if metrics["total"] == 0:
        print(
            f"baseline_loader: basyx {version} loaded 0 objects from {args.package}. "
            "This is the silent-empty-store failure mode: the package dialect does "
            "not match the installed basyx, so no baseline can be trusted.",
            file=sys.stderr,
        )
        return 3

    print(json.dumps(metrics, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
