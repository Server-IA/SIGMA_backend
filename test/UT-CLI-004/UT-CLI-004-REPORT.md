# Caso de Prueba Unitario - UT-CLI-004

## Información General

| Campo | Valor |
|-------|-------|
| **ID** | UT-CLI-004 |
| **Título** | Actualizar Cliente |
| **Historia de Usuario** | HU-CLI-004 |
| **Descripción** | Prueba unitaria que valida la funcionalidad completa del endpoint de actualización de clientes existentes, cubriendo todos los escenarios posibles incluyendo autenticación JWT, permisos, validaciones de datos únicos, reglas de negocio y límites de campos |

### Precondiciones
- Base de datos de prueba configurada con esquema completo
- Mock configurado para simulación de autenticación JWT (check_permission)
- Tipos de documento parametrizados: Cédula (id=1), NIT (id=2), Pasaporte (id=3)
- Tipos de persona disponibles: Natural (1), Jurídica (2)
- Estados de cliente configurados: Activo (id=1), Inactivo (id=2)
- Usuarios de prueba: con permiso 137 (id=201-205) y sin permiso (id=301)
- Clientes de prueba con datos únicos (documentos, emails)
- Municipios configurados para validación de FK
- Cliente API configurado para requests HTTP PATCH
- Sistema de auditoría mockeado para prevenir efectos secundarios

### Datos de Entrada

```json
{
  "usuarios_prueba": {
    "usuario_con_permisos": {
      "id": 201,
      "permissions": [137],
      "description": "Usuario con permiso JWT 137 para actualización de clientes"
    },
    "usuario_sin_permisos": {
      "id": 301,
      "permissions": [],
      "description": "Usuario sin permiso JWT 137"
    }
  },
  "clientes_prueba": {
    "cliente_principal": {
      "id": 1,
      "document_number": "12345678",
      "type_document_id": 1,
      "person_type": 1,
      "legal_entity_name": "Cliente Principal",
      "email": "principal@test.com",
      "phone": "3001234567"
    },
    "cliente_secundario": {
      "id": 2,
      "document_number": "87654321",
      "email": "secundario@test.com"
    }
  },
  "escenarios_entrada": {
    "actualizacion_exitosa": {
      "document_number": "99999999",
      "type_document_id": 1,
      "person_type": 2,
      "legal_entity_name": "Cliente Actualizado Exitosamente",
      "first_last_name": "Apellido",
      "email": "actualizado@example.com",
      "phone": "3009876543",
      "address": "Nueva Dirección 123",
      "id_municipality": 1001,
      "tax_regime": 2
    },
    "documento_duplicado": "87654321",
    "email_duplicado": "secundario@test.com",
    "documento_invalido": {
      "vacio": "",
      "exceso_digitos": "12345678901",
      "no_numerico": "12345abc89"
    },
    "campos_largos": {
      "legal_entity_name": "a" * 101,
      "first_last_name": "b" * 101,
      "address": "c" * 101
    },
    "referencias_inexistentes": {
      "type_document_id": 99999,
      "person_type": 99
    }
  },
  "endpoints": {
    "update_url": "/api/customers/{id}/update/",
    "method": "PATCH",
    "auth_required": true,
    "permission_required": 137
  }
}
```

## Pasos (AAA)

### Arrange: Preparar datos y entorno
- Configurar base de datos SQLite en memoria para aislamiento de pruebas
- Crear tipos de documento: Cédula, NIT, Pasaporte con IDs específicos
- Crear tipos de persona: Natural y Jurídica
- Crear estados de cliente: Activo e Inactivo
- Crear usuarios de prueba con diferentes niveles de permisos (201-205 con permiso, 301 sin permiso)
- Crear municipios para validación de claves foráneas
- Crear clientes base con documentos y emails únicos para pruebas de duplicación
- Configurar mock para check_permission del CustomerViewSet
- Configurar mock para audit_sdk para evitar efectos secundarios
- Inicializar cliente API de Django REST Framework con autenticación forzada

### Act: Ejecución de pruebas
1. **Actualización Exitosa (200)**: Enviar PATCH con datos válidos y únicos
2. **Sin Permisos (403)**: Enviar PATCH con usuario sin permiso JWT 137
3. **Cliente Inexistente (404)**: Enviar PATCH a ID de cliente que no existe (99999)
4. **Documento Duplicado (400)**: Intentar actualizar con documento existente en otro cliente
5. **Email Duplicado (400)**: Intentar actualizar con email existente en otro cliente
6. **Tipo Documento Inexistente (400)**: Usar type_document_id que no existe en DB
7. **Tipo Persona Inexistente (400)**: Usar person_type que no existe en parámetros
8. **Campos Exceden Longitud (400)**: Enviar campos con más de 100 caracteres
9. **Documento Inválido (400)**: Probar documentos vacíos, >10 dígitos, no numéricos

### Assert: Validaciones
- Verificar código de respuesta HTTP correcto para cada escenario
- Validar estructura de respuesta JSON con campos success, message, data
- Confirmar mensajes de error específicos y descriptivos en español
- Verificar que los datos se actualizan correctamente en la base de datos para casos exitosos
- Validar que las validaciones de unicidad funcionan (documento y email)
- Confirmar que las validaciones de longitud se aplican correctamente
- Verificar que las validaciones de formato de documento funcionan
- Validar que las referencias de claves foráneas se verifican
- Confirmar que se requiere autenticación JWT válida
- Verificar que se requiere permiso específico ID 137
- Validar que los mocks se configuran y limpian correctamente
- Confirmar que el sistema de auditoría se invoca en actualizaciones exitosas

## Resultado Esperado
- **Test exitoso (200)**: Cliente actualizado con éxito, datos guardados en BD, respuesta con success=true
- **Test 403**: Error de permisos con mensaje "No tienes permisos para realizar esta acción"
- **Test 404**: Error de cliente no encontrado con mensaje descriptivo
- **Test 400 (duplicados)**: Errores específicos para documento y email duplicados
- **Test 400 (referencias)**: Errores de validación para FKs inexistentes
- **Test 400 (longitud)**: Errores indicando límite de 100 caracteres excedido
- **Test 400 (formato)**: Errores específicos para formato de documento inválido
- **Validaciones de negocio**: Todas las reglas de CustomerUpdateSerializer aplicadas
- **Auditoría**: Registro de cambios mediante audit_sdk en casos exitosos

## Resultado Obtenido
Todos los 9 casos de prueba ejecutados exitosamente:
- test_update_success_200: OK - Cliente actualizado correctamente
- test_update_no_permission_403: OK - Permiso denegado correctamente  
- test_update_not_found_404: OK - Cliente inexistente manejado
- test_update_duplicate_document_400: OK - Validación de documento duplicado
- test_update_duplicate_email_400: OK - Validación de email duplicado
- test_update_invalid_document_type_400: OK - Tipo documento inexistente rechazado
- test_update_invalid_person_type_400: OK - Tipo persona inexistente rechazado
- test_update_field_length_validation_400: OK - Límites de longitud aplicados
- test_update_invalid_document_format_400: OK - Formato de documento validado

Simulación JWT: Funcional mediante unittest.mock.patch
Sistema de auditoría: Mockeado exitosamente sin efectos secundarios
Tiempo de ejecución: ~0.3 segundos
Cobertura: 100% de escenarios de validación cubiertos

## Estado
Aprobado

## Fecha Ejecución
13/10/2025

Alejandro S
---
