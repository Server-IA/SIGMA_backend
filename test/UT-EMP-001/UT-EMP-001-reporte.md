# UT-EMP-001 - Crear Empleado con Contrato

## Descripción
Como usuario del área de Recursos Humanos, quiero crear un nuevo empleado en el sistema con su contrato laboral asociado, para registrar el nuevo personal con todos sus datos contractuales, salario, beneficios y calendario de pagos.

## Precondiciones
- Usuario autenticado con rol "Recursos Humanos" o equivalente.
- Usuario tiene asignado el permiso con ID 3 (employee.create).
- Existe al menos un cargo de empleado (EmployeeCharge) activo en el sistema.
- El sistema tiene parametrización completa (tipos de contrato, frecuencias de pago, etc.).

## Datos de Entrada
```json
{
  "BASE_URL": "http://localhost:8000",
  "ENDPOINT": "/employees/",
  "METHOD": "POST",
  "PERMISSION_ID": 3,
  "USER_ROLE": "Recursos Humanos",
  "EMPLOYEE_EXAMPLE": {
    "id_user": 2,
    "email": "test@example.com",
    "observation": "Empleado de prueba",
    "id_employee_charge": 1,
    "description": "Contrato de prueba",
    "contract_type": 19,
    "start_date": "2025-11-20",
    "end_date": "2025-11-27",
    "payment_frequency_type": "quincenal",
    "minimum_hours": 8,
    "workday_type": 22,
    "work_mode_type": 25,
    "salary_type": "Mensual fijo",
    "salary_base": 100000,
    "currency_type": 17,
    "trial_period_days": 30,
    "vacation_days": 15,
    "vacation_frequency_days": 360,
    "cumulative_vacation": true,
    "start_cumulative_vacation": "2025-11-20",
    "maximum_disability_days": 15,
    "overtime": 30,
    "overtime_period": "semana",
    "notice_period_days": 10,
    "contract_payments": [
      {"id_day_of_week": null, "date_payment": 16},
      {"id_day_of_week": null, "date_payment": 1}
    ]
  }
}
```

## Pasos (AAA)

### Arrange
- Crear usuario autenticado con rol "Recursos Humanos" y permiso 3 en el JWT payload.
- Crear datos de parametrización (tipos de contrato, cargas de trabajo, frecuencias de pago).
- Crear un cargo de empleado (EmployeeCharge) válido activo.
- Preparar payloads válidos e inválidos para diferentes escenarios.
- Preparar usuarios para pruebas de validación.

### Act
- Realizar peticiones POST a `/employees/` con distintos payloads.
- Validar la autenticación JWT y verificación de permisos 3.
- Procesar validaciones de:
  - Usuario existe y está autenticado
  - Usuario tiene permiso 3 para crear empleado
  - Email no está duplicado en el sistema
  - Cargo de empleado existe y es válido
  - Salario base es positivo
  - Fechas de contrato son válidas (fin >= inicio)
  - Tipo de contrato existe
  - Frecuencia de pago es válida
  - Días de vacación no son negativos
  - Campos obligatorios están presentes
- Crear registro de empleado y contrato atómicamente.
- Generar noticias/eventos de creación de empleado.
- Registrar creación en auditoría.
- Retornar 201 Created con datos de empleado creado.

### Assert
- Caso exitoso: status 201, respuesta contiene id_employee y datos creados.
- Sin autenticación: status 401.
- Sin permiso 3: status 403.
- Email duplicado: status 400 o 409.
- Cargo inválido: status 400 o 404.
- Salario negativo: status 400.
- Fecha fin < fecha inicio: status 400.
- Contrato tipo inválido: status 400.
- Frecuencia pago inválida: status 400.
- Vacaciones negativas: status 400.
- Campo obligatorio faltante: status 400.
- Auditoría registrada correctamente.

## Resultado Esperado
1) Endpoint POST `/employees/` accesible y funcional.
2) Validación de autenticación JWT correcta (rechaza sin token, retorna 401).
3) Validación de permiso 3 correcta (rechaza sin permiso, retorna 403).
4) Validación de datos:
   - Email no duplicado (retorna 400/409 si existe).
   - Cargo existe (retorna 400/404 si no existe).
   - Salario positivo (retorna 400 si negativo).
   - Fechas válidas (retorna 400 si fin < inicio).
   - Contrato tipo válido (retorna 400 si no existe).
   - Frecuencia pago válida (retorna 400 si inválida).
   - Vacaciones positivas (retorna 400 si negativas).
   - Campos obligatorios presentes (retorna 400 si falta alguno).
5) Creación atómica:
   - Empleado se crea exitosamente.
   - Contrato se crea asociado al empleado.
   - Ambos se crean juntos o se reversan ambos.
6) Respuesta correcta:
   - Status 201 Created.
   - Body contiene mensaje "Empleado y contrato creados exitosamente."
   - Body contiene datos de empleado creado.
7) Auditoría registrada con actor_id, actor_name, timestamp.

## Casos de Prueba

### Test 1: Crear empleado exitosa (201)
- POST con payload válido completo.
- Respuesta: 201 Created, empleado creado con contrato.

### Test 2: Sin autenticación retorna 401
- POST sin token JWT.
- Respuesta: 401 Unauthorized.

### Test 3: Sin permiso retorna 403
- POST con token pero sin permiso 3.
- Respuesta: 403 Forbidden.

### Test 4: Email duplicado retorna 400/409
- POST con email que ya existe en sistema.
- Respuesta: 400 Bad Request o 409 Conflict.

### Test 5: Cargo inválido retorna 400/404
- POST con id_employee_charge que no existe.
- Respuesta: 400 Bad Request o 404 Not Found.

### Test 6: Salario negativo retorna 400
- POST con salary_base negativo.
- Respuesta: 400 Bad Request.

### Test 7: Fecha fin anterior a inicio retorna 400
- POST con end_date < start_date.
- Respuesta: 400 Bad Request.

### Test 8: Tipo contrato inválido retorna 400
- POST con contract_type que no existe.
- Respuesta: 400 Bad Request.

### Test 9: Campo obligatorio faltante retorna 400
- POST sin campo obligatorio (ej: email).
- Respuesta: 400 Bad Request.

### Test 10: Frecuencia pago inválida retorna 400
- POST con payment_frequency_type inválida (ej: "anual").
- Respuesta: 400 Bad Request.

### Test 11: Vacaciones negativas retorna 400
- POST con vacation_days negativo.
- Respuesta: 400 Bad Request.

### Test 12: Auditoría registrada
- POST exitosa y verificar que se registra en auditoría.
- Respuesta: 201 Created, evento en auditoría.

## Resultado Obtenido
- Exitosa por pruebas unitarias. Todos los 12 tests pasaron correctamente. Verificado:
  - Test 1: Crear empleado exitosa (201 Created)
  - Test 2: Sin autenticación validado
  - Test 3: Sin permiso validado
  - Test 4: Email duplicado validado
  - Test 5: Cargo inválido validado
  - Test 6: Salario negativo validado
  - Test 7: Fecha fin anterior validado
  - Test 8: Tipo contrato inválido validado
  - Test 9: Campo obligatorio faltante validado
  - Test 10: Frecuencia pago inválida validado
  - Test 11: Vacaciones negativas validado
  - Test 12: Auditoría registrada validada

## Estado / Fecha / Ejecutor
- Estado: Aprobado
- Fecha: 2025-11-20
- Ejecutor: Alejandro S