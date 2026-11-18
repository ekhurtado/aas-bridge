# templates/PROMPTS.md — Ready-to-Paste Agent Prompts

> These prompts are for the human. Replace the `<...>` fields. The agents read the referenced
> files; do not paste their contents into chat.

## 1. Architect — new feature or phase

```text
Actúa como `architect` (`.ai/agents/architect.md`).

Lee `.ai/README.md`, `.ai/PROJECT_BRIEF.md`, `.ai/CONSTITUTION.md`, `.ai/CONVENTIONS.md`,
`.ai/ARCHITECTURE.md`, `.ai/ROADMAP.md`, `.ai/IMPLEMENTATION_SPEC.md` y la sección abierta de
`.ai/history/ISSUES.md`.

Petición: <describe la feature/fase en 3-6 líneas>.

No escribas el SPEC todavía. Debate conmigo en 3-4 rondas máximo: por cada decisión, explica
por qué importa, dame 2-4 opciones y una recomendación. Después propone el plan y espera
`APROBADO` antes de escribir `.ai/IMPLEMENTATION_SPEC.md`.

Si la petición depende de hechos de versión, carga `aas-version-research`. Si cambia ley,
arquitectura, interfaz, dependencia o topología, carga `adr-writing`. Si `ui_scope != none`,
carga `ui-contract-authoring`.
```

## 2. Code Executor — implement the active SPEC

```text
Actúa como `code-executor` (`.ai/agents/code-executor.md`).

SPEC activo: `.ai/IMPLEMENTATION_SPEC.md` (`SPEC-XXX`, `Status: active`).
Lee el SPEC completo, `.ai/CONSTITUTION.md`, `.ai/CONVENTIONS.md`, la sección relevante de
`.ai/ARCHITECTURE.md`, `.ai/contracts/UI_SPEC.md` + `.ai/contracts/DESIGN.md` si `ui_scope != none`,
y la sección abierta de `.ai/history/ISSUES.md`.

Implementa solo los ficheros del SPEC. Ejecuta los checks declarados y registra la evidencia.
Lanza el subagente `reviewer` con el SPEC, el diff y la evidencia. Corrige los defectos
`CRITICAL`/`MAJOR` y repite como máximo dos loops. Actualiza el estado `.ai/` permitido y
entrega el handoff en español. No hagas commit.
```

## 3. Reviewer subagent — audit a handoff

```text
Actúa como `reviewer` (`.ai/agents/reviewer.md`).

SPEC: `.ai/IMPLEMENTATION_SPEC.md` (`SPEC-XXX`).
Diff y ficheros: <lista o `git diff`>.
Evidencia del executor: <comandos, resultados, gate, verificación manual>.

Audita el diff contra SPEC §2-§7, `CONVENTIONS.md`, `CONSTITUTION.md` y los contratos UI.
Carga `verification-gate`, `spec-compliance-audit` y, si aplica, `ui-review`,
`manual-verification` y `dependency-review`.

Devuelve un `QA-REPORT` con veredicto `PASS` o `FAIL`, defectos clasificados
(`CRITICAL`/`MAJOR`/`MINOR`), evidencia exacta y siguiente paso. No edites ficheros.
```

## 4. Close a cycle (after PASS + human approval)

```text
Actúa como `code-executor` en modo cierre.

SPEC: `SPEC-XXX` (`PASS` del reviewer + `APROBADO` humano).
Archiva `SPEC.md` y `OUTCOME.md` en `.ai/history/specs/SPEC-XXX_<slug>/`.
Actualiza `.ai/history/SESSION_LOG.md`, `.ai/history/ISSUES.md`, `.ai/ROADMAP.md` y resetea
`.ai/IMPLEMENTATION_SPEC.md` a `Status: none`.
Redacta el mensaje de commit (no lo ejecutes).
```

## 5. Manual verification (human)

```text
He ejecutado la verificación manual del SPEC-XXX:
- Entorno: <SO, Python, navegador/Docker>
- Entrada: <fichero(s)>
- Pasos: <1, 2, 3>
- Resultado observado: <texto, captura o salida>
- Resultado esperado: <según el SPEC>

Valida esta evidencia como `reviewer` e indícame si el ciclo puede cerrarse.
```
