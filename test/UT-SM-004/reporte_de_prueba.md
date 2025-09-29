# Reporte de Pruebas UT-SM-004

## Información General

| **Campo** | **Información** |
|-----------|-----------------|
| **ID de Prueba** | UT-SM-004 |
| **Título** | Consulta de Detalle de Solicitudes de Mantenimiento |
| **Módulo** | Maintenance Request |
| **Endpoint** | GET /maintenance_request/{id}/detail/ |
| **Fecha de Ejecución** | September 29, 2025 |
| **Ejecutado por** | Juan Diego Samboni |
| **Estado General** | ✅ APROBADO |

## Descripción

Se detalla la validación del endpoint GET /maintenance_request/{id}/detail/ para obtener el detalle completo de solicitudes de mantenimiento, cubriendo casos de éxito, errores, permisos y validaciones de integridad.

## Precondiciones

- Usuario autenticado con permiso 123
- Base de datos con datos de prueba configurados
- Docker ejecutándose con servicios activos
- Existencia de solicitudes de mantenimiento en diferentes estados
- Modelos Django configurados (Machinery, MaintenanceRequest, etc.)

## Casos de Prueba Ejecutados

### UT-SM-004.1 - Consulta exitosa con permisos
| **Campo** | **Resultado** |
|-----------|---------------|
| **Objetivo** | Validar que un usuario con permiso 123 pueda obtener el detalle de una solicitud existente |
| **Datos de Entrada** | GET /maintenance_request/1/detail/ con permiso 123 |
| **Resultado Esperado** | Código 200 OK con todos los campos requeridos |
| **Resultado Obtenido** | ✅ PASSED - Respuesta exitosa con campos completos |
| **Estado** | APROBADO |

### UT-SM-004.2 - Solicitud inexistente
| **Campo** | **Resultado** |
|-----------|---------------|
| **Objetivo** | Validar manejo de ID no registrado |
| **Datos de Entrada** | GET /maintenance_request/9999/detail/ |
| **Resultado Esperado** | Código 404 Not Found |
| **Resultado Obtenido** | ✅ PASSED - Error 404 con mensaje apropiado |
| **Estado** | APROBADO |

### UT-SM-004.3 - Usuario sin permisos
| **Campo** | **Resultado** |
|-----------|---------------|
| **Objetivo** | Verificar que usuario sin permiso 123 no pueda acceder |
| **Datos de Entrada** | GET /maintenance_request/1/detail/ sin permiso 123 |
| **Resultado Esperado** | Código 403 Forbidden |
| **Resultado Obtenido** | ✅ PASSED - Error 403 con mensaje de permisos |
| **Estado** | APROBADO |

### UT-SM-004.4 - Solicitud rechazada
| **Campo** | **Resultado** |
|-----------|---------------|
| **Objetivo** | Validar respuesta para solicitud con status_id=12 (rechazada) |
| **Datos de Entrada** | GET /maintenance_request/3/detail/ |
| **Resultado Esperado** | Código 200 OK con status_name="rechazado" |
| **Resultado Obtenido** | ✅ PASSED - Estado rechazado correctamente mostrado |
| **Estado** | APROBADO |

### UT-SM-004.5 - Solicitud programada
| **Campo** | **Resultado** |
|-----------|---------------|
| **Objetivo** | Validar campos de programación para solicitud con status_id=13 |
| **Datos de Entrada** | GET /maintenance_request/4/detail/ |
| **Resultado Esperado** | Código 200 OK con scheduled_at y assigned_technician_id |
| **Resultado Obtenido** | ✅ PASSED - Campos de programación presentes |
| **Estado** | APROBADO |

### UT-SM-004.6 - Solicitud aprobada sin programar
| **Campo** | **Resultado** |
|-----------|---------------|
| **Objetivo** | Validar ausencia de campos de programación para status_id=11 |
| **Datos de Entrada** | GET /maintenance_request/5/detail/ |
| **Resultado Esperado** | Código 200 OK sin campos de programación |
| **Resultado Obtenido** | ✅ PASSED - Campos de programación ausentes correctamente |
| **Estado** | APROBADO |

### UT-SM-004.7 - Validación de integridad de maquinaria
| **Campo** | **Resultado** |
|-----------|---------------|
| **Objetivo** | Confirmar que machinery_serial y machinery_name no sean null |
| **Datos de Entrada** | GET /maintenance_request/6/detail/ |
| **Resultado Esperado** | Código 200 OK con campos de maquinaria no nulos |
| **Resultado Obtenido** | ✅ PASSED - Integridad de maquinaria validada |
| **Estado** | APROBADO |

### UT-SM-004.8 - Error de red/servidor no disponible
| **Campo** | **Resultado** |
|-----------|---------------|
| **Objetivo** | Validar manejo correcto de fallas de conexión |
| **Datos de Entrada** | GET /maintenance_request/1/detail/ con error simulado |
| **Resultado Esperado** | Código 500 con mensaje de error |
| **Resultado Obtenido** | ✅ PASSED - Error 500 manejado correctamente |
| **Estado** | APROBADO |

## Tests Adicionales

### Test de Usuario No Autenticado
- **Objetivo:** Validar respuesta para usuario sin autenticar
- **Resultado:** ✅ PASSED - Código 401 Unauthorized

### Test de Campos Obligatorios
- **Objetivo:** Verificar presencia de todos los campos requeridos
- **Resultado:** ✅ PASSED - Todos los campos presentes

### Test de Formato de Respuesta
- **Objetivo:** Validar estructura correcta de respuesta JSON
- **Resultado:** ✅ PASSED - Formato correcto validado

## Resumen de Resultados

| **Métrica** | **Valor** |
|-------------|-----------|
| **Total de Tests** | 11 |
| **Tests Exitosos** | 11 |
| **Tests Fallidos** | 0 |
| **Porcentaje de Éxito** | 100% |
| **Tiempo de Ejecución** | 2.72 segundos |

## Campos Validados en Respuesta

- ✅ id
- ✅ machinery_serial
- ✅ machinery_name
- ✅ maintenance_type_name
- ✅ description
- ✅ priority_name
- ✅ status_id
- ✅ status_name
- ✅ fecha_solicitud
- ✅ modification_date
- ✅ scheduled_at
- ✅ assigned_technician_id

## Códigos de Estado HTTP Validados

- ✅ 200 OK - Consulta exitosa
- ✅ 401 Unauthorized - Usuario no autenticado
- ✅ 403 Forbidden - Sin permisos
- ✅ 404 Not Found - Solicitud inexistente
- ✅ 500 Internal Server Error - Error de servidor

## Observaciones

1. **Sistema de Permisos:** Funciona correctamente con validación de permiso 123
2. **Manejo de Errores:** Todos los casos de error se manejan apropiadamente
3. **Integridad de Datos:** Campos de maquinaria siempre presentes
4. **Estados de Solicitud:** Diferentes estados se manejan correctamente
5. **Campos de Programación:** Presentes solo cuando corresponde

## Recomendaciones

1. ✅ **Aprobado para Producción:** Todos los casos de prueba pasan exitosamente
2. ✅ **Cobertura Completa:** Se validan todos los escenarios especificados
3. ✅ **Robustez:** Manejo adecuado de errores y casos edge
4. ✅ **Documentación:** Casos de prueba bien documentados

## Conclusión

El endpoint GET /maintenance_request/{id}/detail/ funciona correctamente en todos los escenarios probados. La implementación cumple con los requisitos especificados y maneja apropiadamente los casos de éxito y error.

**Estado Final: ✅ APROBADO - LISTO PARA PRODUCCIÓN**
