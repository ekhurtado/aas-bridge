---
title: "Migración de AAS V3.0 a V3.1"
source: https://claude.ai/share/7a31a6f0-b679-44c7-8660-ff65e536d5d1
snapshot_id: 7a31a6f0-b679-44c7-8660-ff65e536d5d1
conversation_id: a575feef-711c-437e-8ab9-d5f396c78566
shared_at: 2026-11-18T11:34:16Z
creator: Ekaitz
turns: 2
extracted_at: 2026-11-18
---

# Claude — Migración de AAS V3.0 a V3.1

> Transcripción de una conversación compartida de Claude, convertida a Markdown desde el enlace público. El texto de las respuestas se conserva íntegro; las búsquedas web y las fuentes consultadas quedan recogidas en un bloque de trazabilidad al final de cada turno.

| Campo | Valor |
|---|---|
| Enlace original | <https://claude.ai/share/7a31a6f0-b679-44c7-8660-ff65e536d5d1> |
| Snapshot | `7a31a6f0-b679-44c7-8660-ff65e536d5d1` |
| Conversación | `a575feef-711c-437e-8ab9-d5f396c78566` |
| Fecha | 18/11/2026 11:34 UTC |
| Autor | Ekaitz |
| Turnos | 2 |

---

## Turno 1 — Usuario

Actúa como experto en desarrollo Python con agentes SPADE que deben leer modelos AAS (Asset Administration Shell) usando la librería basyx Python SDK. Analiza la siguiente problemática, piensa de forma exhaustiva como se podría resolver, y presenta la mejor opción.

Problemática: el estándar del AAS este último año ha publicado una nueva versión, pasando de la V3.0 a la V3.1. por su parte, basyx sdk hasta la versión 2.0.1 era compatible con la V3.0, y a partir de esa versión (por ejemplo en la última 2.2.0) es compatible con la V3.1 (pero no con la V3.0). Ahí está la problemática, basyx no es retrocompatible con el AAS.

Para esta problemática, veo algunos posibles desarrollos o soluciones. Te las propongo, pero no debes quedarte solamente en estas, debes analizar de forma crítica y rigurosa todas las vías posibles para obtener la más adecuada.

1. Si estamos desarrollando un agente SPADE que lee de modelos AAS usando basyx sdk, es posible añadir retrocompatibilidad con ambas versiones del AAS? Es posible lograrlo sin modificar basyx SDK?
2. Es posible abordarlo desde otra perspectiva, desarrollando un transformador o adaptador de modelos AAS? Que sea capaz de coger un fichero AASX (.aasx), que sea capaz de obtener la especificación completa y estándar del AAS (para diferentes versiones) y, dependiendo de la versión actual y la que se quiera lograr, que añada o modifique el modelo (añadiendo atributos, quitando algunos preguntando al usuario, etc.) y que sea capaz de lograr un fichero AASX (.aasx) compatible con la versión deseada

Además, para la opción 2 cual sería el stack de desarrollo más adecuado? Considerando por una parte que al ser un pipeline de migración y el script de transformación puede ser independiente (fuera del entorno Python si es necesario), y por otra parte que se debe poder obtener las especificaciones del estándar AAS (las oficiales) y tener la capacidad para modificar ficheros AASX (fichero generados por AASX Package Explorer). Complementariamente (solo como funcionalidad añadida si es posible), sería adecuado una interfaz y uso por parte del usuario que no requiera demasiado conocimiento, es decir, una interfaz amigable y sencilla, preferiblemente visual

## Turno 1 — Claude

### Análisis y recomendación: compatibilidad AAS V3.0 / V3.1 en agentes SPADE con BaSyx

#### 0. Una corrección de partida

Los datos que he comprobado en las notas de release oficiales:

| basyx-python-sdk | Metamodelo implementado |
|---|---|
| 2.0.0 (y 2.0.x) | Part 1 **v3.0.1**, API v3.0, AASX v3.0 |
| **2.1.0** | Part 1 **v3.1.2**, API v3.1, IEC 61360 v3.1.1, AASX v3.1 |

El salto de versión es por tanto en la **2.1.0**, no en 2.0.1. No he podido confirmar el contenido de la 2.2.0, pero entiendo que sigue la línea 3.1.

#### 1. Diagnóstico: el delta real es pequeño y asimétrico

Esto condiciona toda la solución. Los cambios de metamodelo V3.0 → V3.1 que he podido verificar son, en su mayoría, **relajaciones o ajustes de tipos**:

- `ValueReferencePair/valueId` pasa de obligatorio a opcional.
- `ValueTypeIec61360` amplía longitud de 2000 a 2048.
- BaSyx 2.1.0 hace opcionales `first`/`second` en relaciones y `contentType` en `Blob`/`File`.
- BaSyx 2.1.0 ajusta el tipo de referencia de `dataSpecification` en JSON, que es un candidato claro a romper ficheros 3.0.
- La mayor parte de las novedades de Part 2 (bulk, queries, Discovery) afectan a la API, no a leer ficheros AASX.

Consecuencias:

- **Subir 3.0 → 3.1** es casi siempre sin pérdida y con pocas reglas.
- **Bajar 3.1 → 3.0** es potencialmente con pérdida: lo que ahora es opcional debe volver a ser obligatorio. Aquí sí hay que rellenar valores o preguntar al usuario.
- Los cambios de forma (espacio de nombres XML, relaciones OPC del AASX, `modelType`) **no los he verificado**. Hay que comprobarlos empíricamente (ver §6).

#### 2. Pregunta 1: ¿retrocompatibilidad en el agente sin tocar BaSyx?

Sí. Estas son las vías, evaluadas:

| Vía | Veredicto |
|---|---|
| A. Fijar `basyx<2.1` | Rápida, pero es un callejón sin salida: no lees 3.1 y acumulas deuda. Solo como parche. |
| B. Dos entornos virtuales y subprocesos (un worker por versión) | Robusta pero pesada: IPC, despliegue doble y ciclo de vida de procesos. Útil solo si necesitas *escribir* en ambas versiones con BaSyx. |
| C. Copia de BaSyx con el espacio de nombres renombrado | Frágil: `basyx` es un paquete con espacio de nombres y las dependencias internas se rompen. No lo recomiendo. |
| **D. `aas-core3.0` + `aas-core3.1` en el mismo proceso** | Muy interesante. Son paquetes independientes con módulos distintos (`aas_core3_1.types`, `.jsonization`, `.xmlization`, `.verification`). Conviven sin conflicto. Ofrecen tipado, (de)serialización y verificación de constraints. |
| **E. Normalizar al entrar** (3.0 → 3.1 a nivel de dict/XML) y leer con `basyx>=2.1` | Muy práctico dado que el delta es mayormente relajaciones. |
| **F. Fachada interna** (puerto `AASReader` con modelo de dominio propio) | Es lo que aísla al agente de cualquier cambio futuro (3.2, 4.0). |

Límite de D: `aas-core` solo cubre el metamodelo (JSON/XML), **no el empaquetado AASX**. El zip/OPC lo gestionas tú con `zipfile` o con `pyecma376-2`, que ya usa BaSyx.

**Mi propuesta para el agente: E + F, con D como detector y validador.** El agente depende de `basyx>=2.1`. Una capa de ingesta detecta la versión (validando contra los esquemas oficiales 3.0.8 y 3.1.x, no fiándose de metadatos). Si es 3.0, aplica el upgrade en memoria antes de pasárselo a BaSyx.

```python
# aas_ingest.py: núcleo independiente de SPADE
import io, zipfile, json
from dataclasses import dataclass


@dataclass
class Loaded:
    store: object  # basyx DictObjectStore / IdentifiableStore
    files: object  # SupplementaryFileContainer
    source_version: str


def detect_version(json_doc: dict) -> str:
    # validar contra schema 3.1 primero; si falla, contra 3.0.8
    ...


def upgrade_30_to_31(doc: dict) -> dict:
    # reglas declarativas (pocas, la mayoría son no-ops)
    ...


def load_aasx(data: bytes) -> Loaded:
    from basyx.aas.adapter import aasx

    with zipfile.ZipFile(io.BytesIO(data)) as z:
        # si la versión es 3.0: reescribir aasx/*.json|xml y relaciones en un
        # zip en memoria con upgrade_30_to_31, y pasarlo a AASXReader
        ...
```

```python
# En el agente SPADE (asyncio): BaSyx es síncrono y bloqueante
import asyncio
from spade.behaviour import CyclicBehaviour


class ReadAAS(CyclicBehaviour):
    async def run(self):
        msg = await self.receive(timeout=10)
        if msg:
            loop = asyncio.get_running_loop()
            loaded = await loop.run_in_executor(None, load_aasx, msg.body_bytes)
            ...
```

Detalle importante: no pases objetos de BaSyx dentro de los mensajes entre agentes. Serializa a JSON.

#### 3. Pregunta 2: ¿un transformador AASX entre versiones?

**Sí, es viable y razonable como herramienta independiente**, con tres matices que conviene tener claros desde el principio:

1. **"Obtener la especificación completa" solo se puede automatizar en parte.** Los JSON Schema y XSD oficiales (repositorio `admin-shell-io/aas-specs-metamodel`, con tags por versión como V3.0.8 o v3.1.x) capturan la estructura, pero **no todos los constraints** (los `AASd-xxx`). Esos los cubre la verificación de `aas-core`. Mi recomendación es fijar y versionar los esquemas dentro del repo con su hash, en lugar de descargarlos en tiempo de ejecución (reproducibilidad). Un script opcional puede actualizarlos.
2. **El diff de esquemas detecta qué cambió, pero no qué hacer.** Puedes automatizar la detección de diferencias estructurales y generar un informe. La semántica de la migración (qué valor poner, qué descartar) son **reglas escritas a mano y revisadas**, en un catálogo declarativo por par de versiones.
3. **Solo la dirección descendente necesita interacción con el usuario.** Por ejemplo, si un `Blob` no tiene `contentType` y 3.0 lo exige, hay que proponer un valor o preguntar. En el upgrade casi nunca hace falta.

##### Pipeline propuesto

```
.aasx → [descomprimir OPC] → [detectar versión] → parsear con aas-core (versión origen)
      → a JSON (lingua franca) → [reglas de transformación + decisiones del usuario]
      → deserializar con aas-core (versión destino) → verificar constraints
      → serializar → [re-empaquetar OPC conservando ficheros adjuntos, miniatura y relaciones]
      → validar (esquema + round-trip con BaSyx/compliance tool) → informe de cambios
```

Puntos críticos del AASX:

- Se edita **reescribiendo el zip**, no con AASX Package Explorer.
- Hay que preservar `[Content_Types].xml`, las relaciones, los ficheros suplementarios y la miniatura.
- Las diferencias de Part 5 (AASX) entre v3.0 y v3.1 hay que verificarlas con ficheros reales.

#### 4. Stack recomendado para el migrador

| Opción | Pros | Contras |
|---|---|---|
| **Python** (`zipfile`, `lxml`, `jsonschema`, `aas-core3.0`+`aas-core3.1`, `typer`) | Ambas versiones en un proceso. Reutiliza el conocimiento del equipo. Funciona como librería, CLI y worker. | No es nativo del ecosistema de Package Explorer. |
| .NET (C#) | Máxima afinidad con AASX Package Explorer, que está hecho en C#. Existen paquetes `aas-core` para C#. | Cambias de ecosistema. No he verificado el soporte de 3.1 en C#. |
| TypeScript | `aas-core` tiene variantes en TS. Permite una web que se ejecute entera en el navegador, sin servidor. | Menos madurez para manejo de OPC. |

**Recomendación: núcleo en Python**, empaquetado para que no dependa del entorno del agente:

- Un CLI (`aas-migrate in.aasx --to 3.1 -o out.aasx`).
- Un contenedor Docker o un binario con PyInstaller/`uv`, que cumple tu requisito de pipeline independiente.
- El agente SPADE puede llamarlo como librería o como proceso externo.

Una comprobación previa antes de invertir: mira si la **versión actual de AASX Package Explorer ya abre un .aasx 3.0 y lo guarda como 3.1**. Si lo hace, el migrador solo necesita cubrir automatización por lotes y la dirección descendente.

#### 5. Interfaz visual (funcionalidad añadida)

Una capa fina sobre el mismo núcleo, sin lógica propia:

- **NiceGUI o Streamlit**: arrastrar y soltar el .aasx, ver versión detectada, elegir versión destino, pantalla de diferencias y formularios para las decisiones ("este elemento no tiene `contentType`: ¿valor?"), y botón de descarga más informe de cambios.
- Alternativa sin instalación: web en TypeScript totalmente en el navegador.

#### 6. Plan y mejor opción global

**Mejor opción: arquitectura en capas.**
1. **Agente**: `basyx>=2.1` detrás de una fachada, con normalización de entrada 3.0 → 3.1 (vías E + F).
2. **Migrador**: núcleo Python independiente (CLI + Docker) con `aas-core3.0`/`aas-core3.1`, reglas declarativas y verificación. La GUI es opcional.
3. **Primer paso empírico**: pasa tu corpus real de .aasx por `basyx 2.1.0` y registra cada error. Ese listado define con precisión las reglas mínimas de migración, y evita construir un transformador genérico para cambios que quizá no te afecten.

**Lo que no he verificado**: el espacio de nombres XML y las relaciones OPC entre versiones, qué construcciones exactas de 3.0 rechaza BaSyx 2.1+, el nombre del módulo de `aas-core3.0` (presumiblemente `aas_core3`) y el soporte de 3.1 en C#. Todo ello se resuelve en minutos con el corpus del primer paso.

Si quieres, el siguiente paso útil es que te prepare el esqueleto del repositorio del migrador (estructura, catálogo de reglas y CLI) o el script de diagnóstico del corpus.

<details>
<summary>Trazabilidad del turno</summary>

**Preámbulo de trabajo**

> Voy a verificar primero el estado actual de basyx-python-sdk y los cambios reales entre V3.0 y V3.1, para no basar el análisis en supuestos.

**Búsquedas web realizadas**

1. `basyx-python-sdk release AAS V3.1 breaking changes`
2. `IDTA AAS Part 1 Metamodel V3.1 changes compared to V3.0.1 JSON schema differences`
3. `aas-core3.1-python PyPI aas-core3.0-python import aas_core3_1 coexist`

**Fuentes consultadas (23)**

- [github.com](https://github.com/eclipse-basyx/basyx-python-sdk/releases/tag/2.1.0)
- [Eclipse BaSyx Eclipse BaSyx 2.1.0 (Python)](https://projects.eclipse.org/projects/dt.basyx/releases/eclipse-basyx-2.1.0-python/review)
- [Eclipse BaSyx 2.0.0 (Python)](https://projects.eclipse.org/projects/dt.basyx/releases/2.0.0-python/review)
- [Eclipse BaSyx 1.0.0 (PYTHON)](https://projects.eclipse.org/projects/dt.basyx/releases/1.0.0-python)
- [Eclipse BaSyx Eclipse BaSyx 2.1.0 (Python)](https://projects.eclipse.org/node/35987)
- [Eclipse BaSyx 2.0.0 (Python)](https://projects.eclipse.org/node/32902)
- [Releases: eclipse-basyx/basyx-python-sdk](https://gh.r-mj.com/eclipse-basyx/basyx-python-sdk/releases)
- [github.com](https://github.com/admin-shell-io/aas-specs/issues/299)
- [Change Notes](https://rwth-iat.github.io/aas-specs-antora/IDTA-01002/v3.1/changelog.html)
- [Change Notes](https://zrgt.github.io/aas-specs-antora/IDTA-01002/v3.1/changelog.html)
- [admin-shell-io.github.io](https://admin-shell-io.github.io/aas-specs-antora/IDTA-01003-a/v3.1/changelog.html)
- [aas specs](https://www.github.com/admin-shell-io/aas-specs)
- [rwth-iat.github.io](https://rwth-iat.github.io/aas-specs-antora/part1puml/puml/index.html)
- [admin-shell-io.github.io](https://admin-shell-io.github.io/aas-specs-antora/IDTA-01002/v3.1/changelog.html)
- [github.xiaohuzi123231346.workers.dev](https://github.xiaohuzi123231346.workers.dev/admin-shell-io/aas-specs-metamodel/commit/0be69759372d8cd50f98850f9cc9ea8ce200455d)
- [IDTA 01003 a 3 0 2 SpecificationAssetAdministrationShell Part3a DataSpecification IEC613601](https://industrialdigitaltwin.org/wp-content/uploads/2024/07/IDTA-01003-a-3-0-2_SpecificationAssetAdministrationShell_Part3a_DataSpecification_IEC613601.pdf)
- [github.com](https://github.com/aas-core-works/aas-core3.0-python/pull/36)
- [aas core3 1](https://pypi.org/project/aas-core3-1/)
- [aas-core31-python.readthedocs.io](https://aas-core31-python.readthedocs.io/en/latest/)
- [data.safetycli.com](https://data.safetycli.com/packages/pypi/aas-core3.0/changelog?page=1)
- [pypi.org](https://pypi.org/project/aas-core3.0/1.0.3)
- [aas-core31-python.readthedocs.io](https://aas-core31-python.readthedocs.io/en/latest/_modules/index.html)
- [Ecosyste.ms: Packages](https://packages.ecosyste.ms/registries/pypi.org/packages/aas-core3.0)

</details>

---

## Turno 2 — Usuario

Como llamarías a esta aplicación, considerando que su objetivo es la compatibilidad de AAS y de AASX?

## Turno 2 — Claude

Mi propuesta principal es **AASBridge**.

Es corto y fácil de recordar. Comunica la idea de "puente entre versiones" y no queda ligado a V3.0 y V3.1, así que sigue valiendo cuando salga la 3.2 o la 4.0. El CLI sería `aasbridge`, y el paquete Python `aasbridge`.

Otras opciones, según el matiz que quieras destacar:

| Nombre | Matiz |
|---|---|
| **AASmigrate** | Muy descriptivo: es una herramienta de migración. Ideal si el uso principal es convertir ficheros. |
| **AASX-Compat** | Directo, y hace explícito que trabaja con ficheros AASX y con compatibilidad. |
| **AASync** | Juego de palabras con *sync*: mantener los modelos alineados con la versión del estándar. |
| **AASlate** | De *translate*: sugiere traducir entre versiones. Original, pero menos evidente a primera vista. |
| **VersaAAS** | Transmite versatilidad y soporte multiversión. |
| **AASX Rosetta** | Referencia a la piedra Rosetta: un traductor entre "idiomas" del estándar. Evocador, aunque más largo. |
| **AASUpgrade** | Útil si el foco es subir de versión, pero no refleja la dirección descendente. |

Si la herramienta crece con interfaz visual y distintos módulos, **AASBridge** admite subproductos naturales como *AASBridge Studio* para la GUI o *AASBridge Core* para la librería.

Antes de decidirte, comprueba que el nombre esté libre en PyPI y GitHub, y que no se confunda con alguna iniciativa existente del ecosistema AAS o de la IDTA. Si quieres, puedo ayudarte a descartar conflictos y a pensar en un nombre de paquete y de comando que no choquen con otros.
