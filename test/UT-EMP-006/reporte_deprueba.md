# Reporte de Pruebas Unitarias - UT-EMP-006

## ID
UT-EMP-006

## Título
Verificar generación de Otro Sí de contratos de empleados mediante endpoint POST

## Descripción
Se prueban los 12 casos de uso del endpoint `POST /employees/{id_employee}/generate-otro-si/` que permite generar un "Otro Sí" (secundary_petition) para un contrato de empleado activo. El proceso finaliza el contrato actual y crea uno nuevo con secundary_petition=True, incrementando la versión del código de contrato. Las pruebas cubren escenarios exitosos, validaciones de datos, autenticación, autorización, validaciones de pagos, deducciones, incrementos e integridad de datos.

## Precondiciones
- Contenedor Docker `machpay_backend` ejecutándose correctamente
- Base de datos PostgreSQL configurada y migraciones aplicadas
- Modelos Employee, EmployeeContract, EmployeeNews, EmployeeContractPayment, EmployeeContractDeduction, EmployeeContractIncrease, Types, TypesCategory, Statues, Units, DaysOfWeek y User creados en la base de datos
- Sistema de autenticación JWT configurado
- Permisos de usuario configurados (permiso ID 187 para employee.create_secundary_petition)
- Estados de contrato: 28 (Activo), 29 (Finalizado)
- Estados de empleado: 1 (Activo), 2 (Inactivo)
- Categorías de tipos: 15 (Tipos de contrato), 16 (Tipos de jornada), 17 (Modos de trabajo), 18 (Tipos de deducción), 19 (Tipos de incremento)
- Categoría de unidades: 10 (Moneda)

## Datos de Entrada
- **Empleado 1 de prueba**: ID=1, estado=1 (Activo), contrato activo con contract_code="CON-2025-0001-00"
- **Empleado 2 de prueba**: ID=2, estado=2 (Inactivo), sin contratos activos
- **Empleado 3 de prueba**: ID=3, estado=1 (Activo), solo contratos finalizados
- **Tipos válidos**: contract_type=19, workday_type=22, work_mode_type=25, currency_type=17
- **Tipos de deducción**: ID=29, categoría=18
- **Tipos de incremento**: ID=31, categoría=19
- **Tokens JWT**: Con permiso 187 (employee.create_secundary_petition) y sin permiso (999)
- **Payloads de prueba**: JSON complejo con observation, id_employee_charge, contract (con todos sus campos), contract_payments, established_deductions y established_increases

## Pasos (AAA)

### Arrange
- Configurar cliente de pruebas APIClient
- Crear usuarios de prueba con IDs específicos
- Configurar parametrización completa (status, categorías de tipos, tipos, departamentos, cargos, unidades, días de la semana)
- Crear múltiples empleados con diferentes estados y contratos
- Preparar tokens JWT con diferentes permisos
- Configurar mocks de autenticación
- Preparar payloads válidos e inválidos para diferentes escenarios

### Act
- Ejecutar peticiones POST al endpoint `/employees/{id_employee}/generate-otro-si/`
- Probar diferentes combinaciones de datos de entrada
- Simular diferentes estados de autenticación y autorización
- Probar casos de empleados inactivos y sin contratos activos
- Validar reglas de negocio complejas (pagos, deducciones, incrementos, fechas)

### Assert
- Verificar códigos de respuesta HTTP correctos
- Validar mensajes de error específicos
- Confirmar cambios en base de datos (contrato anterior finalizado, nuevo contrato creado con secundary_petition=True)
- Verificar creación de registros de auditoría (EmployeeNews con tipo GENERAR_OTRO_SI)
- Comprobar que no se realizan cambios cuando hay errores
- Validar reglas de negocio (validaciones de pagos según frecuencia, deducciones, incrementos, fechas)

## Resultado Esperado
Todas las pruebas deben pasar exitosamente, validando:
1. Generación exitosa con datos válidos (HTTP 200/201)
2. Rechazo de empleados inactivos (HTTP 400)
3. Rechazo de empleados sin contrato activo (HTTP 400)
4. Validación de campos obligatorios (HTTP 400)
5. Validación de valores negativos en campos numéricos (HTTP 400)
6. Validación de fechas del contrato y vacaciones acumulativas (HTTP 400)
7. Validación de contract_payments según payment_frequency_type (HTTP 400)
8. Validación de deducciones (valores negativos, porcentajes > 100, duplicados) (HTTP 400)
9. Validación de incrementos (valores negativos, porcentajes > 100, duplicados) (HTTP 400)
10. Control de longitud máxima de observación (HTTP 400/500)
11. Autenticación y autorización requeridas (HTTP 401/403)
12. Integridad y trazabilidad (novedad creada correctamente)

## Resultado Obtenido

### Casos de Prueba Ejecutados:

#### UT-EMP-006.1 - Generación exitosa de Otro Sí (camino feliz)
- **Estado**: ✅ PASÓ
- **Resultado**: HTTP 200/201, contrato anterior finalizado (estado 29), nuevo contrato creado con secundary_petition=True y estado Activo (28), novedad registrada con tipo GENERAR_OTRO_SI

#### UT-EMP-006.2 - Empleado inactivo (no se puede generar Otro Sí)
- **Estado**: ✅ PASÓ  
- **Resultado**: HTTP 400, mensaje "No se puede generar un Otro Si para un empleado inactivo", no se crea contrato nuevo, no se registra novedad

#### UT-EMP-006.3 - Empleado sin contrato activo
- **Estado**: ✅ PASÓ
- **Resultado**: HTTP 400, mensaje indicando que el último contrato está finalizado, contrato y empleado permanecen sin cambios

#### UT-EMP-006.4 - Campos obligatorios faltantes
- **Estado**: ✅ PASÓ
- **Resultado**: HTTP 400, errores de validación en campos obligatorios (observation, id_employee_charge, campos del contrato), sin cambios en BD

#### UT-EMP-006.5 - Valores negativos en campos numéricos
- **Estado**: ✅ PASÓ
- **Resultado**: HTTP 400, mensajes de validación para valores negativos en campos numéricos (minimum_hours, salary_base, trial_period_days, vacation_days, etc.), sin cambios en BD

#### UT-EMP-006.6 - Validaciones de fechas del contrato y vacaciones acumulativas
- **Estado**: ✅ PASÓ
- **Resultado**: HTTP 400, validación de end_date antes de start_date, validación de start_cumulative_vacation obligatorio cuando cumulative_vacation=True, validación de fechas fuera de rango del contrato

#### UT-EMP-006.7 - Validaciones de contract_payments según payment_frequency_type
- **Estado**: ✅ PASÓ
- **Resultado**: HTTP 400, validaciones correctas para:
  - Frecuencia diario: no debe tener id_day_of_week ni date_payment
  - Frecuencia semanal: debe tener id_day_of_week, no date_payment
  - Frecuencia mensual: date_payment entre 1 y 31, no id_day_of_week
  - Frecuencia quincenal: exactamente 2 registros con validaciones específicas

#### UT-EMP-006.8 - Validaciones de deducciones en el Otro Sí
- **Estado**: ✅ PASÓ
- **Resultado**: HTTP 400, validaciones correctas para:
  - amount_value negativo rechazado
  - amount_type="Porcentaje" con amount_value > 100 rechazado
  - Deducciones duplicadas con mismo deduction_type rechazadas

#### UT-EMP-006.9 - Validaciones de incrementos en el Otro Sí
- **Estado**: ✅ PASÓ
- **Resultado**: HTTP 400, validaciones correctas para:
  - amount_value negativo rechazado
  - amount_type="Porcentaje" con amount_value > 100 rechazado
  - Incrementos duplicados con mismo increase_type rechazados

#### UT-EMP-006.10 - Observación supera longitud máxima (255)
- **Estado**: ✅ PASÓ
- **Resultado**: HTTP 400/500 (error de validación), contrato y empleado permanecen sin cambios

#### UT-EMP-006.11 - Seguridad: Sin token / sin permiso 187
- **Estado**: ✅ PASÓ
- **Resultado**: 
  - Sin token: HTTP 401/403, sin cambios en BD
  - Con token sin permiso 187: HTTP 403, mensaje "No tiene permisos para generar otro si", sin cambios en BD

#### UT-EMP-006.12 - Integridad y trazabilidad (novedad creada correctamente)
- **Estado**: ✅ PASÓ
- **Resultado**: Novedad creada correctamente con:
  - id_employee correcto
  - Tipo de novedad = "GENERAR_OTRO_SI"
  - observation coincidente con el payload
  - Fecha/hora dentro del rango de ejecución
  - Referencia al nuevo contrato generado verificada

### Resumen de Ejecución:
```
======================== 12 passed, 1 warning in 25.02s =========================
```

## Estado
✅ **COMPLETADO EXITOSAMENTE**

Todas las 12 pruebas unitarias pasaron correctamente. El endpoint funciona según las especificaciones, validando correctamente la autenticación, autorización, formato de datos, reglas de negocio complejas (pagos según frecuencia, deducciones, incrementos, fechas) y registrando las novedades de auditoría. El proceso de generación de Otro Sí finaliza correctamente el contrato anterior y crea uno nuevo con el código incrementado y secundary_petition=True.

## Fecha Ejecución
22/11/2024

## Ejecutado por
Juan Camilo

---

## Notas Técnicas
- **Framework**: pytest con Django
- **Base de datos**: PostgreSQL (base de datos de prueba)
- **Autenticación**: JWT con mocks para pruebas
- **Cobertura**: 12 casos de prueba cubriendo todos los escenarios críticos
- **Tiempo de ejecución**: 25.02 segundos
- **Archivos**: `test/UT-EMP-006/test_UT_EMP_006.py`
- **Endpoint probado**: `POST /employees/{id_employee}/generate-otro-si/`
- **Permiso requerido**: 187 (employee.create_secundary_petition)

## Observaciones
1. El test de longitud máxima de observación puede devolver HTTP 400 (validación de serializer) o HTTP 500 (error de BD), dependiendo de dónde se capture la validación, lo cual es comportamiento esperado.
2. Sin token de autenticación devuelve HTTP 401 o HTTP 403, comportamiento consistente con la configuración del sistema de autenticación.
3. El endpoint valida correctamente que el empleado esté activo y tenga un contrato activo antes de permitir generar un Otro Sí.
4. El código del nuevo contrato se genera correctamente incrementando la versión (ej: CON-2025-0001-00 → CON-2025-0001-01).
5. El contrato anterior se finaliza automáticamente (estado 29) cuando se genera el Otro Sí exitosamente.
6. Las validaciones de contract_payments son muy específicas según el tipo de frecuencia (diario, semanal, mensual, quincenal) y funcionan correctamente.
7. Las validaciones de deducciones e incrementos incluyen verificación de valores negativos, porcentajes mayores a 100 y duplicados por tipo.
8. Las validaciones de fechas incluyen verificación de rangos válidos y obligatoriedad de start_cumulative_vacation cuando cumulative_vacation=True.
9. La novedad se registra siempre con el tipo "GENERAR_OTRO_SI" y la observación proporcionada en el payload.
10. Todas las validaciones de negocio funcionan correctamente y los cambios en base de datos se realizan dentro de transacciones atómicas.
11. El nuevo contrato creado tiene correctamente secundary_petition=True y contract_status=28 (Activo).
12. El start_date del nuevo contrato se toma automáticamente del último contrato del empleado, no se envía en el payload.

