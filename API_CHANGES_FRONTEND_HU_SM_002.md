# API Changes for Frontend - HU-SM-002

## Resumen
Este documento detalla los cambios en las respuestas de los endpoints de API que deben ser considerados por el equipo de frontend.

---

## Endpoint: `GET /maintenance/maintenance-request/list`

### Cambios en la Respuesta

#### Antes
```json
{
  "success": true,
  "message": "...",
  "data": [
    {
      "id": "SOL-2025-0001",
      "machinery_serial": "MAQ-001",
      "machinery_name": "Excavadora CAT",
      "requester_id": 123,
      "maintenance_type_name": "Preventivo",
      "fecha_solicitud": "2025-01-15",  // ⚠️ Solo fecha
      "priority_name": "Alta",
      "status_name": "Pendiente",
      "status_id": 10
    }
  ]
}
```

#### Después ✅
```json
{
  "success": true,
  "message": "...",
  "data": [
    {
      "id": "SOL-2025-0001",
      "machinery_serial": "MAQ-001",
      "machinery_name": "Excavadora CAT",
      "requester_id": 123,  // O "Automatico" si es automática
      "maintenance_type_name": "Preventivo",
      "fecha_solicitud": "2025-01-15T10:30:45.123456-05:00",  // ✅ DateTime completo
      "priority_name": "Alta",
      "status_name": "Pendiente",
      "status_id": 10,
      "is_automatic": true  // ✅ NUEVO CAMPO
    }
  ]
}
```

### Recomendaciones Frontend

1. **Mostrar badge/indicador** si `is_automatic === true`
   ```jsx
   {item.is_automatic && <Badge color="blue">Automática</Badge>}
   ```

2. **Formatear fecha completa**
   ```javascript
   const formatDateTime = (isoString) => {
     return new Date(isoString).toLocaleString('es-CO', {
       year: 'numeric',
       month: '2-digit',
       day: '2-digit',
       hour: '2-digit',
       minute: '2-digit'
     });
   };
   ```

3. **Deshabilitar botón "Rechazar"** para solicitudes automáticas
   ```jsx
   <Button 
     disabled={item.is_automatic}
     title={item.is_automatic ? "Las solicitudes automáticas no pueden ser rechazadas" : ""}
   >
     Rechazar
   </Button>
   ```

---

## Endpoint: `GET /maintenance/maintenance-request/{id}/detail`

### Cambios en la Respuesta

#### Antes
```json
{
  "success": true,
  "message": "...",
  "data": {
    "id": "SOL-2025-0001",
    "machinery_serial": "MAQ-001",
    "machinery_name": "Excavadora CAT",
    "maintenance_type_name": "Preventivo",
    "description": "Mantenimiento programado",
    "priority_name": "Alta",
    "status_id": 10,
    "status_name": "Pendiente",
    "fecha_solicitud": "2025-01-15T10:30:45.123456-05:00",
    "response_date": null,
    "scheduled_at": null,
    "assigned_technician_id": null,
    "justification": null,
    "id_response_user": null
  }
}
```

#### Después ✅
```json
{
  "success": true,
  "message": "...",
  "data": {
    "id": "SOL-2025-0001",
    "machinery_serial": "MAQ-001",
    "machinery_name": "Excavadora CAT",
    "maintenance_type_name": "Preventivo",
    "description": "[AUTO] Revisión por inactividad | Inactividad ≥ 14 días",
    "priority_name": "Alta",
    "status_id": 10,
    "status_name": "Pendiente",
    "fecha_solicitud": "2025-01-15T10:30:45.123456-05:00",
    "detected_at": "2025-01-15T10:30:45.123456-05:00",  // ✅ NUEVO CAMPO
    "is_automatic": true,  // ✅ NUEVO CAMPO
    "response_date": null,
    "scheduled_at": null,
    "assigned_technician_id": null,
    "justification": "AUTO",  // Para solicitudes automáticas
    "id_response_user": null
  }
}
```

### Recomendaciones Frontend

1. **Mostrar alerta informativa** para solicitudes automáticas
   ```jsx
   {data.is_automatic && (
     <Alert type="info">
       Esta solicitud fue generada automáticamente por el sistema.
       No puede ser modificada ni eliminada.
     </Alert>
   )}
   ```

2. **Mostrar timestamp de detección**
   ```jsx
   <div>
     <label>Fecha de Registro:</label>
     <span>{formatDateTime(data.fecha_solicitud)}</span>
   </div>
   <div>
     <label>Fecha de Detección:</label>
     <span>{formatDateTime(data.detected_at)}</span>
   </div>
   ```

3. **Ocultar/deshabilitar acciones no permitidas**
   ```jsx
   {!data.is_automatic && (
     <>
       <Button onClick={handleEdit}>Editar</Button>
       <Button onClick={handleDelete}>Eliminar</Button>
     </>
   )}
   ```

---

## Endpoint: `POST /maintenance/maintenance-request/{id}/reject`

### Nuevo Comportamiento

#### Solicitud Manual (funciona como antes)
```http
POST /maintenance/maintenance-request/SOL-2025-0001/reject
{
  "justification": "No es necesario en este momento"
}
```

**Respuesta:** 200 OK
```json
{
  "success": true,
  "message": "Solicitud de mantenimiento rechazada exitosamente",
  "data": {
    "id_maintenance_request": "SOL-2025-0001"
  }
}
```

#### Solicitud Automática ⚠️ NUEVO COMPORTAMIENTO
```http
POST /maintenance/maintenance-request/SOL-2025-0002/reject
{
  "justification": "No es necesario"
}
```

**Respuesta:** 403 FORBIDDEN ✅
```json
{
  "success": false,
  "message": "No se puede rechazar una solicitud automática. Las solicitudes automáticas son generadas por el sistema y no pueden ser modificadas ni eliminadas."
}
```

### Recomendaciones Frontend

1. **Validación preventiva antes de enviar**
   ```javascript
   const handleReject = async (request) => {
     if (request.is_automatic) {
       showError("Las solicitudes automáticas no pueden ser rechazadas");
       return;
     }
     // Continuar con el rechazo
   };
   ```

2. **Manejo del error 403**
   ```javascript
   try {
     await rejectRequest(id, justification);
   } catch (error) {
     if (error.status === 403) {
       showError("Esta solicitud automática no puede ser rechazada");
     } else {
       showError("Error al rechazar la solicitud");
     }
   }
   ```

---

## Endpoint: `POST /maintenance/maintenance-request/create`

### ⚠️ Sin Cambios Funcionales

El endpoint de creación manual de solicitudes **NO se ve afectado**. Las solicitudes creadas manualmente seguirán funcionando igual:

```json
{
  "id_machinery": 1,
  "maintenance_type": 14,
  "description": "Revisión de rutina",
  "priority": 16,
  "detected_at": "2025-01-15"  // Puede ser Date o DateTime
}
```

**Nota:** El campo `is_automatic` se establece automáticamente en `false` para solicitudes manuales.

---

## Nuevos Datos Disponibles

### Campo: `is_automatic`
- **Tipo:** `boolean`
- **Valores:** `true` | `false`
- **Ubicación:** Todos los endpoints de MaintenanceRequest
- **Propósito:** Identificar solicitudes generadas automáticamente

### Campo: `detected_at`
- **Tipo:** `string` (ISO 8601 DateTime)
- **Formato:** `"2025-01-15T10:30:45.123456-05:00"`
- **Ubicación:** Endpoint de detalle
- **Propósito:** Timestamp exacto de detección del problema

### Campo: `fecha_solicitud`
- **Antes:** Date (`"2025-01-15"`)
- **Ahora:** DateTime (`"2025-01-15T10:30:45.123456-05:00"`)
- **Ubicación:** Todos los endpoints
- **Compatibilidad:** ⚠️ Verificar parseo de fechas

---

## Ejemplos de Código

### React/JavaScript

```javascript
// Componente de lista
const RequestItem = ({ request }) => {
  return (
    <div className="request-item">
      <div className="request-header">
        <h3>{request.id}</h3>
        {request.is_automatic && (
          <Badge color="blue" icon={<AutoIcon />}>
            Automática
          </Badge>
        )}
      </div>
      
      <div className="request-details">
        <p>Maquinaria: {request.machinery_name}</p>
        <p>Fecha: {formatDateTime(request.fecha_solicitud)}</p>
        <p>Estado: {request.status_name}</p>
      </div>
      
      <div className="request-actions">
        <Button onClick={() => viewDetail(request.id)}>
          Ver Detalle
        </Button>
        
        {!request.is_automatic && (
          <Button 
            danger 
            onClick={() => rejectRequest(request.id)}
          >
            Rechazar
          </Button>
        )}
        
        {request.status_id === 10 && (
          <Button primary onClick={() => scheduleRequest(request.id)}>
            Programar
          </Button>
        )}
      </div>
    </div>
  );
};

// Utilidad para formatear fechas
const formatDateTime = (isoString) => {
  const date = new Date(isoString);
  return date.toLocaleString('es-CO', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
};

// Validación antes de rechazar
const rejectRequest = async (id, justification) => {
  const request = await fetchRequestDetail(id);
  
  if (request.is_automatic) {
    throw new Error("Las solicitudes automáticas no pueden ser rechazadas");
  }
  
  return await api.post(`/maintenance/maintenance-request/${id}/reject`, {
    justification
  });
};
```

---

## Checklist de Actualización Frontend

- [ ] Actualizar tipos/interfaces para incluir `is_automatic: boolean`
- [ ] Actualizar tipos para `fecha_solicitud` y `detected_at` como DateTime
- [ ] Agregar componente Badge/Indicator para solicitudes automáticas
- [ ] Actualizar función de formateo de fechas para manejar DateTime
- [ ] Deshabilitar botón "Rechazar" para solicitudes automáticas
- [ ] Agregar validación preventiva antes de intentar rechazar
- [ ] Manejar error 403 al intentar rechazar solicitud automática
- [ ] Agregar mensaje informativo en detalle de solicitudes automáticas
- [ ] Actualizar tests unitarios
- [ ] Actualizar tests E2E
- [ ] Documentar cambios en guía de usuario

---

## Compatibilidad hacia Atrás

### ✅ Compatible
- Campo `is_automatic` tiene valor por defecto `false`
- Endpoints existentes NO se rompen
- Solicitudes antiguas funcionan sin cambios

### ⚠️ Requiere Atención
- `fecha_solicitud` ahora retorna DateTime en lugar de Date
  - **Acción:** Actualizar parseo de fechas
  - **Ejemplo:** `new Date("2025-01-15T10:30:45...")` en lugar de `new Date("2025-01-15")`

### ❌ Cambio de Comportamiento
- Intentar rechazar solicitud automática ahora retorna 403
  - **Acción:** Agregar validación o manejo de error

---

## Preguntas Frecuentes

**P: ¿Puedo editar una solicitud automática?**  
R: No. Las solicitudes automáticas no pueden ser editadas, rechazadas ni eliminadas. Solo pueden ser programadas.

**P: ¿Cómo identifico una solicitud automática?**  
R: Verifica el campo `is_automatic === true` o busca el prefijo `[AUTO]` en la descripción.

**P: ¿Las solicitudes manuales se ven afectadas?**  
R: No. Las solicitudes creadas manualmente funcionan exactamente igual que antes.

**P: ¿Necesito migrar datos existentes?**  
R: No. Las solicitudes existentes automáticamente tienen `is_automatic = false`.

**P: ¿Qué pasa si mi código no maneja el nuevo campo?**  
R: El sistema funcionará, pero no mostrarás el indicador visual ni las restricciones apropiadas.

---

## Soporte

Para dudas o problemas, contactar:
- **Backend Team**: DevJFelipe
- **Documentación**: IMPLEMENTATION_HU_SM_002.md
- **API Testing**: Usar Postman collection actualizada

---

**Última actualización:** 2025-01-15  
**Versión API:** 2.0 (HU-SM-002)
