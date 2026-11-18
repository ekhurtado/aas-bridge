# AAS Ecosystem Compatibility — Verified Facts & Evidence

> All facts below were verified on **2026-11-18** unless a source is marked otherwise.
> Update this file whenever a probe, release or ingest adds evidence. Never delete evidence:
> supersede it with a dated note.

## 1. basyx-python-sdk ↔ AAS metamodel matrix

| basyx-python-sdk | AAS Part 1 implemented | Reads AASX v3.0? | Reads AASX v3.1? | Min Python | Notes |
|---|---|---|---|---|---|
| 1.2.x | v3.0.1 | yes | no | 3.9 | historical pin of SMIA images |
| 2.0.0 | v3.0.1 | yes | no | 3.10 | "preparatory release, no AAS spec change" |
| 2.0.1 | v3.0.1 | yes | no | 3.10 | hotfix: publishes Docker server image only |
| **2.1.0** (2025-07-16) | **v3.1.2** | **no** | yes | 3.10 | the real version jump; deprecates DictObjectStore etc. |
| **2.2.0** (2025-10-02, latest) | v3.1.2 | **no** | yes | **3.11** | maintenance: ruff, `__all__` in adapter.json/xml, packaging |

Source: official GitHub releases of `eclipse-basyx/basyx-python-sdk` (fetched 2026-11-18).
Corroborated empirically on the local corpus (§4).

Key 2.1.0 changes relevant to us: optional `first`/`second` in relationship elements,
optional `contentType` in Blob/File, optional `valueId`, tightened `dataSpecification`
JSON reference type, **`walk_submodel()` fixed to traverse `Entity`/`Operation` children
(PR #465)** — this last one breaks a documented SMIA workaround (see
`SMIA_RUNTIME_COMPAT_LAYER.md` §5).

Key 2.2.0 changes: minimum Python 3.11; star-imports of `adapter.xml`/`adapter.json` no
longer expose `xml_deserialization` etc. (SMIA has **no** star-imports — verified by grep,
so unaffected); server build-context restructure (irrelevant to SMIA).

## 2. AASX Package Explorer ↔ AAS metamodel matrix

| AASX Package Explorer | Models | Notes |
|---|---|---|
| v2024-06-10.alpha | AAS v3.0 | version used by the SMIA owner |
| v2025-03-25.alpha | AAS v3.0 | |
| **v2025-10-21.alpha** (latest) | **AAS v3.1** | official note: *"AASPE with this release can be used to load and convert v3.0 AASX files into v3.1. In case of v3.0 modelling, please use the previous releases."* |

Source: `eclipse-aaspe/package-explorer` releases (fetched 2026-11-18).
Role in AAS Bridge: **informative** (provenance of files); basyx is the operative matrix.

## 3. IDTA AAS metamodel deltas (official change notes)

### V3.0 → V3.1 (V3.1 vs V3.0.2): **additive only — zero non-backward-compatible entries**

| Element | V3.0 | V3.1 |
|---|---|---|
| `AssetKind` | Type, Instance | + `Role` |
| `Referable/idShort` (AASd-002) | no hyphens | hyphens allowed |
| `Entity/entityType` | mandatory | optional |
| `File/contentType`, `Blob/contentType` | mandatory | optional |
| `RelationshipElement/first`, `.second` | mandatory | optional |
| `Identifier` length | 2000 | 2048 |
| `ContentType` length | 100 | 128 |
| `BasicEventElement/lastUpdate`, `EventPayload/timeStamp` | dateTime | new `DateTimeUtc` |
| Constraints AASd-090, AASd-120 | present | removed |

**Consequence (design-critical):** every valid V3.0 document is a valid V3.1 document;
re-labelling the namespace declaration of a V3.0 file is a semantically exact V3.1
conversion. Proven empirically (§4).

### V3.1 → V3.2 (V3.2 vs V3.1.2): mostly additive, **one non-backward-compatible change**

- Additive: `AdministrativeInformation/createdAt`, `/updatedAt`; `AssetKind/Batch`;
  AASd-137, AASd-138; recursion-depth note.
- **nc (x): `Range`** — the conditions "missing min = −∞ / missing max = +∞" are removed.
  `Range` is experimental and explicitly non-backward-compatible. ⇒ a V3.1→V3.2
  re-label is NOT safe for documents using unbounded Ranges: the first real **blocking**
  rule of the migration engine.
- Note: IDTA added that bugfix releases are not necessarily backward compatible.

### Version status (2026-11-18)
- AAS Part 1: **v3.2.0 published** (Jul 2026); **v3.3 in progress**.
- basyx 2.2.0 still implements v3.1.2 ⇒ a **second gap** (3.2 vs basyx) already exists.
  This validates the "structural, recurring problem" premise of the project.

## 4. Empirical corpus evidence (this repository, tested 2026-11-18)

Local environment: Windows, Python 3.12.10, basyx-python-sdk 2.0.1 (user env) + ephemeral
venv with basyx-python-sdk 2.2.0 for target-dialect tests.

### 4.1 Corpus inventory

| Folder | File | AAS ns | Internal layout | Supplementary parts |
|---|---|---|---|---|
| aas_v3-0 | CeDRI_PunchingMachine_instanceA.aasx | 3/0 (default xmlns) | `aasx/<Name>/<Name>.aas.xml` | 1 JPG |
| aas_v3-0 | SimulatedAssetHTTP_IndustrialRobot_1.aasx | 3/0 (default xmlns) | same | — |
| aas_v3-0 | SimulatedAssetsHTTP_Plan_1.aasx | 3/0 (default xmlns) | same | `.bpmn` + its `.rels` |
| aas_v3-1 | HumanWorker1.aasx | 3/1 (`xmlns:aas`) | `aasx/data.xml` | `CSS-ontology-smia.owl`, `smia-initialization.properties` |
| aas_v3-1 | LEGO_machine0.aasx | 3/1 (`xmlns:aas`) | `aasx/data.xml` | same |
| aas_v3-1 | SMIA_orchestrator.aasx | 3/1 (`xmlns:aas`) | `aasx/data.xml` | — |

**Layout lesson:** both declaration forms (`xmlns=` default and `xmlns:aas=` prefixed) must
be handled; v3.1 packages carry SMIA-critical supplementary parts that must be preserved
byte-for-byte. Neither corpus generation uses any V3.1-only feature (all `assetKind=Instance`,
zero hyphenated idShorts) — they differ only in namespace.

### 4.2 Load matrix (basyx `AASXReader`, objects = AAS + Submodels + ConceptDescriptions)

| File | basyx 2.0.1 (v3.0 dialect) | basyx 2.2.0 (v3.1 dialect) |
|---|---|---|
| CeDRI_PunchingMachine_instanceA | **22** (1 AAS / 6 SM / 15 CD) | **0** + namespace ERROR log |
| SimulatedAssetHTTP_IndustrialRobot_1 | **20** (1 / 4 / 15) | **0** + log |
| SimulatedAssetsHTTP_Plan_1 | **19** (1 / 3 / 15) | **0** + log |
| HumanWorker1 | **0** + log | **34** (2 / 8 / 24) |
| LEGO_machine0 | **0** + log | **32** (2 / 6 / 24) |
| SMIA_orchestrator | **0** + log | **22** (1 / 4 / 17) |

**Silent-failure mode confirmed:** in every mismatch cell basyx logs
`The following required namespaces are not declared: <its own NS> — Is the input document
of an older version?` and returns an **empty store without raising** (note the message is
wrong in half the cases — the input can be *newer*). SMIA then raises its generic
`CriticalError("The AAS model is not valid...")` via the empty-store guard
(`aas_model_utils.py:58`), which never mentions versions.

### 4.3 Namespace re-label proof (the core transformation)

In-memory swap of the namespace **declaration only** (default-xmlns form) in the v3.0
files, everything else byte-for-byte, loaded with basyx 2.2.0:

| File | Objects after swap | vs 2.0.1 baseline |
|---|---|---|
| CeDRI_PunchingMachine_instanceA | 22 (1 / 6 / 15) | **identical** |
| SimulatedAssetHTTP_IndustrialRobot_1 | 20 (1 / 4 / 15) | **identical** |
| SimulatedAssetsHTTP_Plan_1 | 19 (1 / 3 / 15) | **identical** |

⇒ V3.0→V3.1 upgrade via namespace re-label is proven lossless on the real corpus. This is
the foundation of Phase 1 and of the SMIA runtime layer.

### 4.4 basyx API facts verified against 2.2.0 (implementation enablers)

- `AASXReader.__init__` accepts `Union[os.PathLike, str, IO]` ⇒ in-memory `BytesIO`
  loading works (no temp files).
- `AASXReader.read_into(object_store, file_store, override_existing=False, **kwargs)`.
- `read_aas_xml_file(file: Union[str, bytes, os.PathLike, IO], failsafe=True)` and the
  JSON twin accept bytes / file-likes too.
- `NS_AAS` is importable: `basyx.aas.adapter.xml.xml_serialization.NS_AAS` (and in
  `xml_deserialization`), Clark notation `{https://admin-shell.io/aas/3/1}` ⇒ the target
  dialect must be **imported, never hardcoded**.
- `DictObjectStore` is deprecated (warning) in favour of `DictIdentifiableStore`.

### 4.5 Red herrings to avoid (from colleagues' investigation + ours)

- IEC 61360 references (`.../DataSpecificationTemplates/DataSpecificationIec61360/3/0`)
  contain `/3/0` in **both** corpus generations: versioned external template IDs, **not**
  environment namespace declarations — must never be touched by any transformation.
- The colleagues' reported container "hang" was an unrelated ejabberd exit, not a basyx
  issue. Don't chase ghosts when adding evidence.

### 4.6 basyx JSON adapter facts (verified 2026-11-18; sources: basyx-python-sdk source at
### tags 2.0.1 and 2.2.0 on GitHub, fetched 2026-11-18)

These facts ground SPEC-001's JSON **detect-only** scope (TD-001) and defer JSON migration to
a dedicated evidence cycle:

- **J1 — AASXReader supports JSON parts:** `AASXReader._parse_aas_part` dispatches by content
  type/extension to `read_aas_json_file` (source: `sdk/basyx/aas/adapter/aasx.py` @2.2.0).
  SMIA can therefore read JSON AASX parts.
- **J2 — basyx never validates a JSON version marker:** the JSON deserializers of 2.0.1 and
  2.2.0 parse by `modelType`/attributes only; neither reads nor checks `@context`; there is
  no JSON equivalent of `NS_AAS` (source: `json_deserialization.py` @2.0.1 and @2.2.0).
- **J3 — basyx never writes `@context`:** `object_store_to_json`/`write_aas_json_file` emit
  only the categorized object dicts (source: `json_serialization.py` @2.2.0). JSON files
  produced by basyx carry **no version marker at all** → their version is undetectable by any
  basyx-based mechanism.
- **J4 — the dialect manifests in JSON only through attribute strictness:** e.g. 2.0.1
  requires `entityType`, `contentType`, `RelationshipElement/first|second` (mandatory in
  V3.0), while 2.2.0 accepts their absence (optional in V3.1) (source: constructor comparison
  @2.0.1 vs @2.2.0). A V3.1 JSON document loaded with 2.0.1 fails per-object (failsafe: logs
  and **silently skips**) rather than failing as a whole.

**Consequences:** (a) JSON detection must peek `@context` ourselves, and files without it are
fail-closed "undetectable"; (b) an XML-style evidence gate is **not meaningful for JSON**
(both dialects parse any `@context` identically), so a JSON re-label cannot be stamped as
proven by the current gate; (c) JSON migration needs its own evidence cycle (corpus/fixtures,
possibly JSON-Schema validation with its own decision) before any rule is approved.

Also recorded (packaging evidence for ADR-022, fetched 2026-11-18): licences verified via
PyPI JSON / GitHub API — basyx-python-sdk 2.2.0 MIT (transitives: lxml BSD-3,
python-dateutil BSD-3, pyecma376-2 Apache-2.0), typer 0.29.2 MIT (transitives permissive:
pydantic MIT, rich MIT, shellingham ISC, colorama BSD), pytest MIT (**CVE-2025-71176 /
GHSA-6w46-j5rx-g56g fixed in 9.0.3 → require >=9.0.3**), ruff MIT, build 1.4.0 MIT, mypy MIT.

## 5. SMIA repository facts (verified 2026-11-18, SMIA repo @ v1.0.3.4)

- `pyproject.toml`: `basyx-python-sdk ~= 2.0.1`, `requires-python >= 3.10`.
- **Pin drift (4 different versions across the repo):** `docker/requirements.txt` == 1.2.0,
  `Dockerfile_SMIA_I_KB` == 1.2.0, `docs/requirements.txt` ~= 1.2.1, `README.md` 1.2.1.
  The operative pin is pyproject's (image builds run `pip install smia` from PyPI on
  `python:3.12-alpine`), so fixing pyproject fixes the images — no ad-hoc
  `pip install --upgrade` in Dockerfiles.
- ~12 files under `src/smia/` import `basyx.*` (model access, adapters, traversal).
- Read paths: `.json`, `.xml`, `.aasx` files + AAS-Repository (`FromAASId`, JSON).
  **No AASX write path** in SMIA (`AASXWriter` only in colleagues' manufacturing tooling).
- Documented debt: `extended_aas_model.py:276` TODO (Spanish) — the `Operation` workaround
  must be removed when basyx ≥2.1.0 (release notes echo it); walk_submodel PR #465 makes it
  duplicate OperationVariables in semanticID searches.
- SMIA has no star-imports of `basyx.aas.adapter.xml/json` (verified) ⇒ unaffected by the
  2.2.0 `__all__` change.

## 6. Colleagues' manufacturing stack (context from their report, unverified where noted)

- Toolchain: basyx-python-sdk 2.2.0, AASX Package Explorer v2025-10-21.
- 10 AASX files already namespace-migrated to v3.1 by hand (same swap procedure) and E2E
  verified: boot + 2 real FIPA-CNP negotiations + AASX `OrderHistory` **write-back**
  (`aasx_order_sync.AASXWriter`) re-validated as v3.1.
- Their Dockerfiles pin `basyx-python-sdk==2.1.0` via a post-`FROM` pip upgrade
  (inconsistent with their own 2.2.0 baseline — noted as an anti-pattern to avoid:
  patch the dependency source, not the Dockerfile).
- Caveat they missed: their E2E did not exercise the `extended_aas_model.py:276` path;
  "no SMIA code needed patching" is incomplete (see §5 debt).
