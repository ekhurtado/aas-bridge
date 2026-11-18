---
name: aasx-core
description: >
  Use when implementing AASX package I/O or AAS version detection: xmlns declarations, OPC/ZIP
  parts, rels, content types, byte-preserving rebuild, no input mutation. Do NOT use for basyx
  probing/gate (use basyx-evidence-gate) or GUI (use nicegui-frontend).
version: 1.0.0
consumers:
  - code-executor
---

# AASX Core

## Activation Criteria

- **Applies when:** implementing or changing `../../../src/aas_bridge/engine/detect.py`,
  `../../../src/aas_bridge/engine/transformer.py`, the package reader/writer, namespace detection or the
  V3.0→V3.1 declaration relabel.
- **Does NOT apply when:** implementing the basyx probe or evidence gate
  (`basyx-evidence-gate`), the NiceGUI frontend (`nicegui-frontend`) or test design
  (`python-testing`).

## Environment & Prerequisites

- Read `.ai/ARCHITECTURE.md` §2-§3, `.ai/ECOSYSTEM_COMPATIBILITY.md` §3-§4,
  `.ai/CONVENTIONS.md` §2 and §7, and the SPEC's AASX steps.
- The corpus folders `aas_v3-0/` and `aas_v3-1/` are **read-only** fixtures.
- Python standard library: `zipfile`, `re`, `pathlib`, `tempfile`; `pyecma376-2` only if the
  explicit relationships handling needs it.
- Import `NS_AAS` from the pinned basyx; never hardcode it.

## Technical Guidelines & Best Practices

1. **Detect declarations, not IRIs.** Match only XML namespace declarations:
   `xmlns="https://admin-shell.io/aas/3/0"` (default) and
   `xmlns:aas="https://admin-shell.io/aas/3/1"` (prefixed). A versioned IRI in a value position
   (e.g. IEC 61360 `.../DataSpecificationIec61360/3/0`) is **not** a declaration.
2. **AASX is an OPC/ZIP package.** Preserve `[Content_Types].xml`, `_rels`, supplementary files,
   OWL ontologies, `.properties`, thumbnails, BOMs and the compression of untouched parts.
3. **Byte-for-byte for untouched parts.** Copy the raw bytes and the original `ZipInfo`
   metadata (name, date_time, compress_type, external_attr) for every part except the declaration
   bytes you intentionally change.
4. **Never mutate the input.** Read the original, write a new `<name>-adapted.aasx` next to it or
   to the path declared in the SPEC. The original stays untouched.
5. **No semantic edits.** The V3.0→V3.1 upgrade is a namespace declaration relabel; do not rename
   idShorts, add elements or rewrite external IRIs.
6. **Fail-closed.** A missing declaration, corrupt package, unsupported compression or ambiguous
   target is an error; write no partial output.
7. **Path safety.** Reject absolute names, `..` segments, duplicate entries and zip-slip attempts.
8. **Deterministic output.** Preserve the part order where practical; do not add timestamps or
   comments that change the bytes.
9. **Basyx remains the validator.** The core only manipulates the package; validity is judged by
   the evidence gate.
10. **Windows-safe paths.** Use `pathlib`; handle CRLF and BOMs without re-encoding unchanged
    parts.

## Execution Workflow

1. **Inspect:** open the package, list the parts, identify the XML payload(s), detect the
   declaration form(s) and record the source dialect. Confirm the input is readable and not
   already the target dialect.
2. **Execute:** plan the declaration replacement (only the matched declaration bytes); rebuild
   the package into a new file, copying every other part byte-for-byte; preserve `[Content_Types]`
   and rels; write the adapted file.
3. **Verify:** compare the part list and the hashes of untouched parts; load the adapted file with
   the target-dialect basyx (or hand it to `basyx-evidence-gate`); run the corpus tests; confirm
   the original file is unchanged (hash before/after).

## Edge Cases & Resilience

- **Default vs prefixed xmlns:** support both; a file may use either form.
- **Multiple XML parts:** inspect each; only AAS payload declarations are relabelled.
- **Missing or corrupt package:** raise a specific error; never emit.
- **Duplicate ZIP entries / zip-slip:** reject with a clear message.
- **Encrypted or unsupported compression:** fail with an actionable error.
- **BOM/encoding:** preserve the original encoding; do not normalize the whole document.
- **Large files:** stream or copy in chunks; avoid loading the whole package twice in memory.
- **Already target version:** return a no-op diagnosis, not a rewrite.

## Error Prevention & Anti-Patterns

- ⚠️ **Regex over the whole XML:** rewriting versioned IRIs or comments.
  ✔️ Match only namespace declaration attributes.
- ⚠️ **Re-zipping with different compression:** changes bytes and breaks the baseline.
  ✔️ Preserve `ZipInfo` and raw bytes for untouched parts.
- ⚠️ **Losing supplementary parts:** rebuilding only the AASX XML.
  ✔️ Copy every part and the rels/content types.
- ⚠️ **Mutating the input:** writing in place.
  ✔️ Write `<name>-adapted.aasx`; verify the original hash.
- ⚠️ **Hardcoding `NS_AAS`:** a future basyx upgrade would not move the target.
  ✔️ Import it from basyx.
