# Reporte de Pruebas - UT-CON-004

## UT-CON-004

**ID:** UT-CON-004

**Título:** 200 OK – Listado de contratos establecidos (GET /established_contracts/list/)

**Descripción:** Verificar que el endpoint devuelve 200 con `success=true` y la lista esperada de contratos establecidos cuando el usuario está autenticado y posee el permiso requerido.

**Precondiciones:**
- Usuario autenticado con permiso id=177
- Existen registros de `EstablishedContract` disponibles para listar (creados por fixtures de prueba)
- Serializers y vistas registradas correctamente

**Datos de entrada:**
- GET /established_contracts/list/

---

### Casos (AAA)

- **UT-CON-004-1 — Camino feliz (lista básica):**
  - Arrange: Auth OK con permiso 177; se insertan contratos de prueba.
  - Act: GET /established_contracts/list/
  - Assert: HTTP 200; Content-Type `application/json`; cuerpo con `{'success': True, 'data': [...]}` y cada elemento cumple esquema esperado.
  - Resultado: ✅ PASSED

- **UT-CON-004-2 — Filtro por criterio (search):**
  - Arrange: Auth OK; contratos que cumplen criterio.
  - Act: GET /established_contracts/list/?search=XYZ
  - Assert: 200; solo contratos que coinciden en el resultado.
  - Resultado: ✅ PASSED

- **UT-CON-004-3 — Ordenamiento (ordering):**
  - Arrange: Auth OK; múltiples contratos con fechas distintas.
  - Act: GET /established_contracts/list/?ordering=-start_date
  - Assert: 200; resultados en orden descendente por `start_date`.
  - Resultado: ✅ PASSED

- **UT-CON-004-4 — Filtros combinados:**
  - Arrange: Auth OK; datos parametrizados.
  - Act: GET /established_contracts/list/?status=active&unit=16
  - Assert: 200; solo elementos que cumplen filtros compuestos.
  - Resultado: ✅ PASSED

- **UT-CON-004-5 — Respuesta vacía (sin resultados):**
  - Arrange: Auth OK; no hay contratos que cumplan filtro.
  - Act: GET /established_contracts/list/?search=NO_EXISTE
  - Assert: 200; `data` es lista vacía (`[]`) y `success` es `True`.
  - Resultado: ✅ PASSED

- **UT-CON-004-6 — Schema y tipos de campos:**
  - Arrange: Auth OK; contratos con campos esperados.
  - Act: GET
  - Assert: 200; cada contrato contiene solo los campos del contrato y tipos según contrato (ids numéricos, fechas ISO, strings en campos decimales si aplica).
  - Resultado: ✅ PASSED

- **UT-CON-004-7 — Robustez frente a excepciones internas:**
  - Arrange: Auth OK; simular excepción en repositorio/servicio.
  - Act: GET
  - Assert: Manejo de error consistente (respuesta de error controlada y mensaje claro según implementación).
  - Resultado: ✅ PASSED

- **UT-CON-004-8 — Seguridad: 401 cuando no autenticado:**
  - Arrange: No enviar credenciales / simulate auth None
  - Act: GET
  - Assert: HTTP 401; mensaje de credenciales faltantes.
  - Resultado: ✅ PASSED

- **UT-CON-004-9 — Seguridad: 403 cuando falta permiso 177:**
  - Arrange: Usuario autenticado pero sin el permiso requerido.
  - Act: GET
  - Assert: HTTP 403; mensaje claro de permiso denegado.
  - Resultado: ✅ PASSED

---

## Resumen Ejecutivo

- **Total de Pruebas:** 9
- **Pruebas Exitosas:** 9 ✅
- **Pruebas Fallidas:** 0 ❌
- **Tasa de Éxito:** 100%

- **Fecha Ejecución:** 19/11/2025
- **Ejecutado por:** Suite local dentro del contenedor `web` (ejecución de pytest)
- **Entorno:** Docker container (servicio `web`)
- **Framework:** pytest con Django REST Framework

**Observaciones:**
- Todas las pruebas de la suite UT-CON-004 pasaron. Las comprobaciones de seguridad (401/403) se implementaron con stubs/monkeypatch en tests para permitir pruebas deterministas sin modificar código de producción.
- Se recomienda, si se desea, consolidar el stub de autenticación en `test/conftest.py` como fixture controlable para permitir activar/desactivar la simulación por caso de prueba.

**Estado:** ✅ EXITOSO
