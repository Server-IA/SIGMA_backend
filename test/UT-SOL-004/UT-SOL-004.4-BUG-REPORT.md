# Reporte de Prueba Fallida - UT-SOL-004.4

**De:** Área de Pruebas (QA) - Nicolas Urrutia  
**Para:** Área de Desarrollo  
**Fecha:** 19 de Octubre, 2025  
**Prioridad:** Media  
**Módulo:** Solicitudes de Servicio  
**Endpoint:** `GET /service_requests/{id_request}/details/`

---

## 1. RESUMEN EJECUTIVO

La prueba **UT-SOL-004.4** ha fallado debido a que el endpoint no implementa validación de formato para el parámetro `id_request` antes de realizar la consulta a la base de datos.

**Comportamiento actual:** Retorna HTTP 404 (Not Found)  
**Comportamiento esperado:** Retorna HTTP 400 (Bad Request)

---

## 2. DESCRIPCIÓN DEL PROBLEMA

### 2.1 Caso de Prueba

| **ID** | UT-SOL-004.4 |
|--------|--------------|
| **Título** | Validación de formato de ID inválido |
| **Objetivo** | Verificar que el endpoint rechace IDs con formato inválido retornando HTTP 400 |
| **Endpoint** | `GET /service_requests/{id_request}/details/` |

### 2.2 Escenario de la Prueba

**Entrada:**
- **ID enviado:** `ABC-25-1` (formato inválido)
- **Usuario:** Autenticado con permisos válidos
- **Headers:** `Accept: application/json`

**Resultado Obtenido:**
```
HTTP Status: 404 Not Found
Body: {"error": "No se encontró la solicitud de servicio solicitada"}
```

**Resultado Esperado:**
```
HTTP Status: 400 Bad Request
Body: {"error": "Formato de ID de solicitud inválido"}
```

---

## 3. ANÁLISIS TÉCNICO

### 3.1 Flujo Actual del Código

**Archivo:** `service_requests/api/service_request_viewset.py`  
**Método:** `details(self, request, pk=None)` (líneas 62-96)

```python
@action(detail=True, methods=['get'])
def details(self, request, pk=None):
    try:
        # 1. Verificación de permisos ✓
        if not self.check_permission(request, 154):
            return Response({"error": "..."}, status=403)
        
        try:
            # 2. Búsqueda directa en BD SIN validación de formato ✗
            service_request = ServiceRequest.objects.get(id_request=pk)
            
            # 3. Serialización y respuesta
            serializer = ServiceRequestDetailSerializer(service_request, ...)
            return Response(serializer.data)
            
        except ServiceRequest.DoesNotExist:
            # 4. Retorna 404 para CUALQUIER caso de no encontrado
            return Response({"error": "..."}, status=404)
```

### 3.2 Problema Identificado

**El código actual no distingue entre:**

1. **ID con formato inválido** (ej: `ABC-25-1`, `123`, `SOL-XYZ`)
   - No cumple el patrón esperado
   - Debería retornar **400 Bad Request**

2. **ID con formato válido pero no existe** (ej: `SOL-2099-9999`)
   - Cumple el patrón pero no está en la BD
   - Debería retornar **404 Not Found**

**Consecuencia:** Ambos casos retornan 404, lo cual es semánticamente incorrecto según los estándares REST.

---

## 4. SOLUCIÓN PROPUESTA

### 4.1 Patrón de ID Esperado

Según la nomenclatura del sistema, los IDs de solicitud siguen el formato:

```
SOL-YYYY-NNNN

Donde:
- SOL = Prefijo literal (Solicitud)
- YYYY = Año (4 dígitos)
- NNNN = Número consecutivo (4 dígitos)

Ejemplos válidos:
- SOL-2025-0001
- SOL-2024-1234
- SOL-2025-0054

Ejemplos inválidos:
- ABC-25-1
- SOL-25-1
- SOL2025001
- 123456
- sol-2025-0001 (minúsculas)
```

### 4.2 Implementación Recomendada

**Opción 1: Validación con Regex (Recomendada)**

```python
import re
from django.shortcuts import get_object_or_404

@action(detail=True, methods=['get'])
def details(self, request, pk=None):
    """
    Obtiene los detalles completos de una solicitud de servicio por su ID.
    """
    try:
        # 1. Verificar permisos
        if not self.check_permission(request, 154):
            return Response(
                {"error": "No tiene permiso para ver los detalles de la solicitud"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # 2. NUEVO: Validar formato del ID antes de consultar BD
        id_pattern = r'^SOL-\d{4}-\d{4}$'
        if not re.match(id_pattern, pk):
            return Response(
                {
                    "error": "Formato de ID de solicitud inválido",
                    "detail": "El ID debe seguir el formato SOL-YYYY-NNNN (ej: SOL-2025-0001)"
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # 3. Buscar en BD (solo si formato es válido)
            service_request = ServiceRequest.objects.get(id_request=pk)
            
            # 4. Serializar y retornar
            serializer = ServiceRequestDetailSerializer(service_request, context={'request': request})
            return Response(serializer.data)
            
        except ServiceRequest.DoesNotExist:
            # 5. Retorna 404 SOLO si formato válido pero no existe
            return Response(
                {"error": "No se encontró la solicitud de servicio solicitada"},
                status=status.HTTP_404_NOT_FOUND
            )
            
    except Exception as e:
        logger.error(f"Error al obtener los detalles de la solicitud: {str(e)}")
        return Response(
            {"error": "Ocurrió un error al procesar la solicitud"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
```

**Opción 2: Validador Reutilizable (Mejor Práctica)**

Si otros endpoints también usan este formato, crear un validador centralizado:

```python
# En: service_requests/utils/validators.py
import re
from rest_framework.exceptions import ValidationError

def validate_request_id_format(id_request: str) -> bool:
    """
    Valida que el ID de solicitud siga el formato SOL-YYYY-NNNN.
    
    Args:
        id_request: ID a validar
        
    Returns:
        True si el formato es válido
        
    Raises:
        ValidationError: Si el formato es inválido
    """
    pattern = r'^SOL-\d{4}-\d{4}$'
    
    if not re.match(pattern, id_request):
        raise ValidationError(
            detail={
                "error": "Formato de ID de solicitud inválido",
                "detail": "El ID debe seguir el formato SOL-YYYY-NNNN (ej: SOL-2025-0001)",
                "received": id_request
            },
            code='invalid_format'
        )
    
    return True

# En: service_requests/api/service_request_viewset.py
from service_requests.utils.validators import validate_request_id_format
from rest_framework.exceptions import ValidationError

@action(detail=True, methods=['get'])
def details(self, request, pk=None):
    try:
        if not self.check_permission(request, 154):
            return Response(..., status=403)
        
        # Validar formato
        try:
            validate_request_id_format(pk)
        except ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        
        # Continuar con la lógica existente...
```

---

## 5. CASOS DE PRUEBA AFECTADOS

### 5.1 Casos que AHORA PASARÁN

| Caso | ID | Entrada | Status Esperado | Status Actual | Resultado |
|------|----|---------|--------------------|---------------|-----------|
| UT-SOL-004.4 | Formato inválido | `ABC-25-1` | 400 | 404 | ❌ FALLA |

### 5.2 Casos que DEBEN SEGUIR PASANDO

| Caso | ID | Entrada | Status Esperado | Status Actual | Resultado |
|------|----|---------|--------------------|---------------|-----------|
| UT-SOL-004.1 | ID válido existente | `SOL-2025-0054` | 200 | 200 | ✅ PASA |
| UT-SOL-004.3 | ID válido no existe | `SOL-2099-9999` | 404 | 404 | ✅ PASA |

**Importante:** La validación NO debe romper los casos existentes que ya funcionan.

---

## 6. EJEMPLOS DE VALIDACIÓN

### 6.1 IDs que deben retornar 400

```
❌ ABC-25-1           # Prefijo incorrecto
❌ SOL-25-1           # Año con 2 dígitos
❌ SOL-2025-1         # Consecutivo con menos de 4 dígitos
❌ SOL-2025-12345     # Consecutivo con más de 4 dígitos
❌ SOL2025-0001       # Sin guiones
❌ sol-2025-0001      # Minúsculas
❌ SOL-ABCD-0001      # Letras en año
❌ SOL-2025-ABCD      # Letras en consecutivo
❌ 123456             # Sin formato
❌ SOL-2025           # Incompleto
```

### 6.2 IDs que deben continuar con la consulta (retornar 200 o 404)

```
✅ SOL-2025-0001      # Formato válido
✅ SOL-2024-9999      # Formato válido
✅ SOL-2099-0000      # Formato válido (aunque no exista)
```

---

## 7. IMPACTO Y PRIORIDAD

### 7.1 Severidad

**Media** - No afecta la funcionalidad principal pero viola estándares REST y mejores prácticas.

### 7.2 Impacto

- ✅ **Backend:** Cambio localizado en un método
- ✅ **Frontend:** Sin cambios requeridos (solo mejora mensajes de error)
- ✅ **Base de datos:** Sin cambios
- ✅ **Otros endpoints:** Sin impacto (cambio aislado)

### 7.3 Beneficios del Fix

1. **Semántica HTTP correcta:** Distinción clara entre error del cliente (400) vs recurso no encontrado (404)
2. **Mensajes de error más claros:** El cliente sabrá exactamente qué está mal
3. **Prevención de consultas innecesarias:** No se consulta la BD si el formato es inválido
4. **Mejor debugging:** Los logs mostrarán el tipo correcto de error
5. **Cumplimiento de HU:** Requisito funcional documentado

---

## 8. EVIDENCIA DE LA PRUEBA

### 8.1 Salida de Pytest

```bash
FAILED test/UT-SOL-004/test-UT-SOL-004-V2.py::TestServiceRequestDetailsV2::test_UT_SOL_004_4_400_formato_invalido

[UT-SOL-004.4] Esperado: 400, Obtenido: 404

assert 404 == 400
 +  where 404 = <Response status_code=404, "application/json">.status_code
 +  and   400 = status.HTTP_400_BAD_REQUEST
```

### 8.2 Log del Sistema

```
WARNING  django.request:log.py:253 Not Found: /service_requests/ABC-25-1/details/
```

---

## 9. RECOMENDACIONES ADICIONALES

### 9.1 Documentación

Actualizar la documentación del endpoint para incluir:
- Formato esperado del parámetro `id_request`
- Códigos de respuesta posibles (400, 401, 403, 404, 500)
- Ejemplos de mensajes de error

### 9.2 Testing

Una vez implementado el fix:
1. Ejecutar la suite completa de UT-SOL-004 (33 casos)
2. Verificar que todos los casos pasen (33/33)
3. Confirmar que no se rompieron otros tests del módulo

### 9.3 Consistencia

Revisar si otros endpoints del mismo módulo tienen el mismo problema:
- `POST /service_requests/`
- `PUT /service_requests/{id_request}/`
- `DELETE /service_requests/{id_request}/`

---

## 10. CRITERIOS DE ACEPTACIÓN

La prueba se considerará **APROBADA** cuando:

- ✅ `GET /service_requests/ABC-25-1/details/` retorne **400 Bad Request**
- ✅ Mensaje de error indique claramente el problema de formato
- ✅ `GET /service_requests/SOL-2025-0054/details/` continúe retornando **200 OK**
- ✅ `GET /service_requests/SOL-2099-9999/details/` continúe retornando **404 Not Found**
- ✅ Los 32 casos de prueba que actualmente pasan sigan pasando
- ✅ El caso UT-SOL-004.4 pase exitosamente

---

## 11. ARCHIVOS A MODIFICAR

```
📁 service_requests/
  ├── 📁 api/
  │   └── 📄 service_request_viewset.py  ← MODIFICAR (línea ~62-96)
  └── 📁 utils/
      └── 📄 validators.py  ← CREAR (opcional, recomendado)
```

---

## 12. CONTACTO

Para cualquier duda o clarificación sobre esta prueba:

**Área de Pruebas (QA)**  
Nicolas Urrutia  
Fecha: 19 de Octubre, 2025

**Archivos de referencia:**
- Prueba: `test/UT-SOL-004/test-UT-SOL-004-V2.py` (líneas 214-229)
- Reporte: `test/UT-SOL-004/UT-SOL-004-REPORT.md`
- Endpoint: `service_requests/api/service_request_viewset.py` (método `details`)

---

## 13. ANEXOS

### 13.1 Estado Actual de la Suite

**Resultado general:** 32/33 pruebas aprobadas (96.97%)

```
✅ UT-SOL-004.1  - Detalle válido (200)
✅ UT-SOL-004.2  - Sin permiso (403)
✅ UT-SOL-004.3  - No existe (404)
❌ UT-SOL-004.4  - Formato inválido (400) ← ESTA PRUEBA
✅ UT-SOL-004.5  - Sin token (401)
... (28 pruebas más aprobadas)
```

### 13.2 Referencias

- RFC 7231 - HTTP/1.1 Semantics (Códigos de estado)
- REST API Best Practices
- Django REST Framework Documentation

---

**Fin del reporte**
