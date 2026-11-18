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
- **Date:** 2026-11-18 | **Phase:** 0 | **Status:** Accepted
- **Scope:** Process
- **Alternatives:** uv; pip/venv; Poetry. AGPL-3.0; Apache-2.0; MIT.
- **Decision:** Python ≥3.11, `pip` + `venv`, `pytest`, `ruff`, `mypy` optional; project licence
  **AGPL-3.0**.
- **Justification:** matches the local environment and SMIA's licence; keeps the toolchain small.
  `ruff` and `mypy` are dev dependencies to be added in SPEC-001.
- **Accepted trade-offs:** no `uv` lockfile speed/reproducibility; AGPL-3.0 imposes copyleft
  obligations on network use.
- **Revisable when:** the team standardizes on `uv`/Poetry or the licence policy changes.

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
| Q6 | Project name confirmation: "AAS Bridge" (repo already `AAS_bridge`; all three prior AI sessions converged on a bridge-flavoured name). | Cosmetic but locks the CLI command (`aasbridge`) and package name; check PyPI/GitHub availability before the first release. |

## Sources of the session (inputs)

- Three prior AI analysis transcripts (`ai_sessions_transcripts/`): Claude (version matrix,
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
