# Reporte UT-GM-004

Tabla de resultados:

| ID | Título | HTTP | Aprobado | Datos | Respuesta |
| --- | --- | --- | --- | --- | --- |
| UT-GM-004 | Manejo de recurso inexistente | 404 | APROBADO | `{"id_maintenance": 999999}` | `{"success": false, "message": "Recurso no encontrado.", "errors": {"id": ["No existe el mantenimiento solicitado."]}}` |
| UT-GM-007 | Idempotencia del método DELETE | 1st: 200, 2nd: 404 | APROBADO | `N/A` | `{"first": {"success": true, "message": "Mantenimiento eliminado correctamente.", "data": null}, "second": {"success": false, "message": "Recurso no encontrado.", "errors": {"id": ["No existe el mantenimiento solicitado."]}}}` |
