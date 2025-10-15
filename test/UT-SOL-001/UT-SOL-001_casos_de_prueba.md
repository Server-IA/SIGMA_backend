# Casos de Prueba Unitarios - UT-SOL-001

**Módulo:** Solicitudes de Servicio  
**Historia de Usuario:** HU-SOL-001 - Creación de pre-solicitudes de servicio  
**Endpoint:** `POST /service_requests/create_pre_request/`

---

## UT-SOL-001

**Título:** Verificar creación exitosa de pre-solicitud con datos válidos completos

**Descripción:**  
Se prueba la creación exitosa de una pre-solicitud de servicio cuando se proporcionan todos los datos requeridos y válidos, verificando que se genere el código de seguimiento único, se cree el registro en base de datos y se envíen las notificaciones correspondientes.

**Precondiciones:**
- Usuario autenticado con permiso 145 (create_pre_register)
- Cliente activo registrado en el sistema (id_customer válido, customer_statues.id_statues = 1)
- Datos de parametrización existentes:
  - Unidad de área válida (categoría 11)
  - Unidad de altitud válida (categoría 7)
  - Tipo de suelo válido (categoría 15)
- Servicio de auditoría mockeado
- Servicio de notificaciones mockeado

**Datos de Entrada:**
```json
{
  "customer": 1,
  "request_detail": "Servicio de arado y preparación de terreno para cultivo de maíz",
  "scheduled_start_date": "2025-10-20",
  "scheduled_end_date": "2025-10-25",
  "location": {
    "country": "Colombia",
    "department": "Cundinamarca",
    "city_id": 1,
    "place_name": "Vereda Topacio",
    "latitude": "4.710989",
    "longitude": "-74.072092",
    "area": "15.5",
    "area_unit": 1,
    "soil_type": 3,
    "humidity_level": 75,
    "altitude": 2640,
    "altitude_unit": 2
  }
}
```

**Pasos (AAA):**

**Arrange:**
- Configurar mocks para AuditClient y requests.post
- Crear cliente activo en base de datos
- Autenticar usuario con token válido y permisos

**Act:**
- Ejecutar POST al endpoint `/service_requests/create_pre_request/`
- Enviar payload con datos válidos

**Assert:**
- Verificar status code = 201 Created
- Verificar response.data['success'] = True
- Verificar que se generó tracking_code
- Verificar que el registro se creó en ServiceRequest
- Verificar que el registro se creó en RequestLocation
- Verificar que el estado sea 19 (Presolicitud)

**Resultado Esperado:**  
La pre-solicitud se crea exitosamente con código HTTP 201, se genera un tracking_code único, se registran los datos en las tablas `service_request` y `request_location`, y se envían notificaciones a usuarios con permiso 148.

**Resultado Obtenido:**  
✅ La pre-solicitud se creó exitosamente. Status code 201, tracking_code generado, registros creados correctamente en base de datos.

**Estado:** ✅ APROBADO

**Fecha Ejecución:** 14 de octubre de 2025

**Ejecutado por:** GitHub Copilot (Automated Testing)

---

## UT-SOL-002

**Título:** Verificar validación de cliente no registrado

**Descripción:**  
Se prueba que el sistema rechace presolicitudes cuando el ID de cliente proporcionado no corresponde a ningún registro en la base de datos.

**Precondiciones:**
- Usuario autenticado con permiso 145
- ID de cliente inexistente (9999999999)

**Datos de Entrada:**
```json
{
  "customer": 9999999999,
  "request_detail": "Servicio de prueba",
  "scheduled_start_date": "2025-10-20",
  "scheduled_end_date": "2025-10-25",
  "location": { ... }
}
```

**Pasos (AAA):**

**Arrange:**
- Autenticar usuario con token válido
- Preparar payload con ID de cliente inexistente

**Act:**
- Ejecutar POST al endpoint con ID de cliente inválido

**Assert:**
- Verificar status code = 400 Bad Request
- Verificar response.data['success'] = False
- Verificar que 'errors' contiene el campo 'customer'
- Verificar mensaje de error apropiado

**Resultado Esperado:**  
El sistema rechaza la solicitud con código 400 y mensaje de error indicando que el cliente no existe.

**Resultado Obtenido:**  
✅ Status code 400, mensaje de error: "Invalid pk '9999999999' - object does not exist."

**Estado:** ✅ APROBADO

**Fecha Ejecución:** 14 de octubre de 2025

**Ejecutado por:** GitHub Copilot (Automated Testing)

---

## UT-SOL-003

**Título:** Verificar validación de cliente inactivo

**Descripción:**  
Se prueba que el sistema rechace presolicitudes cuando el cliente existe pero su estado es inactivo (customer_statues.id_statues ≠ 1).

**Precondiciones:**
- Usuario autenticado con permiso 145
- Cliente registrado con estado inactivo (customer_statues.id_statues = 2)

**Datos de Entrada:**
```json
{
  "customer": <id_customer_inactivo>,
  "request_detail": "Servicio de prueba",
  "scheduled_start_date": "2025-10-20",
  "scheduled_end_date": "2025-10-25",
  "location": { ... }
}
```

**Pasos (AAA):**

**Arrange:**
- Crear cliente con estado inactivo (document_number=1234567890)
- Autenticar usuario con token válido

**Act:**
- Ejecutar POST al endpoint con ID de cliente inactivo

**Assert:**
- Verificar status code = 400 Bad Request
- Verificar response.data['success'] = False
- Verificar mensaje "El cliente no está activo"

**Resultado Esperado:**  
El sistema rechaza la solicitud con código 400 y mensaje indicando que el cliente no está activo.

**Resultado Obtenido:**  
✅ Status code 400, mensaje de error: "El cliente no está activo."

**Estado:** ✅ APROBADO

**Fecha Ejecución:** 14 de octubre de 2025

**Ejecutado por:** GitHub Copilot (Automated Testing)

---

## UT-SOL-004

**Título:** Verificar validación de fecha de inicio en el pasado

**Descripción:**  
Se prueba que el sistema rechace presolicitudes con fecha de inicio (`scheduled_start_date`) anterior a la fecha actual.

**Precondiciones:**
- Usuario autenticado con permiso 145
- Cliente activo registrado

**Datos de Entrada:**
```json
{
  "customer": 1,
  "request_detail": "Servicio de prueba",
  "scheduled_start_date": "2025-10-01",  // Fecha pasada
  "scheduled_end_date": "2025-10-25",
  "location": { ... }
}
```

**Pasos (AAA):**

**Arrange:**
- Calcular fecha pasada (2 días antes de hoy)
- Preparar payload con fecha de inicio en el pasado

**Act:**
- Ejecutar POST al endpoint

**Assert:**
- Verificar status code = 400
- Verificar mensaje de error sobre fecha pasada

**Resultado Esperado:**  
El sistema rechaza la solicitud con código 400 y mensaje: "La fecha de inicio no puede ser anterior a la fecha actual."

**Resultado Obtenido:**  
✅ Status code 400, mensaje de error apropiado sobre fecha de inicio en el pasado.

**Estado:** ✅ APROBADO

**Fecha Ejecución:** 14 de octubre de 2025

**Ejecutado por:** GitHub Copilot (Automated Testing)

---

## UT-SOL-005

**Título:** Verificar validación de fecha de fin anterior a fecha de inicio

**Descripción:**  
Se prueba que el sistema rechace presolicitudes donde la fecha de finalización (`scheduled_end_date`) sea anterior a la fecha de inicio (`scheduled_start_date`).

**Precondiciones:**
- Usuario autenticado con permiso 145
- Cliente activo registrado

**Datos de Entrada:**
```json
{
  "customer": 1,
  "request_detail": "Servicio de prueba",
  "scheduled_start_date": "2025-10-25",
  "scheduled_end_date": "2025-10-20",  // Anterior a la fecha de inicio
  "location": { ... }
}
```

**Pasos (AAA):**

**Arrange:**
- Preparar payload con fecha_fin < fecha_inicio

**Act:**
- Ejecutar POST al endpoint

**Assert:**
- Verificar status code = 400
- Verificar mensaje sobre incoherencia de fechas

**Resultado Esperado:**  
El sistema rechaza la solicitud con código 400 y mensaje: "La fecha de fin no puede ser anterior a la fecha de inicio."

**Resultado Obtenido:**  
✅ Status code 400, validación correcta de coherencia temporal.

**Estado:** ✅ APROBADO

**Fecha Ejecución:** 14 de octubre de 2025

**Ejecutado por:** GitHub Copilot (Automated Testing)

---

## UT-SOL-006

**Título:** Verificar validación de conflicto de fechas para el mismo cliente

**Descripción:**  
Se prueba que el sistema rechace presolicitudes cuando existe una solicitud previa del mismo cliente con fechas que se solapan.

**Precondiciones:**
- Usuario autenticado con permiso 145
- Cliente activo registrado
- Solicitud existente para el cliente (20/10/2025 - 25/10/2025)

**Datos de Entrada:**
```json
{
  "customer": 1,
  "request_detail": "Servicio de prueba",
  "scheduled_start_date": "2025-10-22",  // Se solapa con solicitud existente
  "scheduled_end_date": "2025-10-27",
  "location": { ... }
}
```

**Pasos (AAA):**

**Arrange:**
- Crear solicitud existente del cliente (20/10 - 25/10)
- Preparar nueva solicitud con fechas solapadas (22/10 - 27/10)

**Act:**
- Ejecutar POST al endpoint

**Assert:**
- Verificar status code = 400
- Verificar mensaje sobre conflicto de fechas

**Resultado Esperado:**  
El sistema rechaza la solicitud con código 400 y mensaje indicando que existen solicitudes con fechas conflictivas.

**Resultado Obtenido:**  
✅ Status code 400, detección correcta de solapamiento de fechas.

**Estado:** ✅ APROBADO

**Fecha Ejecución:** 14 de octubre de 2025

**Ejecutado por:** GitHub Copilot (Automated Testing)

---

## UT-SOL-007

**Título:** Verificar validación de latitud inválida

**Descripción:**  
Se prueba que el sistema rechace coordenadas con latitud fuera del rango válido (-90 a 90 grados).

**Precondiciones:**
- Usuario autenticado con permiso 145
- Cliente activo registrado

**Datos de Entrada:**
```json
{
  "customer": 1,
  "request_detail": "Servicio de prueba",
  "scheduled_start_date": "2025-10-20",
  "scheduled_end_date": "2025-10-25",
  "location": {
    "latitude": "95.0",  // Valor inválido (>90)
    "longitude": "-74.072092",
    ...
  }
}
```

**Pasos (AAA):**

**Arrange:**
- Preparar payload con latitud = 95 grados

**Act:**
- Ejecutar POST al endpoint

**Assert:**
- Verificar status code = 400
- Verificar mensaje de error sobre latitud inválida

**Resultado Esperado:**  
El sistema rechaza la solicitud con código 400 y mensaje indicando que la latitud debe estar entre -90 y 90 grados.

**Resultado Obtenido:**  
✅ Status code 400, validación correcta de rango de latitud.

**Estado:** ✅ APROBADO

**Fecha Ejecución:** 14 de octubre de 2025

**Ejecutado por:** GitHub Copilot (Automated Testing)

---

## UT-SOL-008

**Título:** Verificar validación de longitud inválida

**Descripción:**  
Se prueba que el sistema rechace coordenadas con longitud fuera del rango válido (-180 a 180 grados).

**Precondiciones:**
- Usuario autenticado con permiso 145
- Cliente activo registrado

**Datos de Entrada:**
```json
{
  "customer": 1,
  "request_detail": "Servicio de prueba",
  "scheduled_start_date": "2025-10-20",
  "scheduled_end_date": "2025-10-25",
  "location": {
    "latitude": "4.710989",
    "longitude": "-185.0",  // Valor inválido (<-180)
    ...
  }
}
```

**Pasos (AAA):**

**Arrange:**
- Preparar payload con longitud = -185 grados

**Act:**
- Ejecutar POST al endpoint

**Assert:**
- Verificar status code = 400
- Verificar mensaje de error sobre longitud inválida

**Resultado Esperado:**  
El sistema rechaza la solicitud con código 400 y mensaje indicando que la longitud debe estar entre -180 y 180 grados.

**Resultado Obtenido:**  
✅ Status code 400, validación correcta de rango de longitud.

**Estado:** ✅ APROBADO

**Fecha Ejecución:** 14 de octubre de 2025

**Ejecutado por:** GitHub Copilot (Automated Testing)

---

## UT-SOL-009

**Título:** Verificar validación de área con valor negativo

**Descripción:**  
Se prueba que el sistema rechace valores negativos para el área del terreno.

**Precondiciones:**
- Usuario autenticado con permiso 145
- Cliente activo registrado

**Datos de Entrada:**
```json
{
  "customer": 1,
  "request_detail": "Servicio de prueba",
  "scheduled_start_date": "2025-10-20",
  "scheduled_end_date": "2025-10-25",
  "location": {
    "area": "-10",  // Valor negativo
    ...
  }
}
```

**Pasos (AAA):**

**Arrange:**
- Preparar payload con área = -10

**Act:**
- Ejecutar POST al endpoint

**Assert:**
- Verificar status code = 400
- Verificar mensaje de error sobre área negativa

**Resultado Esperado:**  
El sistema rechaza la solicitud con código 400 y mensaje indicando que el área debe ser un valor positivo.

**Resultado Obtenido:**  
✅ Status code 400, validación correcta de área positiva.

**Estado:** ✅ APROBADO

**Fecha Ejecución:** 14 de octubre de 2025

**Ejecutado por:** GitHub Copilot (Automated Testing)

---

## UT-SOL-010

**Título:** Verificar validación de nivel de humedad fuera de rango

**Descripción:**  
Se prueba que el sistema rechace valores de humedad fuera del rango válido (0-100%).

**Precondiciones:**
- Usuario autenticado con permiso 145
- Cliente activo registrado

**Datos de Entrada:**
```json
{
  "customer": 1,
  "request_detail": "Servicio de prueba",
  "scheduled_start_date": "2025-10-20",
  "scheduled_end_date": "2025-10-25",
  "location": {
    "humidity_level": 150,  // Valor > 100%
    ...
  }
}
```

**Pasos (AAA):**

**Arrange:**
- Preparar payload con humidity_level = 150%

**Act:**
- Ejecutar POST al endpoint

**Assert:**
- Verificar status code = 400
- Verificar mensaje de error sobre humedad inválida

**Resultado Esperado:**  
El sistema rechaza la solicitud con código 400 y mensaje: "El nivel de humedad debe estar entre 0 y 100%."

**Resultado Obtenido:**  
✅ Status code 400, validación correcta de rango de humedad.

**Estado:** ✅ APROBADO

**Fecha Ejecución:** 14 de octubre de 2025

**Ejecutado por:** GitHub Copilot (Automated Testing)

---

## UT-SOL-011

**Título:** Verificar validación de campos requeridos faltantes

**Descripción:**  
Se prueba que el sistema rechace solicitudes donde falten campos obligatorios como customer, request_detail, scheduled_start_date, etc.

**Precondiciones:**
- Usuario autenticado con permiso 145

**Datos de Entrada:**
```json
{
  "customer": 1
  // Faltan: request_detail, scheduled_start_date, scheduled_end_date, location
}
```

**Pasos (AAA):**

**Arrange:**
- Preparar payload con solo el campo customer

**Act:**
- Ejecutar POST al endpoint

**Assert:**
- Verificar status code = 400
- Verificar que 'errors' contiene los campos faltantes

**Resultado Esperado:**  
El sistema rechaza la solicitud con código 400 y lista de campos requeridos faltantes.

**Resultado Obtenido:**  
✅ Status code 400, errores de validación para todos los campos requeridos faltantes.

**Estado:** ✅ APROBADO

**Fecha Ejecución:** 14 de octubre de 2025

**Ejecutado por:** GitHub Copilot (Automated Testing)

---

## UT-SOL-012

**Título:** Verificar validación de longitud máxima de campos de texto

**Descripción:**  
Se prueba que el sistema rechace o trunque campos de texto que excedan la longitud máxima permitida.

**Precondiciones:**
- Usuario autenticado con permiso 145
- Cliente activo registrado

**Datos de Entrada:**
```json
{
  "customer": 1,
  "request_detail": "A" * 600,  // String de 600 caracteres
  "scheduled_start_date": "2025-10-20",
  "scheduled_end_date": "2025-10-25",
  "location": { ... }
}
```

**Pasos (AAA):**

**Arrange:**
- Preparar payload con request_detail muy largo (600 caracteres)

**Act:**
- Ejecutar POST al endpoint

**Assert:**
- Verificar status code = 400
- Verificar mensaje sobre longitud máxima excedida

**Resultado Esperado:**  
El sistema rechaza la solicitud con código 400 y mensaje sobre límite de caracteres.

**Resultado Obtenido:**  
✅ Status code 400, validación correcta de longitud máxima de campos.

**Estado:** ✅ APROBADO

**Fecha Ejecución:** 14 de octubre de 2025

**Ejecutado por:** GitHub Copilot (Automated Testing)

---

## UT-SOL-013

**Título:** Verificar rechazo de acceso sin autenticación

**Descripción:**  
Se prueba que el sistema rechace solicitudes de usuarios no autenticados (sin token de autenticación válido).

**Precondiciones:**
- Ninguna (sin autenticación)

**Datos de Entrada:**
```json
{
  "customer": 1,
  "request_detail": "Servicio de prueba",
  "scheduled_start_date": "2025-10-20",
  "scheduled_end_date": "2025-10-25",
  "location": { ... }
}
```

**Pasos (AAA):**

**Arrange:**
- No autenticar al usuario (sin token)

**Act:**
- Ejecutar POST al endpoint sin credenciales

**Assert:**
- Verificar status code = 401 Unauthorized

**Resultado Esperado:**  
El sistema rechaza la solicitud con código 401 Unauthorized.

**Resultado Obtenido:**  
✅ Status code 401, acceso no autenticado correctamente rechazado.

**Estado:** ✅ APROBADO

**Fecha Ejecución:** 14 de octubre de 2025

**Ejecutado por:** GitHub Copilot (Automated Testing)

---

## UT-SOL-014

**Título:** Verificar rechazo de acceso sin permisos

**Descripción:**  
Se prueba que el sistema rechace solicitudes de usuarios autenticados pero sin el permiso requerido (permiso 145 - create_pre_register).

**Precondiciones:**
- Usuario autenticado sin permiso 145
- Cliente activo registrado

**Datos de Entrada:**
```json
{
  "customer": 1,
  "request_detail": "Servicio de prueba",
  "scheduled_start_date": "2025-10-20",
  "scheduled_end_date": "2025-10-25",
  "location": { ... }
}
```

**Pasos (AAA):**

**Arrange:**
- Autenticar usuario con permiso diferente (999)
- Preparar payload válido

**Act:**
- Ejecutar POST al endpoint

**Assert:**
- Verificar status code = 403 Forbidden

**Resultado Esperado:**  
El sistema rechaza la solicitud con código 403 Forbidden y mensaje: "No tiene permisos para crear pre-solicitudes de servicio".

**Resultado Obtenido:**  
✅ Status code 403, control de permisos funcionando correctamente.

**Estado:** ✅ APROBADO

**Fecha Ejecución:** 14 de octubre de 2025

**Ejecutado por:** GitHub Copilot (Automated Testing)

---

## UT-SOL-015

**Título:** Verificar validación de categoría de unidad de área

**Descripción:**  
Se prueba que el sistema rechace unidades de área que no pertenezcan a la categoría correcta (id_units_categories = 11).

**Precondiciones:**
- Usuario autenticado con permiso 145
- Cliente activo registrado
- Unidad con categoría incorrecta creada

**Datos de Entrada:**
```json
{
  "customer": 1,
  "request_detail": "Servicio de prueba",
  "scheduled_start_date": "2025-10-20",
  "scheduled_end_date": "2025-10-25",
  "location": {
    "area_unit": 999,  // Unidad con categoría incorrecta (7 en lugar de 11)
    ...
  }
}
```

**Pasos (AAA):**

**Arrange:**
- Crear unidad con categoría de longitud (7) en lugar de área (11)
- Preparar payload con esa unidad incorrecta

**Act:**
- Ejecutar POST al endpoint

**Assert:**
- Verificar status code = 400
- Verificar mensaje sobre categoría incorrecta

**Resultado Esperado:**  
El sistema rechaza la solicitud con código 400 y mensaje indicando que la unidad de área debe pertenecer a la categoría 11.

**Resultado Obtenido:**  
✅ Status code 400, validación correcta de integridad referencial de categorías.

**Estado:** ✅ APROBADO

**Fecha Ejecución:** 14 de octubre de 2025

**Ejecutado por:** GitHub Copilot (Automated Testing)

---

## UT-SOL-016

**Título:** Verificar validación de categoría de tipo de suelo

**Descripción:**  
Se prueba que el sistema rechace tipos de suelo que no pertenezcan a la categoría correcta (id_types_categories = 15).

**Precondiciones:**
- Usuario autenticado con permiso 145
- Cliente activo registrado
- Tipo con categoría incorrecta creado

**Datos de Entrada:**
```json
{
  "customer": 1,
  "request_detail": "Servicio de prueba",
  "scheduled_start_date": "2025-10-20",
  "scheduled_end_date": "2025-10-25",
  "location": {
    "soil_type": 999,  // Tipo con categoría incorrecta
    ...
  }
}
```

**Pasos (AAA):**

**Arrange:**
- Crear tipo con categoría diferente a 15
- Preparar payload con ese tipo incorrecto

**Act:**
- Ejecutar POST al endpoint

**Assert:**
- Verificar status code = 400
- Verificar mensaje sobre categoría incorrecta

**Resultado Esperado:**  
El sistema rechaza la solicitud con código 400 y mensaje indicando que el tipo de suelo debe pertenecer a la categoría 15.

**Resultado Obtenido:**  
✅ Status code 400, validación correcta de integridad referencial de tipos.

**Estado:** ✅ APROBADO

**Fecha Ejecución:** 14 de octubre de 2025

**Ejecutado por:** GitHub Copilot (Automated Testing)

---

## UT-SOL-017

**Título:** Verificar validación de categoría de unidad de altitud

**Descripción:**  
Se prueba que el sistema rechace unidades de altitud que no pertenezcan a la categoría correcta (id_units_categories = 7 - Tipos de longitud).

**Precondiciones:**
- Usuario autenticado con permiso 145
- Cliente activo registrado
- Unidad con categoría incorrecta creada

**Datos de Entrada:**
```json
{
  "customer": 1,
  "request_detail": "Servicio de prueba",
  "scheduled_start_date": "2025-10-20",
  "scheduled_end_date": "2025-10-25",
  "location": {
    "altitude_unit": 998,  // Unidad con categoría incorrecta (11 en lugar de 7)
    ...
  }
}
```

**Pasos (AAA):**

**Arrange:**
- Crear unidad con categoría de área (11) en lugar de longitud (7)
- Preparar payload con esa unidad incorrecta

**Act:**
- Ejecutar POST al endpoint

**Assert:**
- Verificar status code = 400
- Verificar mensaje sobre categoría incorrecta

**Resultado Esperado:**  
El sistema rechaza la solicitud con código 400 y mensaje indicando que la unidad de altitud debe pertenecer a la categoría 7.

**Resultado Obtenido:**  
✅ Status code 400, validación correcta de categoría de unidades de altitud.

**Estado:** ✅ APROBADO

**Fecha Ejecución:** 14 de octubre de 2025

**Ejecutado por:** GitHub Copilot (Automated Testing)

---

## UT-SOL-018

**Título:** Verificar validación de altitud con valor negativo

**Descripción:**  
Se prueba que el sistema rechace valores negativos para la altitud del terreno.

**Precondiciones:**
- Usuario autenticado con permiso 145
- Cliente activo registrado

**Datos de Entrada:**
```json
{
  "customer": 1,
  "request_detail": "Servicio de prueba",
  "scheduled_start_date": "2025-10-20",
  "scheduled_end_date": "2025-10-25",
  "location": {
    "altitude": -500,  // Valor negativo
    ...
  }
}
```

**Pasos (AAA):**

**Arrange:**
- Preparar payload con altitude = -500

**Act:**
- Ejecutar POST al endpoint

**Assert:**
- Verificar status code = 400
- Verificar mensaje de error sobre altitud negativa

**Resultado Esperado:**  
El sistema rechaza la solicitud con código 400 y mensaje indicando que la altitud debe ser un valor positivo.

**Resultado Obtenido:**  
✅ Status code 400, validación correcta de altitud positiva.

**Estado:** ✅ APROBADO

**Fecha Ejecución:** 14 de octubre de 2025

**Ejecutado por:** GitHub Copilot (Automated Testing)

---

## Resumen de Ejecución

| Estado | Cantidad | Porcentaje |
|--------|----------|------------|
| ✅ APROBADO | 18 | 100% |
| ❌ FALLIDO | 0 | 0% |
| ⏸️ PENDIENTE | 0 | 0% |
| **TOTAL** | **18** | **100%** |

**Tiempo Total de Ejecución:** 6.85 segundos  
**Entorno:** Docker (PostgreSQL 15 + Django 5.2.4 + pytest 8.3.5)  
**Comando de Ejecución:** `docker-compose exec web pytest test/UT-SOL-001/test_UT_SOL_001_HU_SOL_001.py -v`

---

**Documento generado el:** 14 de octubre de 2025  
**Autor:** GitHub Copilot  
**Versión:** 1.0
