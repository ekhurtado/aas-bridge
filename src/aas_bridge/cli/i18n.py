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
    "migrate.report_write_failed": {
        "en": (
            "The report could not be written to {path} ({reason}). The gate result "
            "above is unchanged."
        ),
        "es": (
            "No se ha podido escribir el informe en {path} ({reason}). El resultado de "
            "la puerta anterior no cambia."
        ),
    },
    "migrate.no_output": {
        "en": "No output file was written.",
        "es": "No se ha escrito ningún fichero de salida.",
    },
    "error.unsupported_language": {
        "en": "Unsupported language {value!r}; choose one of: {supported}",
        "es": "Idioma no soportado {value!r}; elige uno de: {supported}",
    },
    "help.smia": {
        "en": "Show which AAS versions your SMIA release can read and what to do with a file.",
        "es": (
            "Muestra qué versiones de AAS puede leer tu versión de SMIA y qué hacer con un fichero."
        ),
    },
    "help.update": {
        "en": "Check the official AAS releases and fetch the pinned schema artifacts.",
        "es": "Comprueba las releases oficiales de AAS y descarga los esquemas fijados.",
    },
    "help.shell": {
        "en": "Open the interactive shell (same commands, session language).",
        "es": "Abre la consola interactiva (mismos comandos, idioma de sesión).",
    },
    "help.file_optional": {
        "en": "Optional AASX package to diagnose against your SMIA version.",
        "es": "Paquete AASX opcional para diagnosticar frente a tu versión de SMIA.",
    },
    "smia.title": {
        "en": "AAS Bridge — SMIA guidance",
        "es": "AAS Bridge — guía de SMIA",
    },
    "smia.version": {
        "en": "SMIA: {version}",
        "es": "SMIA: {version}",
    },
    "smia.version_unknown": {
        "en": "SMIA: version not provided",
        "es": "SMIA: versión no indicada",
    },
    "smia.status": {
        "en": "Status: {status}",
        "es": "Estado: {status}",
    },
    "smia.status_installed": {
        "en": "installed in this environment",
        "es": "instalada en este entorno",
    },
    "smia.status_registry": {
        "en": "verified registry table (2026-11-19)",
        "es": "tabla verificada del registro (2026-11-19)",
    },
    "smia.status_pypi": {
        "en": "PyPI release metadata",
        "es": "metadatos de la release en PyPI",
    },
    "smia.status_unverified": {
        "en": "unverified",
        "es": "sin verificar",
    },
    "smia.basyx_pin": {
        "en": "basyx pin: {pin}",
        "es": "pin de basyx: {pin}",
    },
    "smia.basyx_pin_unknown": {
        "en": "basyx pin: unknown",
        "es": "pin de basyx: desconocido",
    },
    "smia.reads": {
        "en": "Reads AAS: {labels}",
        "es": "Lee AAS: {labels}",
    },
    "smia.reads_unknown": {
        "en": "Reads AAS: unknown",
        "es": "Lee AAS: desconocido",
    },
    "smia.source": {
        "en": "Source: {note}",
        "es": "Fuente: {note}",
    },
    "smia.prompt": {
        "en": "Enter your SMIA version (e.g. 1.0.3), or press Enter to skip",
        "es": "Introduce tu versión de SMIA (p. ej. 1.0.3) o pulsa Enter para omitir",
    },
    "smia.unverified_hint": {
        "en": (
            "Cannot verify this SMIA version. Check SMIA's own documentation or run "
            "`pip show smia`."
        ),
        "es": (
            "No se puede verificar esta versión de SMIA. Consulta la documentación de SMIA "
            "o ejecuta `pip show smia`."
        ),
    },
    "smia.guide_title": {
        "en": "What you can do:",
        "es": "Qué puedes hacer:",
    },
    "smia.guide_check": {
        "en": "  - Diagnose a package: aas-bridge check <file>",
        "es": "  - Diagnostica un paquete: aas-bridge check <file>",
    },
    "smia.guide_migrate": {
        "en": "  - Upgrade AAS 3.0 → 3.1 with evidence: aas-bridge migrate <file>",
        "es": "  - Actualiza AAS 3.0 → 3.1 con evidencia: aas-bridge migrate <file>",
    },
    "smia.guide_downgrade": {
        "en": "  - Downgrade AAS 3.1 → 3.0: not available yet (Phase 2)",
        "es": "  - Conversión descendente AAS 3.1 → 3.0: aún no disponible (Fase 2)",
    },
    "smia.file": {
        "en": "File: {file}",
        "es": "Fichero: {file}",
    },
    "smia.detected": {
        "en": "Detected: AAS {version}",
        "es": "Detectado: AAS {version}",
    },
    "smia.detected_undetectable": {
        "en": "Detected: undetectable or inconsistent",
        "es": "Detectado: no detectable o incoherente",
    },
    "smia.verdict_compatible": {
        "en": "Verdict: compatible — nothing to do.",
        "es": "Veredicto: compatible — no hay nada que hacer.",
    },
    "smia.verdict_upgrade": {
        "en": (
            "Verdict: your SMIA reads AAS {labels}; run `aas-bridge migrate {file}` to "
            "upgrade this file."
        ),
        "es": (
            "Veredicto: tu SMIA lee AAS {labels}; ejecuta `aas-bridge migrate {file}` para "
            "actualizar este fichero."
        ),
    },
    "smia.verdict_downgrade": {
        "en": (
            "Verdict: downgrade V3.1→V3.0 is not available yet (Phase 2). Options: "
            "re-author the file with AASX Package Explorer v2024-06-10 or v2025-03-25 "
            "(they model AAS v3.0), or upgrade SMIA to basyx ~=2.2 (ADR-001, Track S1 — "
            "not yet done); after an SMIA upgrade, run `aas-bridge migrate` on your v3.0 "
            "files."
        ),
        "es": (
            "Veredicto: la conversión descendente V3.1→V3.0 aún no está disponible "
            "(Fase 2). Opciones: vuelve a generar el fichero con AASX Package Explorer "
            "v2024-06-10 o v2025-03-25 (modelan AAS v3.0), o actualiza SMIA a basyx "
            "~=2.2 (ADR-001, Track S1 — aún pendiente); tras actualizar SMIA, ejecuta "
            "`aas-bridge migrate` sobre tus ficheros v3.0."
        ),
    },
    "smia.verdict_incompatible": {
        "en": (
            "Verdict: incompatible — your SMIA reads AAS {labels} and this file is AAS {version}."
        ),
        "es": (
            "Veredicto: incompatible — tu SMIA lee AAS {labels} y este fichero es AAS {version}."
        ),
    },
    "smia.verdict_undetectable": {
        "en": (
            "Verdict: the AAS version cannot be determined; run `aas-bridge check {file}` "
            "for the per-part diagnosis."
        ),
        "es": (
            "Veredicto: no se puede determinar la versión de AAS; ejecuta "
            "`aas-bridge check {file}` para el diagnóstico por partes."
        ),
    },
    "smia.verdict_unverified": {
        "en": (
            "Verdict: the SMIA version is unverified, so the verdict cannot be computed. "
            "Check SMIA's installation and documentation."
        ),
        "es": (
            "Veredicto: la versión de SMIA no está verificada, así que no se puede "
            "calcular el veredicto. Revisa la instalación y la documentación de SMIA."
        ),
    },
    "update.title": {
        "en": "AAS Bridge — official AAS releases",
        "es": "AAS Bridge — releases oficiales de AAS",
    },
    "update.source": {
        "en": "Official source: {repo}",
        "es": "Fuente oficial: {repo}",
    },
    "update.status_online": {
        "en": "Status: online",
        "es": "Estado: en línea",
    },
    "update.status_offline": {
        "en": "Status: offline — degraded",
        "es": "Estado: sin conexión — degradado",
    },
    "update.offline_note": {
        "en": (
            "No network access to the official releases feed: {detail}. Rerun when "
            "online; the tool works offline with the pinned registry data."
        ),
        "es": (
            "Sin acceso a la red al feed oficial de releases: {detail}. Vuelve a "
            "ejecutar cuando haya conexión; la herramienta funciona sin conexión con "
            "los datos fijados del registro."
        ),
    },
    "update.covered": {
        "en": "Covered AAS versions: {labels}",
        "es": "Versiones de AAS cubiertas: {labels}",
    },
    "update.covered_pairs": {
        "en": "Covered migration pairs: {pairs}",
        "es": "Pares de migración cubiertos: {pairs}",
    },
    "update.known_uncovered": {
        "en": "Known but not covered: {labels}",
        "es": "Conocidas pero no cubiertas: {labels}",
    },
    "update.new_labels": {
        "en": "NEW AAS versions (ingest pending — Phase 4): {labels}",
        "es": "NUEVAS versiones de AAS (ingesta pendiente — Fase 4): {labels}",
    },
    "update.no_new": {
        "en": "NEW AAS versions: none",
        "es": "Nuevas versiones de AAS: ninguna",
    },
    "update.prereleases": {
        "en": "Prereleases seen (never reported as new): {tags}",
        "es": "Prerreleases vistas (nunca se notifican como nuevas): {tags}",
    },
    "update.artifacts_title": {
        "en": "Artifacts:",
        "es": "Artefactos:",
    },
    "update.artifact_line": {
        "en": "  [{status}] {label} {kind} -> {path}",
        "es": "  [{status}] {label} {kind} -> {path}",
    },
    "update.artifact_status_line": {
        "en": "  [{status}] {label} {kind}",
        "es": "  [{status}] {label} {kind}",
    },
    "update.label_failed": {
        "en": "Cannot fetch the AAS {label} artifacts: {detail}",
        "es": "No se pueden descargar los artefactos de AAS {label}: {detail}",
    },
    "update.registry_dir": {
        "en": "Registry directory: {path}",
        "es": "Directorio del registro: {path}",
    },
    "update.manifest": {
        "en": "Manifest: {path}",
        "es": "Manifiesto: {path}",
    },
    "update.manifest_error": {
        "en": (
            "Cannot write the manifest to {path} ({detail}). Check the directory "
            "permissions or set AASBRIDGE_REGISTRY_DIR."
        ),
        "es": (
            "No se puede escribir el manifiesto en {path} ({detail}). Revisa los permisos "
            "del directorio o define AASBRIDGE_REGISTRY_DIR."
        ),
    },
    "update.directory_error": {
        "en": (
            "Cannot create the registry directory {path} ({detail}). Set "
            "AASBRIDGE_REGISTRY_DIR to a writable directory."
        ),
        "es": (
            "No se puede crear el directorio del registro {path} ({detail}). Define "
            "AASBRIDGE_REGISTRY_DIR con un directorio escribible."
        ),
    },
    "update.no_rule_note": {
        "en": (
            "Fetched artifacts are knowledge only: no migration rule is created or "
            "activated (Phase 4)."
        ),
        "es": (
            "Los artefactos descargados son solo conocimiento: no se crea ni activa "
            "ninguna regla de migración (Fase 4)."
        ),
    },
    "update.status_fetched": {
        "en": "fetched",
        "es": "descargado",
    },
    "update.status_cached": {
        "en": "cached",
        "es": "en caché",
    },
    "update.status_failed": {
        "en": "failed",
        "es": "fallido",
    },
    "update.status_skipped_offline": {
        "en": "skipped (offline)",
        "es": "omitido (sin conexión)",
    },
    "repl.banner_title": {
        "en": "AAS Bridge {version} — AASX detection & migration (AAS 3.x)",
        "es": "AAS Bridge {version} — AASX detection & migration (AAS 3.x)",
    },
    "repl.banner_hint": {
        "en": "type 'help' for commands, 'exit' to leave",
        "es": "escribe 'help' para ver los comandos y 'exit' para salir",
    },
    "repl.unknown_command": {
        "en": "Unknown command: {command}. Type 'help' for the command list.",
        "es": "Comando desconocido: {command}. Escribe 'help' para ver la lista de comandos.",
    },
    "repl.parse_error": {
        "en": "Cannot parse the command line: {detail}",
        "es": "No se puede interpretar la línea de comandos: {detail}",
    },
    "repl.usage": {
        "en": "Usage: {usage}",
        "es": "Uso: {usage}",
    },
    "repl.usage_check": {
        "en": "check <file>",
        "es": "check <file>",
    },
    "repl.usage_migrate": {
        "en": "migrate <file> [--report <path>]",
        "es": "migrate <file> [--report <path>]",
    },
    "repl.usage_smia": {
        "en": "smia [file]",
        "es": "smia [file]",
    },
    "repl.usage_update": {
        "en": "update",
        "es": "update",
    },
    "repl.help_title": {
        "en": "Commands:",
        "es": "Comandos:",
    },
    "repl.help_check": {
        "en": "  check <file>                        diagnose an AASX package",
        "es": "  check <file>                        diagnostica un paquete AASX",
    },
    "repl.help_migrate": {
        "en": "  migrate <file> [--report <path>]    migrate with the evidence gate",
        "es": "  migrate <file> [--report <path>]    migra con la puerta de evidencia",
    },
    "repl.help_smia": {
        "en": "  smia [file]                         SMIA guidance and per-file verdict",
        "es": "  smia [file]                         guía de SMIA y veredicto por fichero",
    },
    "repl.help_update": {
        "en": "  update                              official release check + artifact fetch",
        "es": "  update                              comprobación oficial + descarga de artefactos",
    },
    "repl.help_lang": {
        "en": "  lang [en|es]                        show or change the session language",
        "es": "  lang [en|es]                        muestra o cambia el idioma de la sesión",
    },
    "repl.help_version": {
        "en": "  version                             show the tool version",
        "es": "  version                             muestra la versión de la herramienta",
    },
    "repl.help_help": {
        "en": "  help [command]                      show this help or one command usage",
        "es": "  help [command]                      muestra esta ayuda o el uso de un comando",
    },
    "repl.help_exit": {
        "en": "  exit | quit                         leave the shell",
        "es": "  exit | quit                         sale de la consola",
    },
    "repl.language_current": {
        "en": "Language: {language}",
        "es": "Idioma: {language}",
    },
    "repl.language_set": {
        "en": "Language set to {language}.",
        "es": "Idioma cambiado a {language}.",
    },
    "repl.language_invalid": {
        "en": "Unsupported language {value!r}; choose en or es.",
        "es": "Idioma no soportado {value!r}; elige en o es.",
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
