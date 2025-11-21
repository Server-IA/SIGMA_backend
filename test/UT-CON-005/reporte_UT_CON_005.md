# Reporte de Pruebas Unitarias - UT-CON-005

---

## **ID**
UT-CON-005

## **Título**
Verificar actualización de contrato preestablecido mediante endpoint PUT

## **Descripción**
Se valida el funcionamiento completo del endpoint PUT `/established_contracts/{contract_code}/update_established_contract/` que permite actualizar un contrato preestablecido existente, incluyendo generalidades, términos, pagos, deducciones e incrementos asociados. Se prueban diferentes escenarios de validación de datos, autenticación, autorización, existencia de contratos y coherencia de información.

## **Precondiciones**
- Contenedor Docker ejecutándose con la aplicación Django
- Base de datos PostgreSQL disponible y configurada
- Usuario de prueba creado con ID 1
- Parametrización completa en base de datos:
  - Estados: Activo (ID 1), Inactivo (ID 2)
  - Tipos de contrato (categoría 15), jornada (16), modalidad (17)
  - Tipos de deducciones (18) e incrementos (19)
  - Moneda COP (ID 17)
  - Cargo de empleado: Encargado de Ventas (ID 1)
  - Días de la semana configurados
- Contrato base para actualizaciones:
  - CON-ENCARGADODEVENTAS-0012 (contrato objetivo para todas las pruebas)

## **Datos de Entrada**
- **Endpoint**: PUT `/established_contracts/{contract_code}/update_established_contract/`
- **Tokens JWT**: Con permiso 176, sin permiso, inválidos, ausentes
- **Contract codes**: Existentes, no existentes
- **Headers**: Authorization Bearer, Content-Type application/json
- **Payloads**: Datos válidos e inválidos para diferentes frecuencias de pago

## **Pasos (AAA)**

### **Arrange**
- Configurar cliente API de pruebas (APIClient)
- Crear mocks para autenticación JWT con diferentes payloads
- Establecer datos de prueba en base de datos
- Configurar tokens con diferentes niveles de permisos
- Preparar payloads válidos para diferentes frecuencias de pago
- Crear contrato base para actualizaciones

### **Act**
- Ejecutar peticiones PUT al endpoint con diferentes payloads
- Simular diferentes escenarios de autenticación
- Probar con datos válidos e inválidos
- Enviar requests con y sin headers de autorización
- Validar diferentes tipos de errores de validación

### **Assert**
- Verificar códigos de estado HTTP correctos (200, 400, 401, 403, 404)
- Validar estructura de respuesta JSON para éxitos y errores
- Comprobar que los datos se actualicen correctamente en base de datos
- Verificar mensajes de error específicos para cada validación
- Confirmar que no se modifiquen campos de solo lectura
- Validar transaccionalidad de las operaciones

## **Resultado Esperado**

### **Casos de Éxito (200 OK)**
- Actualización exitosa con pago quincenal (camino feliz)
- Actualización exitosa con pago diario/semanal/mensual
- Respuesta con mensaje de éxito y contract_code actualizado
- Datos persistidos correctamente en base de datos

### **Casos de Error (400 Bad Request)**
- Campos obligatorios faltantes
- Valores negativos o fuera de rango
- Fechas inválidas (start_date >= end_date)
- Validaciones específicas de vacaciones acumulativas
- Validaciones de pagos según frecuencia
- Validaciones de deducciones e incrementos
- Tipos parametrizados incorrectos

### **Casos de Seguridad y Existencia**
- **401 Unauthorized**: Sin token o token inválido
- **403 Forbidden**: Usuario sin permiso 176
- **404 Not Found**: Contract_code no existe

## **Resultado Obtenido**
✅ **TODAS LAS PRUEBAS PASARON EXITOSAMENTE**

**Resumen de Ejecución:**
- **Total de pruebas**: 14
- **Pruebas exitosas**: 14 ✅
- **Pruebas fallidas**: 0 ❌
- **Tiempo de ejecución**: ~12-13 segundos
- **Cobertura**: 100% de casos especificados

**Detalle por caso:**
1. ✅ Actualización exitosa quincenal (200 OK)
2. ✅ Actualización exitosa diario/semanal/mensual (200 OK)
3. ✅ Campos obligatorios faltantes (400 Bad Request)
4. ✅ Valores negativos/inválidos (400 Bad Request)
5. ✅ Validación de fechas (400 Bad Request)
6. ✅ Validación vacaciones acumulativas (400 Bad Request)
7. ✅ Validación pagos diario/semanal/mensual (400 Bad Request)
8. ✅ Validación pagos quincenales (400 Bad Request)
9. ✅ Validación deducciones (400 Bad Request)
10. ✅ Validación incrementos (400 Bad Request)
11. ✅ Validación tipos parametrizados (400 Bad Request)
12. ✅ Sin token de autenticación (401 Unauthorized)
13. ✅ Usuario sin permiso (403 Forbidden)
14. ✅ Contrato no existe (404 Not Found)

**Correcciones Aplicadas:**
- Ajuste en validación de mensajes de error de autenticación (detail vs message)

## **Estado**
✅ **APROBADO** - Todas las pruebas ejecutadas exitosamente

## **Fecha Ejecución**
18/11/2025

## **Ejecutado por**
Juan Camilo

---

## **Comandos de Ejecución**

```bash
# Ejecutar todas las pruebas
docker-compose exec web python -m pytest test/UT-CON-005/test_UT_CON_005.py -v

# Ejecutar prueba específica
docker-compose exec web python -m pytest test/UT-CON-005/test_UT_CON_005.py::TestEstablishedContractUpdate::test_ut_con_005_1_successful_quincenal_update -v

# Ejecutar con cobertura
docker-compose exec web python -m pytest test/UT-CON-005/test_UT_CON_005.py --cov=payroll.api.established_contract_viewset --cov-report=html
```

## **Tecnologías Utilizadas**
- **Framework**: pytest + Django REST Framework
- **Mocking**: unittest.mock para autenticación JWT
- **Base de datos**: PostgreSQL (conexión real)
- **Patrones**: AAA (Arrange-Act-Assert), Factory Pattern
- **Validaciones**: Códigos HTTP, estructura JSON, validaciones de negocio
- **Transacciones**: Django atomic transactions para integridad de datos

## **Casos de Prueba Detallados**

### **UT-CON-005.1 - Actualización Exitosa Quincenal**
- **Descripción**: Verificar actualización completa con frecuencia quincenal
- **Datos**: Payload completo con deducciones e incrementos
- **Resultado**: 200 OK, datos actualizados correctamente

### **UT-CON-005.2 - Actualización Exitosa Otras Frecuencias**
- **Descripción**: Verificar actualización con frecuencias diaria, semanal y mensual
- **Datos**: Payloads específicos para cada frecuencia
- **Resultado**: 200 OK, validaciones específicas por frecuencia

### **UT-CON-005.3 - Campos Obligatorios**
- **Descripción**: Validar error cuando faltan campos requeridos
- **Datos**: Payload sin campos obligatorios
- **Resultado**: 400 Bad Request con errores específicos

### **UT-CON-005.4 - Valores Negativos**
- **Descripción**: Validar rechazo de valores negativos o inválidos
- **Datos**: Salarios, porcentajes y montos negativos
- **Resultado**: 400 Bad Request con mensajes de validación

### **UT-CON-005.5 - Validación de Fechas**
- **Descripción**: Verificar coherencia entre start_date y end_date
- **Datos**: Fechas inválidas (inicio >= fin)
- **Resultado**: 400 Bad Request con error de fechas

### **UT-CON-005.6 - Vacaciones Acumulativas**
- **Descripción**: Validar rangos de días de vacaciones
- **Datos**: Valores fuera del rango permitido (0-365)
- **Resultado**: 400 Bad Request con error específico

### **UT-CON-005.7-8 - Validaciones de Pagos**
- **Descripción**: Verificar validaciones específicas por frecuencia de pago
- **Datos**: Configuraciones inválidas para cada frecuencia
- **Resultado**: 400 Bad Request con errores de coherencia

### **UT-CON-005.9-10 - Deducciones e Incrementos**
- **Descripción**: Validar reglas de negocio para deducciones e incrementos
- **Datos**: Tipos duplicados, fechas incoherentes, montos inválidos
- **Resultado**: 400 Bad Request con errores específicos

### **UT-CON-005.11 - Tipos Parametrizados**
- **Descripción**: Verificar validación de tipos de categorías específicas
- **Datos**: IDs de tipos incorrectos para cada categoría
- **Resultado**: 400 Bad Request con errores de categorización

### **UT-CON-005.12 - Seguridad y Existencia**
- **Descripción**: Validar autenticación, autorización y existencia
- **Datos**: Tokens inválidos, usuarios sin permiso, contratos inexistentes
- **Resultado**: 401, 403, 404 según corresponda

## **Observaciones**
- El endpoint está completamente funcional y listo para producción
- Las validaciones de negocio funcionan correctamente
- Las validaciones de seguridad están implementadas apropiadamente
- La transaccionalidad garantiza integridad de datos
- Los mensajes de error son informativos y específicos
- La API cumple con todos los requisitos de actualización de contratos
- El serializer maneja correctamente las relaciones anidadas
- Los campos de solo lectura están protegidos adecuadamente
