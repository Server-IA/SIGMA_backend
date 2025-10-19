# Reporte de Pruebas Unitarias UT-SOL-008

## UT-SOL-008.1: Finalización Exitosa de Solicitud de Servicio

**ID:** UT-SOL-008.1

**Título:** Verificar finalización exitosa de solicitud en estado "En proceso"

**Descripción:** 
Verificar que el endpoint `/service_requests/{id_request}/complete/` finaliza correctamente una solicitud de servicio que está en estado "En proceso" cuando el usuario tiene permisos válidos y envía observaciones dentro del límite permitido.

**Precondiciones:**
- Usuario autenticado con permiso ID 152 (request.complete_request)
- Solicitud de servicio existe y está en estado "En proceso" (ID 21)
- Cliente asociado a la solicitud existe en la base de datos
- Estados de parametrización configurados (En proceso, Finalizada, Disponible)
- Mocks configurados para AuditClient y requests.post

**Datos de Entrada:**
```json
{
    "completion_cancellation_observations": "Trabajo completado exitosamente según lo programado."
}
```

**Pasos (AAA):**
- **Arrange:** Configurar solicitud con estado "En proceso", usuario autorizado con permisos válidos
- **Act:** Invocar POST `/service_requests/SOL-2025-0020/complete/` con payload válido
- **Assert:** Verificar HTTP 200, success=true, cambio de estado a "Finalizada", fecha y usuario registrados

**Resultado Esperado:**
```json
{
    "success": true,
    "message": "Solicitud finalizada exitosamente. Código: SOL-2025-0020.",
    "id_request": "SOL-2025-0020"
}
```

**Resultado Obtenido:**
```json
{
    "success": true,
    "message": "Solicitud finalizada exitosamente. Código: SOL-2025-0020.",
    "id_request": "SOL-2025-0020"
}
```

**Estado:** ✅ EXITOSA

---

## UT-SOL-008.2: Usuario Sin Permisos para Finalizar

**ID:** UT-SOL-008.2

**Título:** Verificar rechazo de finalización por falta de permisos

**Descripción:**
Verificar que el endpoint deniega la finalización de una solicitud si el usuario no posee el permiso ID 152 requerido para finalizar solicitudes.

**Precondiciones:**
- Usuario autenticado sin permiso ID 152
- Solicitud válida y en estado "En proceso"
- Token JWT configurado con permisos diferentes a 152

**Datos de Entrada:**
```json
{
    "completion_cancellation_observations": "Observaciones de prueba."
}
```

**Pasos (AAA):**
- **Arrange:** Usuario autenticado con token sin permiso 152
- **Act:** POST `/service_requests/SOL-2025-0020/complete/`
- **Assert:** HTTP 403, mensaje de error de permisos

**Resultado Esperado:**
```json
{
    "message": "No tiene permisos para finalizar solicitudes"
}
```

**Resultado Obtenido:**
```json
{
    "message": "No tiene permisos para finalizar solicitudes"
}
```

**Estado:** ✅ EXITOSA

---

## UT-SOL-008.3: Usuario No Autenticado

**ID:** UT-SOL-008.3

**Título:** Verificar rechazo de usuario no autenticado

**Descripción:**
Validar que el endpoint rechaza la solicitud de finalización si no se proporciona token de autenticación válido.

**Precondiciones:**
- No se envía token JWT o sesión válida
- Solicitud existe en estado "En proceso"

**Datos de Entrada:**
```json
{
    "completion_cancellation_observations": "Trabajo completado."
}
```

**Pasos (AAA):**
- **Arrange:** No incluir token JWT en la petición
- **Act:** POST `/service_requests/SOL-2025-0020/complete/`
- **Assert:** HTTP 401, mensaje de usuario no autenticado

**Resultado Esperado:**
```json
{
    "detail": "Authentication credentials were not provided."
}
```

**Resultado Obtenido:**
```json
{
    "detail": "Authentication credentials were not provided."
}
```

**Estado:** ✅ EXITOSA

---

## UT-SOL-008.4: Solicitud Inexistente

**ID:** UT-SOL-008.4

**Título:** Verificar manejo de solicitud inexistente

**Descripción:**
Validar que el endpoint retorna error 404 cuando se intenta finalizar una solicitud que no existe en la base de datos.

**Precondiciones:**
- Usuario autenticado con permiso 152
- ID de solicitud no existe en la base de datos

**Datos de Entrada:**
```json
{
    "completion_cancellation_observations": "Observaciones de prueba."
}
```

**Pasos (AAA):**
- **Arrange:** Usuario autorizado, solicitud inexistente
- **Act:** POST `/service_requests/SOL-2025-0999/complete/`
- **Assert:** HTTP 404, mensaje de no encontrado

**Resultado Esperado:**
```json
{
    "detail": "No ServiceRequest matches the given query."
}
```

**Resultado Obtenido:**
```json
{
    "detail": "No ServiceRequest matches the given query."
}
```

**Estado:** ✅ EXITOSA

---

## UT-SOL-008.5: Campo Vacío o Nulo

**ID:** UT-SOL-008.5

**Título:** Verificar validación de campo obligatorio

**Descripción:**
Verificar que el campo `completion_cancellation_observations` no puede ser nulo o vacío, validando la regla de negocio de observaciones obligatorias.

**Precondiciones:**
- Usuario autenticado con permiso 152
- Solicitud en estado "En proceso"
- Campo de observaciones vacío

**Datos de Entrada:**
```json
{
    "completion_cancellation_observations": ""
}
```

**Pasos (AAA):**
- **Arrange:** Usuario autorizado, campo vacío
- **Act:** POST `/service_requests/SOL-2025-0020/complete/`
- **Assert:** HTTP 400, error de validación de campo en blanco

**Resultado Esperado:**
```json
{
    "success": false,
    "message": "Error en la validación de datos",
    "errors": {
        "completion_cancellation_observations": ["This field may not be blank."]
    }
}
```

**Resultado Obtenido:**
```json
{
    "success": false,
    "message": "Error en la validación de datos",
    "errors": {
        "completion_cancellation_observations": ["This field may not be blank."]
    }
}
```

**Estado:** ✅ EXITOSA

---

## UT-SOL-008.6: Excede Longitud Máxima

**ID:** UT-SOL-008.6

**Título:** Verificar validación de longitud máxima de observaciones

**Descripción:**
Validar que el campo `completion_cancellation_observations` no supere el límite de 500 caracteres establecido en el modelo de datos.

**Precondiciones:**
- Usuario autenticado con permiso 152
- Solicitud en estado "En proceso"
- Campo con longitud superior a 500 caracteres

**Datos de Entrada:**
```json
{
    "completion_cancellation_observations": "A".repeat(501)
}
```

**Pasos (AAA):**
- **Arrange:** Campo con longitud >500 caracteres
- **Act:** POST `/service_requests/SOL-2025-0020/complete/`
- **Assert:** HTTP 400, error de validación de longitud máxima

**Resultado Esperado:**
```json
{
    "success": false,
    "message": "Error en la validación de datos",
    "errors": {
        "completion_cancellation_observations": ["Ensure this field has no more than 500 characters."]
    }
}
```

**Resultado Obtenido:**
```json
{
    "success": false,
    "message": "Error en la validación de datos",
    "errors": {
        "completion_cancellation_observations": ["Ensure this field has no more than 500 characters."]
    }
}
```

**Estado:** ✅ EXITOSA

---

## UT-SOL-008.7: Solicitud Cancelada

**ID:** UT-SOL-008.7

**Título:** Verificar rechazo de finalización de solicitud cancelada

**Descripción:**
Validar que el endpoint no permite finalizar solicitudes que están en estado "Cancelada", aplicando la regla de negocio que impide modificar solicitudes canceladas.

**Precondiciones:**
- Usuario autenticado con permiso 152
- Solicitud en estado "Cancelada" (ID 23)

**Datos de Entrada:**
```json
{
    "completion_cancellation_observations": "Intento de finalizar solicitud cancelada."
}
```

**Pasos (AAA):**
- **Arrange:** Solicitud con estado "Cancelada"
- **Act:** POST `/service_requests/SOL-2025-0015/complete/`
- **Assert:** HTTP 400, mensaje de solicitud cancelada

**Resultado Esperado:**
```json
{
    "success": false,
    "message": "Error en la validación de datos",
    "errors": {
        "non_field_errors": ["No se puede finalizar una solicitud que está cancelada."]
    }
}
```

**Resultado Obtenido:**
```json
{
    "success": false,
    "message": "Error en la validación de datos",
    "errors": {
        "non_field_errors": ["No se puede finalizar una solicitud que está cancelada."]
    }
}
```

**Estado:** ✅ EXITOSA

---

## UT-SOL-008.8: Solicitud No en Proceso

**ID:** UT-SOL-008.8

**Título:** Verificar rechazo de finalización de solicitud no en proceso

**Descripción:**
Validar que solo pueden finalizarse solicitudes que están específicamente en estado "En proceso", rechazando solicitudes en otros estados como "Pendiente".

**Precondiciones:**
- Usuario autenticado con permiso 152
- Solicitud en estado "Pendiente" (ID 20)

**Datos de Entrada:**
```json
{
    "completion_cancellation_observations": "Intento de finalizar solicitud pendiente."
}
```

**Pasos (AAA):**
- **Arrange:** Solicitud con estado diferente de "En proceso"
- **Act:** POST `/service_requests/SOL-2025-0018/complete/`
- **Assert:** HTTP 400, mensaje de estado no permitido

**Resultado Esperado:**
```json
{
    "success": false,
    "message": "Error en la validación de datos",
    "errors": {
        "non_field_errors": ["Solo se pueden finalizar solicitudes que están en proceso (estado aceptado)."]
    }
}
```

**Resultado Obtenido:**
```json
{
    "success": false,
    "message": "Error en la validación de datos",
    "errors": {
        "non_field_errors": ["Solo se pueden finalizar solicitudes que están en proceso (estado aceptado)."]
    }
}
```

**Estado:** ✅ EXITOSA

---

## Resumen Ejecutivo

**Fecha Ejecución:** 19/10/2025  
**Ejecutado por:** Juan Camilo  
**Total de Pruebas:** 8  
**Pruebas Exitosas:** 8 (100%)  
**Pruebas Fallidas:** 0  
**Tiempo de Ejecución:** 36.08 segundos  

### Funcionalidades Validadas

✅ **Autenticación y Autorización**
- Validación de tokens JWT
- Verificación de permisos específicos (ID 152)
- Manejo de usuarios no autenticados

✅ **Validación de Datos**
- Campos obligatorios
- Longitud máxima de caracteres (500)
- Formato y estructura de datos

✅ **Reglas de Negocio**
- Solo solicitudes "En proceso" pueden finalizarse
- Solicitudes canceladas no pueden modificarse
- Estados de maquinaria se actualizan correctamente

✅ **Manejo de Errores**
- Respuestas HTTP apropiadas (200, 400, 401, 403, 404)
- Mensajes de error descriptivos
- Validación de existencia de recursos

### Conclusiones

El endpoint `/service_requests/{id_request}/complete/` cumple con todos los requisitos funcionales y de seguridad especificados. Las pruebas unitarias confirman que:

1. **La funcionalidad principal funciona correctamente** - Las solicitudes en proceso se finalizan exitosamente
2. **La seguridad está implementada** - Solo usuarios autorizados pueden finalizar solicitudes
3. **Las validaciones son robustas** - Se previenen casos de error y datos inválidos
4. **El manejo de errores es apropiado** - Respuestas claras y códigos HTTP correctos

**Estado General:** ✅ **TODAS LAS PRUEBAS EXITOSAS**
