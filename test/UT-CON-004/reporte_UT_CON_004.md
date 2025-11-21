# Reporte de Pruebas Unitarias - UT-CON-004

---

## **ID**
UT-CON-004

## **Título**
Verificar consulta de detalle de contrato preestablecido mediante endpoint GET

## **Descripción**
Se valida el funcionamiento completo del endpoint GET `/established_contracts/{contract_code}/detail/` que permite consultar el detalle de un contrato preestablecido, incluyendo generalidades, términos, deducciones e incrementos asociados. Se prueban diferentes escenarios de autenticación, autorización, existencia de datos y coherencia de información.

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
- Contratos de prueba creados:
  - CON-ENCARGADODEVENTAS-0003 (completo con deducciones/incrementos)
  - CON-AUXILIAR-0001 (sin deducciones/incrementos)
  - CON-OPERARIO-0002 (frecuencia semanal)
  - CON-TECNICO-0003 (términos completos)
  - CON-COMPLETO-0004 (integración completa)

## **Datos de Entrada**
- **Endpoint**: GET `/established_contracts/{contract_code}/detail/`
- **Tokens JWT**: Con permiso 175, sin permiso, inválidos, ausentes
- **Contract codes**: Existentes, no existentes, formato inválido
- **Headers**: Authorization Bearer, Content-Type application/json

## **Pasos (AAA)**

### **Arrange**
- Configurar cliente API de pruebas (APIClient)
- Crear mocks para autenticación JWT con diferentes payloads
- Establecer datos de prueba en base de datos
- Configurar tokens con diferentes niveles de permisos
- Preparar contratos con diferentes características

### **Act**
- Ejecutar peticiones GET al endpoint con diferentes parámetros
- Simular diferentes escenarios de autenticación
- Probar con contract_codes válidos e inválidos
- Enviar requests con y sin headers de autorización

### **Assert**
- Verificar códigos de estado HTTP correctos (200, 401, 403, 404)
- Validar estructura completa de respuesta JSON
- Comprobar tipos de datos específicos (int, float, bool, str, list)
- Verificar formatos de fecha (YYYY-MM-DD)
- Validar coherencia entre campos relacionados
- Confirmar mapeo 1:1 con pestañas de UI (HU-CON-005)

## **Resultado Esperado**

### **Casos de Éxito (200 OK)**
- Consulta exitosa con datos completos del contrato
- Estructura JSON con generalidades, términos, deducciones e incrementos
- Contratos sin deducciones/incrementos devuelven arrays vacíos
- Frecuencias de pago coherentes con datos de pagos
- Contratos inactivos consultables para auditoría

### **Casos de Error**
- **401 Unauthorized**: Sin token o token inválido
- **403 Forbidden**: Usuario sin permiso 175
- **404 Not Found**: Contract_code no existe o formato inválido

### **Validaciones Específicas**
- Campos de generalidades completos y correctos
- Términos del contrato coherentes entre sí
- Arrays de deducciones e incrementos con estructura completa
- Fechas en formato YYYY-MM-DD
- Tipos de datos correctos para cada campo

## **Resultado Obtenido**
✅ **TODAS LAS PRUEBAS PASARON EXITOSAMENTE**

**Resumen de Ejecución:**
- **Total de pruebas**: 11
- **Pruebas exitosas**: 11 ✅
- **Pruebas fallidas**: 0 ❌
- **Tiempo de ejecución**: ~7-9 segundos
- **Cobertura**: 100% de casos especificados

**Detalle por caso:**
1. ✅ Consulta exitosa (200 OK)
2. ✅ Usuario sin permiso (403 Forbidden)
3. ✅ Sin token de autenticación (401 Unauthorized)
4. ✅ Token inválido (401 Unauthorized)
5. ✅ Contrato no existe (404 Not Found)
6. ✅ Formato inválido (404 Not Found)
7. ✅ Sin deducciones/incrementos (200 OK)
8. ✅ Frecuencia semanal coherente (200 OK)
9. ✅ Términos coherentes (200 OK)
10. ✅ Contrato inactivo consultable (200 OK)
11. ✅ Estructura completa para UI (200 OK)

**Correcciones Aplicadas:**
- Ajuste en validación de mensajes de error (detail vs message)
- Uso de jwt.InvalidTokenError específica para tokens inválidos

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
docker-compose exec web python -m pytest test/UT-CON-004/test_UT_CON_004.py -v

# Ejecutar prueba específica
docker-compose exec web python -m pytest test/UT-CON-004/test_UT_CON_004.py::TestEstablishedContractDetail::test_ut_con_005_1_successful_contract_retrieval -v

# Ejecutar con cobertura
docker-compose exec web python -m pytest test/UT-CON-004/test_UT_CON_004.py --cov=payroll.api.established_contract_viewset --cov-report=html
```

## **Tecnologías Utilizadas**
- **Framework**: pytest + Django REST Framework
- **Mocking**: unittest.mock para autenticación JWT
- **Base de datos**: PostgreSQL (conexión real)
- **Patrones**: AAA (Arrange-Act-Assert), Factory Pattern
- **Validaciones**: Códigos HTTP, estructura JSON, tipos de datos

## **Observaciones**
- El endpoint está completamente funcional y listo para producción
- La estructura de respuesta es coherente con los requisitos de UI
- Las validaciones de seguridad funcionan correctamente
- Los datos se serializan apropiadamente
- La API cumple con todos los requisitos de la HU-CON-005
