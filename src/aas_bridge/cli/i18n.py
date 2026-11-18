"""CLI message catalog (English and Spanish).

Every runtime message exists in both locales; a missing key raises immediately so
a partial catalog can never ship. AAS technical terms (``AASX``, ``namespace``,
``basyx``, ``AAS``) stay in English in both locales.

Typer's ``--help`` texts are resolved once at import time from the system
language, because Click renders help before a subcommand's ``--lang`` option is
parsed; they live here so both locales are complete and reviewable.
"""

from __future__ import annotations

import locale
import os

SUPPORTED_LANGUAGES = ("en", "es")
DEFAULT_LANGUAGE = "en"

MESSAGES: dict[str, dict[str, str]] = {
    "app.help": {
        "en": "AAS Bridge: diagnose and migrate AASX packages across AAS metamodel versions.",
        "es": "AAS Bridge: diagnostica y migra paquetes AASX entre versiones del metamodelo AAS.",
    },
    "help.check": {
        "en": "Inspect an AASX package and show the detected version and the available migration.",
        "es": (
            "Inspecciona un paquete AASX y muestra la versión detectada y la migración disponible."
        ),
    },
    "help.migrate": {
        "en": "Migrate an AAS 3.0 package to AAS 3.1 through the evidence gate.",
        "es": "Migra un paquete AAS 3.0 a AAS 3.1 con la puerta de evidencia.",
    },
    "help.file": {
        "en": "AASX package to process.",
        "es": "Paquete AASX a procesar.",
    },
    "help.lang": {
        "en": "Output language: en or es.",
        "es": "Idioma de salida: en o es.",
    },
    "help.report": {
        "en": "Write the JSON migration report to this path.",
        "es": "Escribe el informe JSON de migración en esta ruta.",
    },
    "help.version": {
        "en": "Show the version and exit.",
        "es": "Muestra la versión y termina.",
    },
    "version": {
        "en": "aas-bridge {version}",
        "es": "aas-bridge {version}",
    },
    "error.file_not_found": {
        "en": "File not found: {path}. Check the path and try again.",
        "es": "No se encuentra el fichero: {path}. Revisa la ruta e inténtalo de nuevo.",
    },
    "error.detection": {
        "en": "Cannot read the package: {detail}",
        "es": "No se puede leer el paquete: {detail}",
    },
    "error.migration": {
        "en": "Migration refused: {detail}",
        "es": "Migración rechazada: {detail}",
    },
    "error.gate": {
        "en": "Evidence gate failed: {detail}",
        "es": "La puerta de evidencia ha fallado: {detail}",
    },
    "error.probe": {
        "en": "Basyx dialect handling failed: {detail}",
        "es": "Fallo al manejar la versión de basyx: {detail}",
    },
    "error.unexpected": {
        "en": "Internal error: {detail}. Check the log for details.",
        "es": "Error interno: {detail}. Revisa el registro para más detalles.",
    },
    "check.title": {
        "en": "AAS Bridge — package diagnosis",
        "es": "AAS Bridge — diagnóstico del paquete",
    },
    "check.file": {
        "en": "File: {file}",
        "es": "Fichero: {file}",
    },
    "check.detected": {
        "en": "Detected: AAS {version}",
        "es": "Detectado: AAS {version}",
    },
    "check.detected_undetectable": {
        "en": "undetectable",
        "es": "no detectable",
    },
    "check.parts": {
        "en": "AAS parts: {count}",
        "es": "Partes AAS: {count}",
    },
    "check.part_line": {
        "en": "  - {part} ({format}, {version})",
        "es": "  - {part} ({format}, {version})",
    },
    "check.target": {
        "en": "Target: AAS {version}",
        "es": "Objetivo: AAS {version}",
    },
    "check.upgrade_available": {
        "en": "Upgrade available: yes (namespace relabel 3/0 → 3/1)",
        "es": "Actualización disponible: sí (cambio de namespace 3/0 → 3/1)",
    },
    "check.already_target": {
        "en": "Already AAS {version} — no migration needed",
        "es": "Ya es AAS {version} — no se necesita migración",
    },
    "check.json_detect_only": {
        "en": (
            "JSON AAS part detected: JSON migration is not available in this release (detect-only)."
        ),
        "es": (
            "Parte JSON detectada: la migración JSON no está disponible en esta "
            "versión (solo detección)."
        ),
    },
    "check.inconsistent": {
        "en": ("Undetectable or inconsistent version: {details}. No migration can be planned."),
        "es": (
            "Versión no detectable o incoherente: {details}. No se puede planificar una migración."
        ),
    },
    "migrate.title": {
        "en": "AAS Bridge — migration",
        "es": "AAS Bridge — migración",
    },
    "migrate.status_emitted": {
        "en": "Status: migrated (evidence gate passed)",
        "es": "Estado: migrado (puerta de evidencia superada)",
    },
    "migrate.status_no_migration": {
        "en": "Status: already AAS {version} — no migration needed",
        "es": "Estado: ya es AAS {version} — no se necesita migración",
    },
    "migrate.source": {
        "en": "Source: {file}",
        "es": "Origen: {file}",
    },
    "migrate.baseline": {
        "en": (
            "Baseline: {total} objects ({aas} AAS / {submodels} SM / {cd} CD) with basyx {version}"
        ),
        "es": "Base: {total} objetos ({aas} AAS / {submodels} SM / {cd} CD) con basyx {version}",
    },
    "migrate.target": {
        "en": "Target: {total} objects ({aas} AAS / {submodels} SM / {cd} CD) with basyx {version}",
        "es": (
            "Objetivo: {total} objetos ({aas} AAS / {submodels} SM / {cd} CD) con basyx {version}"
        ),
    },
    "migrate.rules": {
        "en": "Rules applied: {rules}",
        "es": "Reglas aplicadas: {rules}",
    },
    "migrate.gate": {
        "en": "Gate: {result} (round-trip {round_trip})",
        "es": "Puerta: {result} (ida y vuelta {round_trip})",
    },
    "migrate.gate_pass": {
        "en": "PASS",
        "es": "SUPERADA",
    },
    "migrate.gate_fail": {
        "en": "FAIL",
        "es": "FALLIDA",
    },
    "migrate.round_trip_ok": {
        "en": "OK",
        "es": "correcta",
    },
    "migrate.round_trip_failed": {
        "en": "FAILED",
        "es": "fallida",
    },
    "migrate.output": {
        "en": "Output: {path}",
        "es": "Salida: {path}",
    },
    "migrate.report_written": {
        "en": "Report: {path}",
        "es": "Informe: {path}",
    },
    "migrate.no_output": {
        "en": "No output file was written.",
        "es": "No se ha escrito ningún fichero de salida.",
    },
}


def translate(key: str, lang: str, **parameters: object) -> str:
    """Return the localized message ``key`` formatted with ``parameters``."""
    if lang not in SUPPORTED_LANGUAGES:
        raise ValueError(
            f"Unsupported language {lang!r}; supported: {', '.join(SUPPORTED_LANGUAGES)}"
        )
    try:
        template = MESSAGES[key][lang]
    except KeyError as exc:
        raise KeyError(f"Missing i18n message {key!r} for language {lang!r}") from exc
    return template.format(**parameters)


def default_language() -> str:
    """Return ``es`` when the system locale or environment is Spanish, else ``en``."""
    for variable in ("LC_ALL", "LC_MESSAGES", "LANG"):
        value = os.environ.get(variable)
        if value:
            return "es" if value.lower().startswith("es") else DEFAULT_LANGUAGE
    try:
        system_locale = locale.getlocale()[0] or ""
    except ValueError:
        system_locale = ""
    return "es" if system_locale.lower().startswith("es") else DEFAULT_LANGUAGE
