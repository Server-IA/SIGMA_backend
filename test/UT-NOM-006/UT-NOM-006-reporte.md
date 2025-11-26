# UT-NOM-006 - Ver Detalle de Nómina

## Descripción
Como usuario del área de Recursos Humanos, quiero visualizar en detalle la información completa de una nómina generada, incluyendo devengos, deducciones, vigencia del contrato, para consultar de forma clara y trazable el cálculo realizado.

## Precondiciones
- Usuario autenticado con rol "Recursos Humanos" o equivalente.
- Usuario tiene asignado el permiso con ID 190 (payroll.retrieve).
- Existen nóminas generadas en el sistema.
- El empleado asociado a la nómina existe en el sistema.
- El contrato asociado a la nómina existe y está vigente o fue vigente en el período de nómina.

## Datos de Entrada
```json
{
  "BASE_URL": "http://localhost:8000",
  "ENDPOINT": "/payroll/{id_payroll}/view-payroll-detail/",
  "METHOD": "GET",
  "PERMISSION_ID": 190,
  "USER_ROLE": "Recursos Humanos",
  "PAYROLL_EXAMPLE": {
    "id_payroll": 1,
    "id_employee": 2,
    "id_employee_contract": "CON-2025-0001-00",
    "start_date": "2025-11-01",
    "end_date": "2025-11-30",
    "base_salary": 100000,
    "time_worked": 100.0,
    "total_deductions": 5000,
    "total_increments": 10000,
    "net_pay": 105000
  }
}
```

## Pasos (AAA)

### Arrange
- Crear usuario autenticado con rol "Recursos Humanos" y permiso 190 en JWT.
- Crear empleados y contratos en sistema.
- Crear nóminas con diferentes escenarios:
  - Nómina sin deducciones ni incrementos.
  - Nómina con deducciones.
  - Nómina con incrementos.
  - Nómina con deducciones e incrementos.
- Preparar IDs válidos e inválidos de nóminas.

### Act
- Realizar peticiones GET a `/payroll/{id_payroll}/view-payroll-detail/` con distintos IDs.
- Validar autenticación JWT y verificación de permiso 190.
- Obtener datos de nómina:
  - ID de la nómina
  - Documento del empleado
  - Nombre completo
  - Período (fecha desde-hasta)
  - Contrato asociado
  - Fecha de generación
  - Autor
  - Salario base
  - Tiempo trabajado
  - Total deducciones
  - Total incrementos
  - Neto a pagar
- Validar estructura de respuesta con datos completos.
- Procesar deducciones e incrementos en detalle.

### Assert
- Caso exitoso: status 200, respuesta contiene todos los datos de nómina.
- Sin autenticación: status 401.
- Sin permiso 190: status 403.
- Nómina inexistente: status 404.
- Respuesta incluye: id_payroll, document_number, employee_full_name, base_salary, total_deductions, total_increments, net_pay.
- Respuesta incluye arrays de payroll_deductions y payroll_increases.
- Datos de autor incluidos: responsible_user_full_name.
- Información del contrato incluida: id_employee_contract.

## Resultado Esperado
1) Endpoint GET `/payroll/{id_payroll}/view-payroll-detail/` accesible y funcional.
2) Validación de autenticación JWT correcta (rechaza sin token, retorna 401).
3) Validación de permiso 190 correcta (rechaza sin permiso, retorna 403).
4) Respuesta 200 OK con estructura:
   - id_payroll: identificador único de la nómina
   - id_employee: identificador del empleado
   - document_number: documento del empleado
   - employee_full_name: nombre completo
   - id_employee_contract: código del contrato
   - start_date: fecha inicial período
   - end_date: fecha final período
   - base_salary: salario base
   - time_worked: tiempo trabajado (porcentaje o cantidad)
   - total_deductions: suma total de deducciones
   - total_increments: suma total de incrementos
   - net_pay: neto a pagar (salario + incrementos - deducciones)
   - currency_type: tipo de moneda
   - creation_date: fecha de generación
   - responsible_user_full_name: nombre del autor
   - payroll_deductions: array con detalles de cada deducción
   - payroll_increases: array con detalles de cada incremento
5) Nómina inexistente retorna 404.
6) Datos de deducciones incluyen: deduction_type_name, amount_value, description, calculated_amount.
7) Datos de incrementos incluyen: increase_type_name, amount_value, description, calculated_amount.
8) Cálculo de neto es correcto: neto = base_salary * (time_worked/100) + total_increments - total_deductions.

## Resultado Obtenido
- Ejecución completada: 12 tests ejecutados, 12 tests aprobados (100% éxito).
- Endpoint GET /payroll/{id_payroll}/view-payroll-detail/ verificado como implementado y funcional en backend.
- Permiso 190 (payroll.retrieve) correctamente validado por el endpoint.
- Serializer PayrollDetailSerializer integrado con servicio externo de usuarios.
- Campo currency_type agregado correctamente al modelo Payroll durante desarrollo de tests.
- Tiempo de ejecución: 134.64 segundos (2 minutos 14 segundos).

Validaciones implementadas en tests reescritos:
- Autenticación JWT con permiso 190: test verifica 200 OK con permiso, 401 sin token, 403 sin permiso.
- Estructura JSON validada: id_payroll, document_number, employee_full_name, id_employee_contract, start_date, end_date.
- Campos de cálculo verificados: base_salary, time_worked, total_deductions, total_increments, net_pay.
- Validación de arrays: payroll_deductions y payroll_increases presentes en respuesta.
- Validación de autor: responsible_user_full_name incluido en respuesta.
- Cálculo de net_pay verificado: net_pay = base_salary * (time_worked/100) + increments - deductions.
- Nómina inexistente retorna 404 correctamente.

Observaciones técnicas:
- Tests mockean autenticación JWT dinámicamente para simular diferentes permisos.
- Setup crea datos completos: empleado, contrato con currency_type, 2 nóminas.
- Backend depende de servicio externo AUTH_SERVICE_URL para datos de usuarios (genera warnings en tests aislados).

## Estado / Fecha / Ejecutor
- Estado: Aprobado
- Fecha: 2025-11-26
- Ejecutor: Alejandro S
