---
name: dependency-review
description: >
  Use when a feature or diff adds, changes or removes a dependency, including licence and
  GPL-3.0 compatibility. Do NOT use for recording an approved decision (use adr-writing),
  fetching library docs (context7/web) or editing pyproject.toml (the executor owns the tree).
version: 1.0.0
consumers:
  - architect
  - reviewer
---

# Dependency Review

## Activation Criteria

- **Applies when:** a SPEC, branch or diff adds, removes, upgrades or downgrades a runtime or
  development dependency, or vendors a third-party artifact.
- **Does NOT apply when:** recording the already-approved decision (`adr-writing`), fetching
  general library documentation (context7/web) or editing `pyproject.toml` (the executor).

## Environment & Prerequisites

- Read `pyproject.toml`, the lock/constraints file (if any), `.ai/CONSTITUTION.md` L2,
  `.ai/CONVENTIONS.md` §7 and the SPEC's dependency section.
- Project licence: **GPL-3.0**. Vendored IDTA artifacts: **CC-BY-4.0** with attribution.
- Source of truth for licences: the package metadata (PyPI JSON, the project's LICENSE file) and
  the dependency's repository; network may be unavailable.
- The human approves the dependency; the architect records the decision; the reviewer verifies
  the diff.

## Technical Guidelines & Best Practices

1. **Inventory direct and transitive dependencies.** A permissive direct dependency can pull a
   copyleft-incompatible transitive one.
2. **Licence compatibility.** Check every dependency against GPL-3.0: MIT/BSD/Apache-2.0 are
   compatible; GPL/AGPL are compatible only if the project accepts the combined copyleft
   obligations; proprietary/unknown licences are a stop.
3. **AGPL obligations.** Network use of a modified AGPL work triggers source-availability
   obligations; record them in the decision.
4. **Vendored artifacts.** Keep the upstream licence, hash and attribution; never strip the
   CC-BY-4.0 notice.
5. **Prefer the standard library.** Add a dependency only when it removes real complexity or risk.
6. **Pin meaningful ranges.** Avoid unbounded `>=`; record the tested version.
7. **Runtime vs dev.** Dev-only tooling has a lower risk, but it still needs a compatible licence.
8. **Security and maintenance.** Check the last release, known advisories and the maintainer
   status; flag abandoned or unmaintained packages.
9. **No unapproved install.** Never add or upgrade a dependency just to make a test pass; the SPEC
   and the decision must approve it.
10. **Record the verdict.** The decision entry states the licence, the alternative and the
    GPL-3.0 conclusion.

## Execution Workflow

1. **Inspect:** identify the dependency, its version/range, its runtime/dev role and whether it is
   direct or transitive; read the SPEC's justification.
2. **Execute:** fetch the package metadata and LICENSE; build a small licence matrix; check
   transitive dependencies; assess security/maintenance; compare with the standard-library or
   existing alternative; recommend approve/reject/conditional.
3. **Verify:** confirm the `pyproject.toml` diff matches the approved dependency; confirm the
   licence verdict and attribution; link the ADR/TD; re-check the final diff for unapproved
   additions.

## Edge Cases & Resilience

- **Unknown licence:** stop; do not approve until the licence is confirmed.
- **Dual licence:** choose the compatible option and record it.
- **Transitive copyleft:** flag it even if the direct dependency is permissive.
- **Optional extra:** review it only if the SPEC uses it; otherwise note it.
- **Dev-only:** lower risk, same licence check.
- **Vendored data:** keep the hash/attribution; verify the source.
- **Offline:** use the cached metadata and mark the online check as degraded.

## Error Prevention & Anti-Patterns

- ⚠️ **Assuming a licence:** “it's probably MIT”.
  ✔️ Read the LICENSE/metadata and record the source.
- ⚠️ **Ignoring transitive dependencies:** checking only the direct package.
  ✔️ Inspect the resolved tree.
- ⚠️ **AGPL/GPL conflict:** adding a copyleft-incompatible dependency.
  ✔️ Stop and require a decision.
- ⚠️ **Unpinned dependency:** `>=` with no tested upper bound.
  ✔️ Pin a meaningful range and record the tested version.
- ⚠️ **Unapproved install:** adding a package to make a test pass.
  ✔️ Require the SPEC + decision + review.
