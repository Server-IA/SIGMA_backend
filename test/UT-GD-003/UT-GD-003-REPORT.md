# Documentación de Pruebas Unitarias UT-GD-003

Esta documentación detalla las pruebas unitarias para el endpoint de actualización de dispositivos de telemetría, siguiendo el formato estandarizado.

---

## Prueba UT-GD-003.1

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-GD-003.1 |
| Título             | Actualización exitosa con datos válidos |
| Descripción        | Verifica que el endpoint actualiza correctamente un dispositivo con datos válidos y retorna HTTP 200 con estructura JSON correcta. |
| Precondiciones     | Dispositivo con ID 11 existe en BD. Usuario autenticado con permiso telemetry_device.update (114). Parámetros 1-5 existen en la tabla parameters. |
| Datos de Entrada   | {"method":"PUT","path":"/telemetry-devices/11/","body":{"name":"FMC 155","IMEI":123456789012348,"parameters":[1,2,3,4,5]}} |
| Pasos (AAA)        | Arrange: autenticar usuario con permiso 114; Act: llamar al controlador PUT; Assert: que se actualice el dispositivo, retorno 200, payload con success=true y message, y datos en BD actualizados. |
| Resultado Esperado | HTTP 200, {"success":true,"message":"Dispositivo actualizado exitosamente"} |
| Resultado Obtenido | HTTP 200, {"success":true,"message":"Dispositivo actualizado exitosamente"} |
| Estado             | ✅ APROBADO |
| Fecha Ejecución    | October 27, 2025 |
| Ejecutado por      | Daniel Soto |

---

## Prueba UT-GD-003.2

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-GD-003.2 |
| Título             | Usuario sin permiso recibe HTTP 403 |
| Descripción        | Verifica que un usuario sin el permiso telemetry_device.update (114) no pueda actualizar el dispositivo. |
| Precondiciones     | Dispositivo con ID 11 existe. Usuario autenticado sin permiso 114. |
| Datos de Entrada   | {"method":"PUT","path":"/telemetry-devices/11/","body":{"name":"FMC 155","IMEI":123456789012348,"parameters":[1,2,3]}} |
| Pasos (AAA)        | Arrange: autenticar sin permiso 114; Act: PUT; Assert: respuesta 403 con mensaje de permisos insuficientes y no se persiste. |
| Resultado Esperado | HTTP 403, {"success":false,"message":"No tiene permisos para actualizar dispositivos de telemetría."} |
| Resultado Obtenido | HTTP 403, {"success":false,"message":"No tiene permisos para actualizar dispositivos de telemetría."} |
| Estado             | ✅ APROBADO |
| Fecha Ejecución    | October 27, 2025 |
| Ejecutado por      | Daniel Soto |

---

## Prueba UT-GD-003.3

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-GD-003.3 |
| Título             | Sin token de autenticación retorna HTTP 401 |
| Descripción        | Verifica que acceder al endpoint sin Authorization header retorna 401. |
| Precondiciones     | Dispositivo con ID 11 existe. |
| Datos de Entrada   | {"method":"PUT","path":"/telemetry-devices/11/","body":{"name":"FMC 155","IMEI":123456789012348,"parameters":[1,2,3]}} |
| Pasos (AAA)        | Arrange: no configurar token; Act: PUT sin Authorization; Assert: respuesta 401. |
| Resultado Esperado | HTTP 401, {"success":false,"message":"Usuario no autenticado"} |
| Resultado Obtenido | HTTP 401, {"success":false,"message":"Usuario no autenticado"} |
| Estado             | ✅ APROBADO |
| Fecha Ejecución    | October 27, 2025 |
| Ejecutado por      | Daniel Soto |

---

## Prueba UT-GD-003.4

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-GD-003.4 |
| Título             | Campo name faltante retorna HTTP 400 |
| Descripción        | Verifica que enviar el request sin el campo 'name' retorna error de validación. |
| Precondiciones     | Dispositivo con ID 11 existe. Usuario con permiso 114. |
| Datos de Entrada   | {"method":"PUT","path":"/telemetry-devices/11/","body":{"IMEI":123456789012348,"parameters":[1,2,3]}} |
| Pasos (AAA)        | Arrange: usuario con permiso; Act: PUT sin name; Assert: 400 con error de campo requerido. |
| Resultado Esperado | HTTP 400, {"name":["This field is required."]} |
| Resultado Obtenido | HTTP 400, {"name":["This field is required."]} |
| Estado             | ✅ APROBADO |
| Fecha Ejecución    | October 27, 2025 |
| Ejecutado por      | Daniel Soto |

---

## Prueba UT-GD-003.5

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-GD-003.5 |
| Título             | Campo IMEI faltante retorna HTTP 400 |
| Descripción        | Verifica que enviar el request sin el campo 'IMEI' retorna error de validación. |
| Precondiciones     | Dispositivo con ID 11 existe. Usuario con permiso 114. |
| Datos de Entrada   | {"method":"PUT","path":"/telemetry-devices/11/","body":{"name":"FMC 155","parameters":[1,2,3]}} |
| Pasos (AAA)        | Arrange: usuario con permiso; Act: PUT sin IMEI; Assert: 400 con error de campo requerido. |
| Resultado Esperado | HTTP 400, {"IMEI":["This field is required."]} |
| Resultado Obtenido | HTTP 400, {"IMEI":["This field is required."]} |
| Estado             | ✅ APROBADO |
| Fecha Ejecución    | October 27, 2025 |
| Ejecutado por      | Daniel Soto |

---

## Prueba UT-GD-003.6

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-GD-003.6 |
| Título             | Campo parameters faltante retorna HTTP 400 |
| Descripción        | Verifica que enviar el request sin el campo 'parameters' retorna error de validación. |
| Precondiciones     | Dispositivo con ID 11 existe. Usuario con permiso 114. |
| Datos de Entrada   | {"method":"PUT","path":"/telemetry-devices/11/","body":{"name":"FMC 155","IMEI":123456789012348}} |
| Pasos (AAA)        | Arrange: usuario con permiso; Act: PUT sin parameters; Assert: 400 con error de campo requerido. |
| Resultado Esperado | HTTP 400, {"parameters":["This field is required."]} |
| Resultado Obtenido | HTTP 400, {"parameters":["This field is required."]} |
| Estado             | ✅ APROBADO |
| Fecha Ejecución    | October 27, 2025 |
| Ejecutado por      | Daniel Soto |

---

## Prueba UT-GD-003.7

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-GD-003.7 |
| Título             | Nombre duplicado retorna HTTP 400 |
| Descripción        | Verifica que intentar actualizar con un nombre que ya existe en otro dispositivo retorna error de validación. |
| Precondiciones     | Dispositivo con ID 11 y otro con nombre "FMC Dispositivo Existente" existen. Usuario con permiso 114. |
| Datos de Entrada   | {"method":"PUT","path":"/telemetry-devices/11/","body":{"name":"FMC Dispositivo Existente","IMEI":123456789012349,"parameters":[1,2,3]}} |
| Pasos (AAA)        | Arrange: existe dispositivo con nombre duplicado; Act: PUT con nombre duplicado; Assert: 400 con mensaje de duplicidad de nombre. |
| Resultado Esperado | HTTP 400, {"name":["Ya existe otro dispositivo con este nombre."]} |
| Resultado Obtenido | HTTP 400, {"name":["Ya existe otro dispositivo con este nombre."]} |
| Estado             | ✅ APROBADO |
| Fecha Ejecución    | October 27, 2025 |
| Ejecutado por      | Daniel Soto |

---

## Prueba UT-GD-003.8

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-GD-003.8 |
| Título             | IMEI duplicado retorna HTTP 400 |
| Descripción        | Verifica que intentar actualizar con un IMEI que ya existe en otro dispositivo retorna error de validación. |
| Precondiciones     | Dispositivo con ID 11 y otro con IMEI 999999999999999 existen. Usuario con permiso 114. |
| Datos de Entrada   | {"method":"PUT","path":"/telemetry-devices/11/","body":{"name":"FMC Actualizado","IMEI":999999999999999,"parameters":[1,2,3]}} |
| Pasos (AAA)        | Arrange: existe dispositivo con IMEI duplicado; Act: PUT con IMEI duplicado; Assert: 400 con mensaje de duplicidad de IMEI. |
| Resultado Esperado | HTTP 400, {"IMEI":["Ya existe otro dispositivo con este IMEI."]} |
| Resultado Obtenido | HTTP 400, {"IMEI":["Ya existe otro dispositivo con este IMEI."]} |
| Estado             | ✅ APROBADO |
| Fecha Ejecución    | October 27, 2025 |
| Ejecutado por      | Daniel Soto |

---

## Prueba UT-GD-003.9

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-GD-003.9 |
| Título             | IMEI negativo retorna HTTP 400 |
| Descripción        | Verifica que un IMEI con valor negativo sea rechazado. |
| Precondiciones     | Dispositivo con ID 11 existe. Usuario con permiso 114. |
| Datos de Entrada   | {"method":"PUT","path":"/telemetry-devices/11/","body":{"name":"FMC Actualizado","IMEI":-123456789012345,"parameters":[1,2,3]}} |
| Pasos (AAA)        | Arrange: usuario con permiso; Act: PUT con IMEI negativo; Assert: 400 con mensaje de validación. |
| Resultado Esperado | HTTP 400, {"IMEI":["El IMEI no puede ser negativo."]} |
| Resultado Obtenido | HTTP 400, {"IMEI":["El IMEI no puede ser negativo."]} |
| Estado             | ✅ APROBADO |
| Fecha Ejecución    | October 27, 2025 |
| Ejecutado por      | Daniel Soto |

---

## Prueba UT-GD-003.10

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-GD-003.10 |
| Título             | Lista de parámetros vacía retorna HTTP 400 |
| Descripción        | Verifica que enviar una lista vacía de parámetros retorna error. |
| Precondiciones     | Dispositivo con ID 11 existe. Usuario con permiso 114. |
| Datos de Entrada   | {"method":"PUT","path":"/telemetry-devices/11/","body":{"name":"FMC Actualizado","IMEI":123456789012349,"parameters":[]}} |
| Pasos (AAA)        | Arrange: usuario con permiso; Act: PUT con lista vacía; Assert: 400 con mensaje de al menos un parámetro. |
| Resultado Esperado | HTTP 400, {"parameters":["Debe seleccionar al menos un parámetro."]} |
| Resultado Obtenido | HTTP 400, {"parameters":["Debe seleccionar al menos un parámetro."]} |
| Estado             | ✅ APROBADO |
| Fecha Ejecución    | October 27, 2025 |
| Ejecutado por      | Daniel Soto |

---

## Prueba UT-GD-003.11

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-GD-003.11 |
| Título             | Parámetros duplicados en la lista retorna HTTP 400 |
| Descripción        | Verifica que una lista de parámetros con IDs duplicados sea rechazada. |
| Precondiciones     | Dispositivo con ID 11 existe. Usuario con permiso 114. |
| Datos de Entrada   | {"method":"PUT","path":"/telemetry-devices/11/","body":{"name":"FMC Actualizado","IMEI":123456789012349,"parameters":[1,2,2,3,4]}} |
| Pasos (AAA)        | Arrange: usuario con permiso; Act: PUT con duplicados; Assert: 400 con mensaje de duplicados. |
| Resultado Esperado | HTTP 400, {"parameters":["La lista de parámetros contiene duplicados."]} |
| Resultado Obtenido | HTTP 400, {"parameters":["La lista de parámetros contiene duplicados."]} |
| Estado             | ✅ APROBADO |
| Fecha Ejecución    | October 27, 2025 |
| Ejecutado por      | Daniel Soto |

---

## Prueba UT-GD-003.12

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-GD-003.12 |
| Título             | Nombre excediendo 50 caracteres retorna HTTP 400 |
| Descripción        | Verifica que un nombre con más de 50 caracteres sea rechazado. |
| Precondiciones     | Dispositivo con ID 11 existe. Usuario con permiso 114. |
| Datos de Entrada   | {"method":"PUT","path":"/telemetry-devices/11/","body":{"name":"Este es un nombre de dispositivo extremadamente largo que supera los cincuenta caracteres permitidos","IMEI":123456789012349,"parameters":[1,2,3]}} |
| Pasos (AAA)        | Arrange: usuario con permiso; Act: PUT con nombre largo; Assert: 400 con mensaje de longitud. |
| Resultado Esperado | HTTP 400, {"name":["Ensure this field has no more than 50 characters."]} |
| Resultado Obtenido | HTTP 400, {"name":["Ensure this field has no more than 50 characters."]} |
| Estado             | ✅ APROBADO |
| Fecha Ejecución    | October 27, 2025 |
| Ejecutado por      | Daniel Soto |

---

## Prueba UT-GD-003.13

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-GD-003.13 |
| Título             | Dispositivo inexistente retorna HTTP 404 |
| Descripción        | Verifica que intentar actualizar un ID que no existe retorna 404. |
| Precondiciones     | No existe dispositivo con ID 99999. Usuario con permiso 114. |
| Datos de Entrada   | {"method":"PUT","path":"/telemetry-devices/99999/","body":{"name":"FMC Actualizado","IMEI":123456789012349,"parameters":[1,2,3]}} |
| Pasos (AAA)        | Arrange: usuario con permiso; Act: PUT con ID inexistente; Assert: 404 con mensaje de no encontrado. |
| Resultado Esperado | HTTP 404, {"success":false,"message":"Dispositivo no encontrado"} |
| Resultado Obtenido | HTTP 404, {"success":false,"message":"Dispositivo no encontrado"} |
| Estado             | ✅ APROBADO |
| Fecha Ejecución    | October 27, 2025 |
| Ejecutado por      | Daniel Soto |

---

## Prueba UT-GD-003.14

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-GD-003.14 |
| Título             | IDs de parámetros inexistentes retorna HTTP 400 |
| Descripción        | Verifica que intentar asociar parámetros que no existen retorna error. |
| Precondiciones     | Dispositivo con ID 11 existe. Parámetros 99,100,101 no existen. Usuario con permiso 114. |
| Datos de Entrada   | {"method":"PUT","path":"/telemetry-devices/11/","body":{"name":"FMC Actualizado","IMEI":123456789012349,"parameters":[99,100,101]}} |
| Pasos (AAA)        | Arrange: usuario con permiso; Act: PUT con parámetros inexistentes; Assert: 400 con mensaje de parámetro no existe. |
| Resultado Esperado | HTTP 400, {"parameters":["El parámetro con ID 99 no existe."]} |
| Resultado Obtenido | HTTP 400, {"parameters":["El parámetro con ID 99 no existe."]} |
| Estado             | ✅ APROBADO |
| Fecha Ejecución    | October 27, 2025 |
| Ejecutado por      | Daniel Soto |

---

## Prueba UT-GD-003.15

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-GD-003.15 |
| Título             | La fecha de registro no cambia al actualizar |
| Descripción        | Verifica que al actualizar un dispositivo, la fecha de registro original se mantiene sin cambios. |
| Precondiciones     | Dispositivo con ID 11 existe con registration_date conocido. Usuario con permiso 114. |
| Datos de Entrada   | {"method":"PUT","path":"/telemetry-devices/11/","body":{"name":"FMC Con Nueva Fecha","IMEI":123456789012350,"parameters":[1,2,3,4]}} |
| Pasos (AAA)        | Arrange: guardar registration_date original; Act: PUT con cambios; Assert: registration_date no cambió, modification_date sí cambió. |
| Resultado Esperado | HTTP 200, registration_date original preservado |
| Resultado Obtenido | HTTP 200, registration_date original preservado |
| Estado             | ✅ APROBADO |
| Fecha Ejecución    | October 27, 2025 |
| Ejecutado por      | Daniel Soto |

---

## Prueba UT-GD-003.16

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-GD-003.16 |
| Título             | La fecha de modificación se actualiza correctamente |
| Descripción        | Verifica que al actualizar un dispositivo, la fecha de modificación se actualiza al timestamp de la operación. |
| Precondiciones     | Dispositivo con ID 11 existe con modification_date conocido. Usuario con permiso 114. |
| Datos de Entrada   | {"method":"PUT","path":"/telemetry-devices/11/","body":{"name":"FMC Modificado","IMEI":123456789012351,"parameters":[1,2,3]}} |
| Pasos (AAA)        | Arrange: guardar modification_date original; Act: PUT con cambios; Assert: modification_date se actualizó. |
| Resultado Esperado | HTTP 200, modification_date actualizado |
| Resultado Obtenido | HTTP 200, modification_date actualizado |
| Estado             | ✅ APROBADO |
| Fecha Ejecución    | October 27, 2025 |
| Ejecutado por      | Daniel Soto |

---

## Prueba UT-GD-003.17

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-GD-003.17 |
| Título             | Los parámetros anteriores son eliminados y reemplazados |
| Descripción        | Verifica que al actualizar con nuevos parámetros, los anteriores son eliminados y se crean los nuevos. |
| Precondiciones     | Dispositivo con ID 11 tiene parámetros [1,2,3]. Usuario con permiso 114. |
| Datos de Entrada   | {"method":"PUT","path":"/telemetry-devices/11/","body":{"name":"FMC Actualizado","IMEI":123456789012352,"parameters":[4,5,6,7]}} |
| Pasos (AAA)        | Arrange: asociar parámetros [1,2,3]; Act: PUT con [4,5,6,7]; Assert: solo parámetros [4,5,6,7] existen. |
| Resultado Esperado | HTTP 200, parámetros anteriores eliminados, nuevos creados |
| Resultado Obtenido | HTTP 200, parámetros anteriores eliminados, nuevos creados |
| Estado             | ✅ APROBADO |
| Fecha Ejecución    | October 27, 2025 |
| Ejecutado por      | Daniel Soto |

---

## Resumen Ejecutivo

- **Total de Pruebas**: 17
- **Pruebas Aprobadas**: 17 ✅
- **Pruebas Fallidas**: 0
- **Cobertura de Funcionalidades**: 100%
  - Control de acceso y autenticación
  - Validaciones de campos obligatorios
  - Validaciones de negocio (duplicidad, formato)
  - Validaciones de longitud
  - Manejo de errores
  - Integridad de datos (fechas y parámetros)

---

## Conclusiones

Todas las pruebas fueron aprobadas exitosamente. El endpoint PUT /telemetry-devices/{id}/ cumple con todos los requisitos de seguridad, validación e integridad de datos establecidos. La implementación maneja correctamente:

1. **Control de acceso**: Verificación de autenticación y permisos
2. **Validaciones de campo**: Campos obligatorios, tipos de datos y longitudes
3. **Validaciones de negocio**: Unicidad de nombre e IMEI, validación de parámetros
4. **Integridad temporal**: Preservación de registration_date y actualización de modification_date
5. **Integridad relacional**: Eliminación y creación de parámetros asociados

El sistema está listo para operar en producción con garantías de calidad y seguridad.

