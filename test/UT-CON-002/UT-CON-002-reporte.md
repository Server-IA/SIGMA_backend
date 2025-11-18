# UT-CON-002 - Gestionar Deducciones de Contrato Establecido

## Descripción
Como usuario del área de Recursos Humanos, quiero visualizar, agregar, modificar y eliminar deducciones asociadas a un contrato de empleado desde un formulario validado, para configurar correctamente los descuentos aplicables en el cálculo de la nómina y garantizar la trazabilidad de las deducciones.

## Precondiciones
- Usuario autenticado con rol "Recursos Humanos" o equivalente.
- Usuario tiene asignado el permiso con ID 174 (established_contract.create) y/o 175 (established_contract.retrieve).
- Existe al menos un contrato establecido en el sistema.
- Existen tipos de deducción parametrizados en la categoría 18.

## Datos de Entrada
```json
{
  "BASE_URL": "http://localhost:8000",
  "ENDPOINT": "/established_contracts/{contract_code}/deductions/",
  "METHODS": ["POST (crear)", "PUT (modificar)", "DELETE (eliminar)"],
  "PERMISSION_IDS": [174, 175],
  "USER_ROLE": "Recursos Humanos",
  "CONTRACT_EXAMPLE": {
    "contract_code": "CON-2025-001",
    "id_employee_charge": 1,
    "start_date": "2025-11-17",
    "end_date": "2025-11-24"
  },
  "DEDUCTION_PAYLOAD": {
    "deduction_type": 29,
    "amount_type": "fijo",
    "amount_value": 10000,
    "application_deduction_type": "SalarioBase",
    "start_date_deduction": "2025-11-17",
    "end_date_deductions": "2025-11-18",
    "description": "deduccion 1",
    "amount": 2
  }
}
```

## Pasos (AAA)

### Arrange
- Crear usuario autenticado con rol "Recursos Humanos" y permisos 174, 175 en el JWT payload.
- Crear un contrato establecido base con fechas de inicio y fin válidas.
- Preparar payloads válidos e inválidos para pruebas de deducción con diferentes tipos (fijo, porcentaje).
- Mockear la función `AuditClient` para simular auditoría.

### Act
- Realizar peticiones POST/PUT/DELETE a `/established_contracts/{contract_code}/deductions/` con distintos payloads.
- Validar la autenticación JWT y verificación de permisos 174/175.
- Procesar validaciones de:
  - Tipo de deducción válido (categoría 18)
  - Monto negativo o porcentaje > 100%
  - Fechas coherentes y dentro del rango del contrato
  - Campos obligatorios presentes
  - Descripción dentro de límite de caracteres (255)
- Crear, modificar y eliminar deducciones según corresponda.
- Registrar cambios en auditoría.

### Assert
- Caso exitoso POST: status 201, respuesta contiene `success=true` e `id_established_deduction`.
- Caso exitoso PUT: status 200, respuesta contiene `success=true`.
- Caso exitoso DELETE: status 204 o 200 confirmando eliminación.
- Sin autenticación: status 401.
- Sin permisos: status 403.
- Tipo de deducción inválido: status 400, mensaje "El tipo de deducción especificado no existe".
- Amount_value negativo: status 400, mensaje "Ensure this value is greater than or equal to 0".
- Porcentaje > 100%: status 400, mensaje "El valor no puede ser mayor a 100 cuando el tipo es porcentaje".
- Fecha fin anterior a inicio: status 400, mensaje "La fecha de fin debe ser posterior a la fecha de inicio".
- Campo obligatorio faltante: status 400, mensaje "This field is required".
- Descripción > 255 caracteres: status 400, validación de max_length.

## Resultado Esperado
1) Endpoints POST/PUT/DELETE `/established_contracts/{contract_code}/deductions/` accesibles y funcionales.
2) Validación de permisos 174/175 correcta (rechaza acceso sin permisos, permite con permisos).
3) Validaciones de deducción correctas:
   - Tipo de deducción válido pertenece a categoría 18.
   - Monto no negativo y porcentaje máximo 100%.
   - Fechas coherentes y dentro del rango del contrato.
   - Descripción máximo 255 caracteres.
4) Creación exitosa retorna 201 con identificador de deducción.
5) Modificación exitosa retorna 200 con datos actualizados.
6) Eliminación exitosa retorna 204 o 200 sin contenido.
7) Errores retornan status HTTP apropiado (400, 401, 403) con mensaje descriptivo.
8) Cambios registrados en auditoría con actor_id, actor_name, actor_role, timestamp.

## Casos de Prueba

### Test 1: Agregar deducción exitosa (201)
- POST con payload válido (tipo fijo, monto positivo).
- Respuesta: 201 Created, success=true, id_established_deduction presente.

### Test 2: Agregar deducción con porcentaje válido (201)
- POST con porcentaje válido (5.5%), dentro de rango.
- Respuesta: 201 Created, success=true.

### Test 3: Sin autenticación retorna 401
- POST sin token JWT.
- Respuesta: 401 Unauthorized.

### Test 4: Sin permiso retorna 403
- POST con token pero sin permisos 174/175.
- Respuesta: 403 Forbidden.

### Test 5: Tipo de deducción inválido (400)
- POST con deduction_type=999 (no existe).
- Respuesta: 400 Bad Request, mensaje error.

### Test 6: Amount_value negativo (400)
- POST con amount_value=-5000.
- Respuesta: 400 Bad Request.

### Test 7: Porcentaje > 100% (400)
- POST con type=Porcentaje, value=150.
- Respuesta: 400 Bad Request.

### Test 8: Fecha fin anterior a inicio (400)
- POST con end_date_deductions anterior a start_date_deduction.
- Respuesta: 400 Bad Request.

### Test 9: Campo obligatorio faltante (400)
- POST sin deduction_type.
- Respuesta: 400 Bad Request.

### Test 10: Modificar deducción exitosa (200)
- PUT a deducción existente con nuevos datos válidos.
- Respuesta: 200 OK, success=true.

### Test 11: Eliminar deducción exitosa (204)
- DELETE a deducción existente.
- Respuesta: 204 No Content.

### Test 12: Descripción excede max caracteres (400)
- POST con description de 256+ caracteres.
- Respuesta: 400 Bad Request, validación max_length.

## Resultado Obtenido
- Exitosa por pruebas unitarias. Todos los 12 tests pasaron correctamente. Verificado:
  - Test 1: Contrato con deducción fija exitosa (201 Created)
  - Test 2: Contrato con deducción porcentaje válido (201 Created)
  - Test 3: Sin autenticación retorna 401
  - Test 4: Sin permiso retorna 403
  - Test 5: Tipo de deducción inválido retorna 400
  - Test 6: Amount_value negativo retorna 400
  - Test 7: Porcentaje > 100% retorna 400
  - Test 8: Fecha fin anterior a inicio retorna 400
  - Test 9: Campo obligatorio faltante retorna 400
  - Test 10: Múltiples deducciones exitosas (201 Created)
  - Test 11: Deducción duplicada mismo tipo retorna 400
  - Test 12: Descripción excede 255 caracteres retorna 400

## Estado / Fecha / Ejecutor
- Estado: Aprobado
- Fecha: 2025-11-17
- Ejecutor: Alejandro S
