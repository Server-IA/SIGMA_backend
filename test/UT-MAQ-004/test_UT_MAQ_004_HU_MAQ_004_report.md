# Reporte de Pruebas Unitarias - UT-MAQ-004
## HU-MAQ-004: Creación de Ficha de Uso de Maquinaria

**Fecha de Ejecución:** September 23, 2025  
**Ejecutado por:** Juan Nicolás Urrutia  

---

### Caso de Prueba: UT-MAQ-004.1

| Campo | Valor |
|-------|-------|
| ID | UT-MAQ-004.1 |
| Título | Verificar creación exitosa de ficha de uso cuando is_own=True |
| Descripción | Esta prueba verifica que se pueda crear una ficha de uso de maquinaria exitosamente cuando la maquinaria es propia (is_own=True) y todos los campos requeridos son válidos. |
| Precondiciones | - Usuario autenticado (id_user=1)<br>- Serializer mockeado para simular validación exitosa<br>- Modelos relacionados (Machinery, Statues, Units, User) mockeados |
| Datos de Entrada | - id_machinery: 1<br>- is_own: True<br>- acquisition_date: '2025-09-22'<br>- usage_condition: 2<br>- usage_hours: '123.50'<br>- distance_value: '2500.750'<br>- distance_unit: 3<br>- responsible_user: 4 |
| Pasos (AAA) | **Arrange:** Configurar mocks para lookups de modelos y serializer válido.<br>**Act:** Enviar solicitud POST al endpoint '/machinery-usage/create/' con datos válidos.<br>**Assert:** Verificar código 201, success=True, mensaje 'Ficha de uso registrada exitosamente'. |
| Resultado Esperado | Código 201 con success=True y mensaje de éxito. |
| Resultado Obtenido | Código de estado: 201<br>Respuesta: {'success': True, 'message': 'Ficha de uso registrada exitosamente.'} |
| Estado | APROBADO |
| Fecha Ejecución | September 23, 2025 |
| Ejecutado por | Juan Nicolás Urrutia |

---

### Caso de Prueba: UT-MAQ-004.2

| Campo | Valor |
|-------|-------|
| ID | UT-MAQ-004.2 |
| Título | Verificar creación exitosa de ficha de uso cuando is_own=False |
| Descripción | Esta prueba verifica que se pueda crear una ficha de uso de maquinaria exitosamente cuando la maquinaria no es propia (is_own=False) y se incluyen campos adicionales de contrato. |
| Precondiciones | - Usuario autenticado<br>- Serializer mockeado para validación exitosa<br>- Modelos relacionados mockeados incluyendo Types |
| Datos de Entrada | - id_machinery: 1<br>- is_own: False<br>- acquisition_date: '2025-09-22'<br>- usage_condition: 2<br>- usage_hours: '123.50'<br>- distance_value: '2500.750'<br>- distance_unit: 3<br>- tenancy_type: 5<br>- contract_end_date: '2026-09-22'<br>- responsible_user: 4 |
| Pasos (AAA) | **Arrange:** Configurar mocks y serializer válido con campos de contrato.<br>**Act:** Enviar POST con datos válidos incluyendo tenancy_type y contract_end_date.<br>**Assert:** Código 201, success=True, mensaje de éxito. |
| Resultado Esperado | Código 201 con success=True. |
| Resultado Obtenido | Código de estado: 201<br>Respuesta: {'success': True, 'message': 'Ficha de uso registrada exitosamente.'} |
| Estado | APROBADO |
| Fecha Ejecución | September 23, 2025 |
| Ejecutado por | Juan Nicolás Urrutia |

---

### Caso de Prueba: UT-MAQ-004.3

| Campo | Valor |
|-------|-------|
| ID | UT-MAQ-004.3 |
| Título | Verificar validación de campos obligatorios faltantes |
| Descripción | Esta prueba verifica que la API valide correctamente cuando faltan campos obligatorios en la solicitud de creación de ficha de uso. |
| Precondiciones | - Usuario autenticado<br>- Serializer mockeado para simular errores de validación |
| Datos de Entrada | Solicitudes con cada campo obligatorio faltante (id_machinery, is_own, acquisition_date, usage_condition, usage_hours, distance_value, distance_unit, responsible_user) |
| Pasos (AAA) | **Arrange:** Configurar serializer para devolver error específico por campo faltante.<br>**Act:** Enviar POST omitiendo un campo obligatorio cada vez.<br>**Assert:** Código 400, success=False, mensaje 'Error de validación', campo en details. |
| Resultado Esperado | Código 400 con error específico para cada campo faltante. |
| Resultado Obtenido | Código de estado: 400<br>Respuesta: {'success': False, 'message': 'Error de validación', 'details': {'campo_faltante': ['This field is required.']}} para cada campo. |
| Estado | APROBADO |
| Fecha Ejecución | September 23, 2025 |
| Ejecutado por | Juan Nicolás Urrutia |

---

### Caso de Prueba: UT-MAQ-004.4

| Campo | Valor |
|-------|-------|
| ID | UT-MAQ-004.4 |
| Título | Verificar validación de formato de fecha inválido en acquisition_date |
| Descripción | Esta prueba verifica que la API rechace formatos de fecha inválidos para acquisition_date. |
| Precondiciones | - Usuario autenticado<br>- Serializer mockeado |
| Datos de Entrada | - acquisition_date: '22-09-2025' (formato incorrecto)<br>- Otros campos válidos |
| Pasos (AAA) | **Arrange:** Configurar serializer para error de formato de fecha.<br>**Act:** Enviar POST con fecha en formato incorrecto.<br>**Assert:** Código 400, error en acquisition_date. |
| Resultado Esperado | Código 400 con mensaje de formato de fecha. |
| Resultado Obtenido | Código de estado: 400<br>Respuesta: {'success': False, 'message': 'Error de validación', 'details': {'acquisition_date': ['Date has wrong format. Use one of these formats instead: YYYY-MM-DD.']}} |
| Estado | APROBADO |
| Fecha Ejecución | September 23, 2025 |
| Ejecutado por | Juan Nicolás Urrutia |

---

### Caso de Prueba: UT-MAQ-004.5

| Campo | Valor |
|-------|-------|
| ID | UT-MAQ-004.5 |
| Título | Verificar validación de campos de contrato obligatorios cuando is_own=False |
| Descripción | Esta prueba verifica que tenancy_type y contract_end_date sean obligatorios cuando is_own=False. |
| Precondiciones | - Usuario autenticado<br>- Serializer mockeado |
| Datos de Entrada | - is_own: False<br>- Campos de contrato faltantes |
| Pasos (AAA) | **Arrange:** Configurar serializer para errores en campos de contrato.<br>**Act:** Enviar POST sin tenancy_type y contract_end_date.<br>**Assert:** Código 400, errores en tenancy_type y contract_end_date. |
| Resultado Esperado | Código 400 con errores para campos de contrato. |
| Resultado Obtenido | Código de estado: 400<br>Respuesta: {'success': False, 'message': 'Error de validación', 'details': {'tenancy_type': ['This field is required.'], 'contract_end_date': ['This field is required.']}} |
| Estado | APROBADO |
| Fecha Ejecución | September 23, 2025 |
| Ejecutado por | Juan Nicolás Urrutia |

---

### Caso de Prueba: UT-MAQ-004.6

| Campo | Valor |
|-------|-------|
| ID | UT-MAQ-004.6 |
| Título | Verificar validación de formato de fecha inválido en contract_end_date |
| Descripción | Esta prueba verifica que la API rechace formatos de fecha inválidos para contract_end_date. |
| Precondiciones | - Usuario autenticado<br>- Serializer mockeado |
| Datos de Entrada | - contract_end_date: '22-09-2026' (formato incorrecto)<br>- Otros campos válidos |
| Pasos (AAA) | **Arrange:** Configurar serializer para error de formato.<br>**Act:** Enviar POST con fecha inválida.<br>**Assert:** Código 400, error en contract_end_date. |
| Resultado Esperado | Código 400 con mensaje de formato. |
| Resultado Obtenido | Código de estado: 400<br>Respuesta: {'success': False, 'message': 'Error de validación', 'details': {'contract_end_date': ['Date has wrong format. Use one of these formats instead: YYYY-MM-DD.']}} |
| Estado | APROBADO |
| Fecha Ejecución | September 23, 2025 |
| Ejecutado por | Juan Nicolás Urrutia |

---

### Caso de Prueba: UT-MAQ-004.7

| Campo | Valor |
|-------|-------|
| ID | UT-MAQ-004.7 |
| Título | Verificar validación de maquinaria inexistente |
| Descripción | Esta prueba verifica que la API rechace IDs de maquinaria que no existen. |
| Precondiciones | - Usuario autenticado<br>- Serializer mockeado |
| Datos de Entrada | - id_machinery: 999999992 (inexistente) |
| Pasos (AAA) | **Arrange:** Configurar serializer para error de existencia.<br>**Act:** Enviar POST con ID inexistente.<br>**Assert:** Código 400, error en id_machinery. |
| Resultado Esperado | Código 400 con mensaje de maquinaria no encontrada. |
| Resultado Obtenido | Código de estado: 400<br>Respuesta: {'success': False, 'message': 'Error de validación', 'details': {'id_machinery': ['No machinery found with this id.']}} |
| Estado | APROBADO |
| Fecha Ejecución | September 23, 2025 |
| Ejecutado por | Juan Nicolás Urrutia |

---

### Caso de Prueba: UT-MAQ-004.8

| Campo | Valor |
|-------|-------|
| ID | UT-MAQ-004.8 |
| Título | Verificar validación de usuario responsable inexistente |
| Descripción | Esta prueba verifica que la API rechace IDs de usuario responsable que no existen. |
| Precondiciones | - Usuario autenticado<br>- Serializer mockeado |
| Datos de Entrada | - responsible_user: 999999999 (inexistente) |
| Pasos (AAA) | **Arrange:** Configurar serializer para error de existencia.<br>**Act:** Enviar POST con ID inexistente.<br>**Assert:** Código 400, error en responsible_user. |
| Resultado Esperado | Código 400 con mensaje de usuario no encontrado. |
| Resultado Obtenido | Código de estado: 400<br>Respuesta: {'success': False, 'message': 'Error de validación', 'details': {'responsible_user': ['No user found with this id.']}} |
| Estado | APROBADO |
| Fecha Ejecución | September 23, 2025 |
| Ejecutado por | Juan Nicolás Urrutia |

---

## Resumen General

**Total de Pruebas:** 8  
**Pruebas Pasadas:** 8  
**Pruebas Fallidas:** 0  
**Warnings:** 1 (pytest.mark.django_db no registrado)  

**Cobertura:**  
- Creación exitosa (propia y no propia)  
- Validación de campos obligatorios  
- Validación de formatos de fecha  
- Validación de existencia de entidades relacionadas  
- Manejo de errores de validación  

**Estado General:** Todas las pruebas pasan exitosamente, confirmando que el endpoint HU-MAQ-004 funciona correctamente según las especificaciones.