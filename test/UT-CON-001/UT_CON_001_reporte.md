# UT-CON-001 - Registrar Contrato Establecido

## Descripción
Como usuario del área de Recursos Humanos, el sistema debe permitir registrar un contrato de empleado completando sus generalidades y términos, mediante el endpoint POST `/established_contracts/create_established_contract/` (permiso 174: established_contract.create), para asegurar la correcta vinculación laboral y mantener la trazabilidad de los contratos activos dentro del sistema.

El endpoint debe:
- Validar autenticación y autorización (permiso 174 requerido)
- Aceptar estructura JSON con campos obligatorios y opcionales
- Validar fechas coherentes (end_date >= start_date)
- Validar montos no negativos (salary_base, vacation_days, overtime)
- Generar automáticamente un código de contrato único
- Crear registros de deducciones e incrementos si se proporcionan
- Crear registros de pagos según frecuencia (diario, semanal, quincenal, mensual)
- Retornar 201 Created con contract_code al éxito
- Retornar errores descriptivos (400, 401, 403, 500)

## Precondiciones
1. Usuario autenticado con JWT válido.
2. Usuario tiene rol de "Recursos Humanos" o similar.
3. Usuario tiene asignado el permiso con ID 174 (established_contract.create).
4. Existen registros de cargo de empleado (EmployeeCharge) en la base de datos.
5. Existen tipos de contrato en categoría 15 (contract_type).
6. Existen tipos de moneda en categoría 10 (currency_type).
7. Existen tipos de deducción en categoría 18 (si se usan deducciones).
8. Existen tipos de incremento en categoría 19 (si se usan incrementos).
9. Existen tipos de jornada (categoría 16) y modalidad (categoría 17), opcionales.
10. Status "Activo" (ID 1) existe en tabla Statues para establecer estado del contrato.

## Datos de Entrada

### URL del Endpoint
```
POST /established_contracts/create_established_contract/
```

```json
{
  "id_employee_charge": 1,
  "contract_type": 19,
  "start_date": "2025-11-17",
  "end_date": "2025-11-24",
  "payment_frequency_type": "diario",
  "salary_type": "Mensual fijo",
  "salary_base": 100000,
  "currency_type": 17,
  "vacation_days": 15,
  "cumulative_vacation": false,
  "maximum_disability_days": 15,
  "overtime": 30,
  "notice_period_days": 10,
  "contract_payments": [
    {"id_day_of_week": null, "date_payment": null}
  ]
}
```

### Estructura JSON Completa (Con Deducciones e Incrementos)
```json
{
  "id_employee_charge": 1,
  "description": "Contrato técnico especializado",
  "contract_type": 19,
  "start_date": "2025-11-17",
  "end_date": "2025-11-24",
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
  "start_cumulative_vacation": "2025-11-17",
  "maximum_disability_days": 15,
  "overtime": 30,
  "overtime_period": "semana",
  "notice_period_days": 10,
  "contract_payments": [
    {"id_day_of_week": null, "date_payment": 16},
    {"id_day_of_week": null, "date_payment": 1}
  ],
  "established_deductions": [
    {
      "deduction_type": 29,
      "amount_type": "fijo",
      "amount_value": 10000,
      "application_deduction_type": "SalarioBase",
      "start_date_deduction": "2025-11-17",
      "end_date_deductions": "2025-11-23",
      "description": "Deducción por ejemplo",
      "amount": 2
    }
  ],
  "established_increases": [
    {
      "increase_type": 31,
      "amount_type": "Porcentaje",
      "amount_value": 10,
      "application_increase_type": "SalarioBase",
      "start_date_increase": "2025-11-17",
      "end_date_increase": "2025-11-23",
      "description": "Incremento por ejemplo",
      "amount": 3
    }
  ]
}
```

### JWT Payload (Autorización)
```json
{
  "user": {
    "id": 1,
    "username": "hr_user",
    "is_authenticated": true
  },
  "payload": {
    "rol": [
      {
        "id": 10,
        "nombre": "Recursos Humanos",
        "permisos": [
          {"id": 174, "nombre": "established_contract.create"}
        ]
      }
    ]
  }
}
```

### Respuesta Exitosa (201 Created)
```json
{
  "success": true,
  "message": "Contrato creado exitosamente",
  "contract_code": "EMP-001-CON-20251117-001"
}
```

### Respuesta Error - Validación (400 Bad Request)
```json
{
  "success": false,
  "message": "Error al crear el contrato",
  "errors": {
    "end_date": ["La fecha de fin debe ser posterior a la fecha de inicio."],
    "salary_base": ["El salario base no puede ser negativo."],
    "vacation_days": ["Los días de vacaciones no pueden ser negativos."],
    "contract_payments": ["Debe existir exactamente 1 registro de pago para frecuencia diaria."]
  }
}
```

## Pasos (AAA)

### Arrange (Preparación)
1. **Usuario y Autenticación:**
   - Usuario autenticado: ID 1, username "hr_user"
   - Rol: "Recursos Humanos"
   - Permiso 174 presente en JWT payload

2. **Datos del Contrato:**
   - Cargo del empleado: ID 1 (debe existir)
   - Tipo de contrato: ID 19 (categoría 15)
   - Tipo de moneda: ID 17 (categoría 10)
   - Fecha inicio: hoy (yyyy-MM-dd)
   - Fecha fin: mañana (yyyy-MM-dd)
   - Modalidad salarial: "Mensual fijo"
   - Salario base: 100000 (decimal positivo)

3. **Datos Opcionales:**
   - Deducciones: deduction_type 29, amount_type "fijo", amount_value 10000
   - Incrementos: increase_type 31, amount_type "Porcentaje", amount_value 10
   - Jornada laboral: ID 22 (opcional)
   - Modalidad trabajo: ID 25 (opcional)
   - Período prueba: 30 días (opcional)

4. **Pagos del Contrato:**
   - Frecuencia diaria: 1 registro con ambos campos null
   - Frecuencia semanal: 1 registro con id_day_of_week (date_payment null)
   - Frecuencia quincenal: 2 registros con date_payment (1-15, 16-31)
   - Frecuencia mensual: 1 registro con date_payment (1-31)

### Act (Acción)
1. Realizar POST a `/established_contracts/create_established_contract/` con:
   - JSON con todos los campos requeridos
   - JWT en Authorization header
   - Content-Type: application/json

2. ViewSet ejecuta internamente:
   - Verifica autenticación del usuario
   - Valida permiso 174 desde JWT payload
   - Instancia EstablishedContractCreateSerializer con datos y contexto
   - Ejecuta serializer.is_valid() con validaciones cascada:
     * Validar formatos de campos (int, date, decimal)
     * Validar que id_employee_charge existe
     * Validar que contract_type pertenece a categoría 15
     * Validar que currency_type pertenece a categoría 10
     * Validar que salary_base >= 0
     * Validar que end_date >= start_date
     * Validar rangos de vacation_days, overtime, disability_days (>= 0)
     * Validar estructura de contract_payments según payment_frequency_type
     * Validar deducciones: no duplicados, rangos de fecha, montos válidos
     * Validar incrementos: no duplicados, rangos de fecha, montos válidos
   - Si válido: llama serializer.save() dentro de transaction.atomic()
   - Genera código de contrato automáticamente
   - Crea EstablishedContract en BD
   - Crea ContractPaymentsEstablishedContract según frecuencia
   - Crea EstablishedDeduction por cada deducción
   - Crea EstablishedIncrease por cada incremento
   - Registra en auditoría (AuditClient)
   - Retorna respuesta 201 con contract_code

### Assert (Validación)
1. **Casos Exitosos (201 Created):**
   - Sin filtros: contrato creado con código generado automáticamente
   - Con deducciones: deducciones creadas correctamente con relación a contrato
   - Con incrementos: incrementos creados correctamente
   - Frecuencia quincenal: 2 registros de pago creados (16 y 1)
   - Frecuencia semanal: 1 registro con day_of_week establecido
   - Vacaciones acumuladas: start_cumulative_vacation validado

2. **Validación de Permisos (403 Forbidden):**
   - Usuario sin permiso 174: status 403, mensaje "No tiene permisos"
   - Permission check en múltiples roles: funciona si permiso existe en cualquier rol

3. **Validación de Entrada (400 Bad Request):**
   - id_employee_charge faltante: campo requerido
   - contract_type inválido: no pertenece a categoría 15
   - salary_base negativo: "El salario base no puede ser negativo"
   - end_date < start_date: "La fecha de fin debe ser posterior a la fecha de inicio"
   - vacation_days = 0: "Los días de vacaciones no pueden ser negativos"
   - cumulative_vacation=true sin start_cumulative_vacation: campo requerido
   - Deducción con amount_value > 100 para Porcentaje: validación falla
   - contract_payments inválido para semanal (sin day_of_week): error estructura

4. **Validación de Autenticación (401 Unauthorized):**
   - Usuario no autenticado: status 401, mensaje "Usuario no autenticado"

5. **Estructura de Respuesta:**
   - Respuesta 201 incluye: success=true, message, contract_code
   - Respuesta 400 incluye: success=false, message, errors (dict detallado)
   - contract_code generado con patrón: EMP-{id_charge}-CON-{YYYYMMDD}-{seq}
   - Estado del contrato automáticamente "Activo" (status_id=1)

## Resultado Esperado
1) Endpoint POST `/established_contracts/create_established_contract/` accesible y funcional.
2) Validación de permiso 174 correcta (rechaza acceso sin permisos, permite con permiso).
3) Validación de fechas coherentes (end_date >= start_date).
4) Validación de montos no negativos (salary_base, vacation_days, overtime).
5) Respuesta exitosa contiene estructura JSON con:
   - success: true
   - message: mensaje descriptivo
   - contract_code: código generado automáticamente
6) Errores retornan status HTTP apropiado (400, 401, 403, 500) con mensaje descriptivo.

## Resultado Obtenido
- Exitosa por pruebas unitarias. Verificado:
  - Endpoint responde 201 Created para solicitud válida con permiso 174 y campos requeridos.
  - Genera automáticamente código de contrato único con patrón EMP-{id_charge}-CON-{YYYYMMDD}-{seq}.
  - Crea registros de pago según frecuencia especificada (diario, semanal, quincenal, mensual).
  - Crea deducciones e incrementos con validación de montos y rangos de fecha.
  - Rechaza acceso sin autenticación (status 401).
  - Rechaza acceso sin permiso 174 (status 403).
  - Rechaza end_date <= start_date (status 400).
  - Rechaza salary_base negativo (status 400).
  - Rechaza vacation_days <= 0 (status 400).
  - Rechaza cumulative_vacation=true sin start_cumulative_vacation (status 400).
  - Rechaza deducción con porcentaje > 100 (status 400).
  - Rechaza frecuencia semanal sin id_day_of_week (status 400).
  - Rechaza campos requeridos faltantes (id_employee_charge, contract_type, etc).
  - Respuesta 201 incluye success=true, message y contract_code generado.
  - Respuesta 400 incluye success=false, message y errors detallados.
  - Validación de categorías (contract_type→15, currency_type→10, etc) funcional.

## Estado / Fecha / Ejecutor
- Estado: Aprobado
- Fecha: 2025-11-17
- Ejecutor: Alejandro S
