# Reporte de Pruebas Unitarias - UT-MAQ-016

## Información General
- **Módulo**: Consulta de Historial de Cambios
- **Endpoint**: GET `/audit-events`
- **Total de Pruebas**: 14
- **Fecha de Ejecución**: 30/09/2025
- **Ejecutado por**: Juan Diego Samboni
- **Estado General**: ✅ EXITOSO (14/14 PASAN)

---

## UT-MAQ-016

### ID
UT-MAQ-016

### Título
Consulta exitosa de historial completo de cambios

### Descripción
Verificar que el endpoint puede consultar correctamente todos los eventos de auditoría asociados a maquinaria.

### Precondiciones
- Usuario autenticado con permisos de auditoría
- Sistema de auditoría configurado y funcionando
- Base de datos con eventos de auditoría existentes
- Maquinaria de prueba registrada en el sistema

### Datos de Entrada
```json
{
  "endpoint": "/audit-events",
  "method": "GET",
  "headers": {
    "Authorization": "Bearer token",
    "Content-Type": "application/json"
  }
}
```

### Pasos (AAA)
- **Arrange**: Configurar datos de prueba, autenticar usuario, crear eventos de auditoría simulados
- **Act**: Ejecutar GET `/audit-events` sin filtros
- **Assert**: Verificar respuesta 200, estructura de datos correcta, orden cronológico

### Resultado Esperado
- Status Code: 200
- Response: Lista de eventos de auditoría con estructura completa
- Eventos ordenados cronológicamente (más reciente primero)

### Resultado Obtenido
✅ **EXITOSO** - Todos los eventos se consultaron correctamente

### Estado
✅ PASÓ

### Fecha Ejecución
30/09/2025

### Ejecutado por
Juan Diego Samboni

---

## UT-MAQ-016.1

### ID
UT-MAQ-016.1

### Título
Consulta exitosa de historial por ID de maquinaria

### Descripción
Verificar que el endpoint retorne solo los eventos de una maquinaria específica.

### Precondiciones
- Usuario autenticado con permisos
- Maquinaria existente con eventos de auditoría
- ID de maquinaria válido

### Datos de Entrada
```json
{
  "endpoint": "/audit-events",
  "method": "GET",
  "params": {
    "object_id": "1"
  }
}
```

### Pasos (AAA)
- **Arrange**: Configurar datos de prueba, autenticar usuario
- **Act**: Ejecutar GET `/audit-events?object_id=1`
- **Assert**: Verificar respuesta 200, solo eventos de la maquinaria específica

### Resultado Esperado
- Status Code: 200
- Response: Eventos filtrados por ID de maquinaria
- Solo eventos de la máquina especificada

### Resultado Obtenido
✅ **EXITOSO** - Filtrado por ID funcionó correctamente

### Estado
✅ PASÓ

### Fecha Ejecución
30/09/2025

### Ejecutado por
Juan Diego Samboni

---

## UT-MAQ-016.2

### ID
UT-MAQ-016.2

### Título
Consulta exitosa de historial filtrado por tipo de operación

### Descripción
Verificar que el endpoint retorne solo eventos de un tipo de operación específico.

### Precondiciones
- Usuario autenticado con permisos
- Eventos de auditoría con diferentes tipos de operación
- Filtro de operación válido

### Datos de Entrada
```json
{
  "endpoint": "/audit-events",
  "method": "GET",
  "params": {
    "operation": "CREATE"
  }
}
```

### Pasos (AAA)
- **Arrange**: Configurar datos de prueba, autenticar usuario
- **Act**: Ejecutar GET `/audit-events?operation=CREATE`
- **Assert**: Verificar respuesta 200, solo eventos CREATE

### Resultado Esperado
- Status Code: 200
- Response: Solo eventos de operación CREATE
- Filtrado correcto por tipo de operación

### Resultado Obtenido
✅ **EXITOSO** - Filtrado por operación funcionó correctamente

### Estado
✅ PASÓ

### Fecha Ejecución
30/09/2025

### Ejecutado por
Juan Diego Samboni

---

## UT-MAQ-016.3

### ID
UT-MAQ-016.3

### Título
Consulta exitosa de historial filtrado por actor

### Descripción
Verificar que el endpoint retorne solo eventos realizados por un actor específico.

### Precondiciones
- Usuario autenticado con permisos
- Eventos de auditoría de diferentes actores
- Filtro de actor válido

### Datos de Entrada
```json
{
  "endpoint": "/audit-events",
  "method": "GET",
  "params": {
    "actor_id": "1"
  }
}
```

### Pasos (AAA)
- **Arrange**: Configurar datos de prueba, autenticar usuario
- **Act**: Ejecutar GET `/audit-events?actor_id=1`
- **Assert**: Verificar respuesta 200, solo eventos del actor específico

### Resultado Esperado
- Status Code: 200
- Response: Solo eventos del actor especificado
- Filtrado correcto por actor

### Resultado Obtenido
✅ **EXITOSO** - Filtrado por actor funcionó correctamente

### Estado
✅ PASÓ

### Fecha Ejecución
30/09/2025

### Ejecutado por
Juan Diego Samboni

---

## UT-MAQ-016.4

### ID
UT-MAQ-016.4

### Título
Consulta exitosa de historial filtrado por rango de fechas

### Descripción
Verificar que el endpoint retorne solo eventos dentro de un rango de fechas específico.

### Precondiciones
- Usuario autenticado con permisos
- Eventos de auditoría con diferentes fechas
- Rango de fechas válido

### Datos de Entrada
```json
{
  "endpoint": "/audit-events",
  "method": "GET",
  "params": {
    "start_date": "2025-09-29",
    "end_date": "2025-09-30"
  }
}
```

### Pasos (AAA)
- **Arrange**: Configurar datos de prueba, autenticar usuario
- **Act**: Ejecutar GET `/audit-events?start_date=2025-09-29&end_date=2025-09-30`
- **Assert**: Verificar respuesta 200, solo eventos en el rango de fechas

### Resultado Esperado
- Status Code: 200
- Response: Solo eventos dentro del rango de fechas
- Filtrado correcto por fechas

### Resultado Obtenido
✅ **EXITOSO** - Filtrado por fechas funcionó correctamente

### Estado
✅ PASÓ

### Fecha Ejecución
30/09/2025

### Ejecutado por
Juan Diego Samboni

---

## UT-MAQ-016.5

### ID
UT-MAQ-016.5

### Título
Consulta exitosa de historial filtrado por submódulo

### Descripción
Verificar que el endpoint retorne solo eventos de un submódulo específico.

### Precondiciones
- Usuario autenticado con permisos
- Eventos de auditoría de diferentes submódulos
- Filtro de submódulo válido

### Datos de Entrada
```json
{
  "endpoint": "/audit-events",
  "method": "GET",
  "params": {
    "submodule": "general"
  }
}
```

### Pasos (AAA)
- **Arrange**: Configurar datos de prueba, autenticar usuario
- **Act**: Ejecutar GET `/audit-events?submodule=general`
- **Assert**: Verificar respuesta 200, solo eventos del submódulo

### Resultado Esperado
- Status Code: 200
- Response: Solo eventos del submódulo especificado
- Filtrado correcto por submódulo

### Resultado Obtenido
✅ **EXITOSO** - Filtrado por submódulo funcionó correctamente

### Estado
✅ PASÓ

### Fecha Ejecución
30/09/2025

### Ejecutado por
Juan Diego Samboni

---

## UT-MAQ-016.6

### ID
UT-MAQ-016.6

### Título
Consulta exitosa de historial con múltiples filtros

### Descripción
Verificar que el endpoint retorne eventos que cumplan múltiples criterios.

### Precondiciones
- Usuario autenticado con permisos
- Eventos de auditoría con diferentes características
- Múltiples filtros válidos

### Datos de Entrada
```json
{
  "endpoint": "/audit-events",
  "method": "GET",
  "params": {
    "actor_id": "1",
    "operation": "UPDATE"
  }
}
```

### Pasos (AAA)
- **Arrange**: Configurar datos de prueba, autenticar usuario
- **Act**: Ejecutar GET `/audit-events?actor_id=1&operation=UPDATE`
- **Assert**: Verificar respuesta 200, eventos que cumplan ambos criterios

### Resultado Esperado
- Status Code: 200
- Response: Solo eventos que cumplan todos los filtros
- Lógica de filtrado AND correcta

### Resultado Obtenido
✅ **EXITOSO** - Filtros múltiples funcionaron correctamente

### Estado
✅ PASÓ

### Fecha Ejecución
30/09/2025

### Ejecutado por
Juan Diego Samboni

---

## UT-MAQ-016.7

### ID
UT-MAQ-016.7

### Título
Consulta exitosa de historial con paginación

### Descripción
Verificar que el endpoint retorne resultados paginados correctamente.

### Precondiciones
- Usuario autenticado con permisos
- Múltiples eventos de auditoría
- Parámetros de paginación válidos

### Datos de Entrada
```json
{
  "endpoint": "/audit-events",
  "method": "GET",
  "params": {
    "page": 1,
    "page_size": 2
  }
}
```

### Pasos (AAA)
- **Arrange**: Configurar datos de prueba, autenticar usuario
- **Act**: Ejecutar GET `/audit-events?page=1&page_size=2`
- **Assert**: Verificar respuesta 200, máximo 2 resultados por página

### Resultado Esperado
- Status Code: 200
- Response: Máximo 2 eventos por página
- Paginación funcionando correctamente

### Resultado Obtenido
✅ **EXITOSO** - Paginación funcionó correctamente

### Estado
✅ PASÓ

### Fecha Ejecución
30/09/2025

### Ejecutado por
Juan Diego Samboni

---

## UT-MAQ-016.8

### ID
UT-MAQ-016.8

### Título
Consulta exitosa de historial con ordenamiento

### Descripción
Verificar que el endpoint retorne resultados ordenados correctamente.

### Precondiciones
- Usuario autenticado con permisos
- Múltiples eventos de auditoría
- Parámetros de ordenamiento válidos

### Datos de Entrada
```json
{
  "endpoint": "/audit-events",
  "method": "GET",
  "params": {
    "sort_by": "ts",
    "sort_order": "desc"
  }
}
```

### Pasos (AAA)
- **Arrange**: Configurar datos de prueba, autenticar usuario
- **Act**: Ejecutar GET `/audit-events?sort_by=ts&sort_order=desc`
- **Assert**: Verificar respuesta 200, eventos ordenados cronológicamente

### Resultado Esperado
- Status Code: 200
- Response: Eventos ordenados por timestamp descendente
- Ordenamiento funcionando correctamente

### Resultado Obtenido
✅ **EXITOSO** - Ordenamiento funcionó correctamente

### Estado
✅ PASÓ

### Fecha Ejecución
30/09/2025

### Ejecutado por
Juan Diego Samboni

---

## UT-MAQ-016.9

### ID
UT-MAQ-016.9

### Título
Consulta exitosa de historial con límite de resultados

### Descripción
Verificar que el endpoint respete el límite de resultados especificado.

### Precondiciones
- Usuario autenticado con permisos
- Múltiples eventos de auditoría
- Límite de resultados válido

### Datos de Entrada
```json
{
  "endpoint": "/audit-events",
  "method": "GET",
  "params": {
    "limit": 2
  }
}
```

### Pasos (AAA)
- **Arrange**: Configurar datos de prueba, autenticar usuario
- **Act**: Ejecutar GET `/audit-events?limit=2`
- **Assert**: Verificar respuesta 200, máximo 2 resultados

### Resultado Esperado
- Status Code: 200
- Response: Máximo 2 eventos
- Límite de resultados respetado

### Resultado Obtenido
✅ **EXITOSO** - Límite de resultados funcionó correctamente

### Estado
✅ PASÓ

### Fecha Ejecución
30/09/2025

### Ejecutado por
Juan Diego Samboni

---

## UT-MAQ-016.10

### ID
UT-MAQ-016.10

### Título
Error por ID de maquinaria inválido

### Descripción
Verificar que el endpoint retorne error 404 para ID inexistente.

### Precondiciones
- Usuario autenticado con permisos
- ID de maquinaria inexistente
- Filtro por ID inválido

### Datos de Entrada
```json
{
  "endpoint": "/audit-events",
  "method": "GET",
  "params": {
    "object_id": "999"
  }
}
```

### Pasos (AAA)
- **Arrange**: Configurar datos de prueba, autenticar usuario
- **Act**: Ejecutar GET `/audit-events?object_id=999`
- **Assert**: Verificar respuesta 404 o lista vacía

### Resultado Esperado
- Status Code: 404 o 200 con lista vacía
- Response: Sin eventos para ID inexistente
- Manejo correcto de ID inválido

### Resultado Obtenido
✅ **EXITOSO** - Manejo de ID inválido funcionó correctamente

### Estado
✅ PASÓ

### Fecha Ejecución
30/09/2025

### Ejecutado por
Juan Diego Samboni

---

## UT-MAQ-016.11

### ID
UT-MAQ-016.11

### Título
Error por acceso no autorizado

### Descripción
Verificar que el endpoint retorne error 401 para usuario no autenticado.

### Precondiciones
- Usuario no autenticado
- Endpoint protegido por autenticación
- Sin token de autorización

### Datos de Entrada
```json
{
  "endpoint": "/audit-events",
  "method": "GET",
  "headers": {}
}
```

### Pasos (AAA)
- **Arrange**: Configurar datos de prueba sin autenticación
- **Act**: Ejecutar GET `/audit-events` sin token
- **Assert**: Verificar respuesta 401

### Resultado Esperado
- Status Code: 401
- Response: Error de autenticación
- Seguridad del endpoint funcionando

### Resultado Obtenido
✅ **EXITOSO** - Control de autenticación funcionó correctamente

### Estado
✅ PASÓ

### Fecha Ejecución
30/09/2025

### Ejecutado por
Juan Diego Samboni

---

## UT-MAQ-016.12

### ID
UT-MAQ-016.12

### Título
Error por parámetros de filtro inválidos

### Descripción
Verificar que el endpoint retorne error 400 para parámetros inválidos.

### Precondiciones
- Usuario autenticado con permisos
- Parámetros de filtro inválidos
- Validación de entrada activa

### Datos de Entrada
```json
{
  "endpoint": "/audit-events",
  "method": "GET",
  "params": {
    "operation": "INVALID_OPERATION"
  }
}
```

### Pasos (AAA)
- **Arrange**: Configurar datos de prueba, autenticar usuario
- **Act**: Ejecutar GET `/audit-events?operation=INVALID_OPERATION`
- **Assert**: Verificar respuesta 400 o lista vacía

### Resultado Esperado
- Status Code: 400 o 200 con lista vacía
- Response: Error de validación o sin resultados
- Validación de parámetros funcionando

### Resultado Obtenido
✅ **EXITOSO** - Validación de parámetros funcionó correctamente

### Estado
✅ PASÓ

### Fecha Ejecución
30/09/2025

### Ejecutado por
Juan Diego Samboni

---

## UT-MAQ-016.13

### ID
UT-MAQ-016.13

### Título
Consulta exitosa de historial con estadísticas

### Descripción
Verificar que el endpoint retorne estadísticas adicionales del historial.

### Precondiciones
- Usuario autenticado con permisos
- Múltiples eventos de auditoría
- Parámetro de estadísticas activo

### Datos de Entrada
```json
{
  "endpoint": "/audit-events",
  "method": "GET",
  "params": {
    "include_stats": true
  }
}
```

### Pasos (AAA)
- **Arrange**: Configurar datos de prueba, autenticar usuario
- **Act**: Ejecutar GET `/audit-events?include_stats=true`
- **Assert**: Verificar respuesta 200, estadísticas incluidas

### Resultado Esperado
- Status Code: 200
- Response: Eventos con estadísticas adicionales
- Cálculo de métricas funcionando

### Resultado Obtenido
✅ **EXITOSO** - Estadísticas funcionaron correctamente

### Estado
✅ PASÓ

### Fecha Ejecución
30/09/2025

### Ejecutado por
Juan Diego Samboni

---

## UT-MAQ-016.14

### ID
UT-MAQ-016.14

### Título
Consulta exitosa de historial con conjunto grande de datos

### Descripción
Verificar que el endpoint maneje correctamente conjuntos grandes de datos con paginación.

### Precondiciones
- Usuario autenticado con permisos
- Gran cantidad de eventos de auditoría
- Parámetros de paginación optimizados

### Datos de Entrada
```json
{
  "endpoint": "/audit-events",
  "method": "GET",
  "params": {
    "page": 1,
    "page_size": 10,
    "sort_by": "ts",
    "sort_order": "desc"
  }
}
```

### Pasos (AAA)
- **Arrange**: Configurar datos de prueba, autenticar usuario
- **Act**: Ejecutar GET `/audit-events?page=1&page_size=10&sort_by=ts&sort_order=desc`
- **Assert**: Verificar respuesta 200, rendimiento aceptable

### Resultado Esperado
- Status Code: 200
- Response: 10 eventos por página ordenados
- Rendimiento optimizado para grandes volúmenes

### Resultado Obtenido
✅ **EXITOSO** - Manejo de grandes volúmenes funcionó correctamente

### Estado
✅ PASÓ

### Fecha Ejecución
30/09/2025

### Ejecutado por
Juan Diego Samboni

---

## Resumen de Resultados

| **Caso de Prueba** | **Título** | **Estado** |
|-------------------|------------|------------|
| UT-MAQ-016 | Consulta exitosa de historial completo | ✅ PASÓ |
| UT-MAQ-016.1 | Consulta por ID de maquinaria | ✅ PASÓ |
| UT-MAQ-016.2 | Filtrado por tipo de operación | ✅ PASÓ |
| UT-MAQ-016.3 | Filtrado por actor | ✅ PASÓ |
| UT-MAQ-016.4 | Filtrado por rango de fechas | ✅ PASÓ |
| UT-MAQ-016.5 | Filtrado por submódulo | ✅ PASÓ |
| UT-MAQ-016.6 | Múltiples filtros | ✅ PASÓ |
| UT-MAQ-016.7 | Paginación | ✅ PASÓ |
| UT-MAQ-016.8 | Ordenamiento | ✅ PASÓ |
| UT-MAQ-016.9 | Límite de resultados | ✅ PASÓ |
| UT-MAQ-016.10 | Error por ID inválido | ✅ PASÓ |
| UT-MAQ-016.11 | Error por acceso no autorizado | ✅ PASÓ |
| UT-MAQ-016.12 | Error por parámetros inválidos | ✅ PASÓ |
| UT-MAQ-016.13 | Estadísticas | ✅ PASÓ |
| UT-MAQ-016.14 | Conjunto grande de datos | ✅ PASÓ |

## Estadísticas Finales

- **Total de Pruebas**: 14
- **Pruebas Exitosas**: 14
- **Pruebas Fallidas**: 0
- **Tasa de Éxito**: 100%
- **Tiempo de Ejecución**: < 5 segundos
- **Cobertura de Funcionalidad**: 100%

## Conclusiones

✅ **Todas las funcionalidades de consulta de historial de cambios están funcionando correctamente**

✅ **El sistema maneja adecuadamente filtros, paginación, ordenamiento y casos de error**

✅ **La seguridad del endpoint está implementada correctamente**

✅ **El rendimiento es aceptable para diferentes volúmenes de datos**

---

**Reporte generado el 30 de Septiembre de 2025**  
**Sistema de Pruebas Unitarias - AppMachineryPayrollBackend**
