# Documentación de Casos de Prueba - UT-PM-003

Esta documentación detalla los casos de prueba para el módulo de actualización de programaciones de mantenimiento (UT-PM-003). Cada caso sigue el formato AAA (Arrange, Act, Assert) y utiliza mocks para simular el comportamiento del endpoint.

## UT-PM-003.1

**Título:** Verificar actualización completa exitosa

**Descripción:** Prueba que la actualización completa de una programación de mantenimiento se realice correctamente cuando se proporcionan todos los campos válidos.

**Precondiciones:** 
- Mock de instancia de scheduling configurado
- Serializador FakeSerializer válido
- Permisos de usuario (126) presentes

**Datos de Entrada:**
```json
{
  "scheduled_at": "2025-10-05T10:30:00Z",
  "details": "Ajuste de calibración de sensores.",
  "assigned_technician": 42,
  "maintenance_type": 7,
  "id_responsible_user": 1
}
```

**Pasos (AAA):**
- **Arrange:** Configurar instancia DummyScheduling y datos válidos
- **Act:** Llamar a do_patch con datos completos y permisos
- **Assert:** Verificar que el código de respuesta sea 200 y que la respuesta contenga los campos esperados

**Resultado Esperado:** Código 200, mensaje de éxito y datos actualizados en la respuesta

**Resultado Obtenido:** Paso

**Estado:** Aprobado

**Fecha Ejecución:** 2025-09-30

**Ejecutado por:** Nicolas Urrutia

---

## UT-PM-003.2

**Título:** Verificar actualización solo de fecha programada

**Descripción:** Prueba la actualización parcial cuando solo se modifica la fecha programada.

**Precondiciones:** 
- Instancia de scheduling existente
- Fecha futura válida

**Datos de Entrada:**
```json
{
  "scheduled_at": "2025-10-10T08:00:00Z"
}
```

**Pasos (AAA):**
- **Arrange:** Preparar datos con nueva fecha
- **Act:** Ejecutar do_patch con fecha modificada
- **Assert:** Verificar respuesta 400 o 200 según validación de conflicto

**Resultado Esperado:** Respuesta indicando validación o éxito

**Resultado Obtenido:** Paso

**Estado:** Aprobado

**Fecha Ejecución:** 2025-09-30

**Ejecutado por:** Nicolas Urrutia

---

## UT-PM-003.3

**Título:** Verificar actualización solo de detalles

**Descripción:** Prueba la actualización de solo el campo de detalles.

**Precondiciones:** 
- Scheduling existente
- Detalles válidos

**Datos de Entrada:**
```json
{
  "details": "Cambio de correas"
}
```

**Pasos (AAA):**
- **Arrange:** Configurar datos con nuevos detalles
- **Act:** Llamar do_patch
- **Assert:** Verificar código 200 y detalles actualizados

**Resultado Esperado:** Éxito con detalles modificados

**Resultado Obtenido:** Paso

**Estado:** Aprobado

**Fecha Ejecución:** 2025-09-30

**Ejecutado por:** Nicolas Urrutia

---

## UT-PM-003.4

**Título:** Verificar reasignación de técnico

**Descripción:** Prueba la actualización del técnico asignado.

**Precondiciones:** 
- Técnico válido disponible

**Datos de Entrada:**
```json
{
  "assigned_technician": 84
}
```

**Pasos (AAA):**
- **Arrange:** Datos con nuevo técnico
- **Act:** Ejecutar actualización
- **Assert:** Verificar técnico actualizado en respuesta

**Resultado Esperado:** Técnico reasignado correctamente

**Resultado Obtenido:** Paso

**Estado:** Aprobado

**Fecha Ejecución:** 2025-09-30

**Ejecutado por:** Nicolas Urrutia

---

## UT-PM-003.5

**Título:** Verificar actualización de tipo de mantenimiento

**Descripción:** Prueba la modificación del tipo de mantenimiento.

**Precondiciones:** 
- Tipo válido

**Datos de Entrada:**
```json
{
  "maintenance_type": 7
}
```

**Pasos (AAA):**
- **Arrange:** Datos con tipo de mantenimiento
- **Act:** Llamar do_patch
- **Assert:** Verificar tipo actualizado

**Resultado Esperado:** Tipo modificado exitosamente

**Resultado Obtenido:** Paso

**Estado:** Aprobado

**Fecha Ejecución:** 2025-09-30

**Ejecutado por:** Nicolas Urrutia

---

## UT-PM-003.6

**Título:** Verificar comportamiento PUT como PATCH

**Descripción:** Simula PUT emulando PATCH con datos parciales.

**Precondiciones:** 
- Datos parciales válidos

**Datos de Entrada:**
```json
{
  "details": "Solo con PUT"
}
```

**Pasos (AAA):**
- **Arrange:** Configurar datos
- **Act:** Ejecutar do_patch
- **Assert:** Verificar éxito

**Resultado Esperado:** Actualización exitosa

**Resultado Obtenido:** Paso

**Estado:** Aprobado

**Fecha Ejecución:** 2025-09-30

**Ejecutado por:** Nicolas Urrutia

---

## UT-PM-003.7

**Título:** Verificar respuesta contiene maquinaria y fecha de solicitud

**Descripción:** Asegura que la respuesta incluya campos de maquinaria y fecha.

**Precondiciones:** 
- Scheduling con datos completos

**Datos de Entrada:**
```json
{
  "details": "Verificar campos devueltos"
}
```

**Pasos (AAA):**
- **Arrange:** Datos de prueba
- **Act:** Actualizar
- **Assert:** Verificar campos en respuesta

**Resultado Esperado:** Campos presentes en JSON de respuesta

**Resultado Obtenido:** Paso

**Estado:** Aprobado

**Fecha Ejecución:** 2025-09-30

**Ejecutado por:** Nicolas Urrutia

---

## UT-PM-003.8

**Título:** Verificar fecha programada debe ser futura

**Descripción:** Rechaza fechas pasadas.

**Precondiciones:** 
- Fecha pasada

**Datos de Entrada:**
```json
{
  "scheduled_at": "2000-01-01T10:00:00Z"
}
```

**Pasos (AAA):**
- **Arrange:** Fecha pasada
- **Act:** Intentar actualización
- **Assert:** Verificar error 400

**Resultado Esperado:** Error de validación

**Resultado Obtenido:** Paso

**Estado:** Aprobado

**Fecha Ejecución:** 2025-09-30

**Ejecutado por:** Nicolas Urrutia

---

## UT-PM-003.9

**Título:** Verificar longitud de detalles excedida

**Descripción:** Rechaza detalles demasiado largos.

**Precondiciones:** 
- Detalles > 350 caracteres

**Datos de Entrada:**
```json
{
  "details": "x" * 351
}
```

**Pasos (AAA):**
- **Arrange:** Detalles largos
- **Act:** Actualizar
- **Assert:** Error 400

**Resultado Esperado:** Validación falla

**Resultado Obtenido:** Paso

**Estado:** Aprobado

**Fecha Ejecución:** 2025-09-30

**Ejecutado por:** Nicolas Urrutia

---

## UT-PM-003.10

**Título:** Verificar categoría de tipo de mantenimiento incorrecta

**Descripción:** Rechaza tipos inválidos.

**Precondiciones:** 
- Tipo = 99 (inválido)

**Datos de Entrada:**
```json
{
  "maintenance_type": 99
}
```

**Pasos (AAA):**
- **Arrange:** Tipo inválido
- **Act:** Actualizar
- **Assert:** Error

**Resultado Esperado:** Categoría inválida

**Resultado Obtenido:** Paso

**Estado:** Aprobado

**Fecha Ejecución:** 2025-09-30

**Ejecutado por:** Nicolas Urrutia

---

## UT-PM-003.11

**Título:** Verificar técnico no existe

**Descripción:** Rechaza técnico inexistente.

**Precondiciones:** 
- Técnico ID = 99999

**Datos de Entrada:**
```json
{
  "assigned_technician": 99999
}
```

**Pasos (AAA):**
- **Arrange:** Técnico inválido
- **Act:** Actualizar
- **Assert:** Error

**Resultado Esperado:** Técnico no existe

**Resultado Obtenido:** Paso

**Estado:** Aprobado

**Fecha Ejecución:** 2025-09-30

**Ejecutado por:** Nicolas Urrutia

---

## UT-PM-003.12

**Título:** Verificar técnico no disponible

**Descripción:** Conflicto cuando técnico ocupado.

**Precondiciones:** 
- Técnico ocupado en fecha

**Datos de Entrada:**
```json
{
  "assigned_technician": 42,
  "scheduled_at": "2025-10-10T08:00:00Z"
}
```

**Pasos (AAA):**
- **Arrange:** Datos de conflicto
- **Act:** Actualizar
- **Assert:** Error

**Resultado Esperado:** Técnico no disponible

**Resultado Obtenido:** Paso

**Estado:** Aprobado

**Fecha Ejecución:** 2025-09-30

**Ejecutado por:** Nicolas Urrutia

---

## UT-PM-003.13

**Título:** Verificar conflicto cuando ya ejecutado

**Descripción:** Rechaza actualización si ya ejecutado.

**Precondiciones:** 
- Flag de ejecutado

**Datos de Entrada:**
```json
{
  "__executed__": true
}
```

**Pasos (AAA):**
- **Arrange:** Simular ejecutado
- **Act:** Actualizar
- **Assert:** Código 409

**Resultado Esperado:** Conflicto

**Resultado Obtenido:** Paso

**Estado:** Aprobado

**Fecha Ejecución:** 2025-09-30

**Ejecutado por:** Nicolas Urrutia

---

## UT-PM-003.14

**Título:** Verificar 404 cuando no encontrado

**Descripción:** Error si scheduling no existe.

**Precondiciones:** 
- ID inexistente

**Datos de Entrada:**
```json
{
  "__not_found__": true
}
```

**Pasos (AAA):**
- **Arrange:** Simular no encontrado
- **Act:** Actualizar
- **Assert:** Código 404

**Resultado Esperado:** No encontrado

**Resultado Obtenido:** Paso

**Estado:** Aprobado

**Fecha Ejecución:** 2025-09-30

**Ejecutado por:** Nicolas Urrutia

---

## UT-PM-003.15

**Título:** Verificar sin campos proporcionados

**Descripción:** Manejo de datos vacíos.

**Precondiciones:** 
- Datos vacíos

**Datos de Entrada:**
```json
{}
```

**Pasos (AAA):**
- **Arrange:** Sin datos
- **Act:** Actualizar
- **Assert:** Respuesta válida

**Resultado Esperado:** Éxito o error según lógica

**Resultado Obtenido:** Paso

**Estado:** Aprobado

**Fecha Ejecución:** 2025-09-30

**Ejecutado por:** Nicolas Urrutia

---

## UT-PM-003.16

**Título:** Verificar autenticación ausente

**Descripción:** Rechaza sin autenticación.

**Precondiciones:** 
- Usuario no autenticado

**Datos de Entrada:**
```json
{
  "details": "x"
}
```

**Pasos (AAA):**
- **Arrange:** Sin autenticación
- **Act:** Actualizar
- **Assert:** Código 401

**Resultado Esperado:** No autorizado

**Resultado Obtenido:** Paso

**Estado:** Aprobado

**Fecha Ejecución:** 2025-09-30

**Ejecutado por:** Nicolas Urrutia

---

## UT-PM-003.17

**Título:** Verificar permiso faltante

**Descripción:** Rechaza sin permisos.

**Precondiciones:** 
- Permisos insuficientes

**Datos de Entrada:**
```json
{
  "details": "x"
}
```

**Pasos (AAA):**
- **Arrange:** Permisos = (999,)
- **Act:** Actualizar
- **Assert:** Código 403

**Resultado Esperado:** Prohibido

**Resultado Obtenido:** Paso

**Estado:** Aprobado

**Fecha Ejecución:** 2025-09-30

**Ejecutado por:** Nicolas Urrutia

---

## UT-PM-003.18

**Título:** Verificar token expirado

**Descripción:** Rechaza usuario no autenticado.

**Precondiciones:** 
- Usuario no autenticado

**Datos de Entrada:**
```json
{
  "details": "x"
}
```

**Pasos (AAA):**
- **Arrange:** Usuario falso no autenticado
- **Act:** Actualizar
- **Assert:** Código 401

**Resultado Esperado:** No autorizado

**Resultado Obtenido:** Paso

**Estado:** Aprobado

**Fecha Ejecución:** 2025-09-30

**Ejecutado por:** Nicolas Urrutia

---

## UT-PM-003.19

**Título:** Verificar fecha sin zona horaria

**Descripción:** Rechaza fechas sin TZ.

**Precondiciones:** 
- Fecha sin Z u offset

**Datos de Entrada:**
```json
{
  "scheduled_at": "2025-10-05T10:30:00"
}
```

**Pasos (AAA):**
- **Arrange:** Fecha sin TZ
- **Act:** Actualizar
- **Assert:** Error

**Resultado Esperado:** Formato inválido

**Resultado Obtenido:** Paso

**Estado:** Aprobado

**Fecha Ejecución:** 2025-09-30

**Ejecutado por:** Nicolas Urrutia

---

## UT-PM-003.20

**Título:** Verificar normalización de offset a UTC

**Descripción:** Acepta y normaliza offsets.

**Precondiciones:** 
- Fecha con offset

**Datos de Entrada:**
```json
{
  "scheduled_at": "2025-10-05T05:30:00-05:00"
}
```

**Pasos (AAA):**
- **Arrange:** Fecha con offset
- **Act:** Actualizar
- **Assert:** Éxito y normalización

**Resultado Esperado:** Fecha convertida a UTC

**Resultado Obtenido:** Paso

**Estado:** Aprobado

**Fecha Ejecución:** 2025-09-30

**Ejecutado por:** Nicolas Urrutia

---

## UT-PM-003.21

**Título:** Verificar idempotencia con valores iguales

**Descripción:** Actualización con mismos valores.

**Precondiciones:** 
- Valores idénticos

**Datos de Entrada:**
```json
{
  "details": "Original details"
}
```

**Pasos (AAA):**
- **Arrange:** Datos iguales
- **Act:** Actualizar
- **Assert:** Éxito

**Resultado Esperado:** Sin cambios pero éxito

**Resultado Obtenido:** Paso

**Estado:** Aprobado

**Fecha Ejecución:** 2025-09-30

**Ejecutado por:** Nicolas Urrutia

---

## UT-PM-003.22

**Título:** Verificar atomicidad en fallo de validación

**Descripción:** Rollback en error.

**Precondiciones:** 
- Datos mixtos válidos/inválidos

**Datos de Entrada:**
```json
{
  "details": "válido",
  "scheduled_at": "fecha inválida"
}
```

**Pasos (AAA):**
- **Arrange:** Datos con error
- **Act:** Actualizar
- **Assert:** Error completo

**Resultado Esperado:** Validación falla

**Resultado Obtenido:** Paso

**Estado:** Aprobado

**Fecha Ejecución:** 2025-09-30

**Ejecutado por:** Nicolas Urrutia

---

## UT-PM-003.23

**Título:** Verificar auditoría con usuario responsable

**Descripción:** Incluye ID de usuario en auditoría.

**Precondiciones:** 
- ID responsable presente

**Datos de Entrada:**
```json
{
  "details": "x",
  "id_responsible_user": 1
}
```

**Pasos (AAA):**
- **Arrange:** Con ID usuario
- **Act:** Actualizar
- **Assert:** Éxito

**Resultado Esperado:** Auditoría registrada

**Resultado Obtenido:** Paso

**Estado:** Aprobado

**Fecha Ejecución:** 2025-09-30

**Ejecutado por:** Nicolas Urrutia

---

## UT-PM-003.24

**Título:** Verificar auditoría sin usuario responsable

**Descripción:** Auditoría sin ID específico.

**Precondiciones:** 
- Sin ID responsable

**Datos de Entrada:**
```json
{
  "details": "y"
}
```

**Pasos (AAA):**
- **Arrange:** Sin ID
- **Act:** Actualizar
- **Assert:** Éxito

**Resultado Esperado:** Auditoría básica

**Resultado Obtenido:** Paso

**Estado:** Aprobado

**Fecha Ejecución:** 2025-09-30

**Ejecutado por:** Nicolas Urrutia

---

## UT-PM-003.25

**Título:** Verificar notificaciones en reasignación

**Descripción:** Notifica cambios de técnico.

**Precondiciones:** 
- Cambio de técnico

**Datos de Entrada:**
```json
{
  "assigned_technician": 84
}
```

**Pasos (AAA):**
- **Arrange:** Nuevo técnico
- **Act:** Actualizar
- **Assert:** Éxito (notificación mockeada)

**Resultado Esperado:** Notificación enviada

**Resultado Obtenido:** Paso

**Estado:** Aprobado

**Fecha Ejecución:** 2025-09-30

**Ejecutado por:** Nicolas Urrutia

---

## UT-PM-003.26

**Título:** Verificar notificación en cambio sin técnico

**Descripción:** Notifica cambios sin reasignación.

**Precondiciones:** 
- Cambio de fecha

**Datos de Entrada:**
```json
{
  "scheduled_at": "2025-10-12T14:00:00Z"
}
```

**Pasos (AAA):**
- **Arrange:** Nueva fecha
- **Act:** Actualizar
- **Assert:** Éxito

**Resultado Esperado:** Notificación si aplica

**Resultado Obtenido:** Paso

**Estado:** Aprobado

**Fecha Ejecución:** 2025-09-30

**Ejecutado por:** Nicolas Urrutia

---

## UT-PM-003.27

**Título:** Verificar JSON inválido o tipo de contenido

**Descripción:** Rechaza datos no JSON.

**Precondiciones:** 
- Datos no dict

**Datos de Entrada:**
```json
"not-json"
```

**Pasos (AAA):**
- **Arrange:** String en lugar de dict
- **Act:** Actualizar
- **Assert:** Error 400

**Resultado Esperado:** JSON inválido

**Resultado Obtenido:** Paso

**Estado:** Aprobado

**Fecha Ejecución:** 2025-09-30

**Ejecutado por:** Nicolas Urrutia

---

## UT-PM-003.28

**Título:** Verificar mensaje de confirmación en éxito

**Descripción:** Mensaje correcto en respuesta.

**Precondiciones:** 
- Actualización exitosa

**Datos de Entrada:**
```json
{
  "details": "z"
}
```

**Pasos (AAA):**
- **Arrange:** Datos válidos
- **Act:** Actualizar
- **Assert:** Mensaje específico

**Resultado Esperado:** "Programación de mantenimiento actualizada correctamente."

**Resultado Obtenido:** Paso

**Estado:** Aprobado

**Fecha Ejecución:** 2025-09-30

**Ejecutado por:** Nicolas Urrutia

---

## UT-PM-003.29

**Título:** Verificar conflicto por solicitud cerrada

**Descripción:** Rechaza si solicitud asociada cerrada.

**Precondiciones:** 
- Simulación de cerrada

**Datos de Entrada:**
```json
{
  "details": "x"
}
```

**Pasos (AAA):**
- **Arrange:** Condición de conflicto
- **Act:** Actualizar
- **Assert:** Posible error

**Resultado Esperado:** Conflicto posible

**Resultado Obtenido:** Paso

**Estado:** Aprobado

**Fecha Ejecución:** 2025-09-30

**Ejecutado por:** Nicolas Urrutia

---

## UT-PM-003.30

**Título:** Verificar atomicidad con múltiples cambios y colisión

**Descripción:** Rollback en conflicto múltiple.

**Precondiciones:** 
- Datos con colisión

**Datos de Entrada:**
```json
{
  "details": "multi",
  "scheduled_at": "2025-10-10T08:00:00Z"
}
```

**Pasos (AAA):**
- **Arrange:** Datos conflictivos
- **Act:** Actualizar
- **Assert:** Error

**Resultado Esperado:** Validación falla

**Resultado Obtenido:** Paso

**Estado:** Aprobado

**Fecha Ejecución:** 2025-09-30

**Ejecutado por:** Nicolas Urrutia

---

## UT-PM-003.31

**Título:** Verificar respuesta retorna valores finales

**Descripción:** Respuesta con datos actualizados.

**Precondiciones:** 
- Múltiples campos

**Datos de Entrada:**
```json
{
  "details": "final check",
  "assigned_technician": 42,
  "scheduled_at": "2025-10-05T10:30:00Z"
}
```

**Pasos (AAA):**
- **Arrange:** Datos completos
- **Act:** Actualizar
- **Assert:** Valores finales correctos

**Resultado Esperado:** Datos actualizados en respuesta

**Resultado Obtenido:** Paso

**Estado:** Aprobado

**Fecha Ejecución:** 2025-09-30

**Ejecutado por:** Nicolas Urrutia

---

## UT-PM-003.32

**Título:** Verificar protección de actualización ejecutada sin solicitud

**Descripción:** Previene actualización de ejecutadas.

**Precondiciones:** 
- Simulación de ejecutada

**Datos de Entrada:**
```json
{
  "details": "x"
}
```

**Pasos (AAA):**
- **Arrange:** Condición de protección
- **Act:** Actualizar
- **Assert:** Posible error

**Resultado Esperado:** Protección activa

**Resultado Obtenido:** Paso

**Estado:** Aprobado

**Fecha Ejecución:** 2025-09-30

**Ejecutado por:** Nicolas Urrutia
