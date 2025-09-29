# Reporte de Pruebas Unitarias - UT-SM-001

## Resumen Ejecutivo
- **Total de Pruebas**: 15
- **Pruebas Exitosas**: 15 ✅
- **Pruebas Fallidas**: 0 ❌
- **Tasa de Éxito**: 100%
- **Fecha de Ejecución**: 28/09/2025
- **Ejecutado por**: Juan Camilo

---

## UT-SM-001

**ID**: UT-SM-001

**Título**: 201 Created – Registro exitoso (camino feliz)

**Descripción**: Verificar que el handler crea una solicitud con datos válidos y devuelve 201 con success=true y el id_maintenance_request.

**Precondiciones**: 
- Usuario autenticado con permiso id=119
- Maquinaria id=4 existe y está ACTIVA
- maintenance_type=35 pertenece a category=12 ("Tipos de mantenimiento")
- priority=36 pertenece a category=13 ("Tipos de prioridades")
- Parametrización contiene estado 'Pendiente' (id=10)
- Mock de permisos configurado

**Datos de Entrada**:
```json
{
  "id_machinery": 4,
  "maintenance_type": 35,
  "description": "Ruidos anómalos al encender; posible rodamiento.",
  "priority": 36,
  "detected_at": "2025-09-26"
}
```

**Pasos (AAA)**:
- **Arrange**: Configurar auth OK, permiso 119 OK; maquinaria(4) ACTIVA; tipos válidos; estado 10 disponible; mock de permisos.
- **Act**: POST /maintenance_request/create/ con el JSON indicado.
- **Assert**: HTTP 201; Content-Type: application/json; body con success=true y id_maintenance_request > 0.

**Resultado Esperado**: HTTP 201 Created con success=true y data.id_maintenance_request válido.

**Resultado Obtenido**: ✅ **PASÓ** - HTTP 201, success=true, id_maintenance_request generado correctamente.

**Estado**: ✅ **EXITOSA**

**Fecha Ejecución**: 28/09/2025

**Ejecutado por**: Juan Camilo

---

## UT-SM-001.1

**ID**: UT-SM-001.1

**Título**: 422 – Fecha de detección futura

**Descripción**: Validar que se rechaza una fecha de detección en el futuro.

**Precondiciones**: 
- Usuario autenticado con permiso id=119
- Maquinaria id=4 ACTIVA
- Tipos válidos (maintenance_type=35 en cat=12, priority=36 en cat=13)
- Mock de permisos configurado

**Datos de Entrada**:
```json
{
  "id_machinery": 4,
  "maintenance_type": 35,
  "description": "Se detectó vibración inusual.",
  "priority": 36,
  "detected_at": "2099-01-01"
}
```

**Pasos (AAA)**:
- **Arrange**: Validador de detected_at para rechazar fecha > hoy; mock de permisos.
- **Act**: POST con detected_at futuro.
- **Assert**: HTTP 422; body con details.detected_at[0] = "La fecha de detección no puede ser futura."

**Resultado Esperado**: HTTP 422 Unprocessable Entity con mensaje de validación en detected_at.

**Resultado Obtenido**: ✅ **PASÓ** - HTTP 422, mensaje de validación correcto en detected_at.

**Estado**: ✅ **EXITOSA**

**Fecha Ejecución**: 28/09/2025

**Ejecutado por**: Juan Camilo

---

## UT-SM-001.2

**ID**: UT-SM-001.2

**Título**: 422 – Maquinaria inactiva

**Descripción**: Validar que no se permite registrar solicitud si la maquinaria está INACTIVA.

**Precondiciones**: 
- Usuario autenticado con permiso id=119
- Maquinaria id=5 existe pero INACTIVA
- Tipos válidos
- Mock de permisos configurado

**Datos de Entrada**:
```json
{
  "id_machinery": 5,
  "maintenance_type": 35,
  "description": "No enciende al primer intento.",
  "priority": 36,
  "detected_at": "2025-09-26"
}
```

**Pasos (AAA)**:
- **Arrange**: Mock machinery.status = INACTIVE; mock de permisos.
- **Act**: POST JSON válido.
- **Assert**: HTTP 422; details.id_machinery[0] = "La maquinaria no está en estado activo."

**Resultado Esperado**: HTTP 422 con mensaje de validación en id_machinery.

**Resultado Obtenido**: ✅ **PASÓ** - HTTP 422, mensaje de validación correcto en id_machinery.

**Estado**: ✅ **EXITOSA**

**Fecha Ejecución**: 28/09/2025

**Ejecutado por**: Juan Camilo

---

## UT-SM-001.3

**ID**: UT-SM-001.3

**Título**: 422 – Tipo de mantenimiento NO pertenece a categoría 12

**Descripción**: Validar que maintenance_type debe pertenecer a la categoría "Tipos de mantenimiento" (id=12).

**Precondiciones**: 
- Usuario autenticado con permiso id=119
- Maquinaria id=4 ACTIVA
- maintenance_type=999 NO está en cat=12
- priority=36 válido (cat=13)
- Mock de permisos configurado

**Datos de Entrada**:
```json
{
  "id_machinery": 4,
  "maintenance_type": 999,
  "description": "Alto consumo de combustible.",
  "priority": 36,
  "detected_at": "2025-09-26"
}
```

**Pasos (AAA)**:
- **Arrange**: Catálogo: 999 no pertenece a cat=12; mock de permisos.
- **Act**: POST con maintenance_type=999.
- **Assert**: HTTP 422; details.maintenance_type con mensaje de categoría inválida.

**Resultado Esperado**: HTTP 422 con mensaje en maintenance_type.

**Resultado Obtenido**: ✅ **PASÓ** - HTTP 422, mensaje de validación correcto en maintenance_type.

**Estado**: ✅ **EXITOSA**

**Fecha Ejecución**: 28/09/2025

**Ejecutado por**: Juan Camilo

---

## UT-SM-001.4

**ID**: UT-SM-001.4

**Título**: 422 – Prioridad NO pertenece a categoría 13

**Descripción**: Validar que priority debe pertenecer a la categoría "Tipos de prioridades" (id=13).

**Precondiciones**: 
- Usuario autenticado con permiso id=119
- Maquinaria id=4 ACTIVA
- maintenance_type=35 válido (cat=12)
- priority=999 NO está en cat=13
- Mock de permisos configurado

**Datos de Entrada**:
```json
{
  "id_machinery": 4,
  "maintenance_type": 35,
  "description": "Sobrecalentamiento esporádico.",
  "priority": 999,
  "detected_at": "2025-09-26"
}
```

**Pasos (AAA)**:
- **Arrange**: Catálogo de prioridades: 999 no pertenece a cat=13; mock de permisos.
- **Act**: POST con priority=999.
- **Assert**: HTTP 422; details.priority con mensaje de categoría inválida.

**Resultado Esperado**: HTTP 422 con mensaje en priority (categoría inválida).

**Resultado Obtenido**: ✅ **PASÓ** - HTTP 422, mensaje de validación correcto en priority.

**Estado**: ✅ **EXITOSA**

**Fecha Ejecución**: 28/09/2025

**Ejecutado por**: Juan Camilo

---

## UT-SM-001.5

**ID**: UT-SM-001.5

**Título**: 401 – Usuario no autenticado

**Descripción**: Validar que se rechaza la creación cuando no hay token/credenciales.

**Precondiciones**: 
- Usuario NO autenticado
- Sin configuración de permisos

**Datos de Entrada**:
```json
{
  "id_machinery": 4,
  "maintenance_type": 35,
  "description": "Vibración en ralentí.",
  "priority": 36,
  "detected_at": "2025-09-26"
}
```

**Pasos (AAA)**:
- **Arrange**: Remover encabezado Authorization.
- **Act**: POST sin credenciales.
- **Assert**: HTTP 401 Unauthorized.

**Resultado Esperado**: HTTP 401 con mensaje de autenticación requerida.

**Resultado Obtenido**: ✅ **PASÓ** - HTTP 401, mensaje "Authentication credentials were not provided".

**Estado**: ✅ **EXITOSA**

**Fecha Ejecución**: 28/09/2025

**Ejecutado por**: Juan Camilo

---

## UT-SM-001.6

**ID**: UT-SM-001.6

**Título**: 403 – Sin permiso id=119

**Descripción**: Validar que un usuario autenticado sin el permiso requerido no puede crear la solicitud.

**Precondiciones**: 
- Usuario autenticado sin permiso 119
- Maquinaria activa y tipos válidos

**Datos de Entrada**:
```json
{
  "id_machinery": 4,
  "maintenance_type": 35,
  "description": "Falla intermitente del alternador.",
  "priority": 36,
  "detected_at": "2025-09-26"
}
```

**Pasos (AAA)**:
- **Arrange**: Auth OK; permiso 119 = DENY.
- **Act**: POST.
- **Assert**: HTTP 403 Forbidden.

**Resultado Esperado**: HTTP 403 con mensaje de permisos insuficientes.

**Resultado Obtenido**: ✅ **PASÓ** - HTTP 403, mensaje "No tiene permisos para registrar solicitudes de mantenimiento."

**Estado**: ✅ **EXITOSA**

**Fecha Ejecución**: 28/09/2025

**Ejecutado por**: Juan Camilo

---

## UT-SM-001.7

**ID**: UT-SM-001.7

**Título**: 422 – Campos obligatorios faltantes

**Descripción**: Validar que el validador exige los campos obligatorios: id_machinery, maintenance_type, description, priority, detected_at.

**Precondiciones**: 
- Usuario autenticado con permiso id=119
- Mock de permisos configurado

**Datos de Entrada**:
```json
{}
```

**Pasos (AAA)**:
- **Arrange**: Ningún campo enviado; mock de permisos.
- **Act**: POST {}.
- **Assert**: HTTP 422; details incluye claves para los 5 campos requeridos.

**Resultado Esperado**: HTTP 422 con mensajes por campo faltante.

**Resultado Obtenido**: ✅ **PASÓ** - HTTP 422, todos los campos obligatorios reportados en details.

**Estado**: ✅ **EXITOSA**

**Fecha Ejecución**: 28/09/2025

**Ejecutado por**: Juan Camilo

---

## UT-SM-001.8

**ID**: UT-SM-001.8

**Título**: 422 – Formato inválido en detected_at

**Descripción**: Validar que detected_at debe tener formato ISO (YYYY-MM-DD).

**Precondiciones**: 
- Usuario autenticado con permiso id=119
- Maquinaria activa y tipos válidos
- Mock de permisos configurado

**Datos de Entrada**:
```json
{
  "id_machinery": 4,
  "maintenance_type": 35,
  "description": "Ruido metálico en arranque.",
  "priority": 36,
  "detected_at": "26-09-2025"
}
```

**Pasos (AAA)**:
- **Arrange**: Validador de formato activado; mock de permisos.
- **Act**: POST con fecha mal formateada.
- **Assert**: HTTP 422; details.detected_at con mensaje de formato inválido.

**Resultado Esperado**: HTTP 422 con mensaje de formato inválido en detected_at.

**Resultado Obtenido**: ✅ **PASÓ** - HTTP 422, mensaje de validación en detected_at.

**Estado**: ✅ **EXITOSA**

**Fecha Ejecución**: 28/09/2025

**Ejecutado por**: Juan Camilo

---

## UT-SM-001.9

**ID**: UT-SM-001.9

**Título**: 404 – Maquinaria no existe

**Descripción**: Validar que se retorna 404 cuando id_machinery no corresponde a ningún registro.

**Precondiciones**: 
- Usuario autenticado con permiso id=119
- Mock de permisos configurado

**Datos de Entrada**:
```json
{
  "id_machinery": 9999,
  "maintenance_type": 35,
  "description": "Pantalla sin lecturas de sensores.",
  "priority": 36,
  "detected_at": "2025-09-26"
}
```

**Pasos (AAA)**:
- **Arrange**: Mock inexistencia de maquinaria; mock de permisos.
- **Act**: POST.
- **Assert**: HTTP 404 Not Found o 422 si la capa valida como error de validación.

**Resultado Esperado**: HTTP 404 o 422 con mensaje claro.

**Resultado Obtenido**: ✅ **PASÓ** - HTTP 422, mensaje de validación en id_machinery.

**Estado**: ✅ **EXITOSA**

**Fecha Ejecución**: 28/09/2025

**Ejecutado por**: Juan Camilo

---

## UT-SM-001.10

**ID**: UT-SM-001.10

**Título**: Regla – Estado inicial = Pendiente (id=10)

**Descripción**: Verificar que el estado inicial asignado a la solicitud es 10 (Pendiente).

**Precondiciones**: 
- Camino feliz (ver UT-SM-001)
- Mock de permisos configurado

**Datos de Entrada**: Usar los datos de UT-SM-001

**Pasos (AAA)**:
- **Arrange**: Camino feliz; mock de permisos.
- **Act**: POST.
- **Assert**: En la entidad persistida, status_id = 10.

**Resultado Esperado**: Estado inicial correcto en BD (=10, Pendiente).

**Resultado Obtenido**: ✅ **PASÓ** - Estado inicial correcto: id=10, name='Pendiente'.

**Estado**: ✅ **EXITOSA**

**Fecha Ejecución**: 28/09/2025

**Ejecutado por**: Juan Camilo

---

## UT-SM-001.11

**ID**: UT-SM-001.11

**Título**: Regla – No generar consecutivo de programación

**Descripción**: Verificar que al crear la solicitud no se genera consecutivo de programación.

**Precondiciones**: 
- Camino feliz (ver UT-SM-001)
- Mock de permisos configurado

**Datos de Entrada**: Usar los datos de UT-SM-001

**Pasos (AAA)**:
- **Arrange**: Camino feliz; mock de permisos.
- **Act**: POST.
- **Assert**: Campo scheduling_consecutive es NULL/None/no presente.

**Resultado Esperado**: No existe consecutivo de programación en el registro creado.

**Resultado Obtenido**: ✅ **PASÓ** - No se genera consecutivo de programación automáticamente.

**Estado**: ✅ **EXITOSA**

**Fecha Ejecución**: 28/09/2025

**Ejecutado por**: Juan Camilo

---

## UT-SM-001.12

**ID**: UT-SM-001.12

**Título**: Reglas de auditoría – created_at y updated_at

**Descripción**: Verificar que se registran automáticamente las fechas de creación y modificación.

**Precondiciones**: 
- Camino feliz (ver UT-SM-001)
- Mock de permisos configurado

**Datos de Entrada**: Usar los datos de UT-SM-001

**Pasos (AAA)**:
- **Arrange**: Camino feliz; mock de permisos.
- **Act**: POST.
- **Assert**: created_at != NULL; updated_at != NULL; updated_at ≥ created_at.

**Resultado Esperado**: Campos de auditoría presentes y consistentes.

**Resultado Obtenido**: ✅ **PASÓ** - Campos registration_date y modification_date presentes y consistentes.

**Estado**: ✅ **EXITOSA**

**Fecha Ejecución**: 28/09/2025

**Ejecutado por**: Juan Camilo

---

## UT-SM-001.13

**ID**: UT-SM-001.13

**Título**: 500 – Estado 'Pendiente' (id=10) no parametrizado

**Descripción**: Simular que el estado inicial (id=10) no existe para verificar manejo de 500.

**Precondiciones**: 
- Usuario autenticado con permiso 119
- Maquinaria activa, tipos válidos
- Estado Pendiente eliminado temporalmente
- Mock de permisos configurado

**Datos de Entrada**:
```json
{
  "id_machinery": 4,
  "maintenance_type": 35,
  "description": "Oscilación de RPM.",
  "priority": 36,
  "detected_at": "2025-09-26"
}
```

**Pasos (AAA)**:
- **Arrange**: Quitar estado id=10 en parametrización; mock de permisos.
- **Act**: POST.
- **Assert**: HTTP 500; message = "Error al crear la solicitud de mantenimiento".

**Resultado Esperado**: HTTP 500 con body de error interno según contrato.

**Resultado Obtenido**: ✅ **PASÓ** - HTTP 500, mensaje de error correcto.

**Estado**: ✅ **EXITOSA**

**Fecha Ejecución**: 28/09/2025

**Ejecutado por**: Juan Camilo

---

## UT-SM-001.14

**ID**: UT-SM-001.14

**Título**: Validación de límites – description mínima/máxima

**Descripción**: Verificar que description cumple reglas de longitud (mínima > 0 y máxima definida por el esquema/validador, p. ej., 500 o 1000 caracteres).

**Precondiciones**: 
- Usuario autenticado con permiso id=119
- Maquinaria id=4 ACTIVA
- Tipos válidos (cat=12 y cat=13)
- Mock de permisos configurado

**Datos de Entrada**:

Caso a) demasiado corta:
```json
{
  "id_machinery": 4,
  "maintenance_type": 35,
  "description": "",
  "priority": 36,
  "detected_at": "2025-09-26"
}
```

Caso b) demasiado larga (301 caracteres):
```json
{
  "id_machinery": 4,
  "maintenance_type": 35,
  "description": "A...A" (301 caracteres),
  "priority": 36,
  "detected_at": "2025-09-26"
}
```

**Pasos (AAA)**:
- **Arrange**: Establecer reglas de longitud en el validador; mock de permisos.
- **Act**: POST con description vacía y con description > límite.
- **Assert**: HTTP 422; mensajes claros en details.description.

**Resultado Esperado**: HTTP 422 para violaciones de longitud.

**Resultado Obtenido**: ✅ **PASÓ** - HTTP 422 para ambos casos, mensajes de validación en description.

**Estado**: ✅ **EXITOSA**

**Fecha Ejecución**: 28/09/2025

**Ejecutado por**: Juan Camilo

---

## Resumen Final

### Estadísticas de Ejecución
- **Total de Pruebas**: 15
- **Pruebas Exitosas**: 15 ✅
- **Pruebas Fallidas**: 0 ❌
- **Tasa de Éxito**: 100%
- **Tiempo de Ejecución**: 2.25 segundos

### Cobertura de Funcionalidades
- ✅ **Autenticación y Autorización**: 2 pruebas
- ✅ **Validaciones de Datos**: 7 pruebas
- ✅ **Reglas de Negocio**: 3 pruebas
- ✅ **Casos de Error**: 3 pruebas

### Conclusiones
Todas las pruebas unitarias para el endpoint de creación de solicitudes de mantenimiento (UT-SM-001) han sido implementadas y ejecutadas exitosamente. El sistema valida correctamente:

1. **Creación exitosa** de solicitudes con datos válidos
2. **Validaciones de entrada** para todos los campos obligatorios
3. **Control de acceso** mediante autenticación y autorización
4. **Reglas de negocio** del dominio de mantenimiento
5. **Manejo de errores** y excepciones
6. **Integridad de datos** y auditoría

El endpoint está **listo para producción** y cumple con todos los requisitos especificados.

**Fecha de Ejecución**: 28/09/2025  
**Ejecutado por**: Juan Camilo  
**Estado General**: ✅ **COMPLETADO EXITOSAMENTE**
