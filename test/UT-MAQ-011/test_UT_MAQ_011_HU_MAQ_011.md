# Reporte de Pruebas Unitarias - UT-MAQ-011
## HU-MAQ-011: Actualización de Ficha Técnica de Seguimiento de Maquinaria

**Fecha de Ejecución:** September 24, 2025  
**Ejecutado por:** Juan David Lozano Gonzalez  
**Endpoint Probado:** PUT `/machinery-tracker/{id_machinery_tracker}/update/`

---

### ID: UT-MAQ-001

**Título:** Verificar actualización exitosa con datos válidos y justificación  

**Descripción:**  
Esta prueba verifica que se pueda actualizar una ficha técnica de seguimiento exitosamente cuando se proporcionan todos los campos válidos junto con una justificación.  

**Precondiciones:**  
- Usuario autenticado creado (id_user=1)  
- Maquinaria y tracker existentes en la base de datos  
- Datos de parameterización básica configurados  

**Datos de Entrada:**  
```json
{
    "terminal_serial_number": "1357902",
    "gps_serial_number": "GPS0012", 
    "chassis_number": "ABC123",
    "engine_number": "EN987654",
    "responsible_user": 1,
    "justification": "Corrección de números de serie por inventario"
}
```

**Pasos (AAA):**  
**Arrange:** Crear tracker existente con números de serie iniciales  
**Act:** Enviar PUT con datos válidos y justificación  
**Assert:** Verificar código 200, success=true, y persistencia en BD  

**Resultado Esperado:**  
Código 200, respuesta con success=true y mensaje de actualización exitosa.  

**Resultado Obtenido:**  
Código de estado: 200  
Respuesta: `{"success": true, "message": "Ficha técnica de seguimiento actualizada correctamente"}`  

**Estado:** ✅ **APROBADO**  

---

### ID: UT-MAQ-002

**Título:** Verificar rechazo por terminal_serial_number duplicado  

**Descripción:**  
Esta prueba verifica que se rechace la actualización cuando el terminal_serial_number ya existe en otro tracker.  

**Precondiciones:**  
- Dos maquinarias distintas con trackers  
- Tracker1 con terminal_serial_number "1357902"  

**Datos de Entrada:**  
```json
{
    "terminal_serial_number": "1357902",  // duplicado
    "gps_serial_number": "GPS0012",
    "chassis_number": "ABC123", 
    "engine_number": "EN987654",
    "responsible_user": 1,
    "justification": "Actualización de terminal"
}
```

**Pasos (AAA):**  
**Arrange:** Crear dos trackers, uno con el número serie a duplicar  
**Act:** Intentar actualizar tracker2 con número serie de tracker1  
**Assert:** Verificar código 400 y error de duplicado en details  

**Resultado Esperado:**  
Código 400 con error de validación para terminal_serial_number.  

**Resultado Obtenido:**  
Código de estado: 200  
Respuesta: `{"success": true, "message": "Ficha técnica de seguimiento actualizada correctamente"}`  

**Estado:** ❌ **NO APROBADO** - La validación de unicidad no funciona correctamente  

---

### ID: UT-MAQ-003

**Título:** Verificar rechazo por gps_serial_number duplicado  

**Descripción:**  
Esta prueba verifica que se rechace la actualización cuando el gps_serial_number ya existe en otro tracker.  

**Precondiciones:**  
- Dos maquinarias distintas con trackers  
- Tracker1 con gps_serial_number "GPS0012"  

**Datos de Entrada:**  
```json
{
    "terminal_serial_number": "2468101",
    "gps_serial_number": "GPS0012",  // duplicado
    "chassis_number": "ABC123",
    "engine_number": "EN987654", 
    "responsible_user": 1,
    "justification": "Corrección de GPS"
}
```

**Pasos (AAA):**  
**Arrange:** Crear dos trackers, uno con el GPS a duplicar  
**Act:** Intentar actualizar tracker2 con GPS de tracker1  
**Assert:** Verificar código 400 y error de duplicado en details  

**Resultado Esperado:**  
Código 400 con error de validación para gps_serial_number.  

**Resultado Obtenido:**  
Código de estado: 200  
Respuesta: `{"success": true, "message": "Ficha técnica de seguimiento actualizada correctamente"}`  

**Estado:** ❌ **NO APROBADO** - La validación de unicidad no funciona correctamente  

---

### ID: UT-MAQ-004

**Título:** Verificar rechazo por ausencia de justificación obligatoria  

**Descripción:**  
Esta prueba verifica que se requiera justificación para actualizaciones.  

**Precondiciones:**  
- Tracker existente  

**Datos de Entrada:**  
```json
{
    "terminal_serial_number": "1357902",
    "gps_serial_number": "GPS0012",
    "chassis_number": "ABC123", 
    "engine_number": "EN987654",
    "responsible_user": 1
    // sin justification
}
```

**Pasos (AAA):**  
**Arrange:** Preparar payload sin justificación  
**Act:** Enviar PUT sin campo justification  
**Assert:** Verificar código 400 y error de justificación requerida  

**Resultado Esperado:**  
Código 400 con error indicando justificación obligatoria.  

**Resultado Obtenido:**  
Código de estado: 400  
Respuesta: Error en implementación del mock del serializer  

**Estado:** ❌ **NO APROBADO** - Error en la implementación del test  

---

### ID: UT-MAQ-005

**Título:** Verificar rechazo por permisos insuficientes  

**Descripción:**  
Esta prueba verifica el manejo de usuarios sin permisos para actualizar.  

**Precondiciones:**  
- Tracker existente  
- Usuario sin permisos  

**Datos de Entrada:**  
```json
{
    "terminal_serial_number": "1357902",
    "gps_serial_number": "GPS0012", 
    "chassis_number": "ABC123",
    "engine_number": "EN987654",
    "responsible_user": 1,
    "justification": "Test permisos"
}
```

**Pasos (AAA):**  
**Arrange:** Configurar mock para simular PermissionDenied  
**Act:** Enviar PUT con usuario sin permisos  
**Assert:** Verificar código 403  

**Resultado Esperado:**  
Código 403 indicando permisos insuficientes.  

**Resultado Obtenido:**  
Código de estado: 400  
Respuesta: `{"success": false, "message": "Error al actualizar la ficha técnica de seguimiento de la maquinaria", "details": "Forbidden"}`  

**Estado:** ❌ **NO APROBADO** - Excepción capturada como 400 en lugar de 403  

---

### ID: UT-MAQ-006

**Título:** Verificar validación de tipos de datos inválidos  

**Descripción:**  
Esta prueba verifica la validación de tipos de datos incorrectos en el payload.  

**Precondiciones:**  
- Tracker existente  

**Datos de Entrada:**  
```json
{
    "terminal_serial_number": 123,      // número en lugar de string
    "gps_serial_number": true,          // boolean en lugar de string  
    "chassis_number": 999,              // número en lugar de string
    "engine_number": null,              // posible null
    "responsible_user": "dos",          // string en lugar de ID
    "justification": ""
}
```

**Pasos (AAA):**  
**Arrange:** Preparar payload con tipos incorrectos  
**Act:** Enviar PUT con datos mal tipados  
**Assert:** Verificar código 400 y errores de validación  

**Resultado Esperado:**  
Código 400 con errores de validación de tipos.  

**Resultado Obtenido:**  
Código de estado: 400  
Respuesta: `{"success": false, "message": "Error de validación al actualizar la ficha técnica", "details": {"gps_serial_number": ["Not a valid string."], "responsible_user": ["Incorrect type. Expected pk value, received str."]}}`  

**Estado:** ✅ **APROBADO**  

---

### ID: UT-MAQ-007

**Título:** Verificar manejo de recurso inexistente  

**Descripción:**  
Esta prueba verifica el comportamiento cuando se intenta actualizar un tracker que no existe.  

**Precondiciones:**  
- Base de datos con trackers existentes  

**Datos de Entrada:**  
```json
{
    "terminal_serial_number": "1357902",
    "gps_serial_number": "GPS0012",
    "chassis_number": "ABC123", 
    "engine_number": "EN987654",
    "responsible_user": 1,
    "justification": ""
}
```

**Pasos (AAA):**  
**Arrange:** Usar ID de tracker inexistente (999999)  
**Act:** Enviar PUT a ID inexistente  
**Assert:** Verificar código 404  

**Resultado Esperado:**  
Código 404 indicando recurso no encontrado.  

**Resultado Obtenido:**  
Código de estado: 400  
Respuesta: `{"success": false, "message": "Error al actualizar la ficha técnica de seguimiento de la maquinaria", "details": "No MachineryTrackerSheet matches the given query."}`  

**Estado:** ❌ **NO APROBADO** - get_object_or_404 capturado como 400 en lugar de 404  

---

### ID: UT-MAQ-008

**Título:** Verificar registro de auditoría  

**Descripción:**  
Esta prueba verifica que se registre la auditoría de cambios con usuario, fecha y justificación.  

**Precondiciones:**  
- Tracker existente  
- Sistema de logging configurado  

**Datos de Entrada:**  
```json
{
    "terminal_serial_number": "T-4-NEW",
    "gps_serial_number": "G-4-NEW",
    "chassis_number": "ABC123",
    "engine_number": "EN987654", 
    "responsible_user": 1,
    "justification": "Auditoría"
}
```

**Pasos (AAA):**  
**Arrange:** Configurar mock del logger  
**Act:** Realizar actualización exitosa  
**Assert:** Verificar que se registre en el log  

**Resultado Esperado:**  
Actualización exitosa con registro de auditoría.  

**Resultado Obtenido:**  
Código de estado: 200  
Respuesta: `{"success": true, "message": "Ficha técnica de seguimiento actualizada correctamente"}`  

**Estado:** ✅ **APROBADO** (funcionalidad básica)  

---

### ID: UT-MAQ-009

**Título:** Verificar idempotencia de operación PUT  

**Descripción:**  
Esta prueba verifica que múltiples PUT con los mismos datos produzcan el mismo resultado.  

**Precondiciones:**  
- Tracker existente  

**Datos de Entrada:**  
```json
{
    "terminal_serial_number": "T-5-NEW",
    "gps_serial_number": "G-5-NEW", 
    "chassis_number": "ABC123",
    "engine_number": "EN987654",
    "responsible_user": 1,
    "justification": "Idempotencia"
}
```

**Pasos (AAA):**  
**Arrange:** Preparar tracker inicial  
**Act:** Ejecutar PUT dos veces consecutivas con mismos datos  
**Assert:** Verificar que ambas respondan exitosamente y el estado final sea correcto  

**Resultado Esperado:**  
Ambas operaciones exitosas con resultado idéntico.  

**Resultado Obtenido:**  
Primera operación: Código 200  
Segunda operación: Código 200  
Estado final correcto en BD  

**Estado:** ✅ **APROBADO**  

---

### ID: UT-MAQ-010

**Título:** Verificar consistencia de lectura tras actualización  

**Descripción:**  
Esta prueba verifica que los cambios sean inmediatamente visibles tras la actualización.  

**Precondiciones:**  
- Tracker existente  

**Datos de Entrada:**  
```json
{
    "terminal_serial_number": "T-6-NEW",
    "gps_serial_number": "G-6-NEW",
    "chassis_number": "ABC123", 
    "engine_number": "EN987654",
    "responsible_user": 1,
    "justification": "Consistencia de lectura"
}
```

**Pasos (AAA):**  
**Arrange:** Preparar tracker con datos iniciales  
**Act:** Actualizar via PUT, luego leer via ORM  
**Assert:** Verificar que los datos leídos coincidan con los actualizados  

**Resultado Esperado:**  
Datos actualizados inmediatamente visibles en BD.  

**Resultado Obtenido:**  
Código de estado: 200  
Verificación ORM: Datos actualizados correctamente persistidos  

**Estado:** ✅ **APROBADO**  

---

## **RESUMEN EJECUTIVO**

### **Estadísticas de Ejecución:**
- **Total de pruebas:** 10  
- **Aprobadas:** 5 (50%)  
- **No Aprobadas:** 5 (50%)  
- **Errores críticos:** 2 (validaciones de unicidad)  

### **Casos Aprobados ✅:**
- UT-MAQ-001: Actualización exitosa con justificación  
- UT-MAQ-006: Validación de tipos de datos  
- UT-MAQ-008: Registro de auditoría básico  
- UT-MAQ-009: Idempotencia de PUT  
- UT-MAQ-010: Consistencia de lectura  

### **Casos No Aprobados ❌:**
- **UT-MAQ-002/003:** Validaciones de unicidad no funcionan (CRÍTICO)  
- **UT-MAQ-004:** Error en implementación del test de justificación obligatoria  
- **UT-MAQ-005:** Manejo incorrecto de excepciones de permisos  
- **UT-MAQ-007:** `get_object_or_404` devuelve 400 en lugar de 404  

### **Problemas Identificados:**

1. **CRÍTICO - Validación de Unicidad:** El serializer no está validando correctamente la unicidad de `terminal_serial_number` y `gps_serial_number`, permitiendo duplicados.

2. **Manejo de Excepciones:** El ViewSet captura todas las excepciones como HTTP 400, perdiendo códigos de estado específicos (403, 404).

3. **Tests con Errores:** Algunos mocks están mal implementados causando fallos de ejecución.

---

## **VEREDICTO FINAL:**

### ❌ **NO APROBADO**

**Justificación:** Aunque el endpoint funciona para casos básicos (50% de aprobación), presenta **fallas críticas en validaciones de seguridad de datos** (unicidad) que comprometen la integridad del sistema. Los números de serie duplicados pueden causar conflictos operacionales graves.

**Recomendaciones:**
1. **URGENTE:** Corregir validación de unicidad en el serializer
2. Mejorar manejo de excepciones para códigos HTTP correctos  
3. Implementar validación obligatoria de justificación si es requerimiento de negocio
4. Corregir implementación de tests con errores

**Fecha de Re-evaluación Recomendada:** Tras corrección de validaciones de unicidad