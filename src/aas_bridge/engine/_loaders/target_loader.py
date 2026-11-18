"""Load an adapted package with the installed basyx, round-trip it and print metrics.

Run as ``python -m aas_bridge.engine._loaders.target_loader <package>``. It is
executed after the gate restored the target dialect (``~=2.2``). The output is
the target load metrics plus a ``round_trip`` object: the store is re-serialised
with ``write_aas_xml_file``, re-loaded with ``read_aas_xml_file(failsafe=False)``
and compared against the first load.
"""

from __future__ import annotations

import argparse
import io
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from basyx.aas.adapter.xml import read_aas_xml_file, write_aas_xml_file

from aas_bridge.engine._loaders.baseline_loader import (
    METRIC_KEYS,
    installed_basyx_version,
    load_store,
    metrics_from_store,
)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="target_loader",
        description="Load an adapted AASX package, round-trip it and print load metrics.",
    )
    parser.add_argument("package", type=Path, help="Adapted AASX package to load")
    args = parser.parse_args(argv)

    try:
        version = installed_basyx_version()
    except Exception as exc:  # subprocess boundary: report, never swallow
        print(f"target_loader: cannot read the basyx version ({exc})", file=sys.stderr)
        return 2

    try:
        object_store = load_store(args.package)
        metrics = metrics_from_store(object_store)
        if metrics["total"] == 0:
            print(
                f"target_loader: basyx {version} loaded 0 objects from {args.package}. "
                "The adapted package is not readable with the target dialect; the "
                "evidence gate must refuse it.",
                file=sys.stderr,
            )
            return 3

        buffer = io.BytesIO()
        write_aas_xml_file(buffer, object_store)
        buffer.seek(0)
        reloaded = read_aas_xml_file(buffer, failsafe=False)
        round_trip_metrics = metrics_from_store(reloaded)
    except Exception as exc:  # subprocess boundary: report, never swallow
        print(
            f"target_loader: failed to load {args.package} with basyx {version}: {exc}. "
            "The adapted package cannot be validated; the gate must refuse it.",
            file=sys.stderr,
        )
        return 2

    differences = [
        key
        for key in METRIC_KEYS
        if key != "basyx_version" and metrics[key] != round_trip_metrics[key]
    ]
    payload: dict[str, Any] = dict(metrics)
    payload["round_trip"] = {
        "ok": not differences,
        "differences": differences,
        "metrics": round_trip_metrics,
    }
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
