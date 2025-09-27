# Reporte de Pruebas HU-MAQ-013 – Actualizar Información de Uso

Fecha: 2025-09-27 20:40:46 UTC



## UT-MAQ-001 – Actualizar maquinaria propia con limpieza de tenencia

- Metodo: PUT
- URL: /machinery-usage/1/update/
- Status: 200
- Esperado: {'status': 200}

### Payload enviado
```json
{
  "is_own": true,
  "usage_hours": 170.25,
  "distance_value": 1400.125,
  "distance_unit": 701,
  "usage_condition": 6,
  "responsible_user": 1,
  "justification": "Corrección de horas y distancia tras auditoría.",
  "tenancy_type": "",
  "contract_end_date": ""
}
```

### Respuesta
```json
{
  "success": true,
  "message": "Información de uso actualizada correctamente"
}
```

Resultado: APROBADO

---

## UT-MAQ-002 – Actualizar maquinaria no propia con campos obligatorios

- Metodo: PATCH
- URL: /machinery-usage/4/update/
- Status: 200
- Esperado: {'status': 200}

### Payload enviado
```json
{
  "is_own": false,
  "tenancy_type": 1102,
  "contract_end_date": "2026-09-01",
  "responsible_user": 1,
  "justification": "Cambio de modalidad de tenencia."
}
```

### Respuesta
```json
{
  "success": true,
  "message": "Información de uso actualizada correctamente"
}
```

Resultado: APROBADO

---

## UT-MAQ-003 – Rechazo por permisos insuficientes

- Metodo: PUT
- URL: /machinery-usage/5/update/
- Status: 403
- Esperado: {'status': 403}

### Payload enviado
```json
{
  "usage_hours": 200.5,
  "responsible_user": 1,
  "justification": "Intento sin permisos"
}
```

### Respuesta
```json
{
  "message": "No tiene permisos para actualizar una ficha de uso de la maquinaria."
}
```

Resultado: APROBADO

---

## UT-MAQ-004 – Justificación obligatoria si no está en 'En registro'

- Metodo: PUT
- URL: /machinery-usage/7/update/
- Status: 400
- Esperado: {'status': 400}

### Payload enviado
```json
{
  "usage_hours": 250.0,
  "responsible_user": 1
}
```

### Respuesta
```json
{
  "success": false,
  "message": "Error de validación al actualizar la información de uso",
  "details": {
    "justification": [
      "La justificación es obligatoria cuando la maquinaria no está en estado 'En registro'. Estado actual: 'Activa'"
    ]
  }
}
```

Resultado: APROBADO

---

## UT-MAQ-005 – Permitir actualización sin justificación en 'En registro'

- Metodo: PATCH
- URL: /machinery-usage/10/update/
- Status: 200
- Esperado: {'status': 200}

### Payload enviado
```json
{
  "usage_hours": 50.0,
  "distance_value": 100.5,
  "responsible_user": 1
}
```

### Respuesta
```json
{
  "success": true,
  "message": "Información de uso actualizada correctamente"
}
```

Resultado: APROBADO

---

## UT-MAQ-006 – Faltan campos obligatorios cuando no es propia

- Metodo: PATCH
- URL: /machinery-usage/12/update/
- Status: 400
- Esperado: {'status': 400}

### Payload enviado
```json
{
  "is_own": false,
  "tenancy_type": 1102,
  "responsible_user": 1,
  "justification": "Cambio sin completar campos obligatorios"
}
```

### Respuesta
```json
{
  "success": false,
  "message": "Error de validación al actualizar la información de uso",
  "details": {
    "contract_end_date": [
      "La fecha fin de contrato es obligatoria cuando la maquinaria no es propia."
    ]
  }
}
```

Resultado: APROBADO

---

## UT-MAQ-007 – Validación de números negativos

- Metodo: PUT
- URL: /machinery-usage/13/update/
- Status: 400
- Esperado: {'status': 400}

### Payload enviado
```json
{
  "usage_hours": -50.25,
  "distance_value": -100.567,
  "responsible_user": 1,
  "justification": "Prueba de validación números negativos"
}
```

### Respuesta
```json
{
  "success": false,
  "message": "Error de validación al actualizar la información de uso",
  "details": {
    "usage_hours": [
      "Las horas de uso no pueden ser negativas."
    ],
    "distance_value": [
      "La distancia recorrida no puede ser negativa."
    ]
  }
}
```

Resultado: APROBADO

---

## UT-MAQ-008 – Validación de categorías de catálogos

- Metodo: PUT
- URL: /machinery-usage/15/update/
- Status: 400
- Esperado: {'status': 400}

### Payload enviado
```json
{
  "usage_condition": 999,
  "distance_unit": 888,
  "tenancy_type": 777,
  "is_own": false,
  "contract_end_date": "2026-01-01",
  "responsible_user": 1,
  "justification": "Prueba validación catálogos"
}
```

### Respuesta
```json
{
  "success": false,
  "message": "Error de validación al actualizar la información de uso",
  "details": {
    "usage_condition": [
      "El estado de uso debe pertenecer a la categoría 'Estados de uso de la maquinaria'."
    ],
    "distance_unit": [
      "La unidad de distancia debe pertenecer a la categoría 'Longitud'."
    ],
    "tenancy_type": [
      "El tipo de tenencia debe pertenecer a la categoría 'Tenencia'."
    ]
  }
}
```

Resultado: APROBADO

---

## UT-MAQ-009 – Ficha de uso inexistente devuelve 404 (especificación)

- Metodo: PUT
- URL: /machinery-usage/999999/update/
- Status: 400
- Esperado: {'status': 404}

### Payload enviado
```json
{
  "usage_hours": 100.0,
  "responsible_user": 1,
  "justification": "Prueba con ID inexistente"
}
```

### Respuesta
```json
{
  "success": false,
  "message": "Error al actualizar la información de uso de la maquinaria",
  "details": "No MachineryUsageSheet matches the given query."
}
```

Resultado: NO APROBADO

---

## UT-MAQ-010 – PATCH conserva no enviados y fechas

- Metodo: PATCH
- URL: /machinery-usage/19/update/
- Status: 200
- Esperado: {'status': 200}

### Payload enviado
```json
{
  "usage_hours": 300.5,
  "responsible_user": 1,
  "justification": "Actualización parcial solo de horas"
}
```

### Respuesta
```json
{
  "success": true,
  "message": "Información de uso actualizada correctamente"
}
```

Resultado: APROBADO

---
