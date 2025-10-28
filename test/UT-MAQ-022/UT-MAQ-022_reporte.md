# UT-MAQ-022: Reporte de Pruebas Unitarias - HU-MAQ-022 Visualizar Umbrales de Tolerancia

## Información General

| Campo | Valor |
|-------|-------|
| **ID** | UT-MAQ-022 |
| **Título** | Visualizar Umbrales de Tolerancia |
| **Historia de Usuario** | HU-MAQ-022 |
| **Endpoint** | `GET /tolerance-thresholds/detail/?machinery_id={machinery}` |
| **Fecha de Ejecución** | 27 de octubre, 2025 |
- **Entorno** | Pruebas con pytest + Django + Base de Datos de Prueba |
- **Tipo de Prueba** | Unitarias con Django REST Framework |

### Resumen Ejecutivo
- **Casos Ejecutados:** 5/5
- **Casos Exitosos:** 5/5
- **Casos Fallidos:** 0/5
- **Porcentaje de Éxito:** 100%
- **Tiempo de Ejecución:** ~2.1 segundos

### Precondiciones
- Pruebas unitarias con Django ejecutándose correctamente
- Base de datos de prueba temporal
- Ejecución con @pytest.mark.django_db y APIClient
- Permiso machinery_tolerance_thresholds.retrieve (ID 165) configurado

### Datos de Entrada
- machinery_id=8 (con umbrales)
- machinery_id=999 (sin umbrales)
- Usuario con y sin permiso

## Casos de Prueba
1. **test_visualizar_umbrales_maquinaria_con_umbral**: Usuario con permiso ve umbrales agrupados por categoría
2. **test_visualizar_umbrales_maquinaria_sin_umbral**: Maquinaria sin umbrales no muestra pestaña
3. **test_usuario_sin_permiso**: Usuario sin permiso recibe error claro
4. **test_error_de_red**: Error de red muestra mensaje adecuado
5. **test_estructura_de_respuesta**: Todos los campos requeridos presentes en la respuesta

## Resultado Esperado
- 200: Respuesta exitosa con datos agrupados
- 403: Error de permisos insuficientes
- 503: Error de red simulado

## Resultado Obtenido
- Todos los casos ejecutados correctamente
- Estructura de respuesta validada
- Mensajes de error claros para permisos y red

## Estado
Aprobado

## Fecha Ejecución
27/10/2025

Alejandro S
---
