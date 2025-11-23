# Reporte de Pruebas Unitarias - UT-EMP-003
## Endpoint: Detalle de Empleado (GET /employees/{id}/detail/)

**Fecha de Ejecución:** 2025-11-22
**Permiso Requerido:** ID 182 - Ver detalle de empleado

---

## Resumen Ejecutivo

| Métrica | Valor |
|--------:|:-----|
| **Total de Pruebas** | 7 |
| **Aprobadas** | 5 |
| **No Aprobadas** | 2 |
| **Tasa de Éxito** | 71% |
| **Tiempo de Ejecución** | ~6s (aprox.) |

---

## Tabla de Resultados

| ID Test | Título | Estado | Comentario |
|---------|--------|--------|-----------|
| UT-EMP-003-01 | Visualización completa de detalle de empleado con datos completos | ❌ FALLÓ | Esperaba email externo `user123@test.com`, recibió email local `full@test.com` |
| UT-EMP-003-02 | Detalle empleado sin usuario asociado | ✅ APROBADO | Campos externos null, email local mostrado |
| UT-EMP-003-03 | Empleado sin contrato activo o asociado | ✅ APROBADO | `contract_code` = null correctamente |
| UT-EMP-003-04 | Historial de novedades vacío para empleado sin modificaciones | ✅ APROBADO | Lista vacía retornada |
| UT-EMP-003-05 | Acceso denegado sin permiso 182 | ✅ APROBADO | 403 cuando token sin permiso |
| UT-EMP-003-06 | Manejo de error 404 cuando empleado no existe | ✅ APROBADO | 404 retornado correctamente |
| UT-EMP-003-07 | Manejo de errores internos del servicio | ❌ FALLÓ | Se registró excepción registrada pero la vista devolvió 200 en vez de 500 |

---

## Resultados Detallados

### ❌ UT-EMP-003-01: Visualización completa de detalle de empleado con datos completos

**Descripción:** Comprueba que el endpoint retorna `personal_info` completo incluyendo datos desde el servicio externo (nombre, documento, email externo).

**Datos de Entrada:**
GET /employees/{id}/detail/ con token con permiso `182` y configuración de mock del servicio externo que devuelve `email: user123@test.com`.

**Resultado Esperado:**
- HTTP 200
- `personal_info.email` = `user123@test.com` (email proveniente del servicio externo)

**Resultado Obtenido:**
- HTTP 200
- `personal_info.email` = `full@test.com` (email local del modelo Employee)

**Logs / Evidencia:**
```
WARNING  payroll.serializers.employee_contracts_serializers.employee_detail_serializer:employee_detail_serializer.py:231 Error consultando por documento 1079172265: 401 {"detail":"Credenciales inválidas"}
```

**Análisis:**
- El serializer prioriza el `email` local cuando existe, ignorando el email devuelto por `get_users_info_batch`.

**Estado:** FALLÓ

---

### ✅ UT-EMP-003-02: Detalle empleado sin usuario asociado

**Descripción:** Empleado sin `id_user` debe devolver personal_info con campos externos nulos y email local.

**Resultado:** APROBADO (HTTP 200, `email` local presente, campos externos null).

---

### ✅ UT-EMP-003-03: Empleado sin contrato activo o asociado

**Descripción:** Cuando no hay contrato, `contract_code` debe ser null.

**Resultado:** APROBADO (HTTP 200, `contract_code` = null).

---

### ✅ UT-EMP-003-04: Historial de novedades vacío para empleado sin modificaciones

**Descripción:** Lista vacía de novedades si no hay registros.

**Resultado:** APROBADO (HTTP 200, `news_history` lista vacía).

---

### ✅ UT-EMP-003-05: Acceso denegado sin permiso 182

**Descripción:** Verifica 403 cuando el token no contiene permiso `182`.

**Resultado:** APROBADO (HTTP 403, mensaje de acceso denegado).

---

### ✅ UT-EMP-003-06: Manejo de error 404 cuando empleado no existe

**Descripción:** Solicitud a id inexistente debe devolver 404.

**Resultado:** APROBADO (HTTP 404, mensaje "Empleado no encontrado").

---

### ❌ UT-EMP-003-07: Manejo de errores internos del servicio

**Descripción:** Si el helper externo lanza excepción, la vista debería devolver HTTP 500 y un mensaje claro.

**Resultado Esperado:** HTTP 500 con JSON: {"success": false, "message": "Ocurrió un error al procesar la solicitud.", ...}

**Resultado Obtenido:** HTTP 200; logs muestran excepción registrada:
```
Error inesperado consultando servicio externo de usuarios: External Service Error
ERROR    service_requests.utils.external_user_helper:external_user_helper.py:84 Error inesperado consultando servicio externo de usuarios: External Service Error
ERROR    payroll.serializers.employee_contracts_serializers.employee_detail_serializer:employee_detail_serializer.py:197 Error consultando servicio externo de usuarios: External Service Error
```

**Análisis:**
- El helper captura/registrar la excepción pero no la propaga; la vista continúa y devuelve 200.

**Estado:** FALLÓ

---

## Observaciones Generales

- Los fallos están relacionados con la integración con el servicio externo de usuarios:
  - Prioridad del `email` (debe preferirse el valor externo cuando exista).
  - Manejo de errores: las excepciones del helper deben llegar a la vista (o la vista debe interpretar un indicador de error) para devolver `500`.
- Los tests restantes que cubren validaciones y permisos pasan correctamente.

---

## Conclusiones

- La funcionalidad base del endpoint funciona (consulta, contratos, novedades, permisos), pero hay dos defectos de integración con el servicio de usuarios que afectan la exactitud de datos mostrados y la visibilidad de errores.
- Severidad propuesta: MEDIA.

---

## Recomendaciones y pasos para la corrección

1. En `EmployeeDetailSerializer` priorizar `users_data[...]['email']` cuando esté presente sobre `Employee.email`.
2. En `service_requests/utils/external_user_helper.py` no silenciar excepciones inesperadas: registrar y relanzar o devolver una estructura con `_error` que la vista convierta en HTTP 500.
3. Añadir tests unitarios que cubran ambos escenarios:
   - `get_users_info_batch` devuelve email externo → assert email externo en respuesta.
   - `get_users_info_batch` lanza excepción → assert HTTP 500 y mensaje.

---

## Comandos útiles

Ejecutar la suite UT-EMP-003 dentro del contenedor `web`:
```powershell
docker-compose exec web pytest -q test/UT-EMP-003 -q
```

Ejecutar un caso específico:
```powershell
docker-compose exec web pytest -q test/UT-EMP-003/test_UT_EMP_003.py::TestEmployeeDetail::test_ut_emp_003_01_full_detail -q
```

Ver logs del contenedor `web` en tiempo real:
```powershell
docker-compose logs --follow web
```

---

## Archivos relacionados

- `test/UT-EMP-003/test_UT_EMP_003.py` (pruebas)
- `test/UT-EMP-003/UT-EMP-003-reporte.md` (este informe)
- `test/bugs/BUG-UT-EMP-003-EXTERNAL-SERVICE.md` (bug report con evidencia y propuesta)
- `payroll/serializers/employee_contracts_serializers/employee_detail_serializer.py`
- `service_requests/utils/external_user_helper.py`

---

**Generado:** 2025-11-22  (automático)
**Autor:** Equipo de QA/Dev


**Objetivo de la prueba**
- Confirmar que el endpoint `GET /employees/{id}/detail/`:
  - prioriza el `email` proveniente del servicio externo de usuarios cuando está disponible;
  - propaga errores del servicio externo (debe devolver 500 cuando hay fallo inesperado en la consulta externa).

**Resumen ejecutivo (hallazgos)**
- Resultado: la implementación actual NO prioriza el email externo (devuelve `email` local del modelo `Employee` si existe).
- Resultado: cuando hay una excepción al consultar el servicio externo, el error se registra pero la API responde `200 OK` (debería devolver `500 Internal Server Error` según la especificación que esperamos).
- Severidad propuesta: MEDIA — la información mostrada puede ser incorrecta y los errores externos quedan silenciados, escondiendo fallos reales en producción.

**Contexto técnico y entorno**
- Repo: `AppMachineryPayrollBackend` (branch `tests`).
- Servicio probado: `web` (contenedor Docker, ejecutado vía `docker-compose`).
- Framework: Python 3.11, Django + DRF.
- Autenticación: JWT (cabecera `Authorization: Bearer <JWT>`). La comprobación de permisos se realiza por `roles->permisos` en el payload del token.
- Endpoints relevantes:
  - `GET /employees/{id}/detail/` (requiere permiso id `182`).
  - Helper externo: `service_requests.utils.external_user_helper.get_users_info_batch`.

**Pasos reproducibles (rápidos)**
1. Levantar servicios:
```powershell
docker-compose up -d --build
```
2. Generar token con permiso `182` (ejemplo dentro del contenedor `web`):
```powershell
docker-compose exec web /bin/sh -c "python - <<'PY'
import os, jwt
secret = os.getenv('JWT_SECRET') or 'secret'
payload = {'id': 9999, 'email': 'tester@example.com', 'roles': [{'permisos': [{'id': 182}]}]}
print(jwt.encode(payload, secret, algorithm='HS256'))
PY"
```
3. (Opcional) Si la DB está vacía: crear un empleado de prueba (hecho en mis pruebas). Ejemplo (ya ejecutado en entorno de pruebas): se creó `employee.id_employee=1` con `email='full@test.com'` y `id_user=123`.
4. Llamada al endpoint con el token:
```powershell
docker-compose exec web /bin/sh -c "python - <<'PY'
import urllib.request
TOKEN = '<TOKEN>'
url = 'http://127.0.0.1:8000/employees/1/detail/'
req = urllib.request.Request(url)
req.add_header('Authorization', f'Bearer {TOKEN}')
resp = urllib.request.urlopen(req, timeout=10)
print('STATUS', resp.getcode())
print(resp.read().decode('utf-8'))
PY"
```

**Evidencia producida (salidas relevantes)**
- Resultado de ejecutar `pytest -q test/UT-EMP-003` dentro del contenedor `web`:

```
t/UT-EMP-003 -q                                                                                    F.....F                                                                                     [100%]
============================================ FAILURES =============================================
________________________ TestEmployeeDetail.test_ut_emp_003_01_full_detail ________________________
E   AssertionError: assert 'full@test.com' == 'user123@test.com'
---------------------------------------- Captured log call ----------------------------------------
WARNING  payroll.serializers.employee_contracts_serializers.employee_detail_serializer:employee_detail_serializer.py:231 Error consultando por documento 1079172265: 401 {"detail":"Credenciales inválidas"}
____________________ TestEmployeeDetail.test_ut_emp_003_07_internal_error _______________________
E   assert 200 == 500
-------------------------------------- Captured stderr call ---------------------------------------
Error inesperado consultando servicio externo de usuarios: External Service Error
---------------------------------------- Captured log call ----------------------------------------
ERROR    service_requests.utils.external_user_helper:external_user_helper.py:84 Error inesperado consultando servicio externo de usuarios: External Service Error
ERROR    payroll.serializers.employee_contracts_serializers.employee_detail_serializer:employee_detail_serializer.py:197 Error consultando servicio externo de usuarios: External Service Error
```

Codificado manual (prueba en entorno):

```
{"employee_id": 1, "created": true, "id_user_id": 123}
{"token": "eyJhbGci...Qp8"}
STATUS 200
{"success":true,"data":{"personal_info":{"id_user":123,...,"email":"full@test.com",...},"contract_info":{...},"news_history":[]}}
```

**Análisis técnico**
- Causa probable 1 (email local vs externo):
  - En `payroll/serializers/employee_contracts_serializers/employee_detail_serializer.py` la serialización construye `personal_info.email` a partir del modelo `Employee.email` si existe, sin priorizar el `email` proporcionado por `users_data` (datos externos). Cuando `get_users_info_batch` devuelve datos externos con email, el serializer no los prioriza como debería.

- Causa probable 2 (supresión de errores externos):
  - En `service_requests/utils/external_user_helper.py` el helper captura excepciones y devuelve `{}` o datos parciales en vez de relanzar la excepción o devolver un indicador de error. Como resultado, el flujo de la vista/serializer no detecta fallo crítico y continúa devolviendo `200 OK`. Los logs muestran que la excepción se registra, pero no altera la respuesta HTTP.

**Impacto**
- La información de email mostrada puede ser inconsistente con la fuente de verdad (servicio de usuarios). Esto puede causar errores en comunicaciones (envío de correos) o integraciones con otros sistemas.
- La supresión de errores externos oculta fallas en dependencias y dificulta la detección y resolución de incidentes.

**Recomendación técnica (cambio mínimo y seguro)**
1. Priorizar el `email` externo en la serialización (en `EmployeeDetailSerializer`):

```py
email = None
if users_data and users_data.get(employee.id_user_id):
    email = users_data[employee.id_user_id].get('email')
if not email:
    email = getattr(employee, 'email', None)
```

2. No silenciar excepciones inesperadas en `get_users_info_batch`: loggear + relanzar la excepción para que la vista devuelva `500` y el fallo sea evidente. Alternativa: devolver un objeto con `"_error": true` y que la vista valide y transforme en `500`.

3. Añadir tests que cubran ambos escenarios:
  - Cuando `get_users_info_batch` devuelve `email` externo, la respuesta debe contener ese email.
  - Cuando `get_users_info_batch` lanza excepción, la vista debe devolver `500`.

**Archivos/locaciones relevantes**
- `payroll/serializers/employee_contracts_serializers/employee_detail_serializer.py`
- `service_requests/utils/external_user_helper.py`
- Tests afectados: `test/UT-EMP-003/test_UT_EMP_003.py`

**Pasos sugeridos para el PR de corrección**
1. Añadir/actualizar unit tests (dos pruebas: éxito con email externo y fallo con excepción).
2. Ajustar `external_user_helper` para no silenciar errores (o propagar un indicador de error).
3. Ajustar `EmployeeDetailSerializer` para preferir email externo.
4. Ejecutar `pytest test/UT-EMP-003` y verificar que las pruebas pasan.

**Notas adicionales / cómo probar manualmente (Postman)**
- Generar token con permiso `182` y llamar `GET /employees/{id}/detail/`.
- Para simular email externo: ejecutar un mock HTTP que responda a `/users/users/basic-user-list/by-ids` con la entrada que incluya `email: user123@test.com`, apuntar `AUTH_SERVICE_URL` al mock (ej: `http://host.docker.internal:8081`) y reiniciar `web`.
- Para simular fallo externo: hacer que el mock devuelva `500` o cambiar `AUTH_SERVICE_URL` a una IP inalcanzable.

**Adjuntos / pruebas guardadas**
- Archivo de bug creado: `test/bugs/BUG-UT-EMP-003-EXTERNAL-SERVICE.md` (evidencia, logs y propuesta de corrección).
- Salida de `pytest -q test/UT-EMP-003` incluida más arriba.

---
Generado por: equipo de QA/Dev en entorno `web` (contenedor Docker). Si quieres, genero el PR con los cambios mínimos y las pruebas asociadas; dime si quieres que aplique los cambios en el branch `tests` o en una rama nueva `fix/UT-EMP-003-external-user`.
