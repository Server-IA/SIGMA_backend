## Título

UT-SOL-010 — Descarga de factura en formato PDF (endpoint: /invoices/{id}/download_pdf/)

## Descripción

Pruebas unitarias e integración ligera que validan la descarga de la factura en PDF, verificando control de permisos (permiso id 161), estados válidos de la factura, manejo de errores (factura no encontrada, PDF no disponible, errores de almacenamiento) y registro de auditoría (AuditClient.create).

## Precondiciones

- Entorno de pruebas Django disponible (tests ejecutados dentro del contenedor `web` del proyecto).
- Las variables de entorno externas (AUDIT_URL, AUDIT_TOKEN, etc.) pueden estar ausentes; los tests mockean el cliente de auditoría.
- No se realizan cambios en el código de producción; sólo se crean mocks y fixtures en los tests.

## Datos de Entrada

- JWT (claims usados en tests - ejemplo):

```json
{
  "id": 1000,
  "email": "test@example.com",
  "name": "Tester",
  "rol": [{ "permisos": [{ "id": 161 }] }],
  "iat": 1698740000,
  "exp": 1698741800
}
```

- Modelo Invoice (ejemplo usado en mocks):

```json
{
  "id_invoice": 7,
  "status_id": 26,               # VALIDADA
  "invoice_pdf_url": "https://storage.example/f.pdf",
  "reference_code": "REF123",
  "cufe": null
}
```

## Pasos (AAA)

- Arrange:
  - Crear un usuario simulado con el permiso 161 (request.download_invoice) en el payload JWT.
  - Preparar un objeto Invoice simulado (o guardar uno real en la DB para el test marcados con @pytest.mark.django_db).
  - Mockear `requests.get` para devolver contenido PDF simulado (bytes que comienzan con %PDF-).
  - Mockear `AuditClient` con un `DummyAuditClient` instalado por la fixture `audit_clients` para capturar llamadas de auditoría.

- Act:
  - Llamar a la función de vista `download_invoice_pdf(request, id_invoice)` o realizar una petición GET a `/invoices/{id}/download_pdf/` con `APIClient` y cabecera Authorization: Bearer <token>.

- Assert:
  - Verificar que la respuesta tenga `status_code == 200` para el caso exitoso.
  - Verificar encabezados: `Content-Type: application/pdf`, `Content-Disposition` contenga `factura_{reference_code}.pdf`, y `Content-Length` coincida con el tamaño real de los bytes PDF.
  - Verificar que `AuditClient.create(...)` haya sido invocado con `permission_id == 161` y `object_id == str(id_invoice)`.
  - Casos de error adicionales y sus expectativas:
    - Sin permiso -> 403 y mensaje de error adecuado.
    - Factura no encontrada -> 404 y mensaje.
    - Factura en estado no listo -> 400.
    - Error al descargar desde almacenamiento (requests.RequestException) -> 502.
    - No hay PDF disponible -> 404.
    - PDF vacío -> 500 y no crear auditoría.

## Resultado Esperado

- Para el caso feliz: la factura se devuelve como PDF con los encabezados correctos y se registra un evento de auditoría con `permission_id` = 161.
- Para cada caso de error: el endpoint responde con el código HTTP y mensaje definidos en la vista (`403`, `404`, `400`, `502`, `500`), y la auditoría sólo se crea en la ruta exitosa.

## Resultado Obtenido

- Al ejecutar los tests en el contenedor `web` del proyecto:
  - Los tests unitarios y la prueba de integración ligera cubriendo los escenarios listados se ejecutaron con éxito en el entorno de pruebas.
  - Las rutas mockeadas devolvieron el contenido esperado; las comprobaciones de encabezados y el registro de auditoría fueron validados por la fixture `audit_clients`.

## Estado / Fecha / Ejecutor

- Aprobado
- 2025-10-31 12:10 
- Alejandro S.


