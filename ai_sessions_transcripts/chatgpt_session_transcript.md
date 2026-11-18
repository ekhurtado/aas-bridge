---
title: "Compatibilidad AAS y BaSyx"
source: https://chatgpt.com/share/6afd8874-d074-83eb-98dc-c75e051e09d0
conversation_id: 6afd8874-d074-83eb-98dc-c75e051e09d0
shared_at: 2026-11-18T11:13:56Z
model: gpt-6-t-mini
model_setting: auto
turns: 2
extracted_at: 2026-11-18
---

# ChatGPT — Compatibilidad AAS y BaSyx

> Transcripción de una conversación compartida de ChatGPT, convertida a Markdown desde el enlace público. Se ha conservado el texto íntegro; los componentes visuales de la interfaz (tarjetas, insignias, rejillas, iconos) se han traducido a Markdown equivalente y las citas se han resuelto a sus fuentes originales.

| Campo | Valor |
|---|---|
| Enlace original | <https://chatgpt.com/share/6afd8874-d074-83eb-98dc-c75e051e09d0> |
| Conversación | `6afd8874-d074-83eb-98dc-c75e051e09d0` |
| Fecha | 18/11/2026 11:13 UTC |
| Modelo | `gpt-6-t-mini` |
| Turnos | 2 |

---

## Turno 1 — Usuario

Actúa como experto en desarrollo Python con agentes SPADE que deben leer modelos AAS (Asset Administration Shell) usando la librería basyx Python SDK. Analiza la siguiente problemática, piensa de forma exhaustiva como se podría resolver, y presenta la mejor opción.

Problemática: el estándar del AAS este último año ha publicado una nueva versión, pasando de la V3.0 a la V3.1. por su parte, basyx sdk hasta la versión 2.0.1 era compatible con la V3.0, y a partir de esa versión (por ejemplo en la última 2.2.0) es compatible con la V3.1 (pero no con la V3.0). Ahí está la problemática, basyx no es retrocompatible con el AAS.

Para esta problemática, veo algunos posibles desarrollos o soluciones. Te las propongo, pero no debes quedarte solamente en estas, debes analizar de forma crítica y rigurosa todas las vías posibles para obtener la más adecuada.

1. Si estamos desarrollando un agente SPADE que lee de modelos AAS usando basyx sdk, es posible añadir retrocompatibilidad con ambas versiones del AAS? Es posible lograrlo sin modificar basyx SDK?
2. Es posible abordarlo desde otra perspectiva, desarrollando un transformador o adaptador de modelos AAS? Que sea capaz de coger un fichero AASX (.aasx), que sea capaz de obtener la especificación completa y estándar del AAS (para diferentes versiones) y, dependiendo de la versión actual y la que se quiera lograr, que añada o modifique el modelo (añadiendo atributos, quitando algunos preguntando al usuario, etc.) y que sea capaz de lograr un fichero AASX (.aasx) compatible con la versión deseada

Además, para la opción 2 cual sería el stack de desarrollo más adecuado? Considerando por una parte que al ser un pipeline de migración y el script de transformación puede ser independiente (fuera del entorno Python si es necesario), y por otra parte que se debe poder obtener las especificaciones del estándar AAS (las oficiales) y tener la capacidad para modificar ficheros AASX (fichero generados por AASX Package Explorer). Complementariamente (solo como funcionalidad añadida si es posible), sería adecuado una interfaz y uso por parte del usuario que no requiera demasiado conocimiento, es decir, una interfaz amigable y sencilla, preferiblemente visual

## Turno 1 — ChatGPT

### Análisis arquitectónico: compatibilidad entre AAS V3.0, V3.1 y BaSyx Python SDK

#### 1. Conclusión ejecutiva

La problemática que planteas es real y merece abordarse desde una perspectiva arquitectónica, no simplemente intentando adaptar unas cuantas clases de BaSyx.

Mi recomendación es desarrollar una **capa de interoperabilidad AAS independiente del SDK BaSyx**, compuesta por dos funcionalidades:

1. **Adaptador de compatibilidad en tiempo de ejecución:** permite que los agentes SPADE trabajen con modelos AAS de diferentes versiones sin tener que modificar BaSyx ni migrar permanentemente los ficheros originales.
2. **Herramienta de migración AASX:** permite convertir paquetes AASX entre versiones, con análisis previo de incompatibilidades, transformaciones automáticas, decisiones asistidas por el usuario y validación mediante los esquemas oficiales.

No recomendaría elegir exclusivamente una de estas soluciones. Resuelven necesidades distintas y, combinadas, proporcionan una arquitectura bastante más robusta.

Hay, además, una actualización importante que afecta al planteamiento inicial: **a fecha de 11 de noviembre de 2026, ya existe AAS V3.2**. La versión 3.2.0 del metamodelo fue publicada en julio de 2026. Por tanto, diseñaría la solución para trabajar con versiones de metamodelo explícitas y extensibles, no solamente para solucionar la transición 3.0 → 3.1. [^t1-1][^t1-2][^t1-3]

Esto último es importante: conviene desarrollar una solución que siga siendo válida cuando aparezca una nueva versión de la especificación, sin tener que volver a diseñar toda la arquitectura.

---

#### 2. Diagnóstico: ¿cuál es exactamente el problema de compatibilidad?

Antes de decidir cómo resolverlo, hay que distinguir cuatro elementos que a veces se mezclan:

| Elemento | Función |
|---|---|
| AAS Metamodel (Part 1) | Define las clases, atributos, relaciones, restricciones y estructura del modelo AAS. |
| AAS API (Part 2) | Define cómo interactuar con repositorios y servicios AAS. |
| Data Specification (Part 3a) | Define especificaciones de datos complementarias, como IEC 61360. |
| AASX Package File Format (Part 5) | Define cómo empaquetar modelos AAS y sus recursos en un fichero AASX. |

La incompatibilidad entre versiones no tiene por qué afectar de la misma manera a los cuatro elementos.

Por ejemplo, un fichero AASX puede conservar una estructura de empaquetado válida y, sin embargo, contener un JSON cuyo metamodelo no sea compatible con la versión del SDK que intenta interpretarlo.

##### 2.1. Compatibilidad real de las versiones de BaSyx

He contrastado las notas oficiales de las versiones del SDK.

| BaSyx Python SDK | Metamodelo AAS implementado | Situación |
|---|---|---|
| 1.2.1 | 3.0.1 | Línea AAS 3.0 |
| 2.0.0 | 3.0.1 | Línea AAS 3.0 |
| 2.0.1 | 3.0.1 | Línea AAS 3.0 |
| 2.1.0 | 3.1.2 | Línea AAS 3.1 |
| 2.2.0 | 3.1.2 | Línea AAS 3.1 |

Fuentes: notas oficiales de las versiones de [BaSyx Python SDK](https://github.com/eclipse-basyx/basyx-python-sdk/releases) y [BaSyx 2.2.0](https://projects.eclipse.org/projects/dt.basyx/releases/2.2.0-python). [^t1-4][^t1-5]

Hay dos matices relevantes:

- La incompatibilidad se produce por la versión de especificación implementada, no porque el número mayor del SDK haya cambiado de 1 a 2.
- La versión 2.2.0 no introduce un cambio de metamodelo respecto a la 2.1.0. De hecho, es fundamentalmente una actualización de mantenimiento.

Por tanto, no debemos interpretar que BaSyx 2.2.0 sea compatible automáticamente con todas las versiones AAS 3.x.

**Estado de las especificaciones a noviembre de 2026**

BaSyx 2.2.0 — **AAS 3.1.2**

Último metamodelo IDTA — **AAS 3.2.0**

Existe, por tanto, una segunda brecha de compatibilidad: el SDK 2.2.0 todavía no implementa el metamodelo 3.2.0.

Esto refuerza mi recomendación: implementar una arquitectura de interoperabilidad por versiones, en lugar de crear una solución específica para 3.0 y 3.1.

#### 3. Qué diferencias existen realmente entre AAS 3.0 y 3.1

Esta sección es especialmente importante porque determina qué puede automatizarse y qué no.

La IDTA publica un registro oficial de cambios del metamodelo. No es necesario deducir las diferencias comparando manualmente dos documentos PDF.

[Change Log oficial del metamodelo AAS](https://industrialdigitaltwin.io/aas-specifications/IDTA-01001/v3.2/changelog.html).

##### 3.1. Cambios entre 3.0 y 3.1

Estos son algunos de los cambios que debe considerar cualquier conversor:

| Elemento | AAS 3.0 | AAS 3.1 | Implicación |
|---|---|---|---|
| `AssetKind` | Instance, Type | Se añade Role | Una conversión inversa necesita una decisión. |
| `idShort` | No permite guiones | Permite guiones | Puede ser necesario renombrar identificadores. |
| `Entity.entityType` | Obligatorio | Opcional | Al convertir hacia 3.0 hay que recuperar el dato. |
| `File.contentType` | Obligatorio | Opcional | Hay que inferir o solicitar el MIME type. |
| `Blob.contentType` | Obligatorio | Opcional | Mismo problema. |
| `RelationshipElement.first` | Obligatorio | Opcional | Puede faltar información necesaria para 3.0. |
| `RelationshipElement.second` | Obligatorio | Opcional | Mismo problema. |
| `Identifier` | Máximo 2.000 caracteres | Máximo 2.048 | Un identificador puede no ser válido al retroceder. |
| `ContentType` | Máximo 100 caracteres | Máximo 128 | Posible incompatibilidad en la conversión inversa. |
| `BasicEventElement.lastUpdate` | DateTime | DateTimeUtc | Se debe tratar correctamente la semántica temporal. |

La tabla resume los cambios documentados por la IDTA. [^t1-6]

##### 3.2. ¿Qué significa esto para una migración?

Consideremos dos situaciones.

**Caso A: AAS 3.0 → AAS 3.1**

Es una conversión generalmente sencilla.

Un modelo 3.0 que cumple su especificación normalmente seguirá siendo válido en 3.1. No es necesario añadir todos los nuevos atributos que admite la versión 3.1.

Por ejemplo, si un `File` contiene su `contentType`, no hay que modificarlo. Si no se utiliza ninguna funcionalidad nueva, la conversión puede consistir fundamentalmente en validar y serializar correctamente.

**Caso B: AAS 3.1 → AAS 3.0**

Es considerablemente más complejo.

Imaginemos este modelo:

```json
{
  "modelType": "Entity",
  "entityType": "SelfManagedEntity",
  "globalAssetId": "urn:example:asset:123"
}
```

La representación 3.1 también puede admitir que `entityType` no esté especificado.

Sin embargo, al convertir un modelo que carezca de ese atributo a 3.0, el conversor tendrá que solicitar el dato, porque no puede inventárselo.

Lo mismo sucede con:

- Un elemento `File` sin `contentType`.
- Un `RelationshipElement` sin `first` o `second`.
- Un `AssetKind.Role`, que no tiene equivalente directo en 3.0.
- Un `idShort` que contiene guiones.
- Un identificador que supera los 2.000 caracteres.

Es decir, **la conversión 3.1 → 3.0 debe ser semánticamente consciente**, no una simple operación de serialización.

##### 3.3. Hay que considerar también AAS 3.2

La versión 3.2 introduce cambios adicionales:

| Elemento | Cambio |
|---|---|
| `AdministrationInformation.createdAt` | Nuevo atributo. |
| `AdministrationInformation.updatedAt` | Nuevo atributo. |
| `AssetKind.Batch` | Nuevo valor de enumeración. |
| `Range` | Se modifica la interpretación de los límites no especificados. |

El cambio de `Range` está marcado expresamente como no retrocompatible para este elemento experimental. No debe realizarse una conversión automática que modifique su interpretación sin analizar el impacto. [^t1-6]

Además, ya existe una implementación Python independiente para AAS 3.2:

- `aas-core3.2-python`, versión `1.0.0rc2`, publicada el 29 de octubre de 2026.
- Se trata de una versión candidata (*release candidate*), por lo que todavía no la tomaría como dependencia crítica de producción sin realizar pruebas propias. [^t1-7]

Esto nos lleva a una conclusión: necesitamos un mecanismo de transformación que trabaje con reglas explícitas entre versiones, no un conjunto de modificaciones improvisadas.

---

### 4. Solución 1: retrocompatibilidad en los agentes SPADE sin modificar BaSyx

**Viable y recomendable**

La respuesta a tu primera pregunta es sí.

Es perfectamente posible proporcionar retrocompatibilidad a los agentes SPADE sin modificar el código fuente de BaSyx.

La clave es introducir una capa de abstracción entre los agentes y el SDK.

#### 4.1. Arquitectura propuesta: AAS Compatibility Layer

Actualmente, posiblemente tengas una arquitectura similar a esta:

**Agente SPADE**

Lógica de negocio y lectura de propiedades AAS

**BaSyx Python SDK 2.2.0**

Deserialización, modelo de objetos y lectura AAS

**Fichero AASX / JSON / XML**

Modelos AAS de diferentes versiones

El problema es que el agente depende directamente de la implementación y versión concreta del SDK.

Propongo esta estructura:

**Agentes SPADE**

No necesitan conocer la versión del metamodelo

**AAS Compatibility Layer**

**Interfaz común**

Detección de versión · Lectura · Normalización · Adaptación

- **AAS 3.0** — Parser 3.0
- **AAS 3.1** — BaSyx 2.2 / Parser 3.1
- **AAS 3.2** — Parser 3.2

**Modelo de datos común**

Representación independiente de la versión de origen

Lo importante es que los agentes SPADE dejan de consumir directamente las clases de un SDK concreto.

En su lugar, consumen una interfaz propia.

##### 4.2. Cómo implementar esta capa

Crearía un módulo Python independiente, por ejemplo:

```text
aas_compatibility/
│
├── core/
│   ├── interfaces.py
│   ├── models.py
│   ├── version_detector.py
│   └── exceptions.py
│
├── readers/
│   ├── aas_30_reader.py
│   ├── aas_31_reader.py
│   └── aas_32_reader.py
│
├── adapters/
│   ├── basyx_adapter.py
│   ├── aas_core_30_adapter.py
│   ├── aas_core_31_adapter.py
│   └── aas_core_32_adapter.py
│
├── normalization/
│   └── canonical_model.py
│
└── tests/
```

La interfaz de lectura podría ser:

```python
from typing import Protocol, Any


class AASReader(Protocol):
    def read_aas(self, source: str) -> Any: ...

    def read_submodel(self, aas_id: str, submodel_id: str) -> Any: ...

    def get_property_value(self, submodel_id: str, id_short: str) -> Any: ...
```

Naturalmente, en una implementación real utilizaría modelos tipados en lugar de `Any`.

El agente SPADE tendría una dependencia de la interfaz, no de BaSyx:

```python
class MyAASAgent(Agent):
    async def setup(self):

        self.aas_reader = create_aas_reader(source="models/equipment.aasx")

        submodel = await asyncio.to_thread(
            self.aas_reader.read_submodel, "urn:example:aas:001", "urn:example:submodel:001"
        )

        # Trabajar con el modelo normalizado
        # sin conocer su versión AAS de origen.
```

En este ejemplo, el acceso al fichero se ejecuta fuera del bucle de eventos del agente, evitando bloquear innecesariamente su ejecución asíncrona.

##### 4.3. ¿Qué librería utilizar para implementar cada lector?

Aquí hay una alternativa especialmente interesante.

No es obligatorio utilizar BaSyx para leer todas las versiones de AAS.

Existe un proyecto llamado **AAS Core Software Development Kits**, mantenido en el entorno de AAS Core Works, que proporciona SDK específicos para distintas versiones del metamodelo.

| Librería | Funcionalidad |
|---|---|
| [aas-core3.0-python](https://github.com/aas-core-works/aas-core3.0-python) | Manipular, verificar y deserializar modelos 3.0. |
| [aas-core3.1-python](https://github.com/eclipse-aascw/aas-core3.1-python) | Manipular, verificar y deserializar modelos 3.1. |
| [aas-core3.2-python](https://pypi.org/project/aas-core3.2/) | SDK para el metamodelo 3.2, actualmente RC. |

Estas bibliotecas se generan mayoritariamente mediante `aas-core-codegen` y proporcionan verificación de restricciones, manipulación de modelos y serialización/deserialización. [^t1-7][^t1-8][^t1-9][^t1-10]

Esta opción me parece muy atractiva porque podemos utilizar las implementaciones correspondientes a cada versión del metamodelo sin desarrollar desde cero todos los parsers.

De hecho, sus módulos Python tienen espacios de nombres diferenciados:

```python
import aas_core3
import aas_core3_1
import aas_core3_2
```

Esto permite evitar el problema de instalar simultáneamente dos versiones del mismo paquete con un espacio de nombres idéntico.

En cambio, para ejecutar dos versiones de BaSyx, recomendaría entornos virtuales o procesos aislados, ya que ambas versiones utilizan el espacio de nombres `basyx`.

**Mi propuesta sería:**

- Utilizar `aas-core3.0-python` para leer y validar modelos 3.0.
- Utilizar `aas-core3.1-python` para los modelos 3.1.
- Evaluar `aas-core3.2-python` en un entorno de pruebas.
- Mantener BaSyx 2.2.0 para las funcionalidades de BaSyx y los modelos 3.1 que se necesiten integrar con sus clases.

De este modo, no necesitamos mantener varias instalaciones incompatibles de BaSyx.

##### 4.4. Alternativa: instalar dos versiones de BaSyx en entornos separados

También sería viable:

**Proceso de lectura AAS 3.0**

Docker / entorno virtual 1

Python + basyx-python-sdk 2.0.1

---

**Proceso de lectura AAS 3.1**

Docker / entorno virtual 2

Python + basyx-python-sdk 2.2.0

---

HTTP / JSON / mensajes

**Agente SPADE principal**

Recibe datos normalizados

Esta arquitectura permite mantener ambas versiones de BaSyx sin conflictos de dependencias.

Sin embargo, tiene algunas desventajas:

- Aumenta el despliegue y mantenimiento.
- Introduce comunicación entre procesos.
- Duplica parte del código.
- Requiere mantener dos entornos de ejecución.
- Sigue sin resolver las futuras versiones AAS sin añadir nuevos lectores.

La utilizaría únicamente cuando exista una necesidad real de consumir objetos nativos de BaSyx 3.0 y 3.1, y no sea suficiente una representación normalizada.

##### 4.5. Mi valoración de la solución 1

| Alternativa | Viabilidad | Mantenimiento | Mi valoración |
|---|---|---|---|
| Modificar directamente BaSyx | Alta | Alto | No recomendable. |
| Extender decodificadores de BaSyx | Alta | Medio-alto | Posible, pero acopla demasiado la solución. |
| Adaptador con `aas-core` | Alta | Bajo-medio | **Recomendado** |
| Dos BaSyx en contenedores | Alta | Medio-alto | Alternativa especializada. |
| Convertir siempre los ficheros a 3.1 | Alta | Medio | Útil, pero altera los originales. |
| Crear un parser JSON/XML propio | Alta | Alto | No lo desarrollaría desde cero. |

**Conclusión de la solución 1:** la mejor opción es una capa de compatibilidad basada en adaptadores de versión y un modelo de datos común. BaSyx debe ser una implementación que pueda utilizar esa capa, no el elemento del que dependa toda la arquitectura.

---

### 5. Solución 2: desarrollar un transformador y migrador de modelos AASX

**Muy recomendable**

Esta solución tiene más recorrido que la primera, sobre todo si se pretende que el sistema pueda utilizarse con modelos procedentes de diferentes fabricantes, herramientas y versiones de la especificación.

La idea consiste en desarrollar una herramienta independiente que reciba un fichero AASX, determine su versión, analice el modelo y genere otro AASX compatible con la versión que se haya seleccionado.

Pero hay un aspecto fundamental que quiero destacar:

**No desarrollaría un simple conversor AASX. Desarrollaría un motor de migración de modelos AAS basado en las especificaciones oficiales de la IDTA.**

La diferencia es importante.

Un conversor simplemente cambia el formato o estructura de los datos. Un motor de migración conoce las diferencias semánticas entre versiones, identifica problemas, propone alternativas y es capaz de justificar cada transformación.

#### 5.1. ¿Es técnicamente posible?

Sí. De hecho, disponemos de prácticamente todos los elementos necesarios.

La especificación AAS está publicada de forma abierta por la IDTA, incluyendo:

- Especificación normativa del metamodelo.
- Esquemas JSON.
- Esquemas XML.
- Esquemas RDF.
- Documentación de restricciones.
- Ejemplos de serialización.
- Historial de cambios entre versiones.

La fuente principal es el repositorio oficial:

[admin-shell-io/aas-specs-metamodel](https://github.com/admin-shell-io/aas-specs-metamodel).

El propio repositorio explica que contiene la especificación normativa y los esquemas derivados del metamodelo para las distintas serializaciones. [^t1-1][^t1-2]

Por tanto, no necesitamos crear nuestras propias definiciones de las clases AAS ni interpretar manualmente la especificación PDF.

Podemos utilizar los artefactos oficiales como fuente de verdad.

#### 5.2. Comprender la estructura de un fichero AASX

Antes de desarrollar el transformador, necesitamos entender cómo se organiza el fichero.

Un AASX no es simplemente un JSON comprimido.

Es un paquete basado en **Open Packaging Conventions (OPC), ECMA-376**, que utiliza ZIP como contenedor físico.

Dentro puede haber:

- Uno o varios ficheros con modelos AAS.
- Relaciones entre los diferentes componentes del paquete.
- Archivos suplementarios.
- Documentos PDF.
- Imágenes.
- Recursos asociados a elementos `File`.
- Metadatos del paquete.
- Miniaturas.

Además, los ficheros de definición de los modelos no tienen necesariamente un nombre o ruta fija.

La especificación establece que debe utilizarse el sistema de relaciones OPC para localizar el contenido AAS, y no asumir que el modelo se encuentra siempre en una ruta determinada. [^t1-11][^t1-12]

> _Imágenes sugeridas por la interfaz: AASX Package Explorer package contents AASX file structure tree; AASX Package Explorer Asset Administration Shell submodel tree interface_

Esto tiene una consecuencia directa para nuestro desarrollo:

**No recomendaría utilizar exclusivamente `zipfile` para manipular los AASX.**

Aunque técnicamente se puede abrir y generar el ZIP con la biblioteca estándar de Python, hay que gestionar correctamente:

- Relaciones OPC.
- Tipos de contenido MIME.
- Rutas de los componentes.
- Archivos auxiliares.
- Metadatos.
- Referencias internas del paquete.

Una modificación aparentemente pequeña del ZIP podría dejar un paquete AASX estructuralmente inconsistente.

##### Biblioteca recomendada para AASX: pyecma376-2

Existe una biblioteca Python específica:

[PyECMA376-2 en PyPI](https://pypi.org/project/pyecma376-2/).

Sus funcionalidades incluyen:

| Funcionalidad | Soporte |
|---|---|
| Lectura de paquetes OPC | Sí |
| Enumeración de elementos del paquete | Sí |
| Lectura de relaciones | Sí |
| Lectura de metadatos | Sí |
| Creación de paquetes OPC | Sí |
| Añadir relaciones | Sí |
| Añadir tipos de contenido | Sí |
| Modificación in-place | No |
| Gestión de firmas criptográficas | No |

Es una opción muy interesante porque separa la gestión del contenedor de la interpretación del contenido AAS. [^t1-13]

El hecho de que no permita modificar paquetes in-place no supone un problema: podemos reconstruir el AASX de salida a partir de sus componentes originales, incorporando el modelo transformado.

Eso sí, hay que tener una precaución adicional: si el paquete incorpora firmas digitales, no se debe reconstruir como si nada. Una modificación puede invalidar las firmas. La herramienta debería detectarlas y exigir un tratamiento explícito.

---

#### 5.3. Arquitectura que desarrollaría para el motor de migración

Mi propuesta es dividir el proceso en siete fases.

#### Pipeline de migración AASX

1. **Ingesta del AASX**
   Recibir el archivo, inspeccionar su estructura OPC, verificar su integridad y extraer los componentes y recursos.
2. **Identificación y validación de la versión de origen**
   Identificar formato, metamodelo, serialización y versión de las especificaciones aplicables.
3. **Análisis de incompatibilidades**
   Comparar el modelo con la especificación de destino. Detectar atributos, enumeraciones, restricciones y estructuras problemáticas.
4. **Generación de un plan de migración**
   Crear una lista de transformaciones automáticas, cambios que requieren autorización y problemas que impiden completar la migración.
5. **Aplicación de transformaciones**
   Ejecutar las reglas aprobadas y generar un modelo AAS en la versión de destino.
6. **Validación del resultado**
   Validar estructura, esquema, restricciones semánticas, referencias y contenido del paquete.
7. **Generación del AASX final**
   Reconstruir el paquete conservando los archivos suplementarios y generando un informe de migración.

Voy a profundizar en las partes más importantes, especialmente en cómo se obtienen las especificaciones y cómo se implementan las transformaciones.

##### Fase 1. Ingesta y extracción del AASX

El primer componente debe aceptar:

```text
equipment.aasx
```

Y obtener una representación de su contenido:

```text
extracted/
│
├── aas/
│   └── environment.json
│
├── supplementary/
│   ├── datasheet.pdf
│   ├── image.png
│   └── technical_document.pdf
│
├── package_metadata/
│
└── relationships/
```

El nombre de los componentes es ilustrativo: las rutas reales deben determinarse mediante las relaciones OPC.

Recomiendo encapsular completamente esta funcionalidad en un módulo:

```python
class AASXPackageManager:
    def inspect(self, aasx_path):
        """
        Inspecciona el paquete OPC.
        """

    def extract(self, aasx_path):
        """
        Extrae modelos, recursos y metadatos.
        """

    def rebuild(self, output_path, migrated_model, package):
        """
        Reconstruye el AASX conservando
        los recursos originales.
        """
```

El motor de migración no debería tener que conocer cómo funciona internamente OPC.

##### Fase 2. Detección de la versión de origen

Este apartado requiere especial atención.

No debemos confundir:

- Versión del metamodelo AAS.
- Versión del propio Asset Administration Shell.
- Versión del Submodel.
- Versión del formato AASX.
- Versión de la API AAS.

Son conceptos distintos.

Por ejemplo, un AAS puede tener su propia información de versión y revisión sin que eso identifique inequívocamente la versión del metamodelo con el que se serializó.

Por tanto, desarrollaría un detector que utilice varias comprobaciones:

1. Identificar el formato de serialización del contenido AAS.
2. Analizar las estructuras y atributos presentes.
3. Probar los esquemas oficiales de las versiones candidatas.
4. Verificar las restricciones semánticas de cada versión.
5. Solicitar una confirmación cuando existan varias interpretaciones posibles.

El resultado podría ser:

```json
{
  "format": "AASX",
  "serialization": "JSON",
  "metamodel_version": "3.0",
  "confidence": "high",
  "validation": {
    "3.0": "valid",
    "3.1": "valid",
    "3.2": "invalid"
  }
}
```

Este resultado es ilustrativo: un modelo puede validar en más de una versión y eso no demuestra cuál fue la especificación que utilizó su creador.

Por ello, sería conveniente permitir al usuario indicar manualmente la versión de origen y registrar la procedencia cuando esté disponible.

##### Fase 3. Análisis de incompatibilidades

Esta es una de las piezas que más valor aporta al desarrollo.

Debemos disponer de un motor capaz de recibir:

```text
Modelo AAS
Versión origen: 3.1
Versión destino: 3.0
```

Y obtener un informe detallado.

Por ejemplo:

**Informe de compatibilidad** — **3 incidencias**

Origen — **AAS 3.1**

Destino — **AAS 3.0**

---

- **Incompatibilidad: AssetKind.Role**
  No existe un equivalente directo en AAS 3.0.
  **Requiere intervención**

---

- **Incompatibilidad: idShort con guion**
  Debe renombrarse el identificador y comprobar las referencias relacionadas.
  **Requiere intervención**

---

- **Incompatibilidad: File.contentType ausente**
  La versión de destino exige un atributo que no está presente.
  **Requiere intervención**

Para ello desarrollaría un registro de reglas de migración.

Por ejemplo:

| Regla | Origen | Destino | Tratamiento |
|---|---|---|---|
| `idShort` contiene guion | 3.1 | 3.0 | Solicitar renombrado |
| `AssetKind.Role` | 3.1 | 3.0 | Solicitar equivalencia |
| `File.contentType` ausente | 3.1 | 3.0 | Solicitar valor o inferir justificadamente |
| `Identifier` supera 2.000 caracteres | 3.1 | 3.0 | Bloquear o solicitar alternativa |
| `Entity.entityType` ausente | 3.1 | 3.0 | Solicitar valor |
| `RelationshipElement.first/second` ausentes | 3.1 | 3.0 | Solicitar referencias |

El motor debe distinguir cuatro tipos de cambios:

- **Automático** — **Transformaciones sin pérdida semántica.**
  Ejemplo: actualizar una representación temporal cuando su valor y significado estén inequívocamente determinados.

- **Asistido** — **Transformaciones que requieren decisión del usuario.**
  Ejemplo: seleccionar un nuevo `idShort` para un elemento.

- **Bloqueante** — **Transformaciones sin equivalencia conocida.**
  Ejemplo: una enumeración nueva que no puede representarse en la versión de destino.

- **Informativo** — **Cambios que no requieren modificación.**
  Ejemplo: una propiedad opcional que sigue cumpliendo las restricciones del destino.

Es importante que el motor no realice modificaciones destructivas silenciosas.

##### Fase 4. Generación del plan y toma de decisiones

No ejecutaría directamente todas las transformaciones.

Separaría el análisis de la ejecución.

Primero produciría un plan:

```json
{
  "source_version": "3.1",
  "target_version": "3.0",
  "operations": [
    {
      "path": "/submodels/0/submodelElements/0",
      "rule": "rename_id_short",
      "status": "pending_user",
      "suggested_value": "TechnicalData"
    },
    {
      "path": "/assetAdministrationShells/0/assetInformation",
      "rule": "map_asset_kind",
      "status": "pending_user"
    }
  ]
}
```

El usuario podría aceptar las propuestas, modificarlas o rechazarlas.

Una vez aprobado el plan, se ejecutaría la transformación.

Esto aporta tres ventajas fundamentales:

1. El usuario sabe exactamente qué va a cambiar.
2. Podemos garantizar que no se modifique el original.
3. Podemos registrar todas las transformaciones aplicadas y reproducir la operación.

Recomendaría implementar las transformaciones como operaciones sobre rutas JSON o nodos de un modelo tipado, con validaciones antes y después de cada modificación.

##### Fase 5. Generación del nuevo modelo AAS

Aquí se ejecutaría el conjunto de reglas asociado a la conversión.

Por ejemplo:

```text
transformations/
│
├── v3_0_to_v3_1/
│   ├── identifiers.py
│   ├── entities.py
│   ├── relationships.py
│   └── datatypes.py
│
├── v3_1_to_v3_0/
│   ├── identifiers.py
│   ├── entities.py
│   ├── relationships.py
│   └── datatypes.py
│
├── v3_1_to_v3_2/
│
└── v3_2_to_v3_1/
```

No recomiendo escribir una única función genérica que transforme cualquier versión en cualquier otra.

Es mejor mantener reglas explícitas entre versiones.

Para evitar duplicaciones en versiones futuras, se pueden componer las transformaciones:

```text
3.0 → 3.1 → 3.2
```

Y, cuando existan particularidades que hagan necesario un camino directo, implementar una regla específica.

También contemplaría mantener una representación intermedia común, pero no confiaría exclusivamente en ella para todas las conversiones. Una representación intermedia que no preserve campos desconocidos, extensiones o particularidades específicas de una versión puede destruir información.

##### Fase 6. Validación del resultado

Este paso no es opcional.

No basta con que el nuevo fichero JSON se genere correctamente.

Habría que comprobar:

| Nivel | Validación |
|---|---|
| Serialización | JSON o XML bien formado. |
| Esquema | Compatible con el JSON Schema o XSD oficial del destino. |
| Metamodelo | Clases y atributos permitidos. |
| Restricciones semánticas | Identificadores, cardinalidades, referencias, etc. |
| Integridad | Referencias entre AAS, Submodel y elementos. |
| Recursos | Archivos suplementarios y rutas válidas. |
| Paquete | Relaciones OPC y tipos MIME correctos. |
| Lectura real | El nuevo paquete puede abrirse con un lector compatible con la versión destino. |

Para las validaciones de metamodelo recomendaría aprovechar los SDK `aas-core` correspondientes a cada versión.

También mantendría pruebas de ida y vuelta:

```text
AASX original
    ↓
Extraer
    ↓
Transformar
    ↓
Generar nuevo AASX
    ↓
Abrir con el lector destino
    ↓
Volver a extraer
    ↓
Comparar el modelo
```

La comparación no debería limitarse a comparar cadenas JSON, porque puede haber diferencias en el orden de atributos o elementos sin que exista una diferencia semántica.

##### Fase 7. Reconstrucción del AASX

Finalmente, generaríamos el archivo de salida:

```text
equipment_v3_0.aasx
```

La reconstrucción debe conservar:

- Todos los modelos AAS que no se hayan modificado.
- Documentos y archivos suplementarios.
- Imágenes y miniaturas.
- Metadatos del paquete.
- Relaciones necesarias.
- Referencias a los recursos.

Generaría también un informe externo:

```text
equipment_v3_0_migration_report.json
```

Que permita conocer:

- Versión original y versión de destino.
- Reglas ejecutadas.
- Elementos modificados.
- Decisiones adoptadas por el usuario.
- Elementos descartados, si se autorizó expresamente.
- Resultado de todas las validaciones.
- Limitaciones detectadas.

Es importante conservar el fichero original sin alteraciones.

---

### 6. Una alternativa que merece especial atención: aprovechar AASX Package Explorer

Hay una herramienta existente que no debemos pasar por alto:

[Eclipse AASX Package Explorer](https://github.com/eclipse-aaspe/package-explorer).

Es una aplicación desarrollada en C# para visualizar y editar modelos AAS. Su función no se limita a visualizar archivos: también permite trabajar con paquetes y transformarlos.

De hecho, su versión `v2025-10-21.alpha` incorporó soporte para el metamodelo AAS 3.1 y declara expresamente que puede cargar y convertir ficheros AASX 3.0 a 3.1. [^t1-14][^t1-15]

> _Imágenes sugeridas por la interfaz: Eclipse AASX Package Explorer interface 3.1 screenshot; Eclipse AASX Package Explorer Submodel editor interface; Eclipse AASX Package Explorer AASX package tree editor_

Esto es relevante por tres motivos.

**Primero:** ya existe una implementación que resuelve parte de tu problema original: convertir AASX 3.0 a 3.1.

**Segundo:** proporciona una interfaz visual que permite inspeccionar y editar modelos AAS. Puede servir como referencia para diseñar la experiencia de usuario de nuestro migrador.

**Tercero:** su código fuente es abierto y actualmente se encuentra en el ecosistema Eclipse.

Sin embargo, no lo utilizaría como motor principal de la solución que planteo.

Sus limitaciones para nuestro caso son:

- Está desarrollado principalmente en C#.
- La versión publicada mencionada está orientada al metamodelo 3.1.
- No debemos presuponer que cubra conversiones bidireccionales ni las particularidades de 3.2.
- La versión identificada es una publicación alpha.

**Mi recomendación:** utilizar AASX Package Explorer como herramienta complementaria, referencia funcional y banco de pruebas para contrastar conversiones 3.0 → 3.1. No delegaría toda la lógica de migración a esta herramienta.

---

### 7. Stack tecnológico recomendado

Llegamos a una de las decisiones más importantes del proyecto: elegir tecnologías que nos permitan evolucionar el sistema sin generar dependencias innecesarias.

Mi recomendación es mantener todo el núcleo tecnológico en Python.

No veo una ventaja suficiente en desarrollar el motor de migración en otro lenguaje, salvo que se decidiera reutilizar internamente componentes específicos de .NET del AASX Package Explorer.

#### 7.1. Stack propuesto

#### Stack recomendado

- **Python 3.11 o superior**
  Lenguaje principal. BaSyx 2.2.0 exige Python ≥3.11.

---

- **BaSyx Python SDK**
  Integración con AAS y ejecución de agentes que utilizan el SDK.

---

- **AAS Core Python SDKs**
  Lectura, manipulación, deserialización y validación por versión.

---

- **pyecma376-2**
  Gestión de paquetes AASX y relaciones OPC.

---

- **jsonschema + lxml**
  Validación de JSON Schema y XML Schema.

---

- **Typer**
  Interfaz de línea de comandos para el motor de migración.

---

- **NiceGUI**
  Interfaz gráfica web, visual y desarrollada en Python.

---

- **Docker**
  Distribución y despliegue reproducible.

##### Librerías complementarias

| Necesidad | Tecnología |
|---|---|
| Modelos y configuración del sistema | Pydantic |
| CLI | Typer |
| API REST opcional | FastAPI |
| XML | lxml |
| JSON Schema | jsonschema |
| Comparación estructural | deepdiff o implementación propia basada en JSON Pointer |
| Pruebas | pytest, Hypothesis |
| Entornos y dependencias | uv |
| Registro de operaciones | logging estructurado |
| Informes | JSON y HTML |

Hay un motivo especialmente importante para elegir Python 3.11 como base: BaSyx 2.2.0 declara Python 3.11 como versión mínima. [^t1-4]

#### 7.2. Gestión de especificaciones oficiales

Este es un aspecto que diseñaría cuidadosamente desde el principio.

No introduciría los esquemas oficiales directamente dentro del código de las transformaciones.

Crearía un repositorio independiente de especificaciones:

```text
aas-specifications/
│
├── manifest.yaml
│
├── metamodel/
│   ├── v3.0/
│   │   ├── specification/
│   │   ├── json/
│   │   ├── xml/
│   │   └── rdf/
│   │
│   ├── v3.1/
│   │   ├── specification/
│   │   ├── json/
│   │   ├── xml/
│   │   └── rdf/
│   │
│   └── v3.2/
│       ├── specification/
│       ├── json/
│       ├── xml/
│       └── rdf/
│
├── aasx/
│   ├── v3.0/
│   ├── v3.1/
│   └── v3.2/
│
└── data_specification/
    └── iec61360/
```

El fichero `manifest.yaml` sería el índice de todas las versiones:

```yaml
specifications:

  aas_metamodel:

    "3.0":
      idta: "IDTA-01001-3-0-1"
      json_schema: "3.0.9"

    "3.1":
      idta: "IDTA-01001-3-1-2"
      json_schema: "3.1.2"

    "3.2":
      idta: "IDTA-01001-3-2-0"

  readers:

    "3.0":
      package: "aas-core3"

    "3.1":
      package: "aas-core3.1"

    "3.2":
      package: "aas-core3.2"
      status: "pre-release"
```

Los identificadores de las versiones anteriores se corresponden con las publicaciones oficiales de IDTA. [^t1-1][^t1-7][^t1-16]

Una cosa importante: no todas las partes de la especificación AAS tienen necesariamente la misma numeración de versión. Hay que versionar de forma independiente Part 1, Part 2, Part 3a, Part 5, etc.

Tampoco descargaría las especificaciones continuamente durante la ejecución del programa.

Haría lo siguiente:

1. Descargar una versión oficial publicada.
2. Almacenarla en el repositorio de especificaciones.
3. Registrar su versión, procedencia y hash.
4. Desarrollar y probar las reglas de transformación correspondientes.
5. Publicar el conjunto de especificaciones como una versión controlada del proyecto.

La IDTA publica los artefactos normativos con licencia CC-BY-4.0 en su repositorio de metamodelo, por lo que hay que conservar las atribuciones y avisos de licencia correspondientes. [^t1-2]

##### ¿Y si aparece una nueva versión AAS 3.3?

No debería ser necesario reconstruir el sistema.

Bastaría con:

- Incorporar los artefactos oficiales 3.3.
- Incorporar el lector y validador correspondiente.
- Analizar las diferencias con 3.2.
- Implementar las reglas 3.2 → 3.3 y 3.3 → 3.2.
- Añadir pruebas de regresión.

Esto es precisamente lo que se consigue separando las especificaciones de las reglas de negocio.

#### 7.3. ¿Python o Java, C# o Node.js?

Aunque existen alternativas, mi decisión sería Python.

| Tecnología | Valoración |
|---|---|
| Python | **Mi elección** Es el ecosistema natural de BaSyx Python, AAS Core y SPADE. |
| C#/.NET | Interesante si se decide aprovechar internamente el código del AASX Package Explorer. |
| Java | Buen ecosistema industrial AAS, pero introduce otro entorno tecnológico innecesario. |
| Node.js/TypeScript | Muy válido para la interfaz gráfica, pero no lo utilizaría para el motor principal. |

No hay ninguna necesidad técnica de utilizar varios lenguajes.

---

### 8. Diseño de la interfaz gráfica

Considero que esta funcionalidad puede aportar mucho valor al proyecto.

Un usuario no debería necesitar conocer todas las clases y restricciones del metamodelo AAS para transformar un fichero.

Debería poder cargar un archivo, elegir una versión de destino, revisar los cambios propuestos y descargar el resultado.

Mi elección para la primera versión sería **NiceGUI**.

[NiceGUI – documentación oficial](https://nicegui.io/documentation).

¿Por qué?

Porque permite desarrollar interfaces web utilizando Python, sin tener que construir por separado todo el frontend.

Además, dispone de:
- Carga de archivos.
- Árboles jerárquicos.
- Tablas.
- Diálogos y formularios.
- Componentes interactivos.
- Actualización dinámica de la interfaz.

Esto encaja muy bien con una herramienta que tiene que mostrar modelos AAS y permitir revisar transformaciones. [^t1-17][^t1-18]

#### 8.1. Diseño funcional propuesto

Imaginemos que el usuario abre la herramienta.

#### AAS Migration Studio

Asset Administration Shell · Compatibility & Migration

**1. Selección del fichero**

**Arrastra tu fichero AASX aquí**

También puedes seleccionarlo desde tu ordenador.

**equipment.aasx**

**2. Versiones**

- **Versión de origen** — **AAS 3.1** — Detectada automáticamente
- **Versión de destino** — **AAS 3.0** — Seleccionada

**3. Análisis**

Compatibilidad general — **Requiere revisión**

- ## 12 — Automáticas
- ## 3 — Manuales
- ## 0 — Bloqueantes

**Se requieren 3 decisiones**

El usuario deberá revisar las incompatibilidades detectadas antes de generar el nuevo AASX.

Prototipo conceptual de la pantalla; las cifras son ilustrativas.

#### 8.2. Segundo paso: revisión de incompatibilidades

Aquí está el componente visual más interesante.

Se podría mostrar el modelo AAS como un árbol jerárquico y, al seleccionar cada elemento, mostrar sus atributos, errores y transformaciones.

**Revisión de transformaciones**

**Asset Administration Shell** — **Compatible**

Identification

Submodels

TechnicalData — **Revisar**

**Problema detectado: idShort**

El identificador contiene un guion, no permitido por AAS 3.0.

**Nuevo identificador**

`TechnicalData`

**Editar** — **Aceptar propuesta**

Documentation — **Compatible**

---

Transformaciones revisadas: 1/3 — 33 %

Ejemplo ilustrativo de la experiencia de revisión.

La interfaz debería permitir al usuario:

- Aceptar propuestas automáticas.

- Modificar valores sugeridos.

- Introducir atributos obligatorios que falten.

- Seleccionar equivalencias semánticas.

- Autorizar explícitamente la eliminación de información cuando no exista otra alternativa.

- Cancelar una transformación que implique una pérdida de información no aceptable.

#### 8.3. Tercer paso: visualización de diferencias

Añadiría una pantalla que permita comparar:

- Modelo original.

- Modelo transformado.

De esta manera, el usuario puede comprobar qué ha cambiado exactamente.

También mostraría qué transformaciones se han realizado automáticamente y cuáles proceden de decisiones manuales.

#### 8.4. Cuarto paso: exportación

El último paso sería:

**Migración completada** — **Validado**

**equipment_v3_0.aasx**

AAS 3.0 · AASX generado correctamente

---

Validación JSON/XML

Validación semántica

Integridad OPC

Preservación de recursos

La pantalla solo mostraría estos estados cuando las verificaciones se hayan ejecutado satisfactoriamente.

---

### 9. Arquitectura definitiva que recomiendo

Después de analizar las distintas posibilidades, no elegiría entre la solución 1 y la solución 2.

Las desarrollaría de manera conjunta, compartiendo los componentes de lectura, identificación de versiones y validación.

La estructura sería la siguiente:

#### AAS Interoperability Platform

Arquitectura modular propuesta

**Core de interoperabilidad AAS**

Version registry · Parsers · Modelo intermedio · Validadores · Especificaciones IDTA

- **Runtime Adapter** — Compatibilidad para agentes SPADE — --- — Lectura de distintas versiones sin modificar los originales.
- **Migration Engine** — Conversión entre versiones — --- — Reglas, transformaciones, revisión y exportación.

- **SPADE** — Agentes de producción
- **CLI + GUI** — Typer + NiceGUI

**BaSyx + AAS Core SDKs + OPC**

Integraciones y mecanismos de lectura/escritura

La principal ventaja es que el motor de migración funciona de manera independiente de los agentes SPADE.

Por ejemplo, podemos tener:

```text
aas-interoperability/
│
├── specifications/
│
├── core/
│   ├── version_registry.py
│   ├── version_detector.py
│   ├── canonical_model.py
│   └── validation_engine.py
│
├── aasx/
│   ├── package_reader.py
│   ├── package_writer.py
│   └── relationships.py
│
├── adapters/
│   ├── basyx/
│   ├── aas_core_30/
│   ├── aas_core_31/
│   └── aas_core_32/
│
├── migration/
│   ├── rules/
│   ├── planner.py
│   ├── executor.py
│   ├── diff_engine.py
│   └── migration_report.py
│
├── runtime/
│   └── spade_adapter.py
│
├── cli/
│   └── main.py
│
├── gui/
│   └── app.py
│
└── tests/
```

#### 9.1. Una decisión de diseño fundamental: modelo intermedio común

Hay algo que considero especialmente importante.

Los agentes SPADE y el motor de migración necesitan acceder a los modelos AAS, pero no necesariamente necesitan trabajar con las mismas clases.

Crearía una representación intermedia propia que permita:

- Identificar AAS y Submodels.

- Navegar por los elementos.

- Consultar propiedades.

- Obtener referencias.

- Trabajar con identificadores semánticos.

- Consultar extensiones.

- Conservar atributos que no conozca la implementación.

No intentaría reproducir el metamodelo completo dentro de un nuevo conjunto de clases Python que compita con BaSyx y AAS Core.

Utilizaría las implementaciones oficiales para interpretar las estructuras y una representación intermedia cuidadosamente diseñada para intercambiar información.

Además, esta representación debe preservar los datos originales desconocidos. Nunca debería eliminar un campo simplemente porque no tiene una clase equivalente en el modelo común.

Esta distinción permite reutilizar el motor sin acoplarlo a la lógica de los agentes SPADE.

---

### 10. Comparativa final: las alternativas posibles

Para tomar la decisión definitiva, esta sería mi valoración:

| Criterio | Solo compatibilidad | Solo migrador | Solución conjunta |
|---|---:|---:|---:|
| Lectura AAS 3.0 y 3.1 | Sí | Indirecta | Sí |
| Lectura sin modificar originales | Sí | Sí, si se utiliza en modo análisis | Sí |
| Conversión entre versiones | No necesariamente | Sí | Sí |
| Validación oficial | Sí, integrable | Sí | Sí |
| Integración SPADE | Excelente | Indirecta | Excelente |
| Interfaz visual | Opcional | Sí | Sí |
| Escalabilidad a nuevas versiones | Buena | Muy buena | Muy buena |
| Reutilización de componentes | Alta | Alta | Muy alta |

Mi elección es la solución conjunta, pero desarrollada de forma incremental.

---

### 11. Plan de implementación que seguiría

No intentaría desarrollar todas las funcionalidades simultáneamente.

Plantearía cuatro etapas.

1. **Etapa 1. Compatibilidad AAS en SPADE**
   **Prioridad muy alta**
   Desarrollar la capa `AAS Compatibility Layer`, integrar los lectores 3.0 y 3.1 y proporcionar una interfaz común a los agentes.
   Resultado: los agentes pueden leer modelos de ambas versiones sin cambiar su lógica de negocio.
2. **Etapa 2. Motor de migración AASX**
   **Prioridad muy alta**
   Desarrollar extracción OPC, registro de especificaciones, detección de versiones, reglas de transformación, validación y reconstrucción AASX.
   Resultado: una herramienta CLI capaz de convertir AASX 3.0 → 3.1 y 3.1 → 3.0.
3. **Etapa 3. Interfaz gráfica**
   **Prioridad media**
   Desarrollar el asistente visual con NiceGUI, mostrando árboles AAS, problemas de compatibilidad, cambios propuestos y comparación de modelos.
   Resultado: la herramienta puede utilizarse sin conocimientos profundos de la especificación.
4. **Etapa 4. Extensión a AAS 3.2 y versiones futuras**
   **Evolución**
   Incorporar el lector 3.2 cuando su implementación esté suficientemente madura, nuevas reglas y pruebas de interoperabilidad.
   Resultado: plataforma preparada para las siguientes versiones.

Para las primeras pruebas utilizaría modelos oficiales de ejemplo de cada versión y un conjunto de ficheros AASX reales generados con AASX Package Explorer. También probaría modelos con extensiones, recursos auxiliares, múltiples Submodels y campos opcionales.

---

### 12. Recomendación definitiva

Mi recomendación profesional es desarrollar una **plataforma modular de interoperabilidad y migración AAS, cuyo núcleo sea independiente de BaSyx y de SPADE**.

Concretamente:

**Para solucionar el problema actual de los agentes SPADE:**

Desarrollaría primero una capa de compatibilidad basada en `aas-core3.0-python` y `aas-core3.1-python`, manteniendo BaSyx 2.2.0 para la integración que necesite el metamodelo 3.1.

Esto soluciona el problema de lectura sin obligar a modificar los ficheros originales y sin mantener dos versiones de BaSyx en el mismo proceso.

**Para disponer de una solución reutilizable a largo plazo:**

Desarrollaría un motor de migración AASX en Python, basado en:

- Especificaciones oficiales IDTA.

- AAS Core SDKs para lectura y validación.

- `pyecma376-2` para manipular los paquetes.

- Reglas de transformación versionadas.

- Validaciones estructurales y semánticas.

- Sistema de decisiones asistidas por el usuario.

**Para facilitar su utilización:**

Añadiría una interfaz gráfica con NiceGUI, pero mantendría el motor como una biblioteca Python independiente que pueda utilizarse desde CLI, SPADE u otros programas.

Hay una última consideración que considero imprescindible: no prometería una conversión bidireccional siempre sin pérdida de información. Una especificación nueva puede introducir elementos que una versión anterior simplemente no sabe representar. En esos casos, el sistema debe identificar la pérdida potencial, ofrecer alternativas justificadas y permitir cancelar la operación.

La calidad del proyecto dependerá tanto de lo bien que transforme los modelos como de lo bien que sepa identificar cuándo no debe transformarlos.

**En definitiva: no construiría un parche para BaSyx, ni un conversor de JSON. Construiría una capa de interoperabilidad AAS basada en las especificaciones oficiales, con BaSyx como uno de sus posibles consumidores.** Es la opción que mejor resuelve el problema presente y permite incorporar nuevas versiones del estándar sin volver a empezar.

---

#### 13. Referencias técnicas principales

Estas son las fuentes que utilizaría como punto de partida para el desarrollo:

| Recurso | Aplicación |
|---|---|
| [IDTA – AAS Metamodel](https://github.com/admin-shell-io/aas-specs-metamodel) | Especificación oficial y esquemas. |
| [Versiones oficiales AAS](https://github.com/admin-shell-io/aas-specs-metamodel/releases) | Versiones y cambios del metamodelo. |
| [BaSyx Python SDK](https://github.com/eclipse-basyx/basyx-python-sdk/releases) | Compatibilidad y versiones del SDK. |
| [AAS Core 3.1 Python](https://github.com/eclipse-aascw/aas-core3.1-python) | Lector y validador 3.1. |
| [AAS Core 3.0 Python](https://github.com/aas-core-works/aas-core3.0-python) | Lector y validador 3.0. |
| [AAS Core 3.2 Python](https://pypi.org/project/aas-core3.2/) | Implementación en desarrollo para 3.2. |
| [IDTA – AASX Specification](https://github.com/admin-shell-io/aas-specs-aasx) | Especificación oficial del paquete AASX. |
| [PyECMA376-2](https://pypi.org/project/pyecma376-2/) | Gestión de paquetes OPC. |
| [Eclipse AASX Package Explorer](https://github.com/eclipse-aaspe/package-explorer/releases) | Herramienta visual y referencia de conversión. |
| [NiceGUI](https://nicegui.io/documentation) | Desarrollo de la interfaz gráfica. |

#### Siguiente paso que recomiendo

Lo más útil sería convertir esta arquitectura en un diseño técnico implementable: definir las interfaces Python, el modelo intermedio, la matriz exacta de compatibilidad 3.0/3.1/3.2, las reglas iniciales de migración y la estructura del repositorio, empezando por un prototipo funcional que lea un AASX de cada versión y lo entregue normalizado a un agente SPADE.

### Fuentes

[^t1-1]: [Releases · admin-shell-io/aas-specs-metamodel · GitHub](https://github.com/admin-shell-io/aas-specs-metamodel/releases)
[^t1-2]: [GitHub - admin-shell-io/aas-specs-metamodel: Repository of the Asset Administration Shell Specification IDTA-01001 - Metamodel · GitHub](https://github.com/admin-shell-io/aas-specs-metamodel)
[^t1-3]: [aas-specs-metamodel/README.md at master · admin-shell-io/aas-specs-metamodel · GitHub](https://github.com/admin-shell-io/aas-specs-metamodel/blob/master/README.md)
[^t1-4]: [Releases · eclipse-basyx/basyx-python-sdk · GitHub](https://github.com/eclipse-basyx/basyx-python-sdk/releases)
[^t1-5]: [Eclipse BaSyx 2.2.0 (Python) | projects.eclipse.org](https://projects.eclipse.org/projects/dt.basyx/releases/2.2.0-python)
[^t1-6]: [Change Notes](https://industrialdigitaltwin.io/aas-specifications/IDTA-01001/v3.2/changelog.html)
[^t1-7]: [aas-core3.2 · PyPI](https://pypi.org/project/aas-core3.2/)
[^t1-8]: [GitHub - aas-core-works/aas-core3.0-python: Manipulate, verify and de/serialize asset administration shells in Python. · GitHub](https://github.com/aas-core-works/aas-core3.0-python)
[^t1-9]: [GitHub - eclipse-aascw/aas-core3.1-python: Manipulate, verify and de/serialize asset administration shells V3.1 in Python. · GitHub](https://github.com/eclipse-aascw/aas-core3.1-python)
[^t1-10]: [aas-core-works · GitHub](https://github.com/aas-core-works)
[^t1-11]: [aas-specs-aasx/documentation/IDTA-01005/modules/ROOT/pages/aasx.adoc at main · admin-shell-io/aas-specs-aasx · GitHub](https://github.com/admin-shell-io/aas-specs-aasx/blob/main/documentation/IDTA-01005/modules/ROOT/pages/aasx.adoc)
[^t1-12]: [Package File Format for the Asset Administration Shell (AASX) (normative)](https://industrialdigitaltwin.io/aas-specifications/IDTA-01005/v3.2/aasx.html)
[^t1-13]: [pyecma376-2 · PyPI](https://pypi.org/project/pyecma376-2/)
[^t1-14]: [Releases · eclipse-aaspe/package-explorer · GitHub](https://github.com/eclipse-aaspe/package-explorer/releases)
[^t1-15]: referencia no disponible
[^t1-16]: [aas-core3.1 · PyPI](https://pypi.org/project/aas-core3.1/)
[^t1-17]: [ui.tree | NiceGUI](https://nicegui.io/documentation/tree)
[^t1-18]: [NiceGUI Documentation](https://nicegui.io/documentation)
[^t1-19]: [GitHub - eclipse-basyx/basyx-python-sdk: The Eclipse BaSyx Python SDK, an implementation of the Asset Administration Shell (AAS) for Industry 4.0 systems · GitHub](https://github.com/eclipse-basyx/basyx-python-sdk)

<details>
<summary>Trazabilidad del turno</summary>

> Voy a contrastar primero la compatibilidad real entre las versiones del metamodelo AAS y BaSyx, y después evaluaré las alternativas de arquitectura —incluida la migración de AASX— con criterios de fidelidad, mantenibilidad y facilidad de uso. La recomendación distinguirá entre compatibilidad de lectura en tiempo de ejecución y conversión persistente de paquetes AASX, porque resuelven problemas distintos.

> La primera comprobación cambia un matiz importante del diagnóstico: la propia IDTA declara que los incrementos menores del metamodelo (por ejemplo, 3.0 → 3.1 → 3.2) son compatibles hacia atrás a nivel de especificación. Eso no garantiza que cualquier SDK antiguo pueda deserializar cualquier instancia nueva: BaSyx implementa un conjunto concreto de versiones y aplica validaciones estrictas. Por ello, hay que separar **compatibilidad normativa**, **compatibilidad del parser** y **compatibilidad de la aplicación SPADE**. [^t1-2][^t1-4][^t1-19]

> Ya se pueden concretar las transformaciones que la herramienta tendría que gestionar. Entre 3.0 y 3.1 no se trata solo de añadir campos: cambian enumeraciones, restricciones de `idShort`, longitudes permitidas y la opcionalidad de atributos como `contentType`, `entityType` y los extremos de `RelationshipElement`. En 3.2 aparecen, entre otros, `createdAt`, `updatedAt` y `AssetKind.Batch`; además, hay un cambio explícitamente no retrocompatible para `Range` en estado experimental. Por tanto, una migración genérica basada en “añadir/quitar atributos” sería insuficiente. [^t1-6]

</details>

---

## Turno 2 — Usuario

Como llamarías a esta aplicación, considerando que su objetivo es la compatibilidad de AAS y de AASX?

## Turno 2 — ChatGPT

Yo elegiría un nombre que transmita **interoperabilidad, compatibilidad entre versiones y transformación de modelos AAS**, sin limitar la aplicación exclusivamente a ficheros AASX.

Mis propuestas serían las siguientes:

#### Mis 6 nombres favoritos

| Nombre | Concepto que transmite | Valoración |
|---|---|---|
| **AAS Bridge** | Conectar versiones, modelos y herramientas AAS diferentes. | **Mi favorito** |
| **AAS Interop Studio** | Plataforma completa de interoperabilidad AAS/AASX. | **Muy recomendable** |
| **AAS Nexus** | Punto de conexión entre diferentes versiones y ecosistemas AAS. | Muy atractivo |
| **AAS Connect** | Conectar modelos, aplicaciones y versiones. | Sencillo y directo |
| **AAS Evolution** | Adaptación y evolución de modelos entre versiones. | Más orientado a migraciones |
| **ShellBridge** | Puente entre diferentes implementaciones de Asset Administration Shell. | Más original |

#### Mi recomendación: AAS Bridge

#### AAS Bridge

Asset Administration Shell Interoperability Platform

**Mi elección**

---

**Compatibility · Validation · Migration**

A unified platform to read, validate, adapt and migrate AAS models and AASX packages across metamodel versions.

- **Compatibility** — Versiones
- **Validation** — Conformidad
- **Migration** — Transformación

¿Por qué lo elegiría?

1. **No limita el proyecto a AASX.** También representa la interoperabilidad entre modelos AAS en memoria, agentes SPADE, BaSyx y otros SDK.
2. **Es independiente de las versiones.** AAS 3.0, 3.1, 3.2 y futuras versiones encajan perfectamente en el concepto.
3. **Es fácil de recordar y pronunciar.**
4. **Permite ampliar el proyecto** sin que el nombre deje de representar sus funcionalidades.

Además, permite organizar sus componentes con nombres coherentes:

```text
AAS Bridge
│
├── AAS Bridge Core
│   └── Modelo común e interoperabilidad
│
├── AAS Bridge Runtime
│   └── Compatibilidad para agentes SPADE
│
├── AAS Bridge Migration
│   └── Transformación de modelos AAS/AASX
│
├── AAS Bridge Validator
│   └── Validación contra especificaciones IDTA
│
└── AAS Bridge Studio
    └── Interfaz gráfica para el usuario
```

**Mi segunda elección sería AAS Interop Studio**, especialmente si quieres presentar el proyecto como una herramienta software completa, con interfaz visual y funcionalidades de análisis y migración.

Mi voto final: **AAS Bridge**. Es suficientemente amplio, técnico y memorable para convertirse en el nombre de una plataforma de interoperabilidad AAS a largo plazo.

Antes de adoptarlo oficialmente, comprobaría la disponibilidad del nombre, del dominio y posibles conflictos de marca.

---

If you want, I can:

- Continuar análisis de solución 2: transformador/adaptador AASX
- Iniciar ejemplo de código para capa de compatibilidad AAS
- Detalle pasos para evaluación práctica y pruebas del diseño propuesto
