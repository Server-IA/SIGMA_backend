# Reporte de Pruebas Unitarias - UT-CON-007

---

## **ID**
UT-CON-007

## **Título**
Verificar actualización de incrementos en contratos preestablecidos mediante endpoint PUT

## **Descripción**
Se valida el funcionamiento específico del endpoint PUT `/established_contracts/{contract_code}/update_established_contract/` enfocado en la actualización de incrementos asociados a contratos preestablecidos. Se prueban diferentes escenarios de validación de datos para incrementos, incluyendo campos obligatorios, rangos de valores, fechas, duplicidad, tipos válidos, y operaciones de creación, actualización y eliminación de incrementos. También se validan aspectos de seguridad, autenticación y autorización.

## **Precondiciones**
- Contenedor Docker ejecutándose con la aplicación Django
- Base de datos PostgreSQL disponible y configurada
- Usuario de prueba creado con ID 1
- Parametrización completa en base de datos:
  - Estados: Activo (ID 1), Inactivo (ID 2)
  - Tipos de contrato (categoría 15), jornada (16), modalidad (17)
  - Tipos de incrementos (19): Bonificación por Desempeño (ID 31), Auxilio de Transporte (ID 32)
  - Moneda COP (ID 17) con categoría de unidades 10
  - Cargo de empleado: Encargado de Ventas (ID 1)
  - Días de la semana configurados
- Contrato base para actualizaciones:
  - CON-ENCARGADODEVENTAS-0012 (contrato objetivo con incremento existente)

## **Datos de Entrada**
- **Endpoint**: PUT `/established_contracts/{contract_code}/update_established_contract/`
- **Tokens JWT**: Con permiso 176, sin permiso, inválidos, ausentes
- **Contract codes**: CON-ENCARGADODEVENTAS-0012 (existente), contratos inexistentes
- **Headers**: Authorization Bearer, Content-Type application/json
- **Payloads**: Datos de incrementos válidos e inválidos con diferentes validaciones

## **Pasos (AAA)**

### **Arrange**
- Configurar cliente API de pruebas (APIClient)
- Crear mocks para autenticación JWT con diferentes payloads de permisos
- Establecer datos de parametrización en base de datos (tipos, estados, monedas)
- Crear contrato base CON-ENCARGADODEVENTAS-0012 con incremento existente
- Preparar payloads base válidos para actualización de contratos
- Configurar tokens con permiso 176 (established_contract.update) y sin permisos

### **Act**
- Ejecutar peticiones PUT al endpoint con diferentes configuraciones de incrementos
- Simular escenarios de creación, actualización y eliminación de incrementos
- Probar validaciones de campos obligatorios, rangos, fechas y tipos
- Enviar requests con y sin headers de autorización
- Validar comportamiento con contratos activos e inactivos

### **Assert**
- Verificar códigos de estado HTTP correctos (200, 400, 401, 403, 404)
- Validar estructura de respuesta JSON para éxitos y errores
- Comprobar que los incrementos se actualicen correctamente en base de datos
- Verificar mensajes de error específicos para cada tipo de validación
- Confirmar que las validaciones de negocio funcionen apropiadamente
- Validar que la seguridad y autorización funcionen correctamente

## **Resultado Esperado**

### **Casos de Éxito (200 OK)**
- Actualización exitosa de incremento existente con nuevos valores
- Eliminación correcta de incrementos desde el payload
- Respuesta con mensaje de éxito y contract_code actualizado
- Datos de incrementos persistidos correctamente en base de datos

### **Casos de Error (400 Bad Request)**
- Campos obligatorios faltantes en incrementos
- Valores porcentuales mayores a 100%
- Valores negativos en amount_value y amount
- Fechas de incremento fuera del rango del contrato
- Descripción que supera 255 caracteres
- Incrementos duplicados por tipo
- Tipos de incremento inexistentes o inválidos

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
- **Tiempo de ejecución**: ~9.8 segundos
- **Cobertura**: 90.9% de casos especificados

**Detalle por caso:**
1. ✅ **UT-CON-008.1** - Actualización exitosa de incremento (200 OK)
2. ✅ **UT-CON-008.2** - Campos obligatorios faltantes (400 Bad Request)
3. ✅ **UT-CON-008.3** - Valor porcentual mayor a 100% (400 Bad Request)
4. ✅ **UT-CON-008.4** - Valores negativos en incremento (400 Bad Request)
5. ✅ **UT-CON-008.5** - Fechas fuera del rango del contrato (400 Bad Request)
6. ✅ **UT-CON-008.6** - Descripción supera longitud máxima (400 Bad Request)
7. ✅ **UT-CON-008.7** - Incremento duplicado por tipo (400 Bad Request)
8. ✅ **UT-CON-008.8** - Tipo de incremento inválido (400 Bad Request)
9. ❌ **UT-CON-008.9** - Modificar contrato inactivo (Comportamiento inesperado)
10. ✅ **UT-CON-008.10** - Restricciones de seguridad (401/403)
11. ✅ **UT-CON-008.11** - Eliminar incremento correctamente (200 OK)

## **Análisis Detallado del Error**

### **UT-CON-008.9 - Modificar incrementos de contrato inactivo**

**Comportamiento Esperado:**
- El endpoint debería rechazar modificaciones de incrementos cuando el contrato está en estado "Inactivo" o "Finalizado"
- Código de respuesta esperado: `400 Bad Request` o `403 Forbidden`
- Mensaje esperado: "No se pueden modificar incrementos de contratos inactivos o finalizados"

**Comportamiento Actual:**
- El endpoint **permite** modificar incrementos en contratos inactivos
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

### **2. Campos de Modelos de Parametrización**
- **Problema**: Uso de campos inexistentes en modelos (`creation_date`, `modification_date`, `id_responsible_user`)
- **Causa**: Los modelos `ContractPaymentsEstablishedContract`, `EstablishedIncrease`, y `DaysOfWeek` no tienen estos campos
- **Solución**: Simplificación de la creación de objetos usando solo campos requeridos
- **Código**: Eliminación de campos no existentes en `objects.create()`

### **3. Choices de Campos**
- **Problema**: Uso de valores incorrectos para campos con choices
- **Causa**: `payment_frequency_type` usa "quincenal" (minúscula), `salary_type` usa "Mensual fijo", `overtime_period` usa "dia"
- **Solución**: Corrección de valores según las opciones definidas en el modelo
- **Validación**: Verificación de `PAYMENT_FREQUENCY_CHOICES`, `SALARY_TYPE_CHOICES`, `OVERTIME_PERIOD_CHOICES`

### **4. Validación de Moneda**
- **Problema**: Error "El tipo de moneda no es válido"
- **Causa**: Serializer espera `id_units_categories_id = 10` para monedas
- **Solución**: Configuración correcta de categoría de unidades para moneda
- **Código**: `UnitsCategory.objects.get_or_create(id_units_categories=10)`

### **5. Campos Obligatorios Condicionales**
- **Problema**: Error "Este campo es obligatorio cuando las vacaciones son acumulativas"
- **Causa**: Falta campo `start_cumulative_vacation` cuando `cumulative_vacation = True`
- **Solución**: Agregado del campo en payload y setup del contrato
- **Validación**: Campo requerido por lógica de negocio del serializer

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
docker-compose exec web python -m pytest test/UT-CON-007/test_UT_CON_007.py -v

# Ejecutar prueba específica
docker-compose exec web python -m pytest test/UT-CON-007/test_UT_CON_007.py::TestEstablishedContractIncrementsUpdate::test_ut_con_008_1_successful_increment_update -v

# Ejecutar con cobertura
docker-compose exec web python -m pytest test/UT-CON-007/test_UT_CON_007.py --cov=payroll.api.established_contract_viewset --cov-report=html

# Ejecutar solo la prueba que falló
docker-compose exec web python -m pytest test/UT-CON-007/test_UT_CON_007.py::TestEstablishedContractIncrementsUpdate::test_ut_con_008_9_inactive_contract_modification -v
```

## **Tecnologías Utilizadas**
- **Framework**: pytest + Django REST Framework
- **Mocking**: unittest.mock para autenticación JWT
- **Base de datos**: PostgreSQL (conexión real)
- **Patrones**: AAA (Arrange-Act-Assert), Factory Pattern
- **Validaciones**: Códigos HTTP, estructura JSON, validaciones de negocio específicas para incrementos
- **Transacciones**: Django atomic transactions para integridad de datos

## **Casos de Prueba Detallados**

### **UT-CON-008.1 - Actualización Exitosa de Incremento ✅**
- **Descripción**: Verificar actualización completa de incremento existente
- **Datos**: Cambio de tipo porcentaje, nuevas fechas, aplicación y descripción
- **Resultado**: 200 OK, incremento actualizado correctamente en BD
- **Validaciones**: Verificación de todos los campos actualizados

### **UT-CON-008.2 - Campos Obligatorios Faltantes ✅**
- **Descripción**: Validar error cuando faltan campos requeridos en incrementos
- **Datos**: Payload con solo descripción, sin campos obligatorios
- **Resultado**: 400 Bad Request con errores específicos por campo
- **Validaciones**: `increase_type`, `amount_type`, `amount_value`, `application_increase_type`

### **UT-CON-008.3 - Valor Porcentual Mayor a 100% ✅**
- **Descripción**: Rechazar incrementos con porcentaje superior al límite
- **Datos**: `amount_type = "Porcentaje"` con `amount_value = 150`
- **Resultado**: 400 Bad Request con mensaje específico de validación
- **Validación**: "El valor no puede ser mayor a 100 cuando el tipo es porcentaje"

### **UT-CON-008.4 - Valores Negativos ✅**
- **Descripción**: Rechazar incrementos con montos negativos
- **Datos**: `amount_value = -50000`, `amount = -2`
- **Resultado**: 400 Bad Request con errores de validación de rango
- **Validaciones**: Ambos campos deben ser >= 0

### **UT-CON-008.5 - Fechas Fuera del Rango del Contrato ✅**
- **Descripción**: Validar coherencia de fechas de incremento con fechas del contrato
- **Subcasos**: 
  - Fecha inicio antes del contrato
  - Fecha fin después del contrato  
  - Fecha fin antes que fecha inicio
- **Resultado**: 400 Bad Request con mensajes específicos por cada caso
- **Validaciones**: Fechas deben estar dentro del rango del contrato y ser coherentes

### **UT-CON-008.6 - Descripción Supera Longitud Máxima ✅**
- **Descripción**: Rechazar descripciones con más de 255 caracteres
- **Datos**: String de 256 caracteres
- **Resultado**: 400 Bad Request con error de longitud
- **Validación**: Campo `description` limitado a 255 caracteres

### **UT-CON-008.7 - Incremento Duplicado por Tipo ✅**
- **Descripción**: Evitar duplicidad de incrementos con mismo tipo
- **Datos**: Dos incrementos con mismo `increase_type`
- **Resultado**: 400 Bad Request con error de duplicidad
- **Validación**: Unicidad por tipo de incremento

### **UT-CON-008.8 - Tipo de Incremento Inválido ✅**
- **Descripción**: Rechazar tipos de incremento inexistentes
- **Datos**: `increase_type = 999` (ID inexistente)
- **Resultado**: 400 Bad Request con mensaje de tipo no válido
- **Validación**: Tipo debe existir y pertenecer a categoría 19

### **UT-CON-008.9 - Modificar Contrato Inactivo ❌**
- **Descripción**: Impedir modificaciones en contratos inactivos
- **Datos**: Contrato con `established_contract_status = Inactivo`
- **Resultado Esperado**: 400/403 con mensaje de restricción
- **Resultado Actual**: 200 OK (modificación permitida)
- **Estado**: **FALLA - Validación de negocio no implementada**

### **UT-CON-008.10 - Restricciones de Seguridad ✅**
- **Descripción**: Validar autenticación y autorización
- **Subcasos**:
  - Sin token: 401 Unauthorized
  - Sin permiso 176: 403 Forbidden
- **Resultado**: Códigos de error correctos, sin modificaciones en BD
- **Validaciones**: Sistema de seguridad funcionando correctamente

### **UT-CON-008.11 - Eliminar Incremento Correctamente ✅**
- **Descripción**: Simular eliminación de incremento desde frontend
- **Datos**: Payload sin uno de los incrementos existentes
- **Resultado**: 200 OK, incremento eliminado de BD
- **Validaciones**: Solo incrementos en payload permanecen en BD

## **Observaciones Finales**

### **Fortalezas del Endpoint**
- ✅ Validaciones robustas de datos de incrementos
- ✅ Manejo correcto de campos obligatorios y opcionales
- ✅ Validaciones de rangos y tipos apropiadas
- ✅ Sistema de seguridad y autorización funcional
- ✅ Operaciones CRUD de incrementos funcionando correctamente
- ✅ Transaccionalidad garantizada para integridad de datos
- ✅ Validaciones específicas para incrementos (porcentajes, duplicidad, fechas)

### **Áreas de Mejora Identificadas**
- ❌ **Validación de estado del contrato**: Falta implementar restricción para contratos inactivos
- 🔄 **Validaciones de negocio adicionales**: Considerar reglas específicas por tipo de incremento
- 📝 **Mensajes de error**: Estandarizar formato de mensajes de validación
- 🔍 **Logging**: Mejorar trazabilidad de operaciones de actualización

### **Recomendaciones para Producción**
1. **Implementar validación de estado**: Agregar validación que impida modificar contratos inactivos
2. **Auditoría mejorada**: Registrar cambios específicos en incrementos para trazabilidad
3. **Validaciones adicionales**: Considerar reglas de negocio específicas por sector o tipo de contrato
4. **Documentación**: Actualizar documentación de API con validaciones específicas de incrementos

### **Comparación con UT-CON-006 (Deducciones)**
- **Similitudes**: Ambos módulos comparten la misma validación faltante de estado del contrato
- **Consistencia**: Los serializers de deducciones e incrementos tienen validaciones similares
- **Patrón**: El comportamiento es consistente entre deducciones e incrementos, indicando que es un tema sistémico

### **Conclusión**
El endpoint de actualización de incrementos funciona correctamente en el 90.9% de los casos de prueba. La única falla identificada es una validación de negocio faltante que no impacta la funcionalidad core, pero que debería implementarse para mayor robustez del sistema. Las validaciones de datos, seguridad y operaciones CRUD funcionan según lo esperado, manteniendo consistencia con el comportamiento observado en el módulo de deducciones (UT-CON-006).
