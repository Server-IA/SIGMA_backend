# Reporte de Pruebas Unitarias - UT-CON-006

---

## **ID**
UT-CON-006

## **Título**
Verificar actualización de deducciones en contratos preestablecidos mediante endpoint PUT

## **Descripción**
Se valida el funcionamiento específico del endpoint PUT `/established_contracts/{contract_code}/update_established_contract/` enfocado en la actualización de deducciones asociadas a contratos preestablecidos. Se prueban diferentes escenarios de validación de datos para deducciones, incluyendo campos obligatorios, rangos de valores, fechas, duplicidad, tipos válidos, y operaciones de creación, actualización y eliminación de deducciones. También se validan aspectos de seguridad, autenticación y autorización.

## **Precondiciones**
- Contenedor Docker ejecutándose con la aplicación Django
- Base de datos PostgreSQL disponible y configurada
- Usuario de prueba creado con ID 1
- Parametrización completa en base de datos:
  - Estados: Activo (ID 1), Inactivo (ID 2)
  - Tipos de contrato (categoría 15), jornada (16), modalidad (17)
  - Tipos de deducciones (18): Salud (ID 28), Pensión (ID 29)
  - Moneda COP (ID 17) con categoría de unidades 10
  - Cargo de empleado: Encargado de Ventas (ID 1)
  - Días de la semana configurados
- Contrato base para actualizaciones:
  - CON-ENCARGADODEVENTAS-0012 (contrato objetivo con deducción existente)

## **Datos de Entrada**
- **Endpoint**: PUT `/established_contracts/{contract_code}/update_established_contract/`
- **Tokens JWT**: Con permiso 176, sin permiso, inválidos, ausentes
- **Contract codes**: CON-ENCARGADODEVENTAS-0012 (existente), contratos inexistentes
- **Headers**: Authorization Bearer, Content-Type application/json
- **Payloads**: Datos de deducciones válidos e inválidos con diferentes validaciones

## **Pasos (AAA)**

### **Arrange**
- Configurar cliente API de pruebas (APIClient)
- Crear mocks para autenticación JWT con diferentes payloads de permisos
- Establecer datos de parametrización en base de datos (tipos, estados, monedas)
- Crear contrato base CON-ENCARGADODEVENTAS-0012 con deducción existente
- Preparar payloads base válidos para actualización de contratos
- Configurar tokens con permiso 176 (established_contract.update) y sin permisos

### **Act**
- Ejecutar peticiones PUT al endpoint con diferentes configuraciones de deducciones
- Simular escenarios de creación, actualización y eliminación de deducciones
- Probar validaciones de campos obligatorios, rangos, fechas y tipos
- Enviar requests con y sin headers de autorización
- Validar comportamiento con contratos activos e inactivos

### **Assert**
- Verificar códigos de estado HTTP correctos (200, 400, 401, 403, 404)
- Validar estructura de respuesta JSON para éxitos y errores
- Comprobar que las deducciones se actualicen correctamente en base de datos
- Verificar mensajes de error específicos para cada tipo de validación
- Confirmar que las validaciones de negocio funcionen apropiadamente
- Validar que la seguridad y autorización funcionen correctamente

## **Resultado Esperado**

### **Casos de Éxito (200 OK)**
- Actualización exitosa de deducción existente con nuevos valores
- Eliminación correcta de deducciones desde el payload
- Respuesta con mensaje de éxito y contract_code actualizado
- Datos de deducciones persistidos correctamente en base de datos

### **Casos de Error (400 Bad Request)**
- Campos obligatorios faltantes en deducciones
- Valores porcentuales mayores a 100%
- Valores negativos en amount_value y amount
- Fechas de deducción fuera del rango del contrato
- Descripción que supera 255 caracteres
- Deducciones duplicadas por tipo y aplicación
- Tipos de deducción inexistentes o inválidos

### **Casos de Seguridad y Existencia**
- **401 Unauthorized**: Sin token o token inválido
- **403 Forbidden**: Usuario sin permiso 176
- **404 Not Found**: Contract_code no existe

## **Resultado Obtenido**
✅ **10 PRUEBAS PASARON** | ❌ **1 PRUEBA FALLÓ**

**Resumen de Ejecución:**
- **Total de pruebas**: 11
- **Pruebas exitosas**: 10 ✅
- **Pruebas fallidas**: 1 ❌
- **Tiempo de ejecución**: ~17 segundos
- **Cobertura**: 90.9% de casos especificados

**Detalle por caso:**
1. ✅ **UT-CON-007.1** - Actualización exitosa de deducción (200 OK)
2. ✅ **UT-CON-007.2** - Campos obligatorios faltantes (400 Bad Request)
3. ✅ **UT-CON-007.3** - Valor porcentual mayor a 100% (400 Bad Request)
4. ✅ **UT-CON-007.4** - Valores negativos en deducción (400 Bad Request)
5. ✅ **UT-CON-007.5** - Fechas fuera del rango del contrato (400 Bad Request)
6. ✅ **UT-CON-007.6** - Descripción supera longitud máxima (400 Bad Request)
7. ✅ **UT-CON-007.7** - Deducción duplicada por tipo (400 Bad Request)
8. ✅ **UT-CON-007.8** - Tipo de deducción inválido (400 Bad Request)
9. ❌ **UT-CON-007.9** - Modificar contrato inactivo (Comportamiento inesperado)
10. ✅ **UT-CON-007.10** - Restricciones de seguridad (401/403)
11. ✅ **UT-CON-007.11** - Eliminar deducción correctamente (200 OK)

## **Análisis Detallado del Error**

### **UT-CON-007.9 - Modificar deducciones de contrato inactivo**

**Comportamiento Esperado:**
- El endpoint debería rechazar modificaciones de deducciones cuando el contrato está en estado "Inactivo" o "Finalizado"
- Código de respuesta esperado: `400 Bad Request` o `403 Forbidden`
- Mensaje esperado: "No se pueden modificar deducciones de contratos inactivos o finalizados"

**Comportamiento Actual:**
- El endpoint **permite** modificar deducciones en contratos inactivos
- Código de respuesta obtenido: `200 OK`
- La actualización se procesa exitosamente sin validar el estado del contrato

**Análisis Técnico:**
```python
# En la prueba se cambió el estado del contrato a inactivo:
self.base_contract.established_contract_status = self.status_inactive
self.base_contract.save()

# Se esperaba error 400/403, pero se obtuvo 200 OK
assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN]
# AssertionError: assert 200 in [400, 403]
```

**Causa Raíz:**
El serializer `EstablishedContractUpdateSerializer` y el endpoint `update_established_contract` **no implementan validación de estado del contrato**. El campo `established_contract_status` está marcado como `read_only_fields`, pero no hay validación de negocio que impida modificar contratos inactivos.

**Impacto:**
- **Funcional**: Permite modificaciones no deseadas en contratos que deberían estar "cerrados"
- **Negocio**: Posible inconsistencia en datos de contratos finalizados
- **Auditoría**: Cambios en contratos que no deberían ser modificables

**Recomendación:**
Implementar validación en el serializer o viewset:
```python
def validate(self, data):
    if self.instance and self.instance.established_contract_status.name != 'Activo':
        raise serializers.ValidationError(
            "No se pueden modificar contratos inactivos o finalizados."
        )
    return data
```

## **Problemas Resueltos Durante el Desarrollo**

### **1. Estructura de Modelos**
- **Problema**: Uso incorrecto de nombres de campos del modelo `User` (`id` vs `id_user`)
- **Solución**: Corrección a `id_user` como clave primaria del modelo
- **Impacto**: Permitió la creación correcta de usuarios de prueba

### **2. Validación de Moneda**
- **Problema**: Error "El tipo de moneda no es válido" 
- **Causa**: Serializer espera `id_units_categories_id = 10` para monedas
- **Solución**: Cambio de categoría de unidades de 4 a 10
- **Código**: `UnitsCategory.objects.get_or_create(id_units_categories=10)`

### **3. Campos Obligatorios Condicionales**
- **Problema**: Error "Este campo es obligatorio cuando las vacaciones son acumulativas"
- **Causa**: Falta campo `start_cumulative_vacation` cuando `cumulative_vacation = True`
- **Solución**: Agregado del campo en payload y setup del contrato
- **Validación**: Campo requerido por lógica de negocio del serializer

### **4. Estructura de Contratos**
- **Problema**: Nombres incorrectos de campos del modelo `EstablishedContract`
- **Solución**: Corrección de campos (`salary` → `salary_base`, `id_contract_type` → `contract_type`, etc.)
- **Impacto**: Permitió la creación y actualización correcta de contratos

## **Estado**
🟡 **PARCIALMENTE APROBADO** - 10/11 pruebas exitosas con 1 validación de negocio faltante

## **Fecha Ejecución**
18/11/2025

## **Ejecutado por**
Juan Camilo

---

## **Comandos de Ejecución**

```bash
# Ejecutar todas las pruebas
docker-compose exec web python -m pytest test/UT-CON-006/test_UT_CON_006.py -v

# Ejecutar prueba específica
docker-compose exec web python -m pytest test/UT-CON-006/test_UT_CON_006.py::TestEstablishedContractDeductionsUpdate::test_ut_con_007_1_successful_deduction_update -v

# Ejecutar con cobertura
docker-compose exec web python -m pytest test/UT-CON-006/test_UT_CON_006.py --cov=payroll.api.established_contract_viewset --cov-report=html

# Ejecutar solo la prueba que falló
docker-compose exec web python -m pytest test/UT-CON-006/test_UT_CON_006.py::TestEstablishedContractDeductionsUpdate::test_ut_con_007_9_inactive_contract_modification -v
```

## **Tecnologías Utilizadas**
- **Framework**: pytest + Django REST Framework
- **Mocking**: unittest.mock para autenticación JWT
- **Base de datos**: PostgreSQL (conexión real)
- **Patrones**: AAA (Arrange-Act-Assert), Factory Pattern
- **Validaciones**: Códigos HTTP, estructura JSON, validaciones de negocio específicas para deducciones
- **Transacciones**: Django atomic transactions para integridad de datos

## **Casos de Prueba Detallados**

### **UT-CON-007.1 - Actualización Exitosa de Deducción ✅**
- **Descripción**: Verificar actualización completa de deducción existente
- **Datos**: Cambio de tipo fijo a porcentaje, nuevas fechas y descripción
- **Resultado**: 200 OK, deducción actualizada correctamente en BD
- **Validaciones**: Verificación de todos los campos actualizados

### **UT-CON-007.2 - Campos Obligatorios Faltantes ✅**
- **Descripción**: Validar error cuando faltan campos requeridos en deducciones
- **Datos**: Payload con solo descripción, sin campos obligatorios
- **Resultado**: 400 Bad Request con errores específicos por campo
- **Validaciones**: `deduction_type`, `amount_type`, `amount_value`, `application_deduction_type`

### **UT-CON-007.3 - Valor Porcentual Mayor a 100% ✅**
- **Descripción**: Rechazar deducciones con porcentaje superior al límite
- **Datos**: `amount_type = "Porcentaje"` con `amount_value = 150`
- **Resultado**: 400 Bad Request con mensaje específico de validación
- **Validación**: "El valor no puede ser mayor a 100 cuando el tipo es porcentaje"

### **UT-CON-007.4 - Valores Negativos ✅**
- **Descripción**: Rechazar deducciones con montos negativos
- **Datos**: `amount_value = -1000`, `amount = -2`
- **Resultado**: 400 Bad Request con errores de validación de rango
- **Validaciones**: Ambos campos deben ser >= 0

### **UT-CON-007.5 - Fechas Fuera del Rango del Contrato ✅**
- **Descripción**: Validar coherencia de fechas de deducción con fechas del contrato
- **Subcasos**: 
  - Fecha inicio antes del contrato
  - Fecha fin después del contrato  
  - Fecha fin antes que fecha inicio
- **Resultado**: 400 Bad Request con mensajes específicos por cada caso
- **Validaciones**: Fechas deben estar dentro del rango del contrato y ser coherentes

### **UT-CON-007.6 - Descripción Supera Longitud Máxima ✅**
- **Descripción**: Rechazar descripciones con más de 255 caracteres
- **Datos**: String de 256 caracteres
- **Resultado**: 400 Bad Request con error de longitud
- **Validación**: Campo `description` limitado a 255 caracteres

### **UT-CON-007.7 - Deducción Duplicada por Tipo ✅**
- **Descripción**: Evitar duplicidad de deducciones con mismo tipo y aplicación
- **Datos**: Dos deducciones con mismo `deduction_type` y `application_deduction_type`
- **Resultado**: 400 Bad Request con error de duplicidad
- **Validación**: Unicidad por combinación de tipo y aplicación

### **UT-CON-007.8 - Tipo de Deducción Inválido ✅**
- **Descripción**: Rechazar tipos de deducción inexistentes
- **Datos**: `deduction_type = 999` (ID inexistente)
- **Resultado**: 400 Bad Request con mensaje de tipo no válido
- **Validación**: Tipo debe existir y pertenecer a categoría 18

### **UT-CON-007.9 - Modificar Contrato Inactivo ❌**
- **Descripción**: Impedir modificaciones en contratos inactivos
- **Datos**: Contrato con `established_contract_status = Inactivo`
- **Resultado Esperado**: 400/403 con mensaje de restricción
- **Resultado Actual**: 200 OK (modificación permitida)
- **Estado**: **FALLA - Validación de negocio no implementada**

### **UT-CON-007.10 - Restricciones de Seguridad ✅**
- **Descripción**: Validar autenticación y autorización
- **Subcasos**:
  - Sin token: 401 Unauthorized
  - Sin permiso 176: 403 Forbidden
- **Resultado**: Códigos de error correctos, sin modificaciones en BD
- **Validaciones**: Sistema de seguridad funcionando correctamente

### **UT-CON-007.11 - Eliminar Deducción Correctamente ✅**
- **Descripción**: Simular eliminación de deducción desde frontend
- **Datos**: Payload sin una de las deducciones existentes
- **Resultado**: 200 OK, deducción eliminada de BD
- **Validaciones**: Solo deducciones en payload permanecen en BD

## **Observaciones Finales**

### **Fortalezas del Endpoint**
- ✅ Validaciones robustas de datos de deducciones
- ✅ Manejo correcto de campos obligatorios y opcionales
- ✅ Validaciones de rangos y tipos apropiadas
- ✅ Sistema de seguridad y autorización funcional
- ✅ Operaciones CRUD de deducciones funcionando correctamente
- ✅ Transaccionalidad garantizada para integridad de datos

### **Áreas de Mejora Identificadas**
- ❌ **Validación de estado del contrato**: Falta implementar restricción para contratos inactivos
- 🔄 **Validaciones de negocio adicionales**: Considerar reglas específicas por tipo de deducción
- 📝 **Mensajes de error**: Estandarizar formato de mensajes de validación
- 🔍 **Logging**: Mejorar trazabilidad de operaciones de actualización

### **Recomendaciones para Producción**
1. **Implementar validación de estado**: Agregar validación que impida modificar contratos inactivos
2. **Auditoría mejorada**: Registrar cambios específicos en deducciones para trazabilidad
3. **Validaciones adicionales**: Considerar reglas de negocio específicas por sector o tipo de contrato
4. **Documentación**: Actualizar documentación de API con validaciones específicas de deducciones

### **Conclusión**
El endpoint de actualización de deducciones funciona correctamente en el 90.9% de los casos de prueba. La única falla identificada es una validación de negocio faltante que no impacta la funcionalidad core, pero que debería implementarse para mayor robustez del sistema. Las validaciones de datos, seguridad y operaciones CRUD funcionan según lo esperado.