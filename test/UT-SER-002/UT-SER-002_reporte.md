# Reporte de Pruebas UT-SER-002

- Ejecutado por: Nicolas Urrutia
- Fecha de ejecución: 2025-10-14
- Entorno: Docker (contenedor: machpay_backend), Django 5.2.4, DRF 3.16.0, Python 3.11.14
- Endpoints: GET /services/, GET /services/active/

## Resumen

- Total casos: 30
- Pasaron: 30
- Fallaron: 0
- Skipped: 0
- Tiempo total: ~14.34s

## Detalle por caso

| ID | Título | Resultado Esperado | Resultado Obtenido | Estado |
|----|--------|---------------------|--------------------|--------|
| UT-SER-002.1 | Acceso sin token retorna 401 en /services/ | 401 Unauthorized con mensaje de autenticación requerida | 401 con `detail` (DRF) | PASÓ |
| UT-SER-002.2 | Token inválido retorna 401 en /services/ | 401 con mensaje "Token inválido." | 401 con `detail` que indica token inválido | PASÓ |
| UT-SER-002.3 | Token expirado retorna 401 en /services/ | 401 con mensaje de token expirado | 401 con `detail` con expiración/invalidación | PASÓ |
| UT-SER-002.4 | Header Authorization sin prefijo Bearer retorna 401 | 401 Unauthorized | 401 Unauthorized | PASÓ |
| UT-SER-002.5 | Sin permiso 142 retorna 403 en /services/ | 403 con mensaje de prohibición | 403 con `{success:false, message:"No tiene permisos..."}` | PASÓ |
| UT-SER-002.6 | Sin permiso 143 retorna 403 en /services/active/ | 403 | 403 con `{success:false, message:"No tiene permisos..."}` | PASÓ |
| UT-SER-002.7 | Usuario con 142 accede /services/ y falla en /services/active/ | 200 y 403 respectivamente | 200 en /services/ y 403 en /services/active/ | PASÓ |
| UT-SER-002.8 | Listado general 200 y estructura correcta | 200 con estructura y campos esperados | 200 con estructura correcta | PASÓ |
| UT-SER-002.9 | Orden por modification_date descendente | Orden S3, S2, S1 | Orden correcto | PASÓ |
| UT-SER-002.10 | Tipos de datos por campo | Tipos correctos por campo | Tipos correctos | PASÓ |
| UT-SER-002.11 | Coherencia status_id y status_name | Mapeo 1-Activo, 2-Inactivo | Coherente | PASÓ |
| UT-SER-002.12 | Coherencia unidad de medida | unit_id y unit_name consistentes | Consistente | PASÓ |
| UT-SER-002.13 | Rangos válidos de números | base_price ≥ 0; 0 ≤ tax_rate ≤ 100 | Cumple | PASÓ |
| UT-SER-002.14 | is_vat_exempt coherente con impuestos | Exentos con tax_rate=0 | Cumple | PASÓ |
| UT-SER-002.15 | service_type mapeado correctamente | Campos presentes y correctos | Correcto | PASÓ |
| UT-SER-002.16 | Listado vacío retorna arreglo vacío | 200; data=[] | 200; data=[] | PASÓ |
| UT-SER-002.17 | Nuevo servicio aparece inmediatamente y al inicio | Nuevo primero por orden | Primero correctamente | PASÓ |
| UT-SER-002.18 | Edición se refleja en listado | Cambios visibles | Visibles | PASÓ |
| UT-SER-002.19 | Inactivación excluye de /services/active/ | En general inactivo; fuera de activos | Cumple | PASÓ |
| UT-SER-002.20 | Listado de activos solo contiene status_id=1 | Todos activos | Todos activos | PASÓ |
| UT-SER-002.21 | Parámetros desconocidos son ignorados sin error | 200 sin fallas | 200 sin fallas | PASÓ |
| UT-SER-002.22 | Método no permitido retorna 405 | 405 o 403 | 405/403 aceptable (recibido válido) | PASÓ |
| UT-SER-002.23 | Headers de respuesta correctos | Content-Type JSON UTF-8 | Content-Type JSON | PASÓ |
| UT-SER-002.24 | Rendimiento con gran volumen | Dentro de SLO local | ~<3s para 250 items | PASÓ |
| UT-SER-002.25 | Errores 500 manejados sin exponer detalles | 500 controlado | 500 controlado con mensaje | PASÓ |
| UT-SER-002.26 | IDs únicos y sin duplicados | Sin duplicados | Sin duplicados | PASÓ |
| UT-SER-002.27 | Consistencia entre /services/ y /services/active/ | active ⊆ general; status_id=1 | Consistente | PASÓ |
| UT-SER-002.28 | Tolerancia a parámetro Accept y Locale | 200 estable | 200 estable | PASÓ |
| UT-SER-002.29 | Orden estable ante mismos timestamps | Orden determinista | Estable entre llamadas | PASÓ |
| UT-SER-002.30 | Paginación soportada o ignorada sin error | 200 con o sin paginación | 200, parámetros ignorados sin error | PASÓ |

## Observaciones

- La autenticación usa `users.authentication.JWTAuthentication`, que devuelve 401 con `detail` en caso de token ausente/ inválido/ expirado, lo cual se validó.
- Los permisos se validan mediante `ServiceViewSet.check_permission` (IDs 142 y 143). Las respuestas 403 incluyen `{success:false, message}`.
- `ServiceListSerializer` expone el contrato de datos verificado en las pruebas.
- No se requieren migraciones para estos tests, ya que usan la DB activa del contenedor durante la ejecución y crean/eliminan datos de prueba.

## Cómo reproducir (opcional)

```powershell
# Ejecutar toda la suite del caso
docker exec machpay_backend pytest test/UT-SER-002/test_UT_SER_002.py -vv
```
