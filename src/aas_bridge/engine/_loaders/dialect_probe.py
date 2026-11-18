"""Report the installed basyx version and the target dialect it implements.

Run as ``python -m aas_bridge.engine._loaders.dialect_probe``. The module prints
one JSON object to stdout and exits non-zero with an actionable message on
stderr. This is the only place where the target namespace is obtained: the main
process never imports basyx and never hardcodes ``NS_AAS``.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import sys
from collections.abc import Sequence


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="dialect_probe",
        description="Print the installed basyx version and its AAS XML namespace.",
    )
    parser.parse_args(argv)
    try:
        from basyx.aas.adapter.xml.xml_serialization import NS_AAS

        version = importlib.metadata.version("basyx-python-sdk")
    except Exception as exc:  # subprocess boundary: report, never swallow
        print(
            f"dialect_probe: cannot import basyx or read its version ({exc}). "
            "Install the target dialect with: python -m pip install "
            '"basyx-python-sdk~=2.2"',
            file=sys.stderr,
        )
        return 2
    payload = {
        "basyx_version": version,
        "ns_aas": NS_AAS,
        "ns_aas_iri": NS_AAS.strip("{}"),
    }
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
