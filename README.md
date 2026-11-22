<div align="center">

<!-- Theme-specific banners: light and dark. -->
<img src="images/AAS_bridge_logo_light.jpg#gh-light-mode-only" alt="AAS Bridge logo" width="100%">
<img src="images/AAS_bridge_logo_dark.jpg#gh-dark-mode-only" alt="AAS Bridge logo" width="100%">

<h1>AAS Bridge</h1>

<p><strong>Migrate AASX packages across AAS metamodel versions — and prove nothing was lost.</strong></p>

<p>
  <img alt="Version 0.2.0" src="https://img.shields.io/badge/version-0.2.0-blue?style=flat-square">
  <img alt="Python 3.11+" src="https://img.shields.io/badge/python-3.11%2B-blue?style=flat-square">
  <a href="LICENSE"><img alt="Licence: GPL-3.0" src="https://img.shields.io/badge/licence-GPL--3.0--only-lightgrey?style=flat-square"></a>
  <img alt="Status: alpha" src="https://img.shields.io/badge/status-alpha-orange?style=flat-square">
  <img alt="CLI languages: English and Spanish" src="https://img.shields.io/badge/CLI-EN%20%7C%20ES-green?style=flat-square">
</p>

<p>
  <a href="#quick-start">Quick start</a> ·
  <a href="#commands">Commands</a> ·
  <a href="#the-evidence-gate">Evidence gate</a> ·
  <a href="#compatibility">Compatibility</a> ·
  <a href="#ecosystem-awareness">Ecosystem</a> ·

[//]: # (  <a href="#roadmap">Roadmap</a> ·)

  <a href="#contributing">Contributing</a>
</p>

<p><strong>English</strong> · <a href="README.es.md">Español</a></p>

</div>

AAS Bridge is a command-line tool for the **Asset Administration Shell (AAS)**. It
targets a silent failure: an **AASX** package authored for one metamodel version can
load as an empty object store when read by a different generation of the Eclipse
BaSyx SDK, without raising. AAS Bridge names the mismatch, applies only an approved
transformation, and refuses to emit a file it cannot prove.

**Detect** the version · **Diagnose** the toolchain · **Migrate** with one approved rule · **Prove** the result.

> **Status:** `0.2.0` alpha. The headless core and CLI are shipped; the local GUI,
> downgrade path and version-ingest pipeline are on the [roadmap](#roadmap).

New to AAS? Start with the [IDTA AAS metamodel](https://github.com/admin-shell-io/aas-specs-metamodel)
and the [Eclipse BaSyx Python SDK](https://github.com/eclipse-basyx/basyx-python-sdk).

**SMIA** (Self-configurable Manufacturing Industrial Agents) is an open-source,
AAS-compliant, agent-based digital twin for manufacturing. AAS Bridge provides support for SMIA. For more information about this software, see the
[SMIA documentation](https://smia.readthedocs.io/).

[//]: # (Las secciones comentadas no se consideran actualmente imprescindibles en el README, y se quiere dejar un fichero simple y claro, para que sea mas atractivo. Sin embargo, para no perder el contenido, no se han eliminado, si no solamente comentado)

## Quick start

### Requirements

- Python 3.11 or newer.
- `git` and `pip`.
- Network access may be needed the first time you migrate a new package: the gate
  installs the source-dialect BaSyx SDK to build the baseline. Baselines are cached,
  so repeat migrations of the same package are offline.

> [!IMPORTANT]
> Use a dedicated virtual environment. The evidence gate temporarily swaps
> `basyx-python-sdk` in the active environment to load the source dialect, then
> restores `basyx-python-sdk~=2.2`.

### Install from source

AAS Bridge is not published on PyPI yet. Install it from a clone:

<!-- Replace OWNER/REPO with the public repository slug before publishing. -->
```bash
git clone https://github.com/OWNER/REPO.git aas-bridge
cd aas-bridge
python -m venv .venv
```

Activate the environment:

```bash
# macOS / Linux
source .venv/bin/activate
```

```powershell
# Windows (PowerShell)
.venv\Scripts\Activate.ps1
```

Then install and check the version:

```bash
pip install .
aas-bridge --version
```

Expected: `aas-bridge 0.2.0`.

### Diagnose a package

```bash
aas-bridge check path/to/your-package.aasx
```

### Migrate it

```bash
aas-bridge migrate path/to/your-package.aasx --report path/to/report.json
```

The adapted package is written next to the input as `your-package-adapted.aasx`.
The input file is never modified.

### What happens to your file

| Situation | Result |
|---|---|
| AAS 3.0 XML package | Migrated and written as `<name>-adapted.aasx` |
| Already AAS 3.1 | No output file, no gate run, exit `0` |
| JSON AAS parts | Detected, but `migrate` refuses them (exit `1`) |
| Evidence gate failure | No output file; exit `3` |
| Undetectable or inconsistent version | Refused with an explanation; exit `1` |

> [!NOTE]
> The first migration of a new package may need network access. The baseline is
> cached under `AASBRIDGE_CACHE_DIR`; repeat runs of the same package are offline.

[//]: # (## See it in action)

[//]: # ()
[//]: # (```console)

[//]: # ($ mkdir work)

[//]: # ($ cp aas_v3-0/CeDRI_PunchingMachine_instanceA.aasx work/)

[//]: # ($ aas-bridge check work/CeDRI_PunchingMachine_instanceA.aasx --lang en)

[//]: # (AAS Bridge — package diagnosis)

[//]: # (File: work/CeDRI_PunchingMachine_instanceA.aasx)

[//]: # (Detected: AAS 3.0)

[//]: # (AAS parts: 1)

[//]: # (  - /aasx/IndustrialRobot_ABB_CeDRI/IndustrialRobot_ABB_CeDRI.aas.xml &#40;xml, https://admin-shell.io/aas/3/0&#41;)

[//]: # (Target: AAS 3.1)

[//]: # (Upgrade available: yes &#40;namespace relabel 3/0 → 3/1&#41;)

[//]: # ()
[//]: # ($ aas-bridge migrate work/CeDRI_PunchingMachine_instanceA.aasx --report work/machine.report.json --lang en)

[//]: # (AAS Bridge — migration)

[//]: # (Status: migrated &#40;evidence gate passed&#41;)

[//]: # (Source: work/CeDRI_PunchingMachine_instanceA.aasx)

[//]: # (Baseline: 22 objects &#40;1 AAS / 6 SM / 15 CD&#41; with basyx 2.0.1)

[//]: # (Target: 22 objects &#40;1 AAS / 6 SM / 15 CD&#41; with basyx 2.2.0)

[//]: # (Rules applied: v3_0_to_v3_1/namespace-relabel)

[//]: # (Gate: PASS &#40;round-trip OK&#41;)

[//]: # (Output: work/CeDRI_PunchingMachine_instanceA-adapted.aasx)

[//]: # (Report: work/machine.report.json)

[//]: # (```)

[//]: # ()
[//]: # (The example uses the bundled corpus. The corpus is read-only: copy a package to a)

[//]: # (working directory before migrating it &#40;on Windows PowerShell, use `Copy-Item`)

[//]: # (instead of `cp`&#41;.)

## Why AAS Bridge

### The failure is silent

`basyx-python-sdk` matches a single AAS namespace. It does not negotiate versions.
When a package declares a different one, the loader logs a namespace error and
returns an **empty object store** — without raising. In a pipeline, that looks like
a valid empty model; in SMIA, it surfaces as a generic model error that never
mentions the version.

That is the failure AAS Bridge exists to prevent. It makes the mismatch explicit
and gives you a file the target toolchain can actually read, with evidence that the
model survived.

### What you can rely on

| Principle | What it means in practice |
|---|---|
| **Evidence over trust** | The original and the adapted file are loaded with their respective BaSyx dialects; object counts, identifiers and semanticIds must match, and the result must survive a round-trip. |
| **Byte-preserving** | Only namespace declarations change. The OPC/ZIP rebuild copies every untouched part byte-for-byte: OWL ontologies, BPMN diagrams, properties, thumbnails, relationships and content types. |
| **Fail-closed** | Unknown version, JSON payload, unapproved rule, empty baseline or failed gate → refuse and explain. No partial output. |
| **Input is never modified** | The tool operates on a copy and writes a new `<name>-adapted.aasx` next to it. |
| **Offline-first** | `check`, `migrate` with cached baselines, installed-SMIA guidance and the shell work offline. Online features degrade visibly, never silently. |
| **basyx is the only validator** | AAS Bridge learns no metamodel of its own; the installed target-dialect SDK decides what is valid. |

**Who it's for:** SMIA users, AAS integrators maintaining mixed-version factories,
and toolchain authors who need auditable conversions.

**Not a generic converter:** AAS Bridge is a per-pair, human-approved rule engine.
AAS 2.0 ↔ 3.x and sub-version conversions are out of scope (see
[Compatibility](#compatibility)).

## Commands

| Command | What it does | Network |
|---|---|---|
| `aas-bridge check <file>` | Names the AAS version, lists the AAS parts and says whether a migration is available. | No |
| `aas-bridge migrate <file>` | Runs the evidence-gated AAS 3.0 → 3.1 migration and writes `<name>-adapted.aasx`. | First run per package |
| `aas-bridge smia [file]` | Resolves the SMIA release you run and gives an honest per-file verdict. Never writes files. | Optional |
| `aas-bridge update` | Checks official IDTA releases and fetches pinned artifacts with a hash manifest. | Optional |
| `aas-bridge` / `aas-bridge shell` | Opens the interactive shell. | No |

Flags:

| Flag | Applies to | Meaning |
|---|---|---|
| `--lang {en,es}` | `check`, `migrate`, `smia`, `update` | Output language; defaults to the system locale when it is English or Spanish, otherwise English. |
| `--report <path>` | `migrate` | Writes the deterministic JSON migration report. |
| `--version` | Global | Prints `aas-bridge <version>` and exits. |

[//]: # (### Exit codes)

[//]: # ()
[//]: # (| Code | Meaning |)

[//]: # (|---|---|)

[//]: # (| `0` | Success, including "already AAS 3.1 — no migration needed" and the offline `update` state |)

[//]: # (| `1` | User/input error: missing file, not an AASX, undetectable version, JSON parts |)

[//]: # (| `2` | Usage error |)

[//]: # (| `3` | Evidence-gate failure |)

[//]: # (| `4` | Internal error |)

[//]: # ()
[//]: # (`smia` exits `0` whenever it produces a diagnosis, including the visible `unverified`)

[//]: # (state, and `1` only for a missing or undetectable file. `update` exits `0` when it)

[//]: # (ran, including the degraded offline state; check and fetch failures are per-item)

[//]: # (statuses, not process failures. `check` exits `0` whenever it can report a version,)

[//]: # (including JSON packages with a detect-only note; `migrate` exits `1` for JSON parts.)

[//]: # (The shell always exits `0` on `exit`/`quit`, EOF or Ctrl+C; command failures print an)

[//]: # (error and the loop continues.)

### Examples

```bash
aas-bridge check machine.aasx --lang es
aas-bridge migrate machine.aasx --report reports/machine.json
aas-bridge smia machine.aasx
aas-bridge update
```

<details>
<summary>Interactive shell</summary>

Bare `aas-bridge` (or `aas-bridge shell`) opens a standard-library shell — no extra
dependency. The bilingual banner is shown only on entry; the prompt is
`aas-bridge> `.

```text
check <file>                        diagnose an AASX package
migrate <file> [--report <path>]    migrate with the evidence gate
smia [file]                         SMIA guidance and per-file verdict
update                              official release check + artifact fetch
lang [en|es]                        show or change the session language
version                             show the tool version
help [command]                      show the help
exit | quit                         leave the shell
```

Quote paths that contain spaces (`migrate "C:\dir with space\f.aasx"`); Windows
backslashes are preserved. A failing command prints its error and the shell keeps
running.

</details>

<details>
<summary>Environment and data directories</summary>

| Variable | Default |
|---|---|
| `AASBRIDGE_CACHE_DIR` | `%LOCALAPPDATA%\aasbridge\cache` on Windows; `~/.cache/aasbridge` elsewhere |
| `AASBRIDGE_REGISTRY_DIR` | `%LOCALAPPDATA%\aasbridge\registry` on Windows; `~/.local/share/aasbridge/registry` elsewhere |

The cache holds the gate baselines; the registry holds the official artifacts
fetched by `update`.

</details>

[//]: # (## The evidence gate)

[//]: # ()
[//]: # (A migration is a claim. The gate is how AAS Bridge proves it.)

[//]: # ()
[//]: # (```mermaid)

[//]: # (flowchart LR)

[//]: # (    A["AASX 3.0 input"] --> B["Detect namespace"])

[//]: # (    B --> C["Baseline load<br/>basyx 2.0.1"])

[//]: # (    C --> D["Approved rule<br/>namespace relabel"])

[//]: # (    D --> E["OPC/ZIP rebuild<br/>byte-preserving"])

[//]: # (    E --> F["Target load<br/>basyx 2.2"])

[//]: # (    F --> G{"Counts, IDs,<br/>semanticIds match?"})

[//]: # (    G -->|yes| H["Round-trip<br/>re-read"])

[//]: # (    H -->|ok| I["Emit<br/>-adapted.aasx"])

[//]: # (    G -->|no| J["Refuse<br/>exit 3"])

[//]: # (    H -->|no| J)

[//]: # (```)

[//]: # ()
[//]: # (For every AAS 3.0 → 3.1 migration, AAS Bridge:)

[//]: # ()
[//]: # (1. loads the original with the source dialect &#40;`basyx-python-sdk==2.0.1`&#41; and records)

[//]: # (   the object counts &#40;AAS / Submodels / ConceptDescriptions&#41;, a hash of the sorted)

[//]: # (   identifiers and a hash of the sorted semanticIds. A baseline of zero objects is a)

[//]: # (   failure, never a success;)

[//]: # (2. applies only the approved rule &#40;`v3_0_to_v3_1/namespace-relabel`&#41; and rebuilds)

[//]: # (   the OPC/ZIP package, copying every untouched part byte-for-byte;)

[//]: # (3. loads the adapted package with the target dialect &#40;`basyx-python-sdk~=2.2`&#41; and)

[//]: # (   verifies that the installed SDK reports the target namespace;)

[//]: # (4. re-serialises and re-loads the object store as a round-trip check;)

[//]: # (5. emits the adapted file only when the target reproduces the baseline and the)

[//]: # (   round-trip succeeds. Otherwise the file is removed and the command exits `3`.)

[//]: # ()
[//]: # (> [!WARNING])

[//]: # (> If any check fails, the adapted file is removed and the command exits with code)

[//]: # (> `3`. There is no partial output.)

[//]: # ()
[//]: # (<details>)

[//]: # (<summary>How the dialect swap works</summary>)

[//]: # ()
[//]: # (The gate swaps `basyx-python-sdk` in the project virtual environment and runs every)

[//]: # (BaSyx load in a subprocess. The main process never imports the SDK, so it cannot)

[//]: # (keep a stale version in `sys.modules`. The environment is always restored to)

[//]: # (`basyx-python-sdk~=2.2` in a `finally` block. Gate executions are serialized with a)

[//]: # (lock file and baselines are cached by file hash and dialect requirement under)

[//]: # (`AASBRIDGE_CACHE_DIR`.)

[//]: # ()
[//]: # (</details>)

[//]: # ()
[//]: # (<details>)

[//]: # (<summary>Report schema &#40;trimmed example&#41;</summary>)

[//]: # ()
[//]: # (`migrate --report <path>` writes a deterministic JSON report with)

[//]: # (`schema_version: 1`: fixed key order, ISO 8601 timestamps and no NaN/Infinity.)

[//]: # ()
[//]: # (```json)

[//]: # ({)

[//]: # (  "schema_version": 1,)

[//]: # (  "tool_version": "0.2.0",)

[//]: # (  "generated_at": "2026-11-21T12:04:38+00:00",)

[//]: # (  "source": {)

[//]: # (    "file": "machine.aasx",)

[//]: # (    "sha256": "6045f61c…")

[//]: # (  },)

[//]: # (  "detected": {)

[//]: # (    "version_label": "3.0",)

[//]: # (    "consistent": true,)

[//]: # (    "parts": [)

[//]: # (      {)

[//]: # (        "part_name": "/aasx/…/data.xml",)

[//]: # (        "format": "xml",)

[//]: # (        "declared_version": "https://admin-shell.io/aas/3/0",)

[//]: # (        "version_label": "3.0")

[//]: # (      })

[//]: # (    ])

[//]: # (  },)

[//]: # (  "target": {)

[//]: # (    "version_label": "3.1",)

[//]: # (    "namespace": "https://admin-shell.io/aas/3/1",)

[//]: # (    "basyx_version": "2.2.0")

[//]: # (  },)

[//]: # (  "rules_applied": ["v3_0_to_v3_1/namespace-relabel"],)

[//]: # (  "baseline": {)

[//]: # (    "basyx_version": "2.0.1",)

[//]: # (    "total": 22,)

[//]: # (    "counts": {"aas": 1, "submodels": 6, "concept_descriptions": 15},)

[//]: # (    "ids_sha256": "e8d964b3…",)

[//]: # (    "semantic_ids_sha256": "3ab2ff66…")

[//]: # (  },)

[//]: # (  "gate": {)

[//]: # (    "result": "pass",)

[//]: # (    "target": {)

[//]: # (      "basyx_version": "2.2.0",)

[//]: # (      "total": 22,)

[//]: # (      "counts": {"aas": 1, "submodels": 6, "concept_descriptions": 15},)

[//]: # (      "ids_sha256": "e8d964b3…",)

[//]: # (      "semantic_ids_sha256": "3ab2ff66…")

[//]: # (    },)

[//]: # (    "round_trip": true,)

[//]: # (    "message": null)

[//]: # (  },)

[//]: # (  "outcome": {)

[//]: # (    "status": "emitted",)

[//]: # (    "output_file": "machine-adapted.aasx")

[//]: # (  })

[//]: # (})

[//]: # (```)

[//]: # ()
[//]: # (</details>)

## Compatibility

### AAS versions

| Input | Result | Status       |
|---|---|--------------|
| AAS 3.0 XML | Migrates to AAS 3.1 through the evidence gate | Shipped      |
| AAS 3.1 XML | No-op: no output file, exit `0` | Shipped      |
| JSON AAS parts | Detected via a top-level `@context`; migration refused | Detect-only  |
| AAS 3.1 → 3.0 | Document-aware, plan-then-execute | Planned      |
| AAS 3.0.x → 3.0.y | Same namespace; no operational meaning | Out of scope |
| AAS 2.0 ↔ 3.x | Structural rework; use an interactive editor | Out of scope |

> [!NOTE]
> JSON detection is best-effort: BaSyx-written JSON carries no version marker, so a
> missing `@context` is reported as undetectable.

### Toolchain matrix

| `basyx-python-sdk` | Implements | Reads AAS 3.0 | Reads AAS 3.1 |
|---|---|---|---|
| 1.x / 2.0.x | AAS 3.0 | Yes | No — empty object store |
| 2.1+ / 2.2 | AAS 3.1 | No — empty object store | Yes |

The empty-store cells are the failure AAS Bridge exists to prevent. The installed
SDK is the only validator; AAS Bridge does not reimplement the metamodel.

### Out of scope

- AAS 2.0 ↔ 3.x: structural rework, left to interactive tools such as AASX Package
  Explorer.
- Sub-version conversions (for example 3.0.1 → 3.0.2): they share a namespace and
  have no operational meaning.
- A generic any-version converter: rules are per pair, human-approved and
  composable.

## Ecosystem awareness

AAS Bridge is not only a converter. It knows which SMIA/BaSyx combination can read
which AAS version, and it tracks the official metamodel releases.

### `smia` — can my runtime read this package?

[//]: # (TODO AQUI QUEDA EXPLICAR QUE ES SMIA, y ofrece el enlace al repo)

`aas-bridge smia [file]` resolves the SMIA release you run in this order:

1. the SMIA installed in the current environment (`importlib.metadata`; offline and
   authoritative);
2. the verified table of ten PyPI releases;
3. a per-version PyPI JSON probe when the version is missing from the table;
4. `unverified` — printed visibly, exit `0`, with an actionable note.

It prints the SMIA version, its `basyx-python-sdk` pin, the AAS versions that pin can
read and the provenance. With a file it adds a verdict: compatible, upgrade with
`aas-bridge migrate`, downgrade unavailable (Phase 2), or undetectable/inconsistent.
It never writes files.

### `update` — what changed upstream?

`aas-bridge update` checks the official
[`admin-shell-io/aas-specs-metamodel`](https://github.com/admin-shell-io/aas-specs-metamodel)
releases feed, classifies the AAS lines (covered, known but uncovered, and **NEW**
non-prerelease lines), fetches the pinned XSD / JSON Schema / changelog artifacts
and writes a deterministic `manifest.json` with sha256, size, dates, per-item status
and CC-BY-4.0 attribution.

| AAS line | Tag | Artifacts |
|---|---|---|
| 3.0 | `IDTA-01001-3-0-1_schemasV3.0.9` (2024-11-15) | XSD + JSON Schema |
| 3.1 | `v3.1.2` (2025-11-10) | XSD + JSON Schema + changelog |

Only schemas exist for 3.0 at the pinned tag; the 3.1 line also publishes a
changelog. Artifacts land under `AASBRIDGE_REGISTRY_DIR` as `<label>/<filename>`.

> [!NOTE]
> Offline is a degraded state, not an error: the status is printed, the manifest is
> still written with `online: false` and non-`fetched` statuses, and the command
> exits `0`. Fetching never creates or activates a migration rule; activation
> requires human review (Phase 4).

[//]: # (## How it works)

[//]: # ()
[//]: # (AAS Bridge is a thin CLI over a headless core. The core never imports BaSyx)

[//]: # (in-process: every validation runs in a subprocess with the dialect it needs.)

[//]: # ()
[//]: # (```mermaid)

[//]: # (flowchart TB)

[//]: # (    CLI["CLI + interactive shell"] --> Actions["cli/actions"])

[//]: # (    Actions --> Detect["engine/detect"])

[//]: # (    Actions --> Gate["engine/gate"])

[//]: # (    Gate --> Transform["engine/transformer"])

[//]: # (    Gate --> Loaders["BaSyx subprocess loaders"])

[//]: # (    Loaders --> Venv["project venv<br/>2.0.1 ↔ 2.2"])

[//]: # (    Actions --> Registry["registry + probes"])

[//]: # (```)

[//]: # ()
[//]: # (| Layer | Responsibility |)

[//]: # (|---|---|)

[//]: # (| `cli/` | Typer commands and the REPL. Printing and exit codes; no business logic. |)

[//]: # (| `engine/` | Detection, transformation, the evidence gate and the report. |)

[//]: # (| `registry/` | Version IRIs, approved rules, SMIA and IDTA knowledge. |)

[//]: # (| `probes/` | PyPI and GitHub queries; offline-degraded. |)

[//]: # ()
[//]: # (<details>)

[//]: # (<summary>Project layout and package naming</summary>)

[//]: # ()
[//]: # (```text)

[//]: # (src/aas_bridge/)

[//]: # (├── cli/        # Typer commands + REPL)

[//]: # (├── engine/     # detect, transform, gate, report)

[//]: # (├── registry/   # versions, rules, SMIA/IDTA knowledge)

[//]: # (└── probes/     # PyPI + GitHub queries)

[//]: # (```)

[//]: # ()
[//]: # (The distribution and CLI command are `aas-bridge`; the importable package is)

[//]: # (`aas_bridge` under `src/aas_bridge/` &#40;a hyphen is not valid in a Python import)

[//]: # (name&#41;. The cache directory and `AASBRIDGE_CACHE_DIR` keep their historical names.)

[//]: # ()
[//]: # (</details>)

[//]: # ()
[//]: # (## Roadmap)

[//]: # ()
[//]: # (Phases are gates, not promises. Each one ships with its own evidence.)

[//]: # ()
[//]: # (| Phase | Scope | Status |)

[//]: # (|---|---|---|)

[//]: # (| 1 | Headless core + CLI: detection, 3.0 → 3.1 gate, JSON report, `smia`, `update`, shell | Shipped in `0.2.0` |)

[//]: # (| 1b | Local web GUI &#40;NiceGUI, EN/ES&#41; + Docker | Next |)

[//]: # (| 2 | Downgrade 3.1 → 3.0: feature catalog, plan-then-execute, gate reuse | Planned |)

[//]: # (| 3 | Ecosystem probes + `doctor` diagnosis | Planned |)

[//]: # (| 4 | Version ingest pipeline + SMIA whitelist export | Planned |)

[//]: # (| 5 | Generalization: 3.1 ↔ 3.2, GUI polish, standalone binaries | On demand |)

[//]: # ()
[//]: # (Version knowledge lives in a registry of approved rules, not in ad-hoc code. Adding)

[//]: # (a new AAS pair is a reviewed rule plus fixtures; Phase 4 automates the diff, but a)

[//]: # (human still approves activation.)

[//]: # ()
[//]: # (<details>)

[//]: # (<summary>What's in 0.2.0</summary>)

[//]: # ()
[//]: # (- Version detection for AAS 3.0 and 3.1 XML packages; JSON detect-only.)

[//]: # (- Evidence-gated 3.0 → 3.1 migration with a byte-preserving OPC/ZIP rebuild.)

[//]: # (- Stable JSON report &#40;`schema_version: 1`&#41;.)

[//]: # (- English and Spanish CLI output.)

[//]: # (- `smia` guidance and `update` official artifact fetch.)

[//]: # (- Interactive shell.)

[//]: # ()
[//]: # (</details>)

[//]: # ()
[//]: # (## Development)

[//]: # ()
[//]: # (<!-- Replace OWNER/REPO with the public repository slug before publishing. -->)

[//]: # (```bash)

[//]: # (git clone https://github.com/OWNER/REPO.git aas-bridge)

[//]: # (cd aas-bridge)

[//]: # (python -m venv .venv)

[//]: # (source .venv/bin/activate        # Windows: .venv\Scripts\Activate.ps1)

[//]: # (pip install -e ".[dev]")

[//]: # ()
[//]: # (python -m pytest -m "not integration"   # offline unit suite)

[//]: # (python -m pytest                        # includes the corpus gate &#40;swaps BaSyx&#41;)

[//]: # (python -m pytest -m network             # opt-in: real PyPI/GitHub probes)

[//]: # (ruff check .)

[//]: # (ruff format --check .)

[//]: # (python -m build)

[//]: # (mypy src/aas_bridge                     # optional)

[//]: # (```)

[//]: # ()
[//]: # (The `aas_v3-0/` and `aas_v3-1/` folders are read-only corpus fixtures; tests copy)

[//]: # (them to temporary directories before touching them. The corpus gate swaps)

[//]: # (`basyx-python-sdk` in the active environment, so use a dedicated virtual)

[//]: # (environment.)

[//]: # ()
[//]: # (> [!NOTE])

[//]: # (> The current release is developed and verified on Windows. The package is pure)

[//]: # (> Python and uses `pathlib` with POSIX cache paths; macOS and Linux are expected to)

[//]: # (> work but are not yet covered by CI.)

[//]: # ()
[//]: # (CI is planned; until then, run the offline suite and `ruff` locally before opening)

[//]: # (a pull request.)

## Contributing

Issues and pull requests are welcome. For a larger change,
[open an issue](../../issues/new) first so the design and the evidence gate stay
coherent.

Before opening a pull request:

- run `python -m pytest -m "not integration"` and `ruff check .`;
- keep `aas_v3-0/` and `aas_v3-1/` read-only;
- do not weaken the fail-closed gate: a change that can emit an unproven file is
  not mergeable.

## Licence

GPL-3.0-only. See [LICENSE](LICENSE).

Official IDTA metamodel artifacts fetched by `update` are CC-BY-4.0 and are
attributed in the generated `manifest.json`.

## Acknowledgements

AAS Bridge provides support for the
[SMIA](https://github.com/ekhurtado/SMIA) software and stands on the
[Eclipse BaSyx Python SDK](https://github.com/eclipse-basyx/basyx-python-sdk) and the
[IDTA AAS metamodel](https://github.com/admin-shell-io/aas-specs-metamodel).
[AASX Package Explorer](https://github.com/eclipse-aaspe/package-explorer) remains the
interactive alternative for authoring and conversion.

---

<p align="center">
  <sub>Built for the AAS community. If AAS Bridge saved you from a silent version mismatch, a star helps the next engineer find it.</sub>
</p>
