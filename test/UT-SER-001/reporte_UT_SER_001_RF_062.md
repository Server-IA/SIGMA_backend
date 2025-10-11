# Reporte de Pruebas Unitarias - UT-SER-001

## Resumen Ejecutivo
- **Total de Pruebas**: 16
- **Pruebas Exitosas**: 16 ✅
- **Pruebas Fallidas**: 0 ❌
- **Tasa de Éxito**: 100.0%
- **Fecha de Ejecución**: 11/10/2025
- **Ejecutado por**: Sistema de Pruebas Automatizadas

---

## UT-SER-001

**Título**: 201 Created – Registro exitoso (camino feliz)

**Payload**:
```json
{
  "service_name": "Mantenimiento Preventivo Estándar",
  "description": "Servicio de mantenimiento preventivo estándar",
  "service_type": 17,
  "base_price": 150000.0,
  "price_unit": 17,
  "applicable_tax": 1,
  "tax_rate": 19.0,
  "is_vat_exempt": false
}
```

**Resultado Esperado**: HTTP 201

**Resultado Obtenido**: ✅ **PASÓ** - HTTP 201

**Estado**: ✅ **EXITOSA**

**Fecha Ejecución**: 11/10/2025

**Ejecutado por**: Sistema de Pruebas Automatizadas

---

## UT-SER-001.1

**Título**: 400 Bad Request – Campo service_name vacío

**Payload**:
```json
{
  "service_name": "",
  "description": "Servicio de mantenimiento preventivo estándar",
  "service_type": 17,
  "base_price": 150000.0,
  "price_unit": 17,
  "applicable_tax": 1,
  "tax_rate": 19.0,
  "is_vat_exempt": false
}
```

**Resultado Esperado**: HTTP 400

**Resultado Obtenido**: ✅ **PASÓ** - HTTP 400

**Estado**: ✅ **EXITOSA**

**Fecha Ejecución**: 11/10/2025

**Ejecutado por**: Sistema de Pruebas Automatizadas

---

## UT-SER-001.2

**Título**: 400 Bad Request – Campo service_type nulo

**Payload**:
```json
{
  "service_name": "Mantenimiento Preventivo Estándar",
  "description": "Servicio de mantenimiento preventivo estándar",
  "service_type": null,
  "base_price": 150000.0,
  "price_unit": 17,
  "applicable_tax": 1,
  "tax_rate": 19.0,
  "is_vat_exempt": false
}
```

**Resultado Esperado**: HTTP 400

**Resultado Obtenido**: ✅ **PASÓ** - HTTP 400

**Estado**: ✅ **EXITOSA**

**Fecha Ejecución**: 11/10/2025

**Ejecutado por**: Sistema de Pruebas Automatizadas

---

## UT-SER-001.3

**Título**: 400 Bad Request – Campo base_price nulo

**Payload**:
```json
{
  "service_name": "Mantenimiento Preventivo Estándar",
  "description": "Servicio de mantenimiento preventivo estándar",
  "service_type": 17,
  "base_price": null,
  "price_unit": 17,
  "applicable_tax": 1,
  "tax_rate": 19.0,
  "is_vat_exempt": false
}
```

**Resultado Esperado**: HTTP 400

**Resultado Obtenido**: ✅ **PASÓ** - HTTP 400

**Estado**: ✅ **EXITOSA**

**Fecha Ejecución**: 11/10/2025

**Ejecutado por**: Sistema de Pruebas Automatizadas

---

## UT-SER-001.4

**Título**: 400 Bad Request – Campo price_unit nulo

**Payload**:
```json
{
  "service_name": "Mantenimiento Preventivo Estándar",
  "description": "Servicio de mantenimiento preventivo estándar",
  "service_type": 17,
  "base_price": 150000.0,
  "price_unit": null,
  "applicable_tax": 1,
  "tax_rate": 19.0,
  "is_vat_exempt": false
}
```

**Resultado Esperado**: HTTP 400

**Resultado Obtenido**: ✅ **PASÓ** - HTTP 400

**Estado**: ✅ **EXITOSA**

**Fecha Ejecución**: 11/10/2025

**Ejecutado por**: Sistema de Pruebas Automatizadas

---

## UT-SER-001.5

**Título**: 400 Bad Request – Campo applicable_tax nulo

**Payload**:
```json
{
  "service_name": "Mantenimiento Preventivo Estándar",
  "description": "Servicio de mantenimiento preventivo estándar",
  "service_type": 17,
  "base_price": 150000.0,
  "price_unit": 17,
  "applicable_tax": null,
  "tax_rate": 19.0,
  "is_vat_exempt": false
}
```

**Resultado Esperado**: HTTP 400

**Resultado Obtenido**: ✅ **PASÓ** - HTTP 400

**Estado**: ✅ **EXITOSA**

**Fecha Ejecución**: 11/10/2025

**Ejecutado por**: Sistema de Pruebas Automatizadas

---

## UT-SER-001.6

**Título**: 400 Bad Request – Nombre de servicio duplicado

**Payload**:
```json
{
  "service_name": "Mantenimiento Preventivo Estándar",
  "description": "Servicio de mantenimiento preventivo estándar",
  "service_type": 17,
  "base_price": 150000.0,
  "price_unit": 17,
  "applicable_tax": 1,
  "tax_rate": 19.0,
  "is_vat_exempt": false
}
```

**Resultado Esperado**: HTTP 400

**Resultado Obtenido**: ✅ **PASÓ** - HTTP 400

**Estado**: ✅ **EXITOSA**

**Fecha Ejecución**: 11/10/2025

**Ejecutado por**: Sistema de Pruebas Automatizadas

---

## UT-SER-001.7

**Título**: 400 Bad Request – Precio base igual a 0

**Payload**:
```json
{
  "service_name": "Mantenimiento Preventivo Estándar",
  "description": "Servicio de mantenimiento preventivo estándar",
  "service_type": 17,
  "base_price": 0.0,
  "price_unit": 17,
  "applicable_tax": 1,
  "tax_rate": 19.0,
  "is_vat_exempt": false
}
```

**Resultado Esperado**: HTTP 400

**Resultado Obtenido**: ✅ **PASÓ** - HTTP 400

**Estado**: ✅ **EXITOSA**

**Fecha Ejecución**: 11/10/2025

**Ejecutado por**: Sistema de Pruebas Automatizadas

---

## UT-SER-001.8

**Título**: 400 Bad Request – Precio base negativo

**Payload**:
```json
{
  "service_name": "Mantenimiento Preventivo Estándar",
  "description": "Servicio de mantenimiento preventivo estándar",
  "service_type": 17,
  "base_price": -100.0,
  "price_unit": 17,
  "applicable_tax": 1,
  "tax_rate": 19.0,
  "is_vat_exempt": false
}
```

**Resultado Esperado**: HTTP 400

**Resultado Obtenido**: ✅ **PASÓ** - HTTP 400

**Estado**: ✅ **EXITOSA**

**Fecha Ejecución**: 11/10/2025

**Ejecutado por**: Sistema de Pruebas Automatizadas

---

## UT-SER-001.9

**Título**: 400 Bad Request – Tipo de servicio de categoría incorrecta

**Payload**:
```json
{
  "service_name": "Mantenimiento Preventivo Estándar",
  "description": "Servicio de mantenimiento preventivo estándar",
  "service_type": 99,
  "base_price": 150000.0,
  "price_unit": 17,
  "applicable_tax": 1,
  "tax_rate": 19.0,
  "is_vat_exempt": false
}
```

**Resultado Esperado**: HTTP 400

**Resultado Obtenido**: ✅ **PASÓ** - HTTP 400

**Estado**: ✅ **EXITOSA**

**Fecha Ejecución**: 11/10/2025

**Ejecutado por**: Sistema de Pruebas Automatizadas

---

## UT-SER-001.10

**Título**: 400 Bad Request – Unidad de precio de categoría incorrecta

**Payload**:
```json
{
  "service_name": "Mantenimiento Preventivo Estándar",
  "description": "Servicio de mantenimiento preventivo estándar",
  "service_type": 17,
  "base_price": 150000.0,
  "price_unit": 99,
  "applicable_tax": 1,
  "tax_rate": 19.0,
  "is_vat_exempt": false
}
```

**Resultado Esperado**: HTTP 400

**Resultado Obtenido**: ✅ **PASÓ** - HTTP 400

**Estado**: ✅ **EXITOSA**

**Fecha Ejecución**: 11/10/2025

**Ejecutado por**: Sistema de Pruebas Automatizadas

---

## UT-SER-001.11

**Título**: 400 Bad Request – Nombre de servicio muy largo (101 caracteres)

**Payload**:
```json
{
  "service_name": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
  "description": "Servicio de mantenimiento preventivo estándar",
  "service_type": 17,
  "base_price": 150000.0,
  "price_unit": 17,
  "applicable_tax": 1,
  "tax_rate": 19.0,
  "is_vat_exempt": false
}
```

**Resultado Esperado**: HTTP 400

**Resultado Obtenido**: ✅ **PASÓ** - HTTP 400

**Estado**: ✅ **EXITOSA**

**Fecha Ejecución**: 11/10/2025

**Ejecutado por**: Sistema de Pruebas Automatizadas

---

## UT-SER-001.12

**Título**: 400 Bad Request – Descripción muy larga (501 caracteres)

**Payload**:
```json
{
  "service_name": "Mantenimiento Preventivo Estándar",
  "description": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
  "service_type": 17,
  "base_price": 150000.0,
  "price_unit": 17,
  "applicable_tax": 1,
  "tax_rate": 19.0,
  "is_vat_exempt": false
}
```

**Resultado Esperado**: HTTP 400

**Resultado Obtenido**: ✅ **PASÓ** - HTTP 400

**Estado**: ✅ **EXITOSA**

**Fecha Ejecución**: 11/10/2025

**Ejecutado por**: Sistema de Pruebas Automatizadas

---

## UT-SER-001.13

**Título**: 401 Unauthorized – Usuario no autenticado

**Payload**:
```json
{
  "service_name": "Mantenimiento Preventivo Estándar",
  "description": "Servicio de mantenimiento preventivo estándar",
  "service_type": 17,
  "base_price": 150000.0,
  "price_unit": 17,
  "applicable_tax": 1,
  "tax_rate": 19.0,
  "is_vat_exempt": false
}
```

**Resultado Esperado**: HTTP 401

**Resultado Obtenido**: ✅ **PASÓ** - HTTP 401

**Estado**: ✅ **EXITOSA**

**Fecha Ejecución**: 11/10/2025

**Ejecutado por**: Sistema de Pruebas Automatizadas

---

## UT-SER-001.14

**Título**: 403 Forbidden – Usuario sin permisos suficientes

**Payload**:
```json
{
  "service_name": "Mantenimiento Preventivo Estándar",
  "description": "Servicio de mantenimiento preventivo estándar",
  "service_type": 17,
  "base_price": 150000.0,
  "price_unit": 17,
  "applicable_tax": 1,
  "tax_rate": 19.0,
  "is_vat_exempt": false
}
```

**Resultado Esperado**: HTTP 403

**Resultado Obtenido**: ✅ **PASÓ** - HTTP 403

**Estado**: ✅ **EXITOSA**

**Fecha Ejecución**: 11/10/2025

**Ejecutado por**: Sistema de Pruebas Automatizadas

---

## UT-SER-001.15

**Título**: Performance – Tiempo de respuesta: 0.014s (límite: 3s)

**Payload**:
```json
{
  "service_name": "Servicio de Prueba Performance",
  "description": "Servicio de prueba para medir rendimiento",
  "service_type": 17,
  "base_price": 150000.0,
  "price_unit": 17,
  "applicable_tax": 1,
  "tax_rate": 19.0,
  "is_vat_exempt": false
}
```

**Resultado Esperado**: HTTP 201

**Resultado Obtenido**: ✅ **PASÓ** - HTTP 201

**Estado**: ✅ **EXITOSA**

**Fecha Ejecución**: 11/10/2025

**Ejecutado por**: Sistema de Pruebas Automatizadas

---

