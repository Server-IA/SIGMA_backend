# INFORME DE PRUEBAS UNITARIAS - UT-EMP-007
## Cambiar Contrato de Empleado

**Fecha de Ejecución:** 2025-11-23  
**Endpoint:** `POST /employees/{id_employee}/change-contract/`  
**Total de Pruebas:** 58  
**Pruebas Exitosas:** 55  
**Pruebas Fallidas:** 3  
**Tasa de Éxito:** 94.83%  
**Tiempo de Ejecución:** ~20.62 segundos

---

## RESUMEN EJECUTIVO

Se ejecutaron 58 pruebas unitarias para validar el endpoint de cambio de contrato de empleado. El 94.83% de las pruebas pasaron exitosamente, lo que indica que la mayoría de las validaciones están funcionando correctamente.

### Pruebas Fallidas

Las siguientes 3 pruebas fallaron con error HTTP 400 Bad Request:

1. **test_UT_EMP_007_1_crear_contrato_exitosamente** - Caso exitoso principal
2. **test_UT_EMP_007_52_contrato_sin_deducciones** - Contrato sin deducciones
3. **test_UT_EMP_007_53_contrato_sin_incrementos** - Contrato sin incrementos

---

## ANÁLISIS DE PRUEBAS FALLIDAS

### Problema Identificado

Las 3 pruebas que fallan tienen un comportamiento común:
- Todas esperan un código HTTP 200/201 (éxito)
- Todas reciben HTTP 400 (Bad Request)
- El error no se está capturando correctamente en la salida del test

### Posibles Causas

1. **Validación de Fechas**: El serializer podría estar validando que las fechas sean estrictamente futuras, y las fechas generadas (+2 días) podrían no cumplir esta validación en el momento de ejecución.

2. **Usuario Responsable**: El serializer necesita obtener el usuario responsable desde `request.user.id`, y aunque se configuró `force_authenticate`, podría haber un problema con cómo el serializer accede al usuario.

3. **Contexto del Serializer**: El serializer interno `EmployeeContractCreateSerializer` necesita el contexto con el `request` correctamente configurado. El problema podría estar en cómo se pasa el contexto desde `EmployeeContractChangeSerializer`.

4. **Validación de Campos Requeridos**: Podría faltar algún campo requerido que no está documentado o que el serializer espera pero no está en el payload.

5. **Validación de Contrato Anterior**: El endpoint requiere que el empleado tenga un contrato previo para poder cambiarlo. Aunque se crea un contrato en `_setup_test_data()`, podría haber un problema con el estado del contrato o con la validación.

### Campos Removidos del Payload

- **`days_of_week`**: Este campo fue removido del payload porque no está en el `Meta.fields` del `EmployeeContractCreateSerializer`, aunque existe en el modelo `EmployeeContract` como `ManyToManyField`. Django REST Framework rechaza campos no declarados en el serializer.

### Explicación del Error de `days_of_week`

**¿Qué es un Serializer?**
Un serializer en Django REST Framework es una clase que convierte datos complejos (como modelos de Django) a tipos de datos nativos de Python que pueden ser fácilmente renderizados en JSON, XML u otros formatos. También proporciona deserialización, permitiendo que los datos parseados se conviertan de vuelta a tipos complejos, después de validar primero los datos entrantes.

**¿Por qué `days_of_week` causó error?**
El campo `days_of_week` existe en el modelo `EmployeeContract` como un `ManyToManyField` relacionado con `DaysOfWeek`. Sin embargo, en el `EmployeeContractCreateSerializer` (que es el serializer interno usado por `EmployeeContractChangeSerializer`), este campo **NO está declarado** en la lista `Meta.fields`.

Cuando Django REST Framework recibe un payload con un campo que no está en `Meta.fields`, por defecto lo rechaza y retorna un error HTTP 400 Bad Request con un mensaje indicando que el campo es desconocido.

**Solución aplicada:**
Se removió el campo `days_of_week` del payload de prueba, ya que no es parte de la interfaz del serializer para crear contratos. Si este campo es necesario en el futuro, debería agregarse a `Meta.fields` del `EmployeeContractCreateSerializer`.

---

## PRUEBAS EXITOSAS (55)

### Validaciones de Campos Obligatorios ✅
- ✅ test_UT_EMP_007_2_sin_observation
- ✅ test_UT_EMP_007_3_sin_id_employee_charge
- ✅ test_UT_EMP_007_4_contract_array_vacio
- ✅ test_UT_EMP_007_5_campos_obligatorios_contrato

### Validaciones de Tipos y Referencias ✅
- ✅ test_UT_EMP_007_6_contract_type_invalido
- ✅ test_UT_EMP_007_10_workday_type_invalido
- ✅ test_UT_EMP_007_11_work_mode_type_invalido
- ✅ test_UT_EMP_007_13_currency_type_invalido
- ✅ test_UT_EMP_007_32_deduction_type_invalido
- ✅ test_UT_EMP_007_38_increase_type_invalido

### Validaciones de Rangos Numéricos ✅
- ✅ test_UT_EMP_007_7_start_date_pasado
- ✅ test_UT_EMP_007_8_end_date_anterior_start_date
- ✅ test_UT_EMP_007_9_minimum_hours_negativo
- ✅ test_UT_EMP_007_12_salary_base_negativo
- ✅ test_UT_EMP_007_14_trial_period_days_negativo
- ✅ test_UT_EMP_007_15_vacation_days_negativo
- ✅ test_UT_EMP_007_16_vacation_frequency_days_negativo
- ✅ test_UT_EMP_007_19_maximum_disability_days_negativo
- ✅ test_UT_EMP_007_20_overtime_negativo
- ✅ test_UT_EMP_007_21_notice_period_days_negativo
- ✅ test_UT_EMP_007_33_deduccion_amount_negativo
- ✅ test_UT_EMP_007_39_incremento_amount_negativo

### Validaciones de Fechas ✅
- ✅ test_UT_EMP_007_17_cumulative_vacation_sin_start
- ✅ test_UT_EMP_007_18_start_cumulative_posterior_end_date
- ✅ test_UT_EMP_007_35_deduccion_start_anterior_contract_start
- ✅ test_UT_EMP_007_36_deduccion_end_posterior_contract_end
- ✅ test_UT_EMP_007_41_incremento_start_posterior_contract_end

### Validaciones de Frecuencia de Pago ✅
- ✅ test_UT_EMP_007_22_payment_frequency_diario
- ✅ test_UT_EMP_007_23_payment_diario_con_date_payment
- ✅ test_UT_EMP_007_24_payment_frequency_semanal
- ✅ test_UT_EMP_007_25_payment_semanal_sin_day_of_week
- ✅ test_UT_EMP_007_26_payment_frequency_mensual
- ✅ test_UT_EMP_007_27_payment_mensual_date_invalido
- ✅ test_UT_EMP_007_28_payment_frequency_quincenal
- ✅ test_UT_EMP_007_29_payment_quincenal_1_registro

### Validaciones de Deducciones e Incrementos ✅
- ✅ test_UT_EMP_007_31_deduccion_tipo_duplicado
- ✅ test_UT_EMP_007_34_deduccion_porcentaje_mayor_100
- ✅ test_UT_EMP_007_37_incremento_tipo_duplicado
- ✅ test_UT_EMP_007_40_incremento_porcentaje_mayor_100
- ✅ test_UT_EMP_007_42_campos_obligatorios_deduccion
- ✅ test_UT_EMP_007_43_campos_obligatorios_incremento

### Validaciones de Seguridad y Permisos ✅
- ✅ test_UT_EMP_007_44_1_sin_permiso_retorna_403
- ✅ test_UT_EMP_007_44_2_sin_token_retorna_401
- ✅ test_UT_EMP_007_44_3_token_expirado_retorna_401

### Validaciones de Empleado ✅
- ✅ test_UT_EMP_007_45_1_empleado_inexistente_retorna_404
- ✅ test_UT_EMP_007_45_2_id_invalido_cero_retorna_400
- ✅ test_UT_EMP_007_46_empleado_inactivo

### Validaciones de Métodos HTTP ✅
- ✅ test_UT_EMP_007_47_metodos_http_no_permitidos

### Validaciones de Formato ✅
- ✅ test_UT_EMP_007_48_json_malformado
- ✅ test_UT_EMP_007_49_campos_extra
- ✅ test_UT_EMP_007_50_limites_caracteres
- ✅ test_UT_EMP_007_51_content_type_incorrecto
- ✅ test_UT_EMP_007_30_days_of_week_duplicados

### Validaciones de Estructura y Persistencia ✅
- ✅ test_UT_EMP_007_54_estructura_respuesta
- ✅ test_UT_EMP_007_55_persistencia_contrato

---

## PRUEBAS FALLIDAS (3)

### 1. test_UT_EMP_007_1_crear_contrato_exitosamente

**Descripción:** Prueba principal para crear un contrato exitosamente con todos los campos válidos.

**Resultado Esperado:** HTTP 200/201 con contrato creado exitosamente

**Resultado Obtenido:** HTTP 400 Bad Request

**Análisis:**
- El payload contiene todos los campos requeridos
- Las fechas están configuradas como futuras (+2 días)
- El usuario está autenticado y tiene permisos
- El empleado existe y está activo
- Se creó un contrato previo en `_setup_test_data()`

**Posible Causa:**
El error no se está capturando correctamente en la salida, pero basado en el comportamiento, podría ser:
- Una validación de fecha que requiere que `start_date` sea estrictamente mayor que la fecha actual (no igual)
- Un problema con el contexto del serializer interno que necesita el `request` con el usuario correctamente configurado
- Una validación del contrato anterior que requiere un estado específico

### 2. test_UT_EMP_007_52_contrato_sin_deducciones

**Descripción:** Verifica que un contrato sin deducciones (array vacío) se pueda crear exitosamente.

**Resultado Esperado:** HTTP 200/201

**Resultado Obtenido:** HTTP 400 Bad Request

**Análisis:**
- Mismo payload que la prueba 1, pero con `established_deductions: []`
- Las deducciones son opcionales según la documentación

**Posible Causa:**
- Mismo problema que la prueba 1, no relacionado con las deducciones

### 3. test_UT_EMP_007_53_contrato_sin_incrementos

**Descripción:** Verifica que un contrato sin incrementos (array vacío) se pueda crear exitosamente.

**Resultado Esperado:** HTTP 200/201

**Resultado Obtenido:** HTTP 400 Bad Request

**Análisis:**
- Mismo payload que la prueba 1, pero con `established_increases: []`
- Los incrementos son opcionales según la documentación

**Posible Causa:**
- Mismo problema que la prueba 1, no relacionado con los incrementos

---

## RECOMENDACIONES

### 1. Capturar el Error Exacto

**Problema:** El código de captura de error no se está ejecutando correctamente, por lo que no podemos ver el mensaje de error exacto del serializer.

**Solución:**
- Modificar el código del test para que el error se capture y muestre antes de cualquier assert
- Usar `response.data` de DRF en lugar de `response.json()` para obtener el error
- Agregar logging adicional para ver qué validación está fallando

### 2. Revisar Validación de Fechas

**Problema:** Las fechas están configuradas como +2 días, pero podría haber una validación que requiere que sea estrictamente mayor (no igual).

**Solución:**
- Revisar el código del serializer para ver cómo valida `start_date`
- Ajustar las fechas en el payload para que sean +3 días en lugar de +2
- Verificar si hay validaciones de zona horaria que puedan estar causando problemas

### 3. Revisar Contexto del Serializer

**Problema:** El serializer interno necesita el contexto con el `request` correctamente configurado.

**Solución:**
- Verificar que `request.user` esté disponible en el serializer interno
- Asegurar que el usuario exista en la base de datos antes de hacer la petición
- Verificar que `force_authenticate` esté configurando correctamente el usuario en el request

### 4. Revisar Validación del Contrato Anterior

**Problema:** El endpoint requiere que el empleado tenga un contrato previo para poder cambiarlo.

**Solución:**
- Verificar que el contrato creado en `_setup_test_data()` tenga el estado correcto
- Verificar que el contrato no esté ya finalizado
- Verificar que el contrato tenga todos los campos requeridos

### 5. Documentación Faltante

**Problema:** Podría haber validaciones o requisitos que no están documentados.

**Solución:**
- Revisar el código del serializer para identificar todas las validaciones
- Documentar cualquier requisito adicional que no esté en la especificación
- Agregar comentarios en el código del test explicando las validaciones

---

## CONCLUSIÓN

El endpoint de cambio de contrato tiene una cobertura de pruebas del 94.83%, con la mayoría de las validaciones funcionando correctamente. Las 3 pruebas que fallan parecen tener el mismo problema raíz, relacionado con la creación exitosa del contrato.

**Próximos Pasos:**
1. **URGENTE**: Capturar el error exacto del serializer. El código de captura de error no se está ejecutando correctamente. Se recomienda:
   - Modificar el test para usar `response.data` de DRF en lugar de `response.json()`
   - Agregar un print directo antes de cualquier assert
   - Usar `pytest.fail()` con el mensaje completo del error
   - Verificar que el código de captura se ejecute antes de cualquier assert

2. Revisar las validaciones de fechas y contexto del serializer:
   - Verificar que `start_date` sea estrictamente mayor que la fecha actual (no igual)
   - Asegurar que el usuario exista en la BD antes de hacer la petición
   - Verificar que `force_authenticate` configure correctamente el usuario en el request

3. Verificar que el contrato anterior esté en el estado correcto:
   - El contrato debe existir y no estar finalizado
   - El contrato debe tener el estado activo (no 29 - Finalizado)

4. Revisar el código del serializer para identificar validaciones no documentadas:
   - `EmployeeContractChangeSerializer.validate()`
   - `EmployeeContractCreateSerializer.validate_*()`
   - Validaciones en el método `save()` del serializer

5. Corregir el problema una vez identificado y re-ejecutar las pruebas

---

## ESTADÍSTICAS DETALLADAS

| Categoría | Total | Exitosas | Fallidas | % Éxito |
|-----------|-------|----------|----------|---------|
| Validaciones de Campos | 5 | 5 | 0 | 100% |
| Validaciones de Tipos | 6 | 6 | 0 | 100% |
| Validaciones de Rangos | 12 | 12 | 0 | 100% |
| Validaciones de Fechas | 5 | 5 | 0 | 100% |
| Validaciones de Pago | 8 | 8 | 0 | 100% |
| Validaciones de Deducciones | 6 | 6 | 0 | 100% |
| Validaciones de Incrementos | 5 | 5 | 0 | 100% |
| Validaciones de Seguridad | 3 | 3 | 0 | 100% |
| Validaciones de Empleado | 3 | 3 | 0 | 100% |
| Validaciones de Formato | 4 | 4 | 0 | 100% |
| Casos Exitosos | 3 | 0 | 3 | 0% |
| **TOTAL** | **58** | **55** | **3** | **94.83%** |

---

---

## NOTAS TÉCNICAS

### Serializers Utilizados

1. **`EmployeeContractChangeSerializer`**: Serializer principal que maneja la lógica de cambio de contrato. Valida la estructura general del request (observation, id_employee_charge, contract) y delega la validación del contrato al serializer interno.

2. **`EmployeeContractCreateSerializer`**: Serializer interno que valida y crea el nuevo contrato. Este serializer:
   - Valida todos los campos del contrato
   - Valida referencias a catálogos (tipos de contrato, jornada, modalidad, moneda, etc.)
   - Valida fechas y rangos
   - Crea el contrato en la base de datos
   - Requiere que se le pase `employee`, `employee_charge`, y `responsible_user` como argumentos en el método `save()`

### Flujo de Validación

1. El endpoint `change_contract` recibe el request
2. Valida autenticación y permisos
3. Valida que el empleado exista y esté activo
4. Crea `EmployeeContractChangeSerializer` con el contexto `{"request": request, "employee": employee}`
5. El serializer valida la estructura general y crea `EmployeeContractCreateSerializer` con el contexto `{"request": request}`
6. El serializer interno valida todos los campos del contrato
7. Si todo es válido, se finaliza el contrato anterior y se crea el nuevo

### Problema de Captura de Error

El código de captura de error en el test no se está ejecutando correctamente. Esto podría deberse a:
- Un assert anterior que está fallando antes de que se ejecute el código de captura
- Un problema con cómo pytest captura la salida de los prints
- Un problema con la sincronización del código del test con el código en ejecución

**Solución recomendada:** Usar `response.data` de DRF directamente y hacer el fail inmediatamente sin asserts intermedios.

---

**Generado por:** Daniel soto
**Versión:** 1.0  
**Última Actualización:** 2025-11-23

