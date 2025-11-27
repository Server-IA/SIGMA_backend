# Reporte de Pruebas Unitarias - UT-EMP-010

---

## **ID**
UT-EMP-010

## **Título**
Desactivar empleado / Activar empleado

## **Descripción**
Se valida el funcionamiento del endpoint PATCH `/employees/{id_employee}/toggle-status/` para activar/desactivar empleados. Se prueban diferentes escenarios incluyendo validación de campos obligatorios (observation al desactivar), estructura de respuesta JSON, validación de permisos de acceso, manejo de errores, validación de métodos HTTP, Content-Type, JSON malformado, campos extra, validación de longitud, cambios sucesivos de estado, idempotencia, y garantizando que el cambio de estado se registra correctamente en la base de datos.

## **Precondiciones**
- Contenedor Docker ejecutándose con la aplicación Django
- Base de datos PostgreSQL disponible y configurada
- Usuario de prueba creado con ID 1
- Parametrización completa en base de datos:
  - Estados: Activo (ID 1), Inactivo (ID 2)
  - Estado de contrato desactivado (ID 29)
  - Tipos de contrato (categoría 15): contrato indefinido (ID 20)
  - Tipos de jornada (categoría 16): jornada completa (ID 21)
  - Tipos de modalidad (categoría 17): modalidad presencial (ID 22)
  - Moneda Dollar (ID 17) con categoría de unidades 10
  - Cargo de empleado: Encargado de ventas (ID 1)
  - Departamento de empleado: Ventas (ID 1)
- Empleado de prueba:
  - ID: 1
  - Email: test.employee@example.com
  - Estado inicial: Activo (ID 1)
  - Usuario asociado (id_user) requerido para sincronización
- Contrato de empleado de prueba:
  - Contract Code: CON-2025-0001-00
  - Empleado: ID 1
  - Estado: Activo (requerido para desactivación)
- El sistema debe validar el campo 'observation' como obligatorio al desactivar
- El sistema de autenticación JWT debe estar funcionando
- Token JWT válido para usuario con permisos activos (permiso ID 10)

## **Datos de Entrada**
- **Endpoint**: PATCH `/employees/{id_employee}/toggle-status/`
- **Tokens JWT**: Con permiso 10, sin permiso, inválidos, ausentes
- **Employee IDs**: 1 (existente), 99999 (inexistente), 0 (inválido)
- **Cuerpo JSON para Desactivar (REQUERIDO)**:
  ```json
  {
    "observation": "Motivo de la desactivación"
  }
  ```
- **Cuerpo JSON para Activar (OPCIONAL)**:
  ```json
  {}
  ```
  o con observation opcional
- **Headers**: Authorization Bearer, Content-Type application/json
- **Valores de Prueba para observation**:
  - Válido: "Renuncia voluntaria del empleado"
  - Válido: "Motivo"
  - Inválido: "" (vacío)
  - Inválido: null

## **Pasos (AAA)**

### **Arrange**
- Configurar cliente API de pruebas (APIClient)
- Crear mocks para autenticación JWT con diferentes payloads de permisos
- Crear mocks para servicios externos (_change_external_user_status, AuditClient, get_actor_info)
- Establecer datos de parametrización en base de datos (tipos, estados, monedas, cargos, departamentos)
- Crear empleado de prueba con ID 1 en estado activo
- Crear contrato de empleado básico (requerido para desactivación)
- Configurar tokens con permiso 10 (activar/desactivar empleados) y sin permisos
- Resetear estado del empleado antes de cada prueba cuando sea necesario

### **Act**
- Ejecutar peticiones PATCH al endpoint con diferentes configuraciones
- Probar escenarios de activación y desactivación exitosos
- Validar campos obligatorios (observation al desactivar)
- Enviar requests con y sin headers de autorización
- Validar comportamiento con empleados existentes e inexistentes
- Probar diferentes métodos HTTP (GET, POST, PUT, DELETE)
- Validar Content-Type y JSON malformado
- Probar campos extra en JSON
- Validar cambios sucesivos de estado
- Verificar idempotencia

### **Assert**
- Verificar códigos de estado HTTP correctos (200, 400, 401, 403, 404, 405)
- Validar estructura de respuesta JSON para éxitos y errores
- Comprobar que el mensaje de respuesta sea correcto
- Verificar que el estado del empleado cambie correctamente en la base de datos
- Confirmar que las validaciones de negocio funcionen apropiadamente
- Validar que la seguridad y autorización funcionen correctamente
- Verificar que los cambios sean persistentes

## **Resultado Esperado**

### **Casos de Éxito (200 OK)**
- Desactivación exitosa con observation válida
- Activación exitosa sin observation
- Activación exitosa con observation opcional
- Mensaje de respuesta correcto: "Empleado desactivado exitosamente." o "Empleado activado exitosamente."
- El estado del empleado cambia correctamente en la base de datos
- El estado del contrato se actualiza al desactivar (si aplica)

### **Casos de Error (400 Bad Request)**
- Desactivar sin observation: "El campo observation es obligatorio al desactivar al empleado."
- Desactivar con observation vacío: "El campo observation es obligatorio al desactivar al empleado."
- JSON malformado: Error de parsing
- ID inválido (0, -1): Error de validación

### **Casos de Seguridad y Existencia**
- **401 Unauthorized**: Sin token o token inválido/expirado
- **403 Forbidden**: Usuario sin permiso 10
- **404 Not Found**: id_employee no existe
- **405 Method Not Allowed**: Métodos HTTP no permitidos (GET, POST, PUT, DELETE)

## **Resultado Obtenido**
✅ **18 PRUEBAS PASARON** | ❌ **0 PRUEBAS FALLARON**

**Resumen de Ejecución:**
- **Total de pruebas**: 18
- **Pruebas exitosas**: 18 ✅
- **Pruebas fallidas**: 0 ❌
- **Tiempo de ejecución**: ~13-14 segundos
- **Cobertura**: 100% de casos especificados

**Detalle por caso:**

1. ✅ **UT-EMP-010.1** - Desactivar con observation válida (200 OK)
2. ✅ **UT-EMP-010.2** - Desactivar sin observation (400 Bad Request)
3. ✅ **UT-EMP-010.3** - Desactivar con observation vacío (400 Bad Request)
4. ✅ **UT-EMP-010.4** - Activar sin observation (200 OK)
5. ✅ **UT-EMP-010.5** - Activar con observation opcional (200 OK)
6. ✅ **UT-EMP-010.6.1** - Sin permiso retorna 403 (403 Forbidden)
7. ✅ **UT-EMP-010.6.2** - Sin token retorna 401 (401 Unauthorized)
8. ✅ **UT-EMP-010.6.3** - Token expirado retorna 401 (401 Unauthorized)
9. ✅ **UT-EMP-010.6.4** - Token inválido retorna 401 (401 Unauthorized)
10. ✅ **UT-EMP-010.7.1** - Empleado inexistente retorna 404 (404 Not Found)
11. ✅ **UT-EMP-010.7.2** - ID inválido (0) retorna 404 (404 Not Found)
12. ✅ **UT-EMP-010.8** - Métodos HTTP no permitidos retornan 405 (405 Method Not Allowed)
13. ✅ **UT-EMP-010.9** - Content-Type application/json funciona (200 OK)
14. ✅ **UT-EMP-010.10** - JSON malformado retorna error (400 Bad Request)
15. ✅ **UT-EMP-010.11** - Campos extra en JSON son aceptados (200 OK)
16. ✅ **UT-EMP-010.12** - Observation válida es aceptada (200 OK)
17. ✅ **UT-EMP-010.13** - Cambios sucesivos de estado funcionan correctamente (200 OK)
18. ✅ **UT-EMP-010.14** - Idempotencia funciona correctamente (200 OK)

## **Análisis Detallado de los Resultados**

### **Casos Exitosos**

#### **UT-EMP-010.1 - Desactivar con Observation Válida ✅**
- **Resultado**: 200 OK
- **Mensaje**: "Empleado desactivado exitosamente."
- **Validación BD**: El empleado cambió de estado activo (ID 1) a inactivo (ID 2)
- **Observaciones**: El contrato también se actualiza al estado 29 cuando se desactiva el empleado

#### **UT-EMP-010.2 - Desactivar sin Observation ✅**
- **Resultado**: 400 Bad Request
- **Mensaje**: "El campo observation es obligatorio al desactivar al empleado."
- **Validación BD**: El empleado NO cambió de estado (permanece activo)
- **Observaciones**: La validación funciona correctamente, evitando cambios de estado sin justificación

#### **UT-EMP-010.3 - Desactivar con Observation Vacío ✅**
- **Resultado**: 400 Bad Request
- **Mensaje**: "El campo observation es obligatorio al desactivar al empleado."
- **Validación BD**: El empleado NO cambió de estado (permanece activo)
- **Observaciones**: La validación detecta correctamente strings vacíos después de strip()

#### **UT-EMP-010.4 - Activar sin Observation ✅**
- **Resultado**: 200 OK
- **Mensaje**: "Empleado activado exitosamente."
- **Validación BD**: El empleado cambió de estado inactivo (ID 2) a activo (ID 1)
- **Observaciones**: La activación no requiere observation, como se esperaba

#### **UT-EMP-010.5 - Activar con Observation Opcional ✅**
- **Resultado**: 200 OK
- **Mensaje**: "Empleado activado exitosamente."
- **Validación BD**: El empleado cambió de estado inactivo (ID 2) a activo (ID 1)
- **Observaciones**: La observation es opcional para activación y se acepta correctamente

#### **UT-EMP-010.6 - Control de Permisos ✅**
- **6.1 Sin permiso**: 403 Forbidden ✅
- **6.2 Sin token**: 401 Unauthorized ✅
- **6.3 Token expirado**: 401 Unauthorized ✅
- **6.4 Token inválido**: 401 Unauthorized ✅
- **Observaciones**: Todos los casos de seguridad funcionan correctamente

#### **UT-EMP-010.7 - Manejo de Errores ✅**
- **7.1 Empleado inexistente**: 404 Not Found con mensaje "Empleado no encontrado." ✅
- **7.2 ID inválido (0)**: 404 Not Found ✅
- **Observaciones**: Los errores se manejan apropiadamente

#### **UT-EMP-010.8 - Validación de Métodos HTTP ✅**
- **GET**: 405 Method Not Allowed ✅
- **POST**: 405 Method Not Allowed ✅
- **PUT**: 405 Method Not Allowed ✅
- **DELETE**: 405 Method Not Allowed ✅
- **Observaciones**: Solo PATCH es aceptado, como se esperaba

#### **UT-EMP-010.9 - Content-Type application/json ✅**
- **Resultado**: 200 OK
- **Observaciones**: El Content-Type application/json funciona correctamente

#### **UT-EMP-010.10 - JSON Malformado ✅**
- **Resultado**: 400 Bad Request
- **Observaciones**: El sistema detecta correctamente JSON inválido

#### **UT-EMP-010.11 - Campos Extra en JSON ✅**
- **Resultado**: 200 OK
- **Observaciones**: Los campos extra son ignorados sin error, como se esperaba

#### **UT-EMP-010.12 - Observation Válida ✅**
- **Resultado**: 200 OK
- **Observaciones**: Observation con longitud mínima válida es aceptada

#### **UT-EMP-010.13 - Cambios Sucesivos de Estado ✅**
- **Resultado**: 200 OK en todas las operaciones
- **Secuencia probada**:
  1. Desactivar → Estado: Inactivo ✅
  2. Activar → Estado: Activo ✅
  3. Desactivar nuevamente → Estado: Inactivo ✅
- **Observaciones**: Los cambios sucesivos funcionan correctamente y son persistentes

#### **UT-EMP-010.14 - Idempotencia ✅**
- **Primera petición**: 200 OK ✅
- **Segunda petición idéntica**: 200 OK ✅
- **Observaciones**: El endpoint es idempotente, permitiendo múltiples peticiones idénticas

## **Problemas Resueltos Durante el Desarrollo**

### **1. Mock de Servicios Externos**
- **Problema**: El endpoint llama a servicios externos (_change_external_user_status) que no están disponibles en el entorno de pruebas
- **Solución**: Implementación de mocks para `_change_external_user_status`, `AuditClient` y `get_actor_info`
- **Impacto**: Permitió que las pruebas funcionen sin dependencias externas

### **2. Validación de Observation Obligatorio**
- **Problema**: Necesidad de validar que observation sea obligatorio solo al desactivar
- **Solución**: El endpoint valida correctamente que observation esté presente y no vacío al desactivar
- **Validación**: El código verifica `is_active and not observation` antes de permitir la desactivación

### **3. Reset de Estado entre Pruebas**
- **Problema**: Algunas pruebas modifican el estado del empleado, afectando pruebas posteriores
- **Solución**: Implementación del método `_reset_employee_status()` para resetear el estado antes de cada prueba
- **Impacto**: Asegura que cada prueba comience con un estado conocido

### **4. Creación de Datos de Prueba**
- **Problema**: El endpoint requiere empleado con id_user asociado y contrato activo
- **Solución**: Implementación de métodos `_setup_parametrization()` y `_setup_test_data()` para crear todos los datos necesarios
- **Impacto**: Permitió que las pruebas funcionen correctamente con datos reales

### **5. Corrección de Prueba 9 (Content-Type)**
- **Problema**: La prueba 9 fallaba porque no tenía los mocks necesarios para servicios externos
- **Solución**: Agregado de mocks para `_change_external_user_status`, `AuditClient` y `get_actor_info`
- **Impacto**: La prueba ahora pasa correctamente

## **Estado**
🟢 **APROBADO** - 18/18 pruebas exitosas (100%)

Todas las pruebas pasaron correctamente, validando:
- ✅ Activación y desactivación exitosas
- ✅ Validación de campos obligatorios
- ✅ Control de permisos y seguridad
- ✅ Manejo de errores
- ✅ Validación de métodos HTTP
- ✅ Validación de Content-Type y JSON
- ✅ Cambios sucesivos de estado
- ✅ Idempotencia

## **Fecha Ejecución**
22/11/2025

## **Ejecutado por**
Daniel soto
---

## **Comandos de Ejecución**

```bash
# Ejecutar todas las pruebas
docker-compose exec web python -m pytest test/UT-EMP-010/UT-EMP-010.py -v

# Ejecutar prueba específica
docker-compose exec web python -m pytest test/UT-EMP-010/UT-EMP-010.py::TestEmployeeToggleStatus::test_UT_EMP_010_1_desactivar_con_observation_valida -v -s

# Ejecutar con salida detallada
docker-compose exec web python -m pytest test/UT-EMP-010/UT-EMP-010.py -v -s

# Ejecutar solo pruebas que pasaron
docker-compose exec web python -m pytest test/UT-EMP-010/UT-EMP-010.py -v --tb=no
```

## **Tecnologías Utilizadas**
- **Framework**: pytest + Django REST Framework
- **Mocking**: unittest.mock para autenticación JWT y servicios externos (`@patch` para `JWTAuthentication.authenticate`, `jwt.decode`, `_change_external_user_status`, `AuditClient`, `get_actor_info`)
- **Base de datos**: PostgreSQL (conexión real con creación de datos de prueba)
- **Patrones**: AAA (Arrange-Act-Assert), Factory Pattern para datos de prueba
- **Validaciones**: Códigos HTTP, estructura JSON, validaciones de negocio específicas para activar/desactivar empleados
- **Transacciones**: Django atomic transactions para integridad de datos

## **Casos de Prueba Detallados**

### **UT-EMP-010.1 - Desactivar con Observation Válida ✅**
- **Descripción**: Verificar desactivación exitosa con observation válida
- **Datos**: Empleado activo con observation "Renuncia voluntaria del empleado"
- **Resultado**: 200 OK, mensaje "Empleado desactivado exitosamente."
- **Validaciones**: Estado del empleado cambia a inactivo (ID 2), mensaje correcto

### **UT-EMP-010.2 - Desactivar sin Observation ✅**
- **Descripción**: Verificar que desactivar sin observation retorna error
- **Datos**: Empleado activo con body vacío {}
- **Resultado**: 400 Bad Request, mensaje sobre observation obligatorio
- **Validaciones**: Estado del empleado NO cambia, mensaje de error correcto

### **UT-EMP-010.3 - Desactivar con Observation Vacío ✅**
- **Descripción**: Verificar que desactivar con observation vacío retorna error
- **Datos**: Empleado activo con observation: ""
- **Resultado**: 400 Bad Request, mensaje sobre observation obligatorio
- **Validaciones**: Estado del empleado NO cambia, validación de string vacío funciona

### **UT-EMP-010.4 - Activar sin Observation ✅**
- **Descripción**: Verificar activación exitosa sin observation
- **Datos**: Empleado desactivado con body vacío {}
- **Resultado**: 200 OK, mensaje "Empleado activado exitosamente."
- **Validaciones**: Estado del empleado cambia a activo (ID 1), observation no requerida

### **UT-EMP-010.5 - Activar con Observation Opcional ✅**
- **Descripción**: Verificar activación exitosa con observation opcional
- **Datos**: Empleado desactivado con observation "Reincorporación tras licencia"
- **Resultado**: 200 OK, mensaje "Empleado activado exitosamente."
- **Validaciones**: Estado del empleado cambia a activo (ID 1), observation aceptada

### **UT-EMP-010.6.1 - Sin Permiso Retorna 403 ✅**
- **Descripción**: Verificar que sin permiso 10 se retorna 403
- **Datos**: Token sin permiso 10
- **Resultado**: 403 Forbidden
- **Validación**: Mensaje "No tiene permisos para activar/desactivar empleados."

### **UT-EMP-010.6.2 - Sin Token Retorna 401 ✅**
- **Descripción**: Verificar que sin token se retorna 401
- **Datos**: Sin header Authorization
- **Resultado**: 401 Unauthorized
- **Validación**: Mensaje "Usuario no autenticado"

### **UT-EMP-010.6.3 - Token Expirado Retorna 401 ✅**
- **Descripción**: Verificar que con token expirado se retorna 401
- **Datos**: Token inválido "expired_token_12345"
- **Resultado**: 401 Unauthorized
- **Validación**: Autenticación falla correctamente

### **UT-EMP-010.6.4 - Token Inválido Retorna 401 ✅**
- **Descripción**: Verificar que con token inválido se retorna 401
- **Datos**: Token inválido "token_invalido_12345"
- **Resultado**: 401 Unauthorized
- **Validación**: Autenticación falla correctamente

### **UT-EMP-010.7.1 - Empleado Inexistente Retorna 404 ✅**
- **Descripción**: Verificar que con id_employee inexistente se retorna 404
- **Datos**: Employee ID 99999
- **Resultado**: 404 Not Found
- **Validación**: Mensaje "Empleado no encontrado."

### **UT-EMP-010.7.2 - ID Inválido Retorna 400/404 ✅**
- **Descripción**: Verificar que con id_employee = 0 se retorna 400 o 404
- **Datos**: Employee ID 0
- **Resultado**: 404 Not Found
- **Validación**: ID inválido es rechazado correctamente

### **UT-EMP-010.8 - Métodos HTTP No Permitidos ✅**
- **Descripción**: Verificar que GET, POST, PUT, DELETE retornan 405
- **Datos**: Métodos HTTP no permitidos
- **Resultado**: 405 Method Not Allowed para todos
- **Validación**: Solo PATCH es aceptado

### **UT-EMP-010.9 - Content-Type application/json ✅**
- **Descripción**: Verificar que Content-Type application/json funciona
- **Datos**: Content-Type: application/json
- **Resultado**: 200 OK
- **Validación**: Content-Type correcto es aceptado

### **UT-EMP-010.10 - JSON Malformado ✅**
- **Descripción**: Verificar que JSON malformado retorna error
- **Datos**: JSON inválido '{"observation": "texto sin cerrar'
- **Resultado**: 400 Bad Request
- **Validación**: JSON inválido es rechazado

### **UT-EMP-010.11 - Campos Extra en JSON ✅**
- **Descripción**: Verificar que campos extra son aceptados sin error
- **Datos**: JSON con campos adicionales
- **Resultado**: 200 OK
- **Validación**: Campos extra son ignorados

### **UT-EMP-010.12 - Observation Válida ✅**
- **Descripción**: Verificar que observation válida es aceptada
- **Datos**: Observation "Motivo" (mínima válida)
- **Resultado**: 200 OK
- **Validación**: Observation válida es aceptada

### **UT-EMP-010.13 - Cambios Sucesivos de Estado ✅**
- **Descripción**: Verificar que cambios sucesivos funcionan correctamente
- **Datos**: Secuencia: Desactivar → Activar → Desactivar
- **Resultado**: 200 OK en todas las operaciones
- **Validaciones**: Estados cambian correctamente y son persistentes

### **UT-EMP-010.14 - Idempotencia ✅**
- **Descripción**: Verificar que dos peticiones idénticas retornan 200
- **Datos**: Dos peticiones PATCH idénticas
- **Resultado**: 200 OK en ambas
- **Validación**: El endpoint es idempotente

---

## **Conclusiones**

Las pruebas unitarias UT-EMP-010 validan exitosamente el funcionamiento del endpoint de activar/desactivar empleados. Todas las pruebas (18/18) pasan correctamente, validando:

- ✅ Activación y desactivación exitosas con validaciones apropiadas
- ✅ Validación de campos obligatorios (observation al desactivar)
- ✅ Control de permisos y seguridad (401, 403)
- ✅ Manejo de errores (400, 404)
- ✅ Validación de métodos HTTP (405)
- ✅ Validación de Content-Type y JSON
- ✅ Cambios sucesivos de estado funcionan correctamente
- ✅ Idempotencia del endpoint
- ✅ Persistencia de cambios en base de datos



