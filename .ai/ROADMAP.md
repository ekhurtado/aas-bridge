# AAS Bridge — Roadmap

> Status: planning approved 2026-11-18. Phases are sequential; acceptance criteria are
> gates, not suggestions. Evidence base: `ECOSYSTEM_COMPATIBILITY.md`.

## Track A — AAS Bridge tool (this repository)

### Phase 0 — AI development architecture (bootstrap)
**Status: complete (2026-11-18).**

- [x] 0.1 Context: `README`, `PROJECT_BRIEF`, `CONSTITUTION`, `CONVENTIONS`, `ARCHITECTURE`,
      `ROADMAP`, spec placeholder, UI contracts and templates.
- [x] 0.2 Agents: `architect`, `code-executor` (primary) and `reviewer` (subagent).
- [x] 0.3 Skills: 13-skill catalog under `.ai/skills/`.
- [x] 0.4 Audit: file tree and link check; `.ai/tooling/` removed.
- [x] 0.5 Human initial commit (pending; needed before the first SPEC for `git diff`).

### Phase 1 — MVP: detection + upgrade 3.0→3.1 + evidence gate
**Priority: very high. Smallest thing that solves today's real incident.**
**Split into two cycles (2026-11-18): SPEC-001 = headless core + CLI (A1a, A2-A6); SPEC-002 =
minimal bilingual GUI + Docker (A1b).**

- [x] A1a. Package skeleton (SPEC-001): `aas_bridge` Python package under `src/` (distribution
      `aas-bridge`, CLI `aas-bridge` — ADR-024), core engine + registry layout, Typer CLI,
      pytest harness, packaging (pyproject, MANIFEST, LICENSE, README).
- [ ] A1b. Local web GUI (NiceGUI) implementing `contracts/UI_SPEC.md` +
      `contracts/DESIGN.md`, bilingual EN/ES, with: upload → version diagnosis → one-click
      migrate → download `<name>-adapted.aasx` (SPEC-002; Docker smoke optional while
      ISS-004 is open).

- [x] A2. Version detection: inspect AASX XML parts for xmlns declarations (both forms:
      default `xmlns="...aas/3/0"` from PE v3.0 files and prefixed `xmlns:aas=".../3/1"`
      from v3.1 files). Report declared version; distinguish it from versioned external
      IRIs (IEC 61360 `DataSpecificationTemplates/.../3/0`) which are NOT declarations.
      JSON AAS parts are **detect-only** via `@context` ("undetectable" when absent —
      basyx-written JSON carries no marker); migration refuses JSON parts fail-closed
      (TD-001, evidence §4.6). JSON *migration* is deferred to a dedicated evidence cycle.
- [x] A3. Upgrade transformation V3.0 → V3.1: re-label namespace **declarations only**;
      rebuild the OPC/ZIP package preserving every other part byte-for-byte (supplementary
      files, OWL ontologies, `.properties`, thumbnails, BOMs, relationships, `[Content_Types].xml`).
      Operate on a copy; never mutate the original file.
- [x] A4. **Evidence gate (the core asset)**: before/after validation —
      1) load original with source-dialect basyx (2.0.1) → baseline (object counts, IDs,
      semanticIds); 2) load adapted with target-dialect basyx (2.2.0); 3) compare;
      4) round-trip re-read. A file that does not match its baseline is not emitted.
      Mechanism: same-venv pip swap in subprocesses, main process never imports basyx,
      baseline cache + swap lock (ADR-021). A v3.1 input short-circuits to the first-class
      "already AAS 3.1 — no migration needed" result (TD-001).
- [x] A5. Regression corpus: the 6 AASX files of this repo as fixtures with expected
      baselines (v3.0: 22/20/19 objects — AAS 1/1/1, SM 6/4/3, CD 15/15/15;
      v3.1: 34/32/22 — 2/2/1 AAS, 8/6/4 SM, 24/24/17 CD). Expected counts live in tests.
- [x] A6. Migration report (JSON with `schema_version` + human-readable console output
      derived from it, `--lang {en,es}`; golden JSON fixtures).

**Acceptance (SPEC-001, headless):** the 3 v3.0 corpus files migrate and pass the gate via
the CLI; the 3 v3.1 corpus files are diagnosed "already AAS 3.1 — no migration needed";
`aas-bridge check <file>` reports the diagnosis in English and Spanish (via `--lang`, TD-002);
the offline suite, lint, format and build are green; the corpus is untouched and the venv
ends at basyx `~=2.2`. **Acceptance (SPEC-002, GUI):** the 6 corpus files pass through the
GUI flow; docker image runs the GUI on port 8080 (optional smoke test when Docker is
available; `N/A` while ISS-004 is open).

### Phase 2 — Downgrade 3.1→3.0 (document-aware, plan-then-execute)
**Priority: high. Needed for partners stuck on older toolchains.**

- [ ] B1. Feature catalog for the V3.1 delta (each: detection rule + resolution policy):
      `AssetKind/Role` (no 3.0 equivalent → assisted/blocked), `idShort` hyphens (rename +
      reference check), `Entity/entityType` absent, `File|Blob/contentType` absent
      (suggest MIME from filename), `RelationshipElement/first|second` absent,
      `Identifier` > 2000, `ContentType` > 100, `BasicEventElement/lastUpdate`
      DateTimeUtc semantics.
- [ ] B2. Document analysis: scan the file for feature usage → compatibility report:
      automatic / assisted (with suggestion) / blocking, with counts and paths.
- [ ] B3. Plan-then-execute: user reviews decisions (accept / edit / abort) in GUI and CLI
      (CLI: `--plan report.json` non-interactive mode); execution applies only approved ops.
- [ ] B4. Gate reuse: same evidence gate; a downgrade with unresolved assisted items aborts.

**Acceptance:** a v3.1 file using no 3.1-only features downgrades and passes the gate;
a file using `AssetKind=Role` is reported blocking with an explanation.

### Phase 3 — Ecosystem probes + doctor
**Priority: medium-high. Turns the tool into a diagnostic instrument.**

- [ ] C1. SMIA probe: `https://pypi.org/pypi/smia/json` → latest release + its
      `basyx-python-sdk` pin. Cacheable; offline-degraded with visible status.
- [ ] C2. basyx probe (empirical, no scraping): ephemeral venv per version →
      `import NS_AAS` → dialect matrix. Cache in registry; optional heavyweight layer
      (`aas-bridge-full` image) with cached-matrix fallback in the default image.
- [ ] C3. AASX Package Explorer matrix (informative, from release notes; dated).
- [ ] C4. `doctor` UX: drop a file → "your file is AAS X; SMIA latest reads Y;
      automatic migration available / not needed — look elsewhere (config, XMPP, path)".
      The "version is NOT the problem" negative diagnosis is a first-class result.
- [ ] C5. `validator` UX: drop a file → "your file is valid/invalid AAS X; SMIA can/cannot 
      read it; automatic fix available / recommended changes to be valid".

**Acceptance:** doctor reproduces the original incident diagnosis end-to-end, online;
clear offline behaviour with visible status.

### Phase 4 — Version ingest pipeline + SMIA whitelist export
**Priority: medium. The amortization of the maintenance burden; needs registry design.**

- [ ] D1. Registry format: vendored official artifacts (JSON Schema/XSD/changelog) per
      version, pinned with hash + CC-BY-4.0 attribution; feature catalog; per-pair rules;
      ecosystem matrix. Offline by default.
- [ ] D2. `ingest --aas <ver>`: fetch artifacts → schema diff + changelog `nc` column
      analysis → candidate rules (auto/assisted/blocking) → **human review required**
      (fail-closed: unreviewed rules never activate) → registry release + new fixtures.
- [ ] D3. `export --target smia-whitelist`: generate `SWAP_SAFE_SOURCE_NAMESPACES` content
      (+ its evidence/tests) for the SMIA runtime layer. Makes the whitelist a generated
      artifact instead of hand-maintained code.
- [ ] D4. New-version monitoring: compare IDTA/PyPI releases vs registry ("check for new
      versions" button: report-only until ingested).

**Acceptance:** simulated ingest of a hypothetical 3.3 produces a reviewable diff and
leaves the runtime untouched until approved; whitelist export is byte-reviewable.

### Phase 5 — Generalization (on demand)
- [ ] E1. V3.1 ↔ V3.2 pair (when basyx speaks 3.2): includes the **Range blocking case**
      (nc change: absent min/max no longer mean ±infinity) as the first real blocking rule.
- [ ] E2. GUI polish: model tree, visual diff of automatic changes, report viewer.
- [ ] E3. Standalone binaries (PyInstaller) only if a Python-less user materializes.
- [ ] E4. AAS V2.0 only on a demonstrated requirement.

## Track S — SMIA integration (deferred to a dedicated session)

> Full saved design incl. example code: `SMIA_RUNTIME_COMPAT_LAYER.md`.
> These items touch the SMIA repository, not this one.

- [ ] S1. Upgrade SMIA `pyproject.toml`: `basyx-python-sdk ~= 2.2`, `requires-python >= 3.11`;
      unify ALL pins (docker/requirements.txt==1.2.0, Dockerfile_SMIA_I_KB==1.2.0,
      docs/requirements.txt~=1.2.1, README=1.2.1 — current drift is 4 different versions).
- [ ] S2. Add `aas_version_compat.py` ingestion layer (detect / whitelist / in-memory
      re-label / fail-fast) per the saved design; integrate in `read_aas_model_object_store()`.
- [ ] S3. Remove the `Operation` workaround at `extended_aas_model.py:276`: basyx ≥2.1
      `walk_submodel()` now traverses Operation/Entity children (PR #465), so the manual
      `get_operation_variables_by_semantic_id` extension would duplicate results in
      semanticID searches. Verify with E2E capability requests.
- [ ] S4. Migrate deprecated `DictObjectStore` → `DictIdentifiableStore` (basyx ≥2.1).
- [ ] S5. Corpus-based regression tests + full E2E manual verification (DoD per SMIA process).

## Open scheduling questions (see `history/DECISIONS.md` § open questions)
- Q1 (auto-upgrade vs minimal variant) decides the depth of S2 — answer before Track S.
- Q5 (any v3.0-only consumers of colleagues' written AASX?) decides whether downgrade
  (Phase 2) is urgent or can follow Phase 3.
- Q6 (PyPI release latency for SMIA images) affects how S1 ships to Docker users.
