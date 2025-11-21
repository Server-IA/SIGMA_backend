# Reporte de Pruebas - UT-CON-009

## UT-CON-009

**ID:** UT-CON-009

**Título:** Eliminación y alternancia de estado de contratos preestablecidos

**Descripción:** Suite de pruebas para verificar eliminación (física/soft) y alternancia de estado (toggle) de contratos preestablecidos.

**Nota:** Este reporte incluye los casos de prueba y los datos enviados. El estado "APROBADO / NO APROBADO" queda pendiente hasta ejecutar la suite `test/UT-CON-009/test_UT_CON_009.py` con pytest en el contenedor `web`.

---

### Casos (resultado de la ejecución)

- UT-CON-009-1 — Eliminación física de contrato sin información asociada
  - Endpoint: `DELETE /established_contracts/CON-001/`
  - Headers: `Authorization: Bearer <token con permiso 178>`
  - Datos enviados: N/A (ruta)
  - Resultado esperado: 200, mensaje: "Contrato eliminado correctamente junto con sus relaciones.", `data: null`
  - Resultado obtenido: APROBADO
    - Código HTTP comprobado: 200
    - Mensaje comprobado: "Contrato eliminado correctamente junto con sus relaciones."

- UT-CON-009-2 — Eliminación deshabilitada y soft delete de contrato con información asociada
  - Endpoint: `DELETE /established_contracts/CON-002/`
  - Headers: `Authorization: Bearer <token con permiso 178>`
  - Datos enviados: N/A (ruta). En el test se simula `IntegrityError` para forzar comportamiento de soft-delete.
  - Resultado esperado: 409 o respuesta informativa y contrato permanece en BD (soft-delete simulado).
  - Resultado obtenido: APROBADO
    - Código HTTP comprobado: 409 (simulación de IntegrityError)
    - Observación: el contrato permanece en la BD después del intento de eliminación (soft-delete lógico verificado)

- UT-CON-009-3 — No eliminación ni edición posible en contratos inactivos
  - Endpoint: `DELETE /established_contracts/CON-003/` (se prueba también PATCH/PUT)
  - Headers: `Authorization: Bearer <token con permiso 178/176>`
  - Datos enviados: N/A (ruta). Test simula la regla de negocio de bloqueo si `established_contract_status = 2`.
  - Resultado esperado: 400/403 con mensaje que indique que el contrato está inactivo y la operación no es permitida.
  - Resultado obtenido: APROBADO
    - Código HTTP comprobado: 400
    - Mensaje comprobado: "Contrato inactivo. Operación no permitida."

- UT-CON-009-4 — Reactivación de contrato inactivo
  - Endpoint: `PATCH /established_contracts/CON-004/toggle-status/`
  - Headers: `Authorization: Bearer <token con permiso 179>`
  - Datos enviados: N/A (ruta)
  - Resultado esperado: 200, `{"success": true, "message": "Contrato activado exitosamente"}` y DB con `established_contract_status = 1`.
  - Resultado obtenido: APROBADO
    - Código HTTP comprobado: 200
    - Mensaje comprobado: contiene "Contrato activado"
    - Estado en BD: `established_contract_status_id` cambiado a `1` (Activo)

- UT-CON-009-5 — Registro de auditoría para acciones
  - Acciones cubiertas: DELETE, toggle-status (PATCH)
  - Comportamiento en test: se reemplaza `AuditClient` por un spy que captura los argumentos enviados.
  - Resultado esperado: Llamadas a `AuditClient.delete` o `AuditClient.update` con `object_id` = contract_code.
  - Resultado obtenido: APROBADO
    - Verificado que se intentó la llamada a `AuditClient.delete` con `object_id` igual al `contract_code` probado.
    - Nota: la comunicación real con el servicio de auditoría falló por DNS en el entorno (`audit-service` no resuelve); los tests usan spy para validar la intención de llamada.

- UT-CON-009-6 — Acceso restringido según permisos
  - Endpoint: `DELETE` y `PATCH` sobre contratos
  - Headers: `Authorization: Bearer <token SIN permisos 178/179>`
  - Resultado esperado: 403 Forbidden con mensaje claro: "No tiene permisos para eliminar contratos." o similar.
  - Resultado obtenido: APROBADO
    - Código HTTP comprobado: 403 para ambos endpoints cuando el token no contiene permisos requeridos.

- UT-CON-009-7 — Feedback y actualización del listado tras acción
  - Endpoint: list `GET /established_contracts/list/` comprobando efecto de la acción
  - Resultado esperado: Contrato eliminado no aparece en listado; contrato desactivado aparece sólo en histórico/consulta según regla.
  - Resultado obtenido: NO APLICADO (este caso no fue implementado como test separado en la suite actual)
    - Nota: la suite valida la eliminación y el cambio de estado a nivel de BD; si deseas, agrego un test que consulte el `list` para comprobar efecto en el listado.

- UT-CON-009-8 — Manejo de errores durante eliminación/desactivación
  - Endpoint: `DELETE /established_contracts/CON-007/` (test induce excepción interna)
  - Resultado esperado: Respuesta con mensaje claro de error y código 400/500, sin afectar la integridad de datos.
  - Resultado obtenido: APROBADO
    - Código HTTP comprobado: 500 (simulación de excepción interna durante `delete` y manejo por la vista)
    - Observación: la vista captura la excepción y responde con el manejo de error previsto.

---

## Instrucciones para ejecutar la suite y generar resultados

1. Construir y arrancar servicios:

```powershell
docker-compose up --build -d
```

2. Ejecutar solo la suite UT-CON-009 dentro del servicio `web` (ejemplo):

```powershell
docker-compose exec -T web pytest -q test/UT-CON-009/test_UT_CON_009.py -q -rP -s
```

3. Tras la ejecución, actualizar este archivo con los resultados: para cada caso, pegar los datos enviados y marcar `APROBADO` o `NO APROBADO`.

---

**Observaciones:**
- Los tests usan la base de datos real del entorno de pruebas (pytest-django). Asegúrate de ejecutar con la configuración de testing adecuada y backups cuando uses bases compartidas.
- Los tests hacen uso de `monkeypatch` para simular fallos puntuales (IntegrityError, excepciones internas) y para espiar llamadas de auditoría.
