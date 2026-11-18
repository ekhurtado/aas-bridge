"""Exception hierarchy shared by every AAS Bridge layer.

All errors raised by the library derive from :class:`AASBridgeError` so callers
(CLI, GUI, tests) can distinguish tool failures from unrelated exceptions.
Messages must state what failed, why, and what to do next.
"""


class AASBridgeError(Exception):
    """Base class for all AAS Bridge errors."""


class DetectionError(AASBridgeError):
    """The input cannot be read as an AASX package or its AAS version is undetectable."""


class MigrationError(AASBridgeError):
    """A migration cannot be planned or applied under the approved rules."""


class EvidenceGateError(AASBridgeError):
    """The evidence gate refused a migration (baseline mismatch or unverified dialect)."""


class ProbeError(AASBridgeError):
    """A basyx dialect probe or the venv swap failed."""


class IngestError(AASBridgeError):
    """A registry artifact cannot be ingested or verified."""
