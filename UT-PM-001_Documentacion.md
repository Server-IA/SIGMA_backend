# Caso de Prueba Unitario - UT-PM-001

|-------|-------|
| **ID** | UT-PM-001 |
| **Título** | Programar Mantenimiento Manual |
| **Descripción** | Prueba unitaria que valida la creación de mantenimientos programados sin solicitud previa, cubriendo los criterios de aceptación y reglas de negocio principales. |

### Precondiciones
- Base de datos de prueba con maquinaria activa
- Técnicos activos disponibles
- Tipos de mantenimiento parametrizados en categoría id=12
- Usuario autenticado con permiso 117 (maintenance_scheduling.create)
- Mock configurado para simulación de permisos y disponibilidad de técnicos

### Datos de Entrada

```json
{
  "id_machinery": 2,
  "scheduled_at": "2025-10-01T14:30:00Z",
  "details": "Cambio de filtros y revisión de frenos",
  "assigned_technician": 7,
  "maintenance_type": 35
}
```

## Pasos (AAA)

### Arrange: Preparar datos y entorno
- Crear maquinaria activa en base de datos
- Crear técnicos activos y parametrizar disponibilidad
- Crear tipos de mantenimiento en categoría id=12
- Configurar usuario autenticado con permiso 117
- Configurar mocks para disponibilidad de técnicos y permisos
- Inicializar cliente API de Django REST Framework

### Act: Ejecución de pruebas
1. **Creación exitosa (201)**: Enviar POST con datos válidos y usuario con permiso
2. **Fecha pasada (422)**: Enviar POST con fecha en el pasado
3. **Técnico no disponible (422)**: Enviar POST con técnico en conflicto de agenda
4. **Tipo de mantenimiento inválido (422)**: Enviar POST con tipo fuera de categoría id=12
5. **Sin permisos (403)**: Enviar POST con usuario sin permiso 117

### Assert: Validaciones
* Verificar código de respuesta HTTP correcto para cada escenario
* Validar estructura de respuesta JSON con campos success, message, data o detalles de error
* Confirmar generación de consecutivo único anual (id_consecutive)
* Verificar que el mantenimiento se crea con estado Programado (id=13)
* Validar que se envía notificación al técnico asignado (mock)
* Confirmar que el mantenimiento aparece en el historial y lista de programados
* Validar mensajes de error específicos para cada caso

## Resultado Esperado
- **Creación exitosa (201)**: Mantenimiento creado, consecutivo generado, estado Programado, notificación enviada
- **Fecha pasada (422)**: Error de validación en campo scheduled_at
- **Técnico no disponible (422)**: Error de validación por conflicto de agenda
- **Tipo de mantenimiento inválido (422)**: Error de validación en campo maintenance_type
- **Sin permisos (403)**: Error de autorización

## Estado
**Aprobado**

## Fecha Ejecución
01/10/2025

Alejandro Saenz C
---
