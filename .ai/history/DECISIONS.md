# history/DECISIONS.md — AAS Bridge Decision Ledger

> **Tier:** HISTORY (cold archive). Append-only; entries immutable once written.
> **Writer:** Architect (new ADR/TD only). Supersede = set `Status: Superseded by [ID]` on the
> old entry and append the new one; never edit the old content.
> **Access:** by ID or grep; never bulk-loaded.
> **Language:** new entries in English; legacy entries remain frozen as-is.

## Entry Format

```md
## [ADR-XXX | TD-XXX] <short title>
- **Date:** YYYY-MM-DD | **Phase:** N | **Status:** Accepted | Superseded by [ID] | Deprecated
- **Scope:** Core | Data | Interface | UI | Feature (<name>) | Process
- **Alternatives:** A, B, C
- **Decision:** X
- **Justification:** <concrete reasons; for a conditional dependency include the approved alternative + delta>
- **Accepted trade-offs:** <known costs>
- **Revisable when:** <condition that justifies re-evaluation>
```

---

## Session 2026-11-18 — strategy & design (D1-D13)

### [ADR-001] SMIA upgrades to `basyx-python-sdk ~= 2.2`
- **Date:** 2026-11-18 | **Phase:** 0 | **Status:** Accepted
- **Scope:** Core
- **Alternatives:** stay on 2.0.1; use 2.1.0; use 2.2.0.
- **Decision:** SMIA upgrades to `basyx-python-sdk ~= 2.2` (not 2.1).
- **Justification:** lockstep with the manufacturing-stack colleagues; latest; same metamodel
  (3.1.2); Python ≥3.11 is not blocking (images are 3.12-alpine, local env 3.12.10). 2.1.0
  would split the ecosystem again.
- **Accepted trade-offs:** SMIA must move to Python ≥3.11; existing pins must be unified.
- **Revisable when:** the ecosystem moves to a newer basyx line or a consumer is stuck on 2.0.x.

### [ADR-002] Runtime normalization direction is upgrade-only
- **Date:** 2026-11-18 | **Phase:** 0 | **Status:** Accepted
- **Scope:** Core
- **Alternatives:** bidirectional normalization; upgrade-only; no normalization.
- **Decision:** the SMIA runtime layer normalizes only upward.
- **Justification:** the AAS V3.x line is additive upward: every valid 3.0 document is a valid
  3.1 document. Downgrade is lossy and belongs to an interactive tool, not an autonomous agent.
- **Accepted trade-offs:** v3.1-only features cannot be consumed by a v3.0-only reader.
- **Revisable when:** a real downgrade requirement appears at runtime.

### [ADR-003] SMIA gets a thin ingestion layer
- **Date:** 2026-11-18 | **Phase:** 0 | **Status:** Accepted
- **Scope:** Interface
- **Alternatives:** patch basyx; duplicate reader; thin ingestion layer.
- **Decision:** add `aas_version_compat.py` to SMIA (design in `SMIA_RUNTIME_COMPAT_LAYER.md`).
- **Justification:** detect by xmlns → load directly / in-memory re-label for whitelisted older
  versions / fail-fast with an actionable error. basyx stays the only validator; SMIA learns no
  metamodel; fail-closed. Fixes the silent-empty-store failure mode.
- **Accepted trade-offs:** one more module in SMIA and a whitelist to maintain.
- **Revisable when:** basyx implements native version negotiation.

### [ADR-004] The whitelist is opt-in and coupled to basyx upgrades
- **Date:** 2026-11-18 | **Phase:** 0 | **Status:** Accepted
- **Scope:** Core
- **Alternatives:** auto-detect any older namespace; explicit whitelist; no whitelist.
- **Decision:** `SWAP_SAFE_SOURCE_NAMESPACES` is opt-in and changes only with basyx-upgrade events.
- **Justification:** entries are added only after checking the IDTA changelog `nc` column and the
  corpus regression. Maintenance is amortized: it only changes with a dependency upgrade that
  requires retesting anyway. Target dialect is imported from basyx (`NS_AAS`), never hardcoded.
- **Accepted trade-offs:** a new additive version is not supported until the whitelist is updated.
- **Revisable when:** AAS Bridge Phase 4 generates the whitelist automatically.

### [ADR-005] AAS Bridge is a standalone project
- **Date:** 2026-11-18 | **Phase:** 0 | **Status:** Accepted
- **Scope:** Process
- **Alternatives:** `additional_tools/` inside SMIA; separate repository/project.
- **Decision:** AAS Bridge is standalone in this repository.
- **Justification:** other consumers (the colleagues' stack) already exist; licensing/versioning
  decoupled from SMIA; the tool outlives any single consumer.
- **Accepted trade-offs:** a second repository/package to maintain and release.
- **Revisable when:** a single consumer becomes the only user and integration cost dominates.

### [ADR-006] Version knowledge is centralized in the registry
- **Date:** 2026-11-18 | **Phase:** 0 | **Status:** Accepted
- **Scope:** Data
- **Alternatives:** keep knowledge in SMIA; duplicate per consumer; central registry + generated export.
- **Decision:** the tool's registry is the single source; the SMIA whitelist is a generated export.
- **Justification:** removes hand-maintenance of SMIA code; the registry holds vendored official
  artifacts (hash + CC-BY-4.0), feature catalog, per-pair rules and the ecosystem matrix.
- **Accepted trade-offs:** registry schema and ingest pipeline must be designed (Phase 4).
- **Revisable when:** another consumer needs a different knowledge format.

### [ADR-007] Every migration must pass the evidence gate
- **Date:** 2026-11-18 | **Phase:** 0 | **Status:** Accepted
- **Scope:** Core
- **Alternatives:** trust the converter; schema validation only; baseline + round-trip gate.
- **Decision:** every migration passes baseline comparison + round-trip; a file that does not
  reproduce its baseline is not emitted.
- **Justification:** the differentiating asset; proves losslessness instead of trusting the
  converter.
- **Accepted trade-offs:** migrations are slower and some files are refused.
- **Revisable when:** a stronger formal verification method becomes available.

### [ADR-008] Ecosystem facts via empirical probes
- **Date:** 2026-11-18 | **Phase:** 0 | **Status:** Accepted
- **Scope:** Data
- **Alternatives:** scrape release notes; empirical probes; static documentation.
- **Decision:** basyx dialect via an ephemeral venv probe; PyPI JSON API for SMIA latest; PE
  matrix informative only.
- **Justification:** evidence beats documentation; release-note scraping is fragile. Online
  features degrade visibly offline.
- **Accepted trade-offs:** probes need network/venv and must be cached with dates.
- **Revisable when:** the ecosystem publishes a stable machine-readable compatibility matrix.

### [ADR-009] Scope discipline: V3.x bidirectional
- **Date:** 2026-11-18 | **Phase:** 0 | **Status:** Accepted
- **Scope:** Core
- **Alternatives:** any-version engine; V3.x only; V2.0 included.
- **Decision:** V3.x bidirectional; V2.0 out; sub-versions out; "any version" means "any ingested
  version with approved rules".
- **Justification:** V2↔V3 is structural rework that PE already covers; no operational need
  exists. Rules register per version pair and compose; a generic engine would silently corrupt
  models.
- **Accepted trade-offs:** V2.0 users are not served by this tool.
- **Revisable when:** a demonstrated V2.0 requirement appears.

### [ADR-010] Compatibility is judged per document
- **Date:** 2026-11-18 | **Phase:** 0 | **Status:** Accepted
- **Scope:** Interface
- **Alternatives:** per version pair only; per document analysis; both.
- **Decision:** additive pairs are automatic for all documents; mixed pairs require per-document
  analysis; the plan taxonomy is automatic / assisted / blocking.
- **Justification:** the V3.2 `Range` change proves that a version pair can be partially
  incompatible. Never silent data loss.
- **Accepted trade-offs:** the plan-then-execute flow is more interactive.
- **Revisable when:** every future pair is proven fully additive.

### [ADR-011] GUI is a thin web-local frontend over a headless core
- **Date:** 2026-11-18 | **Phase:** 0 | **Status:** Accepted
- **Scope:** UI
- **Alternatives:** desktop framework; Streamlit; NiceGUI + Typer.
- **Decision:** NiceGUI for the local web GUI; Typer for the CLI; both over the same headless core.
- **Justification:** desktop frameworks break Docker; Streamlit freezes badly; NiceGUI works
  identically native (browser auto-open, exit button) and containerized (port map, HTTP
  upload/download). Core-first: features exist in the tested core before any UI.
- **Accepted trade-offs:** web UI adds a browser dependency; NiceGUI is a smaller ecosystem.
- **Revisable when:** NiceGUI cannot meet the required UX or packaging constraints.

### [ADR-012] New AAS versions onboarded via ingest + human review
- **Date:** 2026-11-18 | **Phase:** 0 | **Status:** Accepted
- **Scope:** Process
- **Alternatives:** manual research; automatic rule activation; auto diff + human review.
- **Decision:** `ingest` fetches official artifacts, diffs them, proposes candidate rules and
  requires human review; unreviewed rules never activate.
- **Justification:** automation can compute *what changed*, not *what the correct semantic
  transformation is* (the `Range` case proves it). Review of a prepared diff ≈ 30 min/version
  vs continuous manual tracking.
- **Accepted trade-offs:** onboarding is not fully automatic.
- **Revisable when:** a formally verified semantic diff becomes possible.

### [ADR-013] SMIA work is deferred to a dedicated session
- **Date:** 2026-11-18 | **Phase:** 0 | **Status:** Accepted
- **Scope:** Process
- **Alternatives:** implement both projects now; defer SMIA; abandon SMIA layer.
- **Decision:** defer the basyx upgrade, runtime layer and debt cleanup to a dedicated SMIA
  session (Track S of `ROADMAP.md`).
- **Justification:** keeps this repository focused on the tool; the SMIA changes touch another
  repo and need its own verification.
- **Accepted trade-offs:** the production incident remains until Track S ships.
- **Revisable when:** the incident recurs and the runtime layer becomes urgent.

---

## Bootstrap 2026-11-18 — AI development architecture (ADR-014..020)

### [ADR-014] Two primary agents plus a reviewer subagent
- **Date:** 2026-11-18 | **Phase:** 0 | **Status:** Accepted
- **Scope:** Process
- **Alternatives:** full triad; two agents with self-review; two agents + reviewer subagent.
- **Decision:** `architect` and `code-executor` are primary; `reviewer` is a subagent launched by
  the executor. The executor owns implementation, verification and `.ai/` state updates; the
  human is the final gate.
- **Justification:** matches the requested workflow, keeps the interaction surface small and
  preserves an independent audit step without a third cold session.
- **Accepted trade-offs:** the executor could ignore a `FAIL`; the agent rules forbid it and the
  human verifies. No independent primary reviewer.
- **Revisable when:** the project needs a separate cold review session or stricter segregation.

### [ADR-015] Simplified context layout
- **Date:** 2026-11-18 | **Phase:** 0 | **Status:** Accepted
- **Scope:** Process
- **Alternatives:** full configurator layout; simplified layout; minimal layout without history.
- **Decision:** keep 9 root context files, `contracts/`, `history/` (DECISIONS, ISSUES,
  SESSION_LOG, specs), `templates/`, `agents/` and `skills/`. Drop `AGENTS_ARCHITECTURE.md`,
  `CURRENT_STATE.md`, `KNOWN_ISSUES.md` and `RESOLVED_ISSUES.md`.
- **Justification:** the topology and write matrix fit in `README.md`; a single `ISSUES.md`
  covers open and resolved issues; fewer files reduce context rot.
- **Accepted trade-offs:** less separation between live state and history; `README.md` carries
  more responsibility.
- **Revisable when:** the project grows enough to need a separate live-state file.

### [ADR-016] UI is in scope and bilingual
- **Date:** 2026-11-18 | **Phase:** 0 | **Status:** Accepted
- **Scope:** UI
- **Alternatives:** `has_ui: false` (defer UI contracts); minimal UI contract; full design system.
- **Decision:** `has_ui: true` with a minimal NiceGUI contract, light theme and bilingual EN/ES.
- **Justification:** the product's primary UX is a local web GUI; a minimal contract keeps the
  UI proportional while making the bilingual requirement explicit.
- **Accepted trade-offs:** two UI contract files and UI-specific skills; i18n maintenance.
- **Revisable when:** a dark theme or a fuller design system is needed.

### [ADR-017] Skill catalog of 13 skills
- **Date:** 2026-11-18 | **Phase:** 0 | **Status:** Accepted
- **Scope:** Process
- **Alternatives:** no skills; minimal 8; full 13.
- **Decision:** 13 atomic skills: 4 architect-specific, 4 executor-specific, 3 reviewer-specific,
  and 2 shared (`verification-gate`, `dependency-review`).
- **Justification:** each skill maps to a distinct, recurring capability; shared skills avoid
  duplication. The catalog is documented in `.ai/README.md` and the agents' §7.
- **Accepted trade-offs:** more files and maintenance; each agent has five skills, the maximum
  recommended by the Playbook.
- **Revisable when:** a skill is unused for two cycles or two skills overlap >40%.

### [ADR-018] Permissions baseline
- **Date:** 2026-11-18 | **Phase:** 0 | **Status:** Accepted
- **Scope:** Process
- **Alternatives:** permissive agents; strict deny-all; scoped writes + broad reads.
- **Decision:** `read/glob/grep` allowed for the project; `edit` denied by default with explicit
  per-agent allows; `shell` asks by default with a broad read-only allowlist and explicit
  build/test allows; destructive git denied; `external_directory: * deny`; the executor may
  launch only the `reviewer` subagent.
- **Justification:** removes friction for reading context and read-only commands while keeping
  writes and destructive operations bounded.
- **Accepted trade-offs:** more permission rules per agent; a new command may need an explicit
  allow.
- **Revisable when:** a recurring read-only command is missing from the allowlist.

### [ADR-019] Adopt the existing `.ai/` with controlled migration
- **Date:** 2026-11-18 | **Phase:** 0 | **Status:** Accepted
- **Scope:** Process
- **Alternatives:** recreate the context from scratch; adopt/migrate; `evolve`.
- **Decision:** adopt the existing context, keep `ARCHITECTURE.md`,
  `ECOSYSTEM_COMPATIBILITY.md` and `SMIA_RUNTIME_COMPAT_LAYER.md` at the `.ai/` root, migrate
  `DECISIONS.md` to `history/DECISIONS.md`, and fill the empty `CONSTITUTION.md` and
  `CONVENTIONS.md`.
- **Justification:** preserves the approved design and evidence; no destructive overwrite.
- **Accepted trade-offs:** root context is larger than the original six-file list.
- **Revisable when:** the evidence files move to an archive or a separate reference repository.

### [ADR-020] Python and licence baseline
- **Date:** 2026-11-18 | **Phase:** 0 | **Status:** Accepted | Superseded by [ADR-023]
- **Scope:** Process
- **Alternatives:** uv; pip/venv; Poetry. AGPL-3.0; Apache-2.0; MIT.
- **Decision:** Python ≥3.11, `pip` + `venv`, `pytest`, `ruff`, `mypy` optional; project licence
  **AGPL-3.0**.
- **Justification:** matches the local environment and SMIA's licence; keeps the toolchain small.
  `ruff` and `mypy` are dev dependencies to be added in SPEC-001.
- **Accepted trade-offs:** no `uv` lockfile speed/reproducibility; AGPL-3.0 imposes copyleft
  obligations on network use.
- **Revisable when:** the team standardizes on `uv`/Poetry or the licence policy changes.
- **Note (2026-11-18, ISS-005/D3):** this entry was briefly amended in place to GPL-3.0;
  the original AGPL-3.0 text above is restored and the licence change is recorded as the
  superseding ADR-023.

---

## Rejected alternatives (kept for the record)

- **Staying on basyx 2.0.1 / degrading v3.1 files:** swims against the ecosystem (PE no longer
  models 3.0; 2.0.x unmaintained; Py 3.10 EOL); only postpones the problem.
- **Two basyx versions (venvs / subinterpreters / gateway agents):** same-namespace packages
  cannot coexist in one process; multi-process gateways add permanent operational complexity
  for something a namespace re-label solves.
- **aas-core as SMIA's runtime reader:** would rewrite ~12 modules consuming basyx objects.
  Correct role: validator inside AAS Bridge.
- **Full "AAS interoperability platform" (own intermediate model, generic engine):** YAGNI;
  would re-implement parts of the metamodel; the registry + gate deliver ~90% of the value.
- **Modifying basyx-python-sdk:** excluded by requirement; also unnecessary (see ADR-003).
- **Runtime downgrade inside SMIA:** lossy by nature, needs human decisions — an autonomous
  agent must not block on interactive choices (antipattern in MAS).
- **A full triad of cold sessions:** rejected for now in favour of two primary agents plus a
  reviewer subagent (ADR-014); revisit if independence becomes insufficient.

## Open questions (must be answered before/during implementation)

| # | Question | Impact |
|---|---|---|
| Q1 | Will SMIA receive v3.0 AASX "hot" from third parties, or is the file repo controlled? | Decides the depth of the SMIA layer: full auto-upgrade vs detect-only + tool. |
| Q2 | Upgrade the owner's AASX Package Explorer to v2025-10-21? | Recommended (models 3.1, converts on load); would make new files natively 3.1. |
| Q3 | Ingestion scope: only `.aasx`, or also standalone `.xml`/`.json` + AAS-Repository path? | SMIA reads all three; the runtime layer covers `.aasx`/`.xml` and declares JSON out of scope (no embedded version). |
| Q4 | In the colleagues' stack, are there v3.0-only consumers of AASX files written back by their tooling (`OrderHistory` writes)? | Fixes the ecosystem write version; decides urgency of downgrade (Phase 2). |
| Q5 | SMIA Docker images install `smia` from PyPI — is release latency acceptable for shipping the basyx upgrade, or should local builds use `pip install .`? | Affects how Track S reaches Docker users. |
| Q6 | Project name confirmation: "AAS Bridge" (repo already `AAS_bridge`; all three prior AI sessions converged on a bridge-flavoured name). | Cosmetic but locks the CLI command (`aas-bridge`) and package name; check PyPI/GitHub availability before the first release. |

## Sources of the session (inputs)

- Three prior AI analysis transcripts (`../ai_sessions_transcripts/`): Claude (version matrix,
  aas-core option, normalization intuition), Gemini (infeasibility of dual-SDK in one process,
  web-local GUI analysis), ChatGPT (v3.2/v3.3 horizon, per-pair rules, pyecma376-2, plan
  taxonomy). Their factual errors (e.g. Gemini's "structural changes 3.0→3.1") are superseded by
  `ECOSYSTEM_COMPATIBILITY.md`.
- Colleagues' investigation report (namespace-swap migration + E2E evidence on their stack).
- Official sources fetched 2026-11-18: basyx-python-sdk releases, eclipse-aaspe
  package-explorer releases, IDTA Part 1 v3.2 change notes.
- Local empirical probes on the 6-file corpus (basyx 2.0.1 and ephemeral 2.2.0).
- AI architecture bootstrap: `.ai/tooling/` (temporary; removed after sync), Playbook v1.4,
  configurator methodology v1.0, agent generator v3.1.

---

## Phase 1 planning 2026-11-18 — SPEC-001 (ADR-021, ADR-022, TD-001)

> Debated with and approved by the human on 2026-11-18 (4 rounds: cycle structure, gate
> mechanism, CLI/JSON/report, tests/packaging).

### [ADR-021] Evidence gate dialect mechanism: same-venv pip swap in subprocesses
- **Date:** 2026-11-18 | **Phase:** 1 | **Status:** Accepted
- **Scope:** Core (Feature: evidence gate)
- **Alternatives:** (A) tool-owned persistent second venv with basyx 2.0.1; (B) pip swap in
  the project venv orchestrated by the tool; (C) precomputed baseline fixtures.
- **Decision:** Option B, chosen by the human: the tool swaps `basyx-python-sdk`
  (`==2.0.1` ↔ `~=2.2`) in the project venv. Mitigations mandated by the design: the main
  process **never imports basyx** (detection/transformation are pure zipfile/XML; every basyx
  load runs in a `python -m` subprocess after the corresponding `pip install`); the venv is
  restored to `~=2.2` in a `finally` block; baseline results are cached by
  (file sha256, basyx version) so swaps are rare; gate executions are serialized with a lock
  file; pip/subprocess failures raise an actionable `ProbeError` naming both versions.
- **Justification:** the human owns the single project venv and accepts the trade-off; the
  no-import-in-main-process design removes the module-cache and GUI-race hazards and makes
  the mechanism safe for the SPEC-002 GUI running in the same venv. L1-9 is preserved: basyx
  remains the only validator; the target dialect is imported from the installed basyx
  (`NS_AAS` via a dialect-probe subprocess), never hardcoded.
- **Accepted trade-offs:** the venv is temporarily mutated (restored on exit; a crash
  mid-swap leaves 2.0.1 installed with an explicit recovery command in the error); the first
  baseline for a new file may need network for pip — a documented, human-accepted deviation
  from strict L1-14 offline-first (`check` and all offline features stay network-free; the
  baseline is cached afterwards); concurrent external pip use of the same venv during a swap
  can conflict (mitigated by the lock, not eliminated).
- **Revisable when:** the SPEC-002 GUI or distribution (Docker/PyPI) makes swap serialization
  or first-run network unacceptable — then revisit option A (persistent probe venv) or a
  vendored wheelhouse.

### [ADR-022] Dependency baseline for SPEC-001
- **Date:** 2026-11-18 | **Phase:** 1 | **Status:** Accepted | Superseded by [ADR-024]
- **Scope:** Data (dependencies)
- **Alternatives:** (A) minimal set now, GUI/validators later with their own decisions;
  (B) include nicegui and aas-core already; (C) declare unused dependencies "for later".
- **Decision:** Option A. Runtime: `basyx-python-sdk ~= 2.2` (tested 2.2.0), `typer ~= 0.29`
  (tested 0.29.2), `pyecma376-2 >= 1.0.2` (tested 1.0.2; used directly for OPC I/O, so
  declared explicitly instead of relying on basyx's transitive pin). Dev extras:
  `pytest >= 9.0.3` (minimum set by CVE-2025-71176 / GHSA-6w46-j5rx-g56g, fixed in 9.0.3),
  `ruff >= 0.16`, `build >= 1.4.0`, `mypy >= 1.15` (optional). NiceGUI joins in SPEC-002 as
  the `gui` extra; aas-core is deferred (basyx is the only validator, L1-9).
- **Justification:** `dependency-review` verdict APPROVE (2026-11-18, sources: PyPI JSON and
  GitHub API, see `ECOSYSTEM_COMPATIBILITY.md` §4.6): all licences MIT/Apache-2.0/BSD/ISC —
  GPL-3.0-compatible, including the transitive trees (lxml BSD-3, python-dateutil BSD-3,
  pydantic MIT, rich MIT, shellingham ISC, colorama BSD). No known vulnerabilities except
  the pytest advisory, addressed by the pin. GPL-3.0 network-use source obligations apply
  to the project itself and are accepted.
- **Accepted trade-offs:** version ranges need retesting on bumps; `pyecma376-2` is a small,
  RWTH-maintained package (Production/Stable, Apache-2.0).
- **Revisable when:** SPEC-002 adds nicegui; a pin must move; or a transitive conflict with
  SMIA-style environments appears.

### [TD-001] CLI contract, JSON detect-only scope, and the no-migration result
- **Date:** 2026-11-18 | **Phase:** 1 | **Status:** Accepted | Superseded by [TD-002]
- **Scope:** Interface (CLI + detection semantics)
- **Alternatives:** CLI language: always print EN+ES together vs `--lang` flag (chosen).
  JSON parts: unsupported/fail-closed total vs detect-only (chosen) vs full migration now.
  v3.1 inputs: emit an identical no-op copy vs first-class "no migration needed" (chosen).
- **Decision:** `aas-bridge check <file>` and `aas-bridge migrate <file>` with
  `--lang {en,es}` (system-locale default, `en` fallback); the roadmap acceptance "prints
  the diagnosis in English and Spanish" is interpreted as *available in both via the flag*.
  JSON AASX parts are **detect-only**: the declared version is reported from `@context` when
  present ("undetectable" otherwise — basyx-written JSON has no marker), and migration
  refuses them fail-closed with an actionable message. A v3.1 input is a first-class success
  ("already AAS 3.1 — no migration needed"): exit 0, no output file, no gate run. Exit codes
  per `CONVENTIONS.md` §2.
- **Justification:** bilingual-always output is noisy for batch use; JSON migration cannot be
  evidenced by the current gate (basyx ignores `@context`, facts J2-J4 in
  `ECOSYSTEM_COMPATIBILITY.md` §4.6) and shipping it would sell an unproven stamp — the core
  asset's credibility; emitting a byte-identical copy for v3.1 files contradicts
  never-mutate/no-redundant-output and adds no value.
- **Accepted trade-offs:** JSON authors get a diagnosis but no fix until the dedicated JSON
  evidence cycle lands (roadmap); `--lang` locks the public CLI contract (L2-18).
- **Revisable when:** the JSON evidence cycle (probe + fixtures + possible aas-core schema
  decision) is approved, or user feedback demands always-bilingual console output.

---

## Rename consolidation 2026-11-18 — SPEC-001 rev 2 (ADR-023, ADR-024, TD-002)

> Human-approved on 2026-11-18 (rename Option A: distribution `aas-bridge`, package
> `aas_bridge`, CLI `aas-bridge`, `src/` layout; licence stays GPL-3.0 — "keep GPL, like the
> LICENSE file"). Closes ISS-005 (D3 licence trail) and records the reviewer loop-1 decisions
> (ISS-007 M2).

### [ADR-023] Project licence is GPL-3.0
- **Date:** 2026-11-18 | **Phase:** 1 | **Status:** Accepted
- **Scope:** Process (licensing)
- **Alternatives:** (A) keep AGPL-3.0 (ADR-020); (B) GPL-3.0; (C) Apache-2.0/MIT (permissive).
- **Decision:** Option B, confirmed by the human ("keep GPL, like the LICENSE file"):
  the project licence is **GPL-3.0**. `LICENSE` carries the full GPL-3.0 text;
  `pyproject.toml` classifiers/SPDX are aligned (executor, reviewer D1).
- **Justification:** the licence was changed in place mid-cycle without a decision trail
  (reviewer finding D3, ISS-005); the trail is corrected here: ADR-020's original AGPL-3.0
  text is restored and marked superseded, and the human confirms GPL-3.0 as the intended
  licence. GPL-3.0 keeps strong copyleft. The `dependency-review` verdict (ADR-022/ADR-024
  baseline) is unaffected: MIT/Apache-2.0/BSD/ISC dependencies remain GPL-3.0-compatible.
  GPL-3.0 contains **no network-use provision** (that clause is AGPL-specific): source
  obligations trigger on distribution/conveyance, not on offering the tool over a network.
  Vendored IDTA artifacts stay CC-BY-4.0 with attribution (one-way compatible with GPL-3.0
  distribution). CONSTITUTION L2-15 and the README already align with GPL-3.0.
- **Accepted trade-offs:** stronger copyleft obligations on any binary/source distribution of
  the tool; dropping the AGPL network-use clause means network service use no longer
  triggers source availability — relevant only if the tool is ever offered as a service.
- **Revisable when:** a distribution channel or partner requires different terms, or the
  human changes the licence policy (then supersede with a new dated ADR, never in place).

### [ADR-024] Naming, layout and packaging: `aas-bridge` / `aas_bridge` / src layout
- **Date:** 2026-11-18 | **Phase:** 1 | **Status:** Accepted
- **Scope:** Interface + Process (packaging); supersedes [ADR-022] and carries its dependency
  baseline forward unchanged.
- **Alternatives:** (A) keep `aasbridge` (hyphenless distribution + flat layout);
  (B) distribution `aas-bridge`, import package `aas_bridge`, CLI `aas-bridge`, `src/`
  layout (chosen); (C) underscore everywhere (`aas_bridge` as distribution name too).
- **Decision:** Option A of the human's rename proposal, approved 2026-11-18:
  - Distribution/PyPI name: **`aas-bridge`**.
  - Importable package: **`aas_bridge`** (a hyphen is not valid in a Python package/import
    name; the human's `src/aas-bridge/` folder is consolidated to `src/aas_bridge/`).
  - CLI command: **`aas-bridge`** (replaces `aasbridge`; public interface change → TD-002).
  - Layout: **`src/aas_bridge/`** (canonical src layout; setuptools `package-dir = {"" =
    "src"}`, `packages.find where = ["src"], include = ["aas_bridge*"]`; ruff `src =
    ["src", "tests"]` with a per-file-ignore for `src/aas_bridge/cli/main.py`).
  - Version banner: `"aas-bridge {version}"`.
  - **Unchanged identifiers:** `AASBRIDGE_CACHE_DIR` and the default cache dir path
    (`%LOCALAPPDATA%/aasbridge/cache` / `~/.cache/aasbridge`) — the cache name and paths do
    NOT change with the rename (renaming them would silently invalidate cached baselines);
    they are internal, not public interface.
- **Justification:** a hyphen cannot appear in a Python module/import path, so `aas-bridge`
  as an importable package is invalid (the executor verified `ModuleNotFoundError`); the src
  layout is canonical packaging practice and prevents accidental imports of the working
  directory; PEP 503 normalizes `aas-bridge` and `aas_bridge` to the same PyPI key, so the
  hyphenated distribution name is the readable canonical form. The ADR-022 dependency
  baseline (runtime `basyx-python-sdk ~= 2.2` / `typer ~= 0.29` / `pyecma376-2 >= 1.0.2`;
  dev `pytest >= 9.0.3` incl. the CVE-2025-71176 pin, `ruff >= 0.16`, `build >= 1.4.0`,
  `mypy >= 1.15`; licences MIT/Apache-2.0/BSD/ISC, GPL-3.0-compatible; verdict APPROVE,
  2026-11-18) is carried forward unchanged. Note: ADR-022's justification text had also been
  amended in place during the licence trail (AGPL → GPL wording); its operative content is
  restated here so the superseded entry needs no further edits.
- **Accepted trade-offs:** public interface change (CLI rename) → every user/venv must
  reinstall and any script calling `aasbridge` must be updated (TD-002); docs, contracts,
  skills and agent definitions were re-aligned in this consolidation; one extra `pip
  install -e` + rebuild cycle in SPEC-001 rev 2.
- **Revisable when:** a PyPI name conflict appears at first publish, or tooling imposes a
  different naming/layout constraint.

### [TD-002] CLI contract v2: command `aas-bridge`; refusal-report persistence
- **Date:** 2026-11-18 | **Phase:** 1 | **Status:** Accepted
- **Scope:** Interface (CLI + detection semantics); supersedes [TD-001] (the command name
  part; all other semantics carried forward).
- **Alternatives:** (A) keep the `aasbridge` command and change only import/layout;
  (B) rename the command to `aas-bridge` (chosen, human-approved); refused-report handling:
  (i) discard refusal evidence, (ii) persist it with `--report` (chosen).
- **Decision:** the CLI is invoked as **`aas-bridge`** (`aas-bridge --version` prints
  `"aas-bridge 0.1.0"`). Everything else from TD-001 is unchanged and remains in force:
  `check <file>` / `migrate <file>`, `--lang {en,es}` (system-locale default, `en` fallback),
  `--report <path>`, exit codes per `CONVENTIONS.md` §2 (0/1/2/3/4), JSON AAS parts
  **detect-only** (fail-closed migration refusal), and the first-class "already AAS 3.1 —
  no migration needed" result (exit 0, no output file, no gate run). **New:** `migrate
  --report <path>` also persists the report when the gate refuses (outcome `refused`, gate
  `fail`), so fail-closed evidence is retained on disk (resolves ISS-007/M2); the report
  schema stays `schema_version: 1` with no new keys. This is a public interface change
  recorded under L2-18.
- **Justification:** the command name follows the distribution name for a consistent UX
  (ADR-024); a refused migration is evidence — the gate's value is exactly that it proves
  and explains refusals, so discarding the refusal report contradicts the fail-closed,
  evidence-first design (G2, L1-16).
- **Accepted trade-offs:** users of the pre-rename builds must reinstall/update scripts;
  a `--report` file may now exist with outcome `refused` (tests cover it).
- **Revisable when:** the JSON evidence cycle lands (schema 2) or user feedback demands
  always-bilingual console output.
