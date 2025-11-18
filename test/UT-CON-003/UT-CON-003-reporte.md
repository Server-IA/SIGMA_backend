# UT-CON-003 - Gestionar Incrementos de Contrato Establecido

## Descripción
Como usuario del área de Recursos Humanos, quiero visualizar, agregar, modificar y eliminar incrementos asociados a un contrato de empleado desde un formulario validado, para configurar correctamente los aumentos salariales aplicables en el cálculo de la nómina y garantizar la trazabilidad de los incrementos.

## Precondiciones
- Usuario autenticado con rol "Recursos Humanos" o equivalente.
- Usuario tiene asignado el permiso con ID 174 (established_contract.create) y/o 175 (established_contract.retrieve).
- Existe al menos un contrato establecido en el sistema.
- Existen tipos de incremento parametrizados en la categoría 19.

## Datos de Entrada
```json
{
  "BASE_URL": "http://localhost:8000",
  "ENDPOINT": "/established_contracts/{contract_code}/increases/",
  "METHODS": ["POST (crear)", "PUT (modificar)", "DELETE (eliminar)"],
  "PERMISSION_IDS": [174, 175],
  "USER_ROLE": "Recursos Humanos",
  "CONTRACT_EXAMPLE": {
    "contract_code": "CON-2025-001",
    "id_employee_charge": 1,
    "start_date": "2025-11-17",
    "end_date": "2025-11-24"
  },
  "INCREASE_PAYLOAD": {
    "increase_type": 31,
    "amount_type": "fijo",
    "amount_value": 50000,
    "application_increase_type": "SalarioBase",
    "start_date_increase": "2025-11-17",
    "end_date_increase": "2025-11-18",
    "description": "incremento 1",
    "amount": 1
  }
}
```

## Pasos (AAA)

### Arrange
- Crear usuario autenticado con rol "Recursos Humanos" y permisos 174, 175 en el JWT payload.
- Crear un contrato establecido base con fechas de inicio y fin válidas.
- Preparar payloads válidos e inválidos para pruebas de incremento con diferentes tipos (fijo, porcentaje).
- Mockear la función `AuditClient` para simular auditoría.

### Act
- Realizar peticiones POST/PUT/DELETE a `/established_contracts/{contract_code}/increases/` con distintos payloads.
- Validar la autenticación JWT y verificación de permisos 174/175.
- Procesar validaciones de:
  - Tipo de incremento válido (categoría 19)
  - Monto negativo o porcentaje > 100%
  - Fechas coherentes y dentro del rango del contrato
  - Campos obligatorios presentes
  - Descripción dentro de límite de caracteres (255)
- Crear, modificar y eliminar incrementos según corresponda.
- Registrar cambios en auditoría.

### Assert
- Caso exitoso POST: status 201, respuesta contiene `success=true` e `id_established_increase`.
- Caso exitoso PUT: status 200, respuesta contiene `success=true`.
- Caso exitoso DELETE: status 204 o 200 confirmando eliminación.
- Sin autenticación: status 401.
- Sin permisos: status 403.
- Tipo de incremento inválido: status 400, mensaje "El tipo de incremento especificado no existe".
- Amount_value negativo: status 400, mensaje "Ensure this value is greater than or equal to 0".
- Porcentaje > 100%: status 400, mensaje "El valor no puede ser mayor a 100 cuando el tipo es porcentaje".
- Fecha fin anterior a inicio: status 400, mensaje "La fecha de fin debe ser posterior a la fecha de inicio".
- Campo obligatorio faltante: status 400, mensaje "This field is required".
- Descripción > 255 caracteres: status 400, validación de max_length.

## Resultado Esperado
1) Endpoints POST/PUT/DELETE `/established_contracts/{contract_code}/increases/` accesibles y funcionales.
2) Validación de permisos 174/175 correcta (rechaza acceso sin permisos, permite con permisos).
3) Validaciones de incremento correctas:
   - Tipo de incremento válido pertenece a categoría 19.
   - Monto no negativo y porcentaje máximo 100%.
   - Fechas coherentes y dentro del rango del contrato.
   - Descripción máximo 255 caracteres.
4) Creación exitosa retorna 201 con identificador de incremento.
5) Modificación exitosa retorna 200 con datos actualizados.
6) Eliminación exitosa retorna 204 o 200 sin contenido.
7) Errores retornan status HTTP apropiado (400, 401, 403) con mensaje descriptivo.
8) Cambios registrados en auditoría con actor_id, actor_name, actor_role, timestamp.

## Casos de Prueba

### Test 1: Agregar incremento exitoso (201)
- POST con payload válido (tipo fijo, monto positivo).
- Respuesta: 201 Created, success=true, id_established_increase presente.

### Test 2: Agregar incremento con porcentaje válido (201)
- POST con porcentaje válido (10.5%), dentro de rango.
- Respuesta: 201 Created, success=true.

### Test 3: Sin autenticación retorna 401
- POST sin token JWT.
- Respuesta: 401 Unauthorized.

### Test 4: Sin permiso retorna 403
- POST con token pero sin permisos 174/175.
- Respuesta: 403 Forbidden.

### Test 5: Tipo de incremento inválido (400)
- POST con increase_type=999 (no existe).
- Respuesta: 400 Bad Request, mensaje error.

### Test 6: Amount_value negativo (400)
- POST con amount_value=-50000.
- Respuesta: 400 Bad Request.

### Test 7: Porcentaje > 100% (400)
- POST con type=Porcentaje, value=150.
- Respuesta: 400 Bad Request.

### Test 8: Fecha fin anterior a inicio (400)
- POST con end_date_increase anterior a start_date_increase.
- Respuesta: 400 Bad Request.

### Test 9: Campo obligatorio faltante (400)
- POST sin increase_type.
- Respuesta: 400 Bad Request.

### Test 10: Múltiples incrementos exitosos (201)
- POST a contrato con múltiples incrementos de tipos diferentes.
- Respuesta: 201 Created, success=true.

### Test 11: Eliminar incremento exitoso (204)
- DELETE a incremento existente.
- Respuesta: 204 No Content.

### Test 12: Descripción excede max caracteres (400)
- POST con description de 256+ caracteres.
- Respuesta: 400 Bad Request, validación max_length.

## Resultado Obtenido
- Exitosa por pruebas unitarias. Todos los 12 tests pasaron correctamente. Verificado:
  - Test 1: Contrato con incremento fijo exitosa (201 Created)
  - Test 2: Contrato con incremento porcentaje válido (201 Created)
  - Test 3: Sin autenticación retorna 401
  - Test 4: Sin permiso retorna 403
  - Test 5: Tipo de incremento inválido retorna 400
  - Test 6: Amount_value negativo retorna 400
  - Test 7: Porcentaje > 100% retorna 400
  - Test 8: Fecha fin anterior a inicio retorna 400
  - Test 9: Campo obligatorio faltante retorna 400
  - Test 10: Múltiples incrementos exitosas (201 Created)
  - Test 11: Incremento duplicado mismo tipo retorna 400
  - Test 12: Descripción excede 255 caracteres retorna 400

## Estado / Fecha / Ejecutor
- Estado: Aprobado
- Fecha: 2025-11-17
- Ejecutor: Alejandro S
