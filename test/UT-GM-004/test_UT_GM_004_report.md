# Reporte HU-GM-004 (DELETE /maintenance/{id_maintenance}/)

| ID | Título | HTTP | Estado | Payload | Respuesta |
| --- | --- | --- | --- | --- | --- |
| UT-GM-001 | Verificar eliminación exitosa de mantenimiento sin asociaciones | 200 | APROBADO | `N/A` | `{"success": true, "message": "Mantenimiento eliminado correctamente.", "data": null}` |
| UT-GM-002 | Verificar inactivación de mantenimiento con asociaciones activas | 409 | APROBADO | `N/A` | `{"success": false, "message": "No se puede eliminar.", "errors": {"detail": ["Existen referencias a este mantenimiento."]}}` |
| UT-GM-003 | Verificar rechazo por permisos insuficientes (403 Forbidden) | 403 | APROBADO | `N/A` | `{"detail": "Forbidden"}` |
| UT-GM-004 | Verificar manejo de recurso inexistente (404 Not Found) | 404 | APROBADO | `{"id_maintenance": 999999}` | `{"success": false, "message": "Recurso no encontrado.", "errors": {"id": ["No existe el mantenimiento solicitado."]}}` |
| UT-GM-005 | Verificar registro de auditoría en eliminación exitosa | 200 | APROBADO | `N/A` | `{"success": true, "message": "Mantenimiento eliminado correctamente.", "data": null}` |
| UT-GM-006 | Verificar registro de auditoría en inactivación | 409 | APROBADO | `N/A` | `{"success": false, "message": "No se puede eliminar.", "errors": {"detail": ["Existen referencias a este mantenimiento."]}}` |
| UT-GM-007 | Verificar idempotencia del método DELETE | 1st:200 2nd:404 | APROBADO | `N/A` | `{"first": {"success": true, "message": "Mantenimiento eliminado correctamente.", "data": null}, "second": {"success": false, "message": "Recurso no encontrado.", "errors": {"id": ["No existe el mantenimiento solicitado."]}}}` |
| UT-GM-008 | Verificar ocultación en formularios tras inactivación | 200 | APROBADO | `N/A` | `{"in_active_list": false, "count": 3}` |
| UT-GM-009 | Verificar validación de asociaciones antes de eliminación | no_assoc:200 with_assoc:409 | APROBADO | `N/A` | `{"no_assoc": {"success": true, "message": "Mantenimiento eliminado correctamente.", "data": null}, "with_assoc": {"success": false, "message": "No se puede eliminar.", "errors": {"detail": ["Existen referencias a este mantenimiento."]}}}` |
| UT-GM-010 | Verificar manejo de errores de base de datos | 409 | APROBADO | `{"maintenance_id": 28}` | `{"success": false, "message": "No se puede eliminar.", "errors": {"detail": ["Existen referencias a este mantenimiento."]}}` |
