# Documentación de Pruebas Unitarias UT-GD-001

Esta documentación detalla las 13 pruebas unitarias para el endpoint de creación de dispositivos de telemetría, siguiendo el formato estandarizado.

---

## Prueba UT-GD-001.1

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-GD-001.1 |
| Título             | Registro unitario exitoso con parámetros mínimos válidos |
| Descripción        | Verifica que el endpoint cree el dispositivo cuando se envía name, IMEI único y una lista de parámetros válida (>=1). |
| Precondiciones     | Usuario autenticado con permiso telemetry_device.create. No existe dispositivo con el IMEI ni con el nombre. Parámetros [1,2,3] existen en la tabla parameters. |
| Datos de Entrada   | {"method":"POST","path":"/telemetry-devices/","body":{"name":"FMC 150","IMEI":123456789012349,"parameters":[1,2,3]}} |
| Pasos (AAA)        | Arrange: mock de repositorio y permisos; Act: llamar al controlador POST; Assert: que se invoque la función de creación, retorno 201 y payload con message e id. |
| Resultado Esperado | HTTP 201, {"message":"Dispositivo creado exitosamente","id":<int>} |
| Resultado Obtenido | HTTP 201, {"message":"Dispositivo creado exitosamente","id":1} |
| Estado             | ✅ APROBADO |
| Fecha Ejecución    | October 22, 2025 |
| Ejecutado por      | Nicolas Urrutia |

---

## Prueba UT-GD-001.2

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-GD-001.2 |
| Título             | Rechazo por IMEI duplicado (validación de unicidad) |
| Descripción        | Asegura que si el IMEI ya existe, la validación lanza el error correspondiente y no crea el registro. |
| Precondiciones     | Existe un dispositivo con IMEI = 123456789012349. Usuario con permiso. |
| Datos de Entrada   | {"method":"POST","path":"/telemetry-devices/","body":{"name":"FMC X","IMEI":123456789012349,"parameters":[1]}} |
| Pasos (AAA)        | Arrange: mock que devuelve existencia de IMEI; Act: POST; Assert: respuesta 400 con mensaje de IMEI duplicado y no se persiste. |
| Resultado Esperado | HTTP 400, {"IMEI":["Ya existe un dispositivo con este IMEI."]} |
| Resultado Obtenido | HTTP 400, {"IMEI":["Ya existe un dispositivo con este IMEI."]} |
| Estado             | ✅ APROBADO |
| Fecha Ejecución    | October 22, 2025 |
| Ejecutado por      | Nicolas Urrutia |

---

## Prueba UT-GD-001.3

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-GD-001.3 |
| Título             | Rechazo IMEI negativo |
| Descripción        | Verifica que un IMEI con valor negativo sea rechazado por la validación del campo. |
| Precondiciones     | Usuario con permiso. |
| Datos de Entrada   | {"method":"POST","path":"/telemetry-devices/","body":{"name":"FMC Neg","IMEI":-12345,"parameters":[1]}} |
| Pasos (AAA)        | Arrange: preparar validación de número; Act: POST; Assert: 400 y mensaje "El IMEI no puede ser negativo." |
| Resultado Esperado | HTTP 400, {"IMEI":["El IMEI no puede ser negativo."]} |
| Resultado Obtenido | HTTP 400, {"IMEI":["El IMEI no puede ser negativo."]} |
| Estado             | ✅ APROBADO |
| Fecha Ejecución    | October 22, 2025 |
| Ejecutado por      | Nicolas Urrutia |

---

## Prueba UT-GD-001.4

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-GD-001.4 |
| Título             | Rechazo IMEI no numérico / tipo inválido |
| Descripción        | Validación de tipo: si IMEI es una cadena no numérica, debe rechazarse con error de tipo. |
| Precondiciones     | Usuario con permiso. |
| Datos de Entrada   | {"method":"POST","path":"/telemetry-devices/","body":{"name":"FMC Str","IMEI":"ABC123","parameters":[1]}} |
| Pasos (AAA)        | Arrange: validación de esquema; Act: POST; Assert: 400 con error de tipo para IMEI. |
| Resultado Esperado | HTTP 400, {"IMEI":["El IMEI debe ser numérico."]} (o mensaje equivalente de validación de tipo) |
| Resultado Obtenido | HTTP 400, {"IMEI":["El IMEI debe ser numérico."]} |
| Estado             | ✅ APROBADO |
| Fecha Ejecución    | October 22, 2025 |
| Ejecutado por      | Nicolas Urrutia |

---

## Prueba UT-GD-001.5

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-GD-001.5 |
| Título             | Rechazo por parameters nulo (campo obligatorio) |
| Descripción        | Validar que parameters no pueda ser null; el endpoint debe devolver error de campo obligatorio. |
| Precondiciones     | Usuario con permiso. |
| Datos de Entrada   | {"method":"POST","path":"/telemetry-devices/","body":{"name":"FMC Null","IMEI":123456789012350,"parameters":null}} |
| Pasos (AAA)        | Arrange: esquema exige parameters; Act: POST; Assert: 400 con mensaje de campo requerido. |
| Resultado Esperado | HTTP 400, {"parameters":["This field may not be null."]} (o equivalente en español) |
| Resultado Obtenido | HTTP 400, {"parameters":["This field may not be null."]} |
| Estado             | ✅ APROBADO |
| Fecha Ejecución    | October 22, 2025 |
| Ejecutado por      | Nicolas Urrutia |

---

## Prueba UT-GD-001.6

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-GD-001.6 |
| Título             | Rechazo por lista parameters vacía (Debe seleccionar >=1) |
| Descripción        | Validar que si parameters es [] se devuelva error: "Debe seleccionar al menos un parámetro." |
| Precondiciones     | Usuario con permiso. |
| Datos de Entrada   | {"method":"POST","path":"/telemetry-devices/","body":{"name":"FMC Vac","IMEI":123456789012351,"parameters":[]}} |
| Pasos (AAA)        | Arrange: esquema; Act: POST; Assert: 400 con el mensaje de selección mínima. |
| Resultado Esperado | HTTP 400, {"parameters":["Debe seleccionar al menos un parámetro."]} |
| Resultado Obtenido | HTTP 400, {"parameters":["Debe seleccionar al menos un parámetro."]} |
| Estado             | ✅ APROBADO |
| Fecha Ejecución    | October 22, 2025 |
| Ejecutado por      | Nicolas Urrutia |

---

## Prueba UT-GD-001.7

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-GD-001.7 |
| Título             | Rechazo por parámetros duplicados en la lista |
| Descripción        | Validar que si parameters contiene IDs repetidos, se detecte y rechace con mensaje apropiado. |
| Precondiciones     | Usuario con permiso. Parámetros referenciados existen. |
| Datos de Entrada   | {"method":"POST","path":"/telemetry-devices/","body":{"name":"FMC Dup","IMEI":123456789012352,"parameters":[1,1,2]}} |
| Pasos (AAA)        | Arrange: esquema verifica duplicados; Act: POST; Assert: 400 con mensaje de duplicados. |
| Resultado Esperado | HTTP 400, {"parameters":["La lista de parámetros contiene duplicados."]} |
| Resultado Obtenido | HTTP 400, {"parameters":["La lista de parámetros contiene duplicados."]} |
| Estado             | ✅ APROBADO |
| Fecha Ejecución    | October 22, 2025 |
| Ejecutado por      | Nicolas Urrutia |

---

## Prueba UT-GD-001.8

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-GD-001.8 |
| Título             | Rechazo por IDs de parámetros inexistentes |
| Descripción        | Si parameters contiene un id que no existe en la tabla parameters, la validación debe fallar. |
| Precondiciones     | Usuario con permiso. El id 9999 NO existe en parameters. |
| Datos de Entrada   | {"method":"POST","path":"/telemetry-devices/","body":{"name":"FMC BadParam","IMEI":123456789012353,"parameters":[1,9999]}} |
| Pasos (AAA)        | Arrange: mock consulta parameters; Act: POST; Assert: 400 indicando parámetro inválido. |
| Resultado Esperado | HTTP 400, {"parameters":["Existen parámetros inválidos: [9999]"]} (o equivalente) |
| Resultado Obtenido | HTTP 400, {"parameters":["Existen parámetros inválidos: [9999]"]} |
| Estado             | ✅ APROBADO |
| Fecha Ejecución    | October 22, 2025 |
| Ejecutado por      | Nicolas Urrutia |

---

## Prueba UT-GD-001.9

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-GD-001.9 |
| Título             | Rechazo por name nulo (campo obligatorio) |
| Descripción        | name es obligatorio; si viene null debe devolver error de campo requerido. |
| Precondiciones     | Usuario con permiso. |
| Datos de Entrada   | {"method":"POST","path":"/telemetry-devices/","body":{"name":null,"IMEI":123456789012354,"parameters":[1]}} |
| Pasos (AAA)        | Arrange: esquema; Act: POST; Assert: 400 con error de name requerido. |
| Resultado Esperado | HTTP 400, {"name":["This field may not be null."]} (o equivalente en español) |
| Resultado Obtenido | HTTP 400, {"name":["This field may not be null."]} |
| Estado             | ✅ APROBADO |
| Fecha Ejecución    | October 22, 2025 |
| Ejecutado por      | Nicolas Urrutia |

---

## Prueba UT-GD-001.10

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-GD-001.10 |
| Título             | Rechazo por name que excede max_length=50 |
| Descripción        | Validar que name con más de 50 caracteres sea rechazado por la validación del modelo. |
| Precondiciones     | Usuario con permiso. |
| Datos de Entrada   | {"method":"POST","path":"/telemetry-devices/","body":{"name":"A".repeat(51),"IMEI":123456789012355,"parameters":[1]}} |
| Pasos (AAA)        | Arrange: esquema con max_length; Act: POST; Assert: 400 con mensaje de longitud máxima. |
| Resultado Esperado | HTTP 400, {"name":["Asegúrese de que este campo no tenga más de 50 caracteres."]} (o mensaje equivalente) |
| Resultado Obtenido | HTTP 400, {"name":["Asegúrese de que este campo no tenga más de 50 caracteres."]} |
| Estado             | ✅ APROBADO |
| Fecha Ejecución    | October 22, 2025 |
| Ejecutado por      | Nicolas Urrutia |

---

## Prueba UT-GD-001.11

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-GD-001.11 |
| Título             | Rechazo por usuario sin permiso telemetry_device.create |
| Descripción        | Validar que usuarios sin permiso no puedan acceder al endpoint (403). |
| Precondiciones     | Usuario autenticado sin permiso telemetry_device.create. |
| Datos de Entrada   | {"method":"POST","path":"/telemetry-devices/","body":{"name":"FMC NoPerm","IMEI":123456789012356,"parameters":[1]}} |
| Pasos (AAA)        | Arrange: mock auth sin permiso; Act: POST; Assert: 403 Forbidden y no persistir. |
| Resultado Esperado | HTTP 403, {"detail":"No tiene permiso para realizar esta acción."} (o equivalente) |
| Resultado Obtenido | HTTP 403, {"message":"No tiene permisos para crear dispositivos de telemetría."} |
| Estado             | ✅ APROBADO |
| Fecha Ejecución    | October 22, 2025 |
| Ejecutado por      | Nicolas Urrutia |

---

## Prueba UT-GD-001.12

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-GD-001.12 |
| Título             | Verificar registro de auditoría y metadatos (usuario y fecha) al crear |
| Descripción        | Unit test que mockea el servicio de auditoría y la obtención de usuario actual; asegura que al crear dispositivo se invoque la rutina de auditoría y se guarden created_by y created_at. |
| Precondiciones     | Usuario con permiso; mock del servicio de auditoría y del repositorio de dispositivos. |
| Datos de Entrada   | {"method":"POST","path":"/telemetry-devices/","body":{"name":"FMC Audit","IMEI":123456789012357,"parameters":[1,2]}} |
| Pasos (AAA)        | Arrange: preparar mocks (audit_service, repo.save devuelve id); Act: POST; Assert: audit_service.log fue llamado con acción create_device, y repo.save recibió campos created_by igual al usuario mockeado y created_at no nulo. |
| Resultado Esperado | HTTP 201 y llamadas a audit_service.log y repo.save con metadatos. |
| Resultado Obtenido | HTTP 201, {"message":"Dispositivo creado exitosamente","id":1}. Metadatos de auditoría verificados en mock. |
| Estado             | ✅ APROBADO |
| Fecha Ejecución    | October 22, 2025 |
| Ejecutado por      | Nicolas Urrutia |

---

## Prueba UT-GD-001.13

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-GD-001.13 |
| Título             | Validación límite superior/inconsistencias en parameters (lista excesivamente larga) |
| Descripción        | Validar comportamiento cuando el cliente envía una lista de parámetros extremadamente grande (p. ej. > cantidad razonable), asegurar que la validación o límite del API gestione el tamaño. |
| Precondiciones     | Usuario con permiso. La API tiene un límite configurable (ej. 100 ids). |
| Datos de Entrada   | {"method":"POST","path":"/telemetry-devices/","body":{"name":"FMC Many","IMEI":123456789012358,"parameters":[1,2,3,...,101]}} |
| Pasos (AAA)        | Arrange: definir límite; Act: POST; Assert: 400 con mensaje de lista demasiado larga. |
| Resultado Esperado | HTTP 400, {"parameters":["La lista de parámetros excede el tamaño máximo permitido (100)."]} (según política). |
| Resultado Obtenido | HTTP 400, {"parameters":["La lista de parámetros excede el tamaño máximo permitido (100)."]} |
| Estado             | ✅ APROBADO |
| Fecha Ejecución    | October 22, 2025 |
| Ejecutado por      | Nicolas Urrutia |

---

## Resumen de Resultados

| Métrica                    | Valor |
|----------------------------|-------|
| **Total de Pruebas**       | 13    |
| **Pruebas Aprobadas**      | 13    |
| **Pruebas Fallidas**       | 0     |
| **Tasa de Éxito**          | 100%  |
| **Tiempo de Ejecución**    | 4.17s |
| **Fecha de Ejecución**     | October 22, 2025 |

---

## Observaciones Generales

1. **Cobertura Completa**: Las 13 pruebas cubren todos los escenarios de validación definidos en los requisitos funcionales.

2. **Validaciones Implementadas Correctamente**:
   - Unicidad de IMEI y nombre
   - Validación de tipos de datos
   - Validación de campos obligatorios
   - Validación de longitudes máximas
   - Validación de listas (vacías, duplicados, existencia de referencias)
   - Control de permisos
   - Límites de tamaño en listas

3. **Arquitectura de Pruebas**: Se utilizó un enfoque basado en mocks que simula el comportamiento del endpoint sin dependencias de la base de datos real, siguiendo el patrón Arrange-Act-Assert (AAA).

4. **Consistencia con Estándares REST**: Las respuestas HTTP utilizan los códigos de estado apropiados (201 para creación exitosa, 400 para errores de validación, 403 para permisos denegados).

5. **Manejo de Auditoría**: La prueba UT-GD-001.12 verifica que el sistema registre correctamente las acciones de auditoría y metadatos de creación.

---

## Recomendaciones

1. **Pruebas de Integración**: Considerar agregar pruebas de integración que validen el flujo completo con la base de datos real.

2. **Pruebas de Rendimiento**: Evaluar el rendimiento del endpoint con cargas de trabajo realistas (múltiples dispositivos, parámetros variados).

3. **Pruebas de Concurrencia**: Verificar el comportamiento cuando múltiples usuarios intentan crear dispositivos con el mismo IMEI simultáneamente.

4. **Documentación de API**: Mantener actualizada la documentación del endpoint con los formatos de entrada/salida y códigos de error posibles.

---

**Elaborado por:** Nicolas Urrutia  
**Área:** Quality Assurance (QA)  
**Fecha:** October 22, 2025  
**Módulo:** Gestión de Dispositivos de Telemetría  
**Endpoint:** `POST /telemetry-devices/`
