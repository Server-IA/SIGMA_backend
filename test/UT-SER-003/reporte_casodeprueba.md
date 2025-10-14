# Reporte de Pruebas Unitarias - UT-SER-003

## Resumen Ejecutivo
- **Total de Pruebas**: 17
- **Pruebas Exitosas**: 17 ✅
- **Pruebas Fallidas**: 0 ❌
- **Tasa de Éxito**: 100.0%
- **Fecha de Ejecución**: 14/10/2025
- **Ejecutado por**: Juan Camilo

---

## UT-SER-003

**Título**: 200 OK / 201 Created – Actualización exitosa (camino feliz)

**Payload**:
```json
{
  "service_name": "Mantenimiento PreventivoSOSo",
  "description": "Servicio de mantenimiento preventivo estándar",
  "service_type": 17,
  "base_price": 150000.0,
  "price_unit": 17,
  "applicable_tax": 1,
  "tax_rate": 19.0,
  "is_vat_exempt": false
}
```

**Resultado Esperado**: HTTP 200

**Resultado Obtenido**: ✅ **PASÓ** - HTTP 200

**Estado**: ✅ **EXITOSA**

**Fecha Ejecución**: 14/10/2025

**Ejecutado por**: Juan Camilo

---

## UT-SER-003.1

**Título**: 409 Conflict – Nombre duplicado

**Payload**:
```json
{
  "service_name": "Mantenimiento PreventivoSOSo",
  "description": "desc",
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

**Fecha Ejecución**: 14/10/2025

**Ejecutado por**: Juan Camilo

---

## UT-SER-003.2

**Título**: 400 Bad Request – Campos obligatorios faltantes

**Payload**:
```json
{
  "service_name": "",
  "description": "x",
  "service_type": null,
  "base_price": null,
  "price_unit": null,
  "applicable_tax": null,
  "tax_rate": null,
  "is_vat_exempt": false
}
```

**Resultado Esperado**: HTTP 400

**Resultado Obtenido**: ✅ **PASÓ** - HTTP 400

**Estado**: ✅ **EXITOSA**

**Fecha Ejecución**: 14/10/2025

**Ejecutado por**: Juan Camilo

---

## UT-SER-003.3

**Título**: 400 – Precio base negativo

**Payload**:
```json
{
  "service_name": "Srv X",
  "description": "x",
  "service_type": 17,
  "base_price": -1.0,
  "price_unit": 17,
  "applicable_tax": 1,
  "tax_rate": 19.0,
  "is_vat_exempt": false
}
```

**Resultado Esperado**: HTTP 400

**Resultado Obtenido**: ✅ **PASÓ** - HTTP 400

**Estado**: ✅ **EXITOSA**

**Fecha Ejecución**: 14/10/2025

**Ejecutado por**: Juan Camilo

---

## UT-SER-003.4

**Título**: 400 – Precio base en cero

**Payload**:
```json
{
  "service_name": "Srv X",
  "description": "x",
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

**Fecha Ejecución**: 14/10/2025

**Ejecutado por**: Juan Camilo

---

## UT-SER-003.5

**Título**: 400 – Unidad de precio fuera de categoría válida

**Payload**:
```json
{
  "service_name": "Srv X",
  "description": "x",
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

**Fecha Ejecución**: 14/10/2025

**Ejecutado por**: Juan Camilo

---

## UT-SER-003.6

**Título**: 400 – Tipo de servicio fuera de su categoría

**Payload**:
```json
{
  "service_name": "Srv X",
  "description": "x",
  "service_type": 88,
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

**Fecha Ejecución**: 14/10/2025

**Ejecutado por**: Juan Camilo

---

## UT-SER-003.7

**Título**: 400 – Nombre vacío o solo espacios

**Payload**:
```json
{
  "service_name": " ",
  "description": "x",
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

**Fecha Ejecución**: 14/10/2025

**Ejecutado por**: Juan Camilo

---

## UT-SER-003.8

**Título**: 400 – Longitud máxima de nombre superada (max_length=100)

**Payload**:
```json
{
  "service_name": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
  "description": "x",
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

**Fecha Ejecución**: 14/10/2025

**Ejecutado por**: Juan Camilo

---

## UT-SER-003.9

**Título**: 400 – Longitud máxima de descripción superada (max_length=500)

**Payload**:
```json
{
  "service_name": "Srv X",
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

**Fecha Ejecución**: 14/10/2025

**Ejecutado por**: Juan Camilo

---

## UT-SER-003.10

**Título**: 400 – Tasa de impuesto inválida cuando hay impuesto aplicable

**Payload**:
```json
{
  "service_name": "Srv X",
  "description": "x",
  "service_type": 17,
  "base_price": 150000.0,
  "price_unit": 17,
  "applicable_tax": 1,
  "tax_rate": 0,
  "is_vat_exempt": false
}
```

**Resultado Esperado**: HTTP 400

**Resultado Obtenido**: ✅ **PASÓ** - HTTP 400

**Estado**: ✅ **EXITOSA**

**Fecha Ejecución**: 14/10/2025

**Ejecutado por**: Juan Camilo

---

## UT-SER-003.11

**Título**: 200 – Servicio exento de IVA (is_vat_exempt=true) ignora tax_rate

**Payload**:
```json
{
  "service_name": "Servicio Exento",
  "description": "x",
  "service_type": 17,
  "base_price": 1000.0,
  "price_unit": 17,
  "applicable_tax": 0,
  "tax_rate": 0,
  "is_vat_exempt": true
}
```

**Resultado Esperado**: HTTP 200

**Resultado Obtenido**: ✅ **PASÓ** - HTTP 200

**Estado**: ✅ **EXITOSA**

**Fecha Ejecución**: 14/10/2025

**Ejecutado por**: Juan Camilo

---

## UT-SER-003.12

**Título**: 403 Forbidden – Usuario sin permiso service.update

**Payload**:
```json
{
  "service_name": "Srv X",
  "description": "x",
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

**Fecha Ejecución**: 14/10/2025

**Ejecutado por**: Juan Camilo

---

## UT-SER-003.13

**Título**: 404 Not Found – Servicio no existe

**Payload**:
```json
{
  "service_name": "Srv X",
  "description": "x",
  "service_type": 17,
  "base_price": 150000.0,
  "price_unit": 17,
  "applicable_tax": 1,
  "tax_rate": 19.0,
  "is_vat_exempt": false
}
```

**Resultado Esperado**: HTTP 404

**Resultado Obtenido**: ✅ **PASÓ** - HTTP 404

**Estado**: ✅ **EXITOSA**

**Fecha Ejecución**: 14/10/2025

**Ejecutado por**: Juan Camilo

---

## UT-SER-003.14

**Título**: 500 / 503 – Error técnico al guardar (rollback)

**Payload**:
```json
{
  "service_name": "Srv X",
  "description": "x",
  "service_type": 17,
  "base_price": 150000.0,
  "price_unit": 17,
  "applicable_tax": 1,
  "tax_rate": 19.0,
  "is_vat_exempt": false
}
```

**Resultado Esperado**: HTTP 500

**Resultado Obtenido**: ✅ **PASÓ** - HTTP 500

**Estado**: ✅ **EXITOSA**

**Fecha Ejecución**: 14/10/2025

**Ejecutado por**: Juan Camilo

---

## UT-SER-003.15

**Título**: 422 – Tipo de dato inválido (ej.: tax_rate string)

**Payload**:
```json
{
  "service_name": "Srv",
  "description": "x",
  "service_type": 17,
  "base_price": 1000.0,
  "price_unit": 17,
  "applicable_tax": 1,
  "tax_rate": "diecinueve",
  "is_vat_exempt": false
}
```

**Resultado Esperado**: HTTP 400

**Resultado Obtenido**: ✅ **PASÓ** - HTTP 400

**Estado**: ✅ **EXITOSA**

**Fecha Ejecución**: 14/10/2025

**Ejecutado por**: Juan Camilo

---

## UT-SER-003.16

**Título**: 200 – Actualización parcial (solo algunos campos)

**Payload**:
```json
{
  "service_name": "Nueva Descripción Solo",
  "description": "Solo cambio descripción"
}
```

**Resultado Esperado**: HTTP 200

**Resultado Obtenido**: ✅ **PASÓ** - HTTP 200

**Estado**: ✅ **EXITOSA**

**Fecha Ejecución**: 14/10/2025

**Ejecutado por**: Juan Camilo

---

