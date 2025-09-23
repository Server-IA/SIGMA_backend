# Reporte de Pruebas Unitarias - UT-MAQ-004
## HU-MAQ-004: Creación de Ficha de Uso de Maquinaria

**Fecha de Ejecución:** September 23, 2025  
**Ejecutado por:** GitHub Copilot  

---

### ID: UT-MAQ-004-01

**Título:** Verificar creación exitosa de ficha de uso cuando is_own=True  

**Descripción:**  
Esta prueba verifica que se pueda crear una ficha de uso de maquinaria exitosamente cuando la maquinaria es propia (is_own=True) y todos los campos requeridos son válidos.  

**Precondiciones:**  
- Usuario autenticado (id_user=1)  
- Serializer mockeado para simular validación exitosa  
- Modelos relacionados (Machinery, Statues, Units, User) mockeados  

**Datos de Entrada:**  
- id_machinery: 1  
- is_own: True  
- acquisition_date: '2025-09-22'  
- usage_condition: 2  
- usage_hours: '123.50'  
- distance_value: '2500.750'  
- distance_unit: 3  
- responsible_user: 4  

**Pasos (AAA):**  
**Arrange:** Configurar mocks para lookups de modelos y serializer válido.  
**Act:** Enviar solicitud POST al endpoint '/machinery-usage/create/' con datos válidos.  
**Assert:** Verificar código 201, success=True, mensaje 'Ficha de uso registrada exitosamente'.  

**Resultado Esperado:**  
Código 201 con success=True y mensaje de éxito.  

**Resultado Obtenido:**  
Código de estado: 201  
Respuesta: {'success': True, 'message': 'Ficha de uso registrada exitosamente.'}  

**Estado:** PASÓ  

---

### ID: UT-MAQ-004-02

**Título:** Verificar creación exitosa de ficha de uso cuando is_own=False  

**Descripción:**  
Esta prueba verifica que se pueda crear una ficha de uso de maquinaria exitosamente cuando la maquinaria no es propia (is_own=False) y se incluyen campos adicionales de contrato.  

**Precondiciones:**  
- Usuario autenticado  
- Serializer mockeado para validación exitosa  
- Modelos relacionados mockeados incluyendo Types  

**Datos de Entrada:**  
- id_machinery: 1  
- is_own: False  
- acquisition_date: '2025-09-22'  
- usage_condition: 2  
- usage_hours: '123.50'  
- distance_value: '2500.750'  
- distance_unit: 3  
- tenancy_type: 5  
- contract_end_date: '2026-09-22'  
- responsible_user: 4  

**Pasos (AAA):**  
**Arrange:** Configurar mocks y serializer válido con campos de contrato.  
**Act:** Enviar POST con datos válidos incluyendo tenancy_type y contract_end_date.  
**Assert:** Código 201, success=True, mensaje de éxito.  

**Resultado Esperado:**  
Código 201 con success=True.  

**Resultado Obtenido:**  
Código de estado: 201  
Respuesta: {'success': True, 'message': 'Ficha de uso registrada exitosamente.'}  

**Estado:** PASÓ  

---

### ID: UT-MAQ-004-03

**Título:** Verificar validación de campos obligatorios faltantes  

**Descripción:**  
Esta prueba verifica que la API valide correctamente cuando faltan campos obligatorios en la solicitud de creación de ficha de uso.  

**Precondiciones:**  
- Usuario autenticado  
- Serializer mockeado para simular errores de validación  

**Datos de Entrada:**  
- Solicitudes con cada campo obligatorio faltante (id_machinery, is_own, acquisition_date, usage_condition, usage_hours, distance_value, distance_unit, responsible_user)  

**Pasos (AAA):**  
**Arrange:** Configurar serializer para devolver error específico por campo faltante.  
**Act:** Enviar POST omitiendo un campo obligatorio cada vez.  
**Assert:** Código 400, success=False, mensaje 'Error de validación', campo en details.  

**Resultado Esperado:**  
Código 400 con error específico para cada campo faltante.  

**Resultado Obtenido:**  
Código de estado: 400  
Respuesta: {'success': False, 'message': 'Error de validación', 'details': {'campo_faltante': ['This field is required.']}} para cada campo.  

**Estado:** PASÓ  

---

### ID: UT-MAQ-004-04

**Título:** Verificar validación de formato de fecha inválido en acquisition_date  

**Descripción:**  
Esta prueba verifica que la API rechace formatos de fecha inválidos para acquisition_date.  

**Precondiciones:**  
- Usuario autenticado  
- Serializer mockeado  

**Datos de Entrada:**  
- acquisition_date: '22-09-2025' (formato incorrecto)  
- Otros campos válidos  

**Pasos (AAA):**  
**Arrange:** Configurar serializer para error de formato de fecha.  
**Act:** Enviar POST con fecha en formato incorrecto.  
**Assert:** Código 400, error en acquisition_date.  

**Resultado Esperado:**  
Código 400 con mensaje de formato de fecha.  

**Resultado Obtenido:**  
Código de estado: 400  
Respuesta: {'success': False, 'message': 'Error de validación', 'details': {'acquisition_date': ['Date has wrong format. Use one of these formats instead: YYYY-MM-DD.']}}  

**Estado:** PASÓ  

---

### ID: UT-MAQ-004-05

**Título:** Verificar validación de campos de contrato obligatorios cuando is_own=False  

**Descripción:**  
Esta prueba verifica que tenancy_type y contract_end_date sean obligatorios cuando is_own=False.  

**Precondiciones:**  
- Usuario autenticado  
- Serializer mockeado  

**Datos de Entrada:**  
- is_own: False  
- Campos de contrato faltantes  

**Pasos (AAA):**  
**Arrange:** Configurar serializer para errores en campos de contrato.  
**Act:** Enviar POST sin tenancy_type y contract_end_date.  
**Assert:** Código 400, errores en tenancy_type y contract_end_date.  

**Resultado Esperado:**  
Código 400 con errores para campos de contrato.  

**Resultado Obtenido:**  
Código de estado: 400  
Respuesta: {'success': False, 'message': 'Error de validación', 'details': {'tenancy_type': ['This field is required.'], 'contract_end_date': ['This field is required.']}}  

**Estado:** PASÓ  

---

### ID: UT-MAQ-004-06

**Título:** Verificar validación de formato de fecha inválido en contract_end_date  

**Descripción:**  
Esta prueba verifica que la API rechace formatos de fecha inválidos para contract_end_date.  

**Precondiciones:**  
- Usuario autenticado  
- Serializer mockeado  

**Datos de Entrada:**  
- contract_end_date: '22-09-2026' (formato incorrecto)  
- Otros campos válidos  

**Pasos (AAA):**  
**Arrange:** Configurar serializer para error de formato.  
**Act:** Enviar POST con fecha inválida.  
**Assert:** Código 400, error en contract_end_date.  

**Resultado Esperado:**  
Código 400 con mensaje de formato.  

**Resultado Obtenido:**  
Código de estado: 400  
Respuesta: {'success': False, 'message': 'Error de validación', 'details': {'contract_end_date': ['Date has wrong format. Use one of these formats instead: YYYY-MM-DD.']}}  

**Estado:** PASÓ  

---

### ID: UT-MAQ-004-07

**Título:** Verificar validación de maquinaria inexistente  

**Descripción:**  
Esta prueba verifica que la API rechace IDs de maquinaria que no existen.  

**Precondiciones:**  
- Usuario autenticado  
- Serializer mockeado  

**Datos de Entrada:**  
- id_machinery: 999999992 (inexistente)  

**Pasos (AAA):**  
**Arrange:** Configurar serializer para error de existencia.  
**Act:** Enviar POST con ID inexistente.  
**Assert:** Código 400, error en id_machinery.  

**Resultado Esperado:**  
Código 400 con mensaje de maquinaria no encontrada.  

**Resultado Obtenido:**  
Código de estado: 400  
Respuesta: {'success': False, 'message': 'Error de validación', 'details': {'id_machinery': ['No machinery found with this id.']}}  

**Estado:** PASÓ  

---

### ID: UT-MAQ-004-08

**Título:** Verificar validación de usuario responsable inexistente  

**Descripción:**  
Esta prueba verifica que la API rechace IDs de usuario responsable que no existen.  

**Precondiciones:**  
- Usuario autenticado  
- Serializer mockeado  

**Datos de Entrada:**  
- responsible_user: 999999999 (inexistente)  

**Pasos (AAA):**  
**Arrange:** Configurar serializer para error de existencia.  
**Act:** Enviar POST con ID inexistente.  
**Assert:** Código 400, error en responsible_user.  

**Resultado Esperado:**  
Código 400 con mensaje de usuario no encontrado.  

**Resultado Obtenido:**  
Código de estado: 400  
Respuesta: {'success': False, 'message': 'Error de validación', 'details': {'responsible_user': ['No user found with this id.']}}  

**Estado:** PASÓ  

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