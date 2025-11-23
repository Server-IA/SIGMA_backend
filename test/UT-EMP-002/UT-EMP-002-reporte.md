# Reporte de Pruebas Unitarias - UT-EMP-002
## Endpoint: Listar Empleados (GET /employees/list)

**Fecha de Ejecución:** 2025-11-22  
**Permiso Requerido:** ID 183 - Consultar/Listar Empleados

---

## Resumen Ejecutivo

| Métrica | Valor |
|---------|-------|
| **Total de Pruebas** | 8 |
| **Aprobadas** | 8 |
| **No Aprobadas** | 0 |
| **Tasa de Éxito** | 100% ✅ |
| **Tiempo de Ejecución** | ~8 segundos |

---

## Tabla de Resultados

| ID Test | Título | Estado | Fecha Ejecución |
|---------|--------|--------|-----------------|
| UT-EMP-002-01 | Listado exitoso de empleados paginado | ✅ APROBADO | 2025-11-22 16:30 |
| UT-EMP-002-02 | Filtro por estado de empleado | ✅ APROBADO | 2025-11-22 16:30 |
| UT-EMP-002-03 | Búsqueda por nombre y documento | ✅ APROBADO | 2025-11-22 16:30 |
| UT-EMP-002-04 | Ordenamiento (ascendente/descendente) | ✅ APROBADO | 2025-11-22 16:30 |
| UT-EMP-002-05 | Respuesta vacía con mensaje | ✅ APROBADO | 2025-11-22 16:30 |
| UT-EMP-002-06 | Validación de paginación | ✅ APROBADO | 2025-11-22 16:30 |
| UT-EMP-002-07 | Acceso denegado sin permiso | ✅ APROBADO | 2025-11-22 16:30 |
| UT-EMP-002-08 | Validación de cambios en tiempo real | ✅ APROBADO | 2025-11-22 16:30 |

---

## Resultados Detallados

### ✅ UT-EMP-002-01: Listado exitoso de empleados paginado

**Descripción:**  
Verifica que el endpoint retorna correctamente el listado paginado y estructurado de empleados.

**Datos de Entrada:**
```http
GET /employees/list?page=1&page_size=10
Authorization: Bearer <JWT con permiso 183>
```

**Resultado Esperado:**
- HTTP 200 OK
- `success: true`
- `data` con empleados (mínimo 4)
- Todos los campos requeridos presentes
- Paginación correcta con `page_size: 10`

**Resultado Obtenido:**
- ✅ HTTP 200 OK
- ✅ `success: true`
- ✅ Empleados retornados con todos los campos
- ✅ Paginación correcta

**Estado:** **APROBADO**

---

### ✅ UT-EMP-002-02: Filtro por estado de empleado

**Descripción:**  
Valida que el parámetro `status` permite filtrar el listado por estado (1=Activo, 2=Inactivo).

**Datos de Entrada:**
```http
GET /employees/list?status=2
Authorization: Bearer <JWT con permiso 183>
```

**Resultado Esperado:**
- HTTP 200 OK
- `success: true`
- `data` con `status_id: 2` (Inactivo)
- `status_name: "Inactivo"` para todos los registros

**Resultado Obtenido:**
- ✅ HTTP 200 OK
- ✅ `success: true`
- ✅ 2 empleados inactivos retornados
- ✅ Todos con `status_id: 2` y `status_name: "Inactivo"`

**Estado:** **APROBADO**

---

### ✅ UT-EMP-002-03: Búsqueda por nombre y búsqueda por documento

**Descripción:**  
Verifica el comportamiento de los parámetros `search` y `search_type`.

**Datos de Entrada:**

Búsqueda por nombre:
```http
GET /employees/list?search=martina&search_type=nombre
Authorization: Bearer <JWT con permiso 183>
```

Búsqueda por documento:
```http
GET /employees/list?search=321321321&search_type=documento
Authorization: Bearer <JWT con permiso 183>
```

**Resultado Esperado:**
- HTTP 200 OK para ambas búsquedas
- Búsqueda por nombre: 1 registro con "Martina" en `full_name`
- Búsqueda por documento: 1 registro con `document_number: "321321321"`

**Resultado Obtenido:**
- ✅ HTTP 200 OK para ambas búsquedas
- ✅ Búsqueda por nombre retorna 1 empleado con "Martina Gómez Rivera"
- ✅ Búsqueda por documento retorna 1 empleado con documento "321321321"

**Estado:** **APROBADO**

---

### ✅ UT-EMP-002-04: Ordenamiento por columna (ascendente/descendente)

**Descripción:**  
Valida que el parámetro `ordering` ordena el resultado adecuadamente.

**Datos de Entrada:**
```http
GET /employees/list?ordering=-name
Authorization: Bearer <JWT con permiso 183>
```

**Resultado Esperado:**
- HTTP 200 OK
- Empleados ordenados alfabéticamente descendente por nombre
- "Zulema" aparece antes que "Aura"

**Resultado Obtenido:**
- ✅ HTTP 200 OK
- ✅ Orden correcto: "Zulema Zapata Zuluaga" primero
- ✅ "Aura Álvarez Arias" último

**Estado:** **APROBADO**

---

### ✅ UT-EMP-002-05: Respuesta vacía y mensaje cuando no hay coincidencias

**Descripción:**  
Valida que cuando no hay empleados que cumplan los criterios, se retorna lista vacía con mensaje apropiado.

**Datos de Entrada:**
```http
GET /employees/list?search=no_existe_este_nombre
Authorization: Bearer <JWT con permiso 183>
```

**Resultado Esperado:**
- HTTP 200 OK
- `data: []`
- `pagination.total: 0`
- `pagination.total_pages: 0`
- Mensaje: "No se encontraron empleados con los criterios seleccionados."

**Resultado Obtenido:**
- ✅ HTTP 200 OK
- ✅ `data: []`
- ✅ `pagination.total: 0`
- ✅ `pagination.total_pages: 0`
- ✅ Mensaje correcto presente

**Estado:** **APROBADO**

---

### ✅ UT-EMP-002-06: Validación de paginación y límites válidos

**Descripción:**  
Valida que las opciones de `page_size` aceptadas sean solo 10, 25, 50 o 100.

**Datos de Entrada:**

Caso válido:
```http
GET /employees/list?page=2&page_size=25
Authorization: Bearer <JWT con permiso 183>
```

Caso inválido:
```http
GET /employees/list?page_size=200
Authorization: Bearer <JWT con permiso 183>
```

**Resultado Esperado:**
- Caso válido: HTTP 200 OK, página 2 con 5 empleados (30 total - 25 en página 1)
- Caso inválido: HTTP 400 Bad Request con mensaje "page_size debe ser uno de: 10, 25, 50, 100."

**Resultado Obtenido:**
- ✅ Caso válido: HTTP 200 OK
- ✅ `pagination.page: 2`, `pagination.page_size: 25`
- ✅ 5 empleados en página 2
- ✅ Caso inválido: HTTP 400 Bad Request
- ✅ Mensaje de error correcto

**Estado:** **APROBADO**

---

### ✅ UT-EMP-002-07: Acceso denegado sin permiso

**Descripción:**  
Valida que el recurso rechaza acceso sin el permiso 183.

**Datos de Entrada:**
```http
GET /employees/list
Authorization: Bearer <JWT sin permiso 183>
```

**Resultado Esperado:**
- HTTP 403 Forbidden con mensaje "No tiene permisos para acceder al listado de empleados."

**Resultado Obtenido:**
- ✅ HTTP 403 Forbidden
- ✅ Mensaje de error correcto

**Estado:** **APROBADO**

---

### ✅ UT-EMP-002-08: Validación de acciones y cambios en tiempo real

**Descripción:**  
Verifica que el listado se actualiza tras altas, bajas o cambios en empleados.

**Datos de Entrada:**
```http
# Estado inicial
GET /employees/list
Authorization: Bearer <JWT con permiso 183>

# Después de crear empleado
GET /employees/list

# Después de cambiar estado a inactivo
GET /employees/list?status=2

# Después de cambiar cargo
GET /employees/list
```

**Resultado Esperado:**
- Lista se actualiza inmediatamente después de cada cambio
- Nuevo empleado aparece en el listado
- Empleado desactivado aparece en lista de inactivos
- Cambio de cargo se refleja correctamente

**Resultado Obtenido:**
- ✅ Lista inicial con N empleados
- ✅ Después de alta: N+1 empleados
- ✅ Empleado desactivado aparece en filtro `status=2`
- ✅ Cargo actualizado se muestra correctamente: "Analista de Recursos Humanos"

**Estado:** **APROBADO**

---

## Observaciones Generales

1. **Mocking Exitoso**: El mock del servicio externo de usuarios funciona correctamente.

2. **Cobertura Funcional Completa**: Los tests cubren exitosamente:
   - ✅ Paginación con valores válidos
   - ✅ Filtrado por estado
   - ✅ Búsqueda por nombre y documento
   - ✅ Ordenamiento personalizado
   - ✅ Manejo de resultados vacíos
   - ✅ Validación de paginación
   - ✅ Control de permisos
   - ✅ Actualización en tiempo real

3. **Base de Datos Real**: Todos los tests utilizan la base de datos real de Django.

---

## Conclusiones

**✅ TODOS LOS TESTS APROBADOS - 8/8 (100%)**

El endpoint de listado de empleados funciona correctamente en todos los casos de uso validados:
- Funcionalidad core operativa
- Validaciones de seguridad implementadas
- Paginación y filtros funcionando correctamente

**Estado para Producción:** ✅ **LISTO**

---

## Comandos de Ejecución

Para ejecutar todas las pruebas:
```bash
docker exec machpay_backend pytest test/UT-EMP-002/test_UT_EMP_002.py -v
```

Para ejecutar un test específico:
```bash
docker exec machpay_backend pytest test/UT-EMP-002/test_UT_EMP_002.py::TestEmployeeList::test_ut_emp_002_02_filter_by_status -v
```

---

**Generado:** 2025-11-22 16:40  
**Versión:** 1.1  
**Autor:** Sistema de Pruebas Automatizadas
