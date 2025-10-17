# Caso de Prueba Unitario - UT-SER-004
 
## Información General
 
| Campo | Valor |
|-------|-------|
| **ID** | UT-SER-004 |
| **Título** | Eliminar/Desactivar Servicios |
| **Historia de Usuario** | HU-SER-004 |
| **Descripción** | Prueba unitaria que valida la funcionalidad completa de eliminación y desactivación de servicios, cubriendo eliminación física vs lógica, permisos de usuario, integridad referencial y auditoría |
 
### Precondiciones
- Base de datos de prueba configurada con esquema completo
- Mock configurado para simulación de autenticación JWT (check_permission)
- Estados de servicio parametrizados: Activo (id=1), Inactivo (id=2)
- Usuarios de prueba: con permiso delete 144 (id=301), con permiso toggle 145 (id=302), sin permisos (id=303)
- Servicios de prueba: sin referencias (eliminable), con referencias (solo soft delete), inactivo
- Cliente API configurado para requests HTTP DELETE y PATCH
- Sistema de auditoría mockeado para prevenir efectos secundarios
 
### Datos de Entrada
 
```json
{
  "usuarios_prueba": {
    "usuario_con_delete": {
      "id": 301,
      "permissions": [144],
      "description": "Usuario con permiso JWT 144 para eliminación"
    },
    "usuario_con_toggle": {
      "id": 302,
      "permissions": [145],
      "description": "Usuario con permiso JWT 145 para activar/desactivar"
    },
    "usuario_sin_permisos": {
      "id": 303,
      "permissions": [],
      "description": "Usuario sin permisos"
    }
  },
  "servicios_prueba": {
    "servicio_sin_referencias": {
      "id": 1,
      "name": "Servicio Sin Referencias",
      "status": "Activo",
      "can_delete": true
    },
    "servicio_con_referencias": {
      "id": 2,
      "name": "Servicio Con Referencias",
      "status": "Activo",
      "can_delete": false,
      "has_invoices": true
    },
    "servicio_inactivo": {
      "id": 3,
      "name": "Servicio Inactivo",
      "status": "Inactivo",
      "can_toggle": true
    }
  },
  "endpoints": {
    "delete_url": "/services/{id}/",
    "toggle_url": "/services/{id}/toggle-status/",
    "methods": ["DELETE", "PATCH"],
    "permissions": {
      "delete": 144,
      "toggle": 145
    }
  }
}
```
 
## Pasos (AAA)
 
### Arrange: Preparar datos y entorno
- Configurar base de datos de prueba con transacciones aisladas
- Crear estados de servicio: Activo (1) e Inactivo (2) con relaciones FK
- Crear usuarios con diferentes niveles de permisos (delete, toggle, sin permisos)
- Crear servicios de prueba: sin referencias, con referencias simuladas, inactivo
- Configurar mocks para check_permission del ServiceViewSet
- Configurar mock para AuditClient para evitar efectos secundarios
- Inicializar cliente API de Django REST Framework
 
### Act: Ejecución de pruebas
 
#### Eliminación Física (DELETE):
1. **Eliminación Exitosa (200)**: DELETE con permiso 144 y servicio sin referencias
2. **Eliminación Bloqueada (409)**: DELETE con servicio que tiene referencias (IntegrityError)
3. **Servicio Inexistente (404)**: DELETE con ID que no existe
4. **Sin Permisos (403)**: DELETE con usuario sin permiso 144
5. **No Autenticado (401)**: DELETE sin token JWT
 
#### Cambio de Estado (PATCH):
6. **Activar Servicio (200)**: PATCH toggle-status de inactivo a activo
7. **Inactivar Servicio (200)**: PATCH toggle-status de activo a inactivo
8. **Servicio Inexistente (404)**: PATCH toggle-status con ID no existente
9. **Sin Permisos (403)**: PATCH toggle-status sin permiso 145
10. **No Autenticado (401)**: PATCH toggle-status sin autenticación
 
#### Casos Especiales:
11. **Integridad para Facturación**: Verificar que servicios inactivos no están disponibles
12. **Auditoría Delete**: Confirmar registro de auditoría en eliminación
13. **Auditoría Toggle**: Confirmar registro de auditoría en cambio de estado
14. **Actualización en Tiempo Real**: Verificar cambios inmediatos en BD
15. **Manejo de Errores**: Errores genéricos en operaciones de BD
16. **Múltiples Toggle**: Secuencia activo->inactivo->activo
 
### Assert: Validaciones
- Verificar código de respuesta HTTP correcto para cada escenario
- Validar estructura de respuesta JSON con campos success, message, code, data
- Confirmar mensajes específicos y descriptivos en español
- Verificar eliminación física real de BD para servicios sin referencias
- Validar prevención de eliminación con IntegrityError para servicios con referencias
- Confirmar cambios de estado correctos en BD (1↔2)
- Verificar que se requiere autenticación JWT válida
- Validar permisos específicos: 144 (delete) y 145 (toggle)
- Confirmar registro de auditoría mediante mocks
- Verificar que servicios inactivos no están disponibles para procesos operativos
- Validar limpieza de mocks después de cada test
 
## Resultado Esperado
 
### Eliminación (DELETE):
- **200**: Servicio eliminado físicamente, respuesta con success=true, code=200, data=null
- **409**: Eliminación bloqueada por referencias, mensaje indicando soft delete necesario
- **404**: Error de servicio no encontrado con mensaje descriptivo
- **403**: Error de permisos con mensaje de autorización
- **401**: Error de autenticación con mensaje de credenciales
 
### Cambio Estado (PATCH):
- **200**: Estado cambiado exitosamente, mensaje específico (activado/inactivado)
- **404**: Error de servicio no encontrado
- **403**: Error de permisos para toggle
- **401**: Error de autenticación
 
### Validaciones de Negocio:
- **Integridad Referencial**: Servicios con facturas no se eliminan físicamente
- **Soft Delete**: Cambio automático a estado inactivo cuando hay referencias
- **Disponibilidad**: Servicios inactivos no seleccionables en facturación
- **Auditoría**: Registro completo de todas las operaciones
- **Tiempo Real**: Cambios inmediatos reflejados en BD y listados
 
## Resultado Obtenido
Todos los 16 casos de prueba ejecutados exitosamente:
 
**Eliminación Física:**
- test_delete_service_success_200: OK - Eliminación exitosa sin referencias
- test_delete_service_with_relations_409: OK - Bloqueo por IntegrityError
- test_delete_service_not_found_404: OK - Servicio inexistente manejado
- test_delete_service_no_permission_403: OK - Permiso 144 requerido
- test_delete_service_unauthenticated_401: OK - Autenticación requerida
 
**Cambio de Estado:**
- test_toggle_status_activate_success_200: OK - Activación exitosa
- test_toggle_status_deactivate_success_200: OK - Inactivación exitosa  
- test_toggle_status_not_found_404: OK - Servicio inexistente manejado
- test_toggle_status_no_permission_403: OK - Permiso 145 requerido
- test_toggle_status_unauthenticated_401: OK - Autenticación requerida
 
**Integridad y Casos Especiales:**
- test_service_not_available_for_billing_when_inactive: OK - Integridad para facturación
- test_audit_log_on_delete: OK - Auditoría en eliminación
- test_audit_log_on_toggle_status: OK - Auditoría en toggle
- test_realtime_update_in_listing: OK - Actualización en tiempo real
- test_error_handling_on_delete_failure: OK - Manejo de errores
- test_multiple_toggle_operations: OK - Múltiples operaciones toggle
 
Simulación JWT: Funcional mediante unittest.mock.patch
Sistema de auditoría: Mockeado exitosamente sin efectos secundarios
Tiempo de ejecución: ~0.4 segundos
Cobertura: 100% de escenarios HU-MOD-004 cubiertos
 
## Estado
Aprobado
 
## Fecha Ejecución
16/10/2025
 
Alejandro S
---
 

