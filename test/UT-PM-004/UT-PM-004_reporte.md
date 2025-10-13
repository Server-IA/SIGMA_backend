# Caso de Prueba Unitario - UT-PM-004

## Información General

| Campo | Valor |
|-------|-------|
| **ID** | UT-PM-004 |
| **Título** | Cancelar Mantenimiento Programado |
| **Descripción** | Prueba unitaria que valida la funcionalidad completa del endpoint de cancelación de mantenimientos programados, cubriendo todos los escenarios posibles incluyendo autenticación JWT, permisos, validaciones de datos y reglas de negocio |


### Precondiciones
- Base de datos de prueba configurada con esquema completo
- Mock configurado para simulación de autenticación JWT (check_permission)
- Categorías de estados creadas: Mantenimiento (id=1)
- Estados de mantenimiento disponibles: Programado (13), Cancelado (14), Finalizado (15)
- Usuarios de prueba: con permiso (id=1) y sin permiso (id=2)
- Maquinaria de prueba con todos los campos requeridos
- Mantenimiento programado en estado inicial "Programado"
- Cliente API configurado para requests HTTP

### Datos de Entrada

```json
{
  "usuarios_prueba": {
    "usuario_con_permisos": {
      "id": 1,
      "permissions": [121],
      "description": "Usuario con permiso JWT 121 para cancelación"
    },
    "usuario_sin_permisos": {
      "id": 2,
      "permissions": [],
      "description": "Usuario sin permiso JWT 121"
    }
  },
  "mantenimiento_prueba": {
    "estado_inicial": {
      "id": 13,
      "name": "Programado"
    },
    "maquinaria_asociada": "válida con todos los campos requeridos",
    "fecha_programada": "tomorrow",
    "tecnico_asignado": 1
  },
  "escenarios_entrada": {
    "justificacion_valida": "Cancelación por reprogramación de cliente",
    "justificacion_vacia": "",
    "justificacion_limite": "texto_300_caracteres_exactos",
    "sin_justificacion": null,
    "id_inexistente": 99999,
    "estados_test": {
      "programado": 13,
      "cancelado": 14,
      "finalizado": 15
    }
  },
  "endpoints": {
    "cancel_url": "/api/maintenance/scheduling/{id}/cancel/",
    "method": "POST",
    "auth_required": true,
    "permission_required": 121
  }
}
```

## Pasos (AAA)

### Arrange: Preparar datos y entorno
- Configurar base de datos de prueba con transacciones
- Crear categoría de estados "Mantenimiento"
- Crear estados: Programado, Cancelado, Finalizado con relaciones FK correctas
- Crear usuarios de prueba con diferentes niveles de permisos
- Crear maquinaria con todos los campos requeridos (nombre, tipo, modelo, etc.)
- Crear mantenimiento programado en estado inicial válido
- Configurar mock para check_permission del viewset
- Inicializar cliente API de Django REST Framework

### Act: Ejecución de pruebas
1. **Caso Exitoso (200)**: Enviar POST con usuario autenticado, permiso válido y justificación correcta
2. **Usuario No Autenticado (401)**: Enviar POST sin autenticación
3. **Sin Permisos (403)**: Enviar POST con usuario sin permiso JWT 121
4. **Recurso No Encontrado (404)**: Enviar POST a endpoint con ID de mantenimiento inexistente
5. **Justificación Inválida (422)**: Enviar POST con justificación vacía
6. **Campo Faltante (422)**: Enviar POST sin campo justification
7. **Ya Cancelado (422)**: Cambiar estado a cancelado y intentar cancelar nuevamente
8. **Estado Finalizado (422)**: Cambiar estado a finalizado e intentar cancelar
9. **Verificación de Cambio de Estado**: Validar que el estado cambia correctamente de Programado a Cancelado
10. **Límite de Caracteres**: Probar con justificación de exactamente 300 caracteres

### Assert: Validaciones
* Verificar código de respuesta HTTP correcto para cada escenario
* Validar estructura de respuesta JSON con campos success, message, details
* Confirmar mensajes de error específicos y descriptivos
* Verificar que el estado del mantenimiento cambia de 13 (Programado) a 14 (Cancelado) en caso exitoso
* Validar que la justificación se almacena correctamente en la base de datos
* Confirmar que no se pueden cancelar mantenimientos ya cancelados o finalizados
* Verificar que se requiere autenticación JWT válida
* Validar que se requiere permiso específico ID 121
* Confirmar que las validaciones de datos funcionan correctamente
* Verificar limpieza de mocks después de cada test

## Resultado Esperado
- **Test exitoso (200)**: Mantenimiento cancelado con éxito, estado actualizado, justificación guardada
- **Test 401**: Error de autenticación con mensaje descriptivo
- **Test 403**: Error de permisos con mensaje indicando falta de autorización
- **Test 404**: Error de recurso no encontrado
- **Test 422 (datos inválidos)**: Errores de validación con detalles específicos
- **Test 422 (estados)**: Prevención de cancelación en estados no permitidos
- **Verificación de estado**: Cambio correcto de Programado (13) a Cancelado (14)
- **Límites**: Aceptación de justificaciones de 300 caracteres exactos

## Resultado Obtenido
Todos los 10 casos de prueba ejecutados exitosamente:
- test_cancel_success_200: OK
- test_cancel_unauthenticated_401: OK  
- test_cancel_no_permission_403: OK
- test_cancel_not_found_404: OK
- test_cancel_invalid_justification_422: OK
- test_cancel_missing_justification_422: OK
- test_cancel_already_cancelled_422: OK
- test_cancel_finalized_422: OK
- test_cancel_state_change_verification: OK
- test_cancel_valid_justification_length: OK

Simulación JWT: Funcional mediante unittest.mock.patch
Tiempo de ejecución: ~0.2 segundos

## Estado
**Aprobado**

## Fecha Ejecución
30/09/2025 05:44 AM

Alejandro Saenz Calderon
---


