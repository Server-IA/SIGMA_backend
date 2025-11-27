# Reporte de Pruebas Unitarias - UT-NOM-007 (007-file)

## Endpoint: `GET /payroll/{id_payroll}/download/`

**Fecha de Ejecución:** 2025-11-26
**Permiso Requerido:** ID 191 - `payroll.download`

---

## Resumen Ejecutivo

| Métrica | Valor |
|--------:|:-----|
| **Total de Pruebas** | 12 |
| **Aprobadas** | 11 |
| **No Aprobadas** | 1 |
| **Tasa de Éxito** | 91.67% |
| **Tiempo de Ejecución (aprox.)** | 9s |

---

## Resultados por prueba

| ID Test | Título | Estado | Comentario |
|---------|--------|--------|-----------|
| UT-NOM-007-01 | Descarga exitosa de PDF con datos completos | ✅ APROBADO | PDF generado (mock) y headers correctos |
| UT-NOM-007-02 | Nómina no encontrada retorna 404 | ✅ APROBADO | 404 con mensaje esperado |
| UT-NOM-007-03 | Sin autenticación retorna 401 | ❌ FALLÓ | Se devolvió 403 con mensaje de permisos en vez de "no autenticado" |
| UT-NOM-007-04 | Sin permiso 191 retorna 403 | ✅ APROBADO | 403 cuando token sin permiso |
| UT-NOM-007-05 | Estructura del PDF (mock) | ✅ APROBADO | Generador llamado con args correctos |
| UT-NOM-007-06 | Nombre de archivo con timestamp | ✅ APROBADO | Content-Disposition con timestamp correcto |
| UT-NOM-007-07 | Devengos incluidos | ✅ APROBADO | Incrementos presentes en payroll pasado al generador |
| UT-NOM-007-08 | Deducciones incluidas | ✅ APROBADO | Deducciones presentes en payroll pasado al generador |
| UT-NOM-007-09 | Cálculo neto correcto | ✅ APROBADO | net_pay correcto tras devengos y deducciones |
| UT-NOM-007-10 | Datos del empleado precargados | ✅ APROBADO | Mock de usuarios externos retornado correctamente |
| UT-NOM-007-11 | Pie de página con usuario | ✅ APROBADO | Nombre del descargador pasado al generador |
| UT-NOM-007-12 | Error interno 500 con manejo correcto | ✅ APROBADO | Cuando el generador lanza Exception, la vista devuelve 500 |

---

## Detalle del fallo (UT-NOM-007-03)

**Descripción:** La prueba crea un cliente anónimo (sin Authorization header) y espera que la API devuelva 401 o al menos un mensaje que contenga "no autenticado". En ejecución se obtuvo HTTP 403 con mensaje: `"No tiene permisos para descargar nóminas."`.

**Salida de pytest (extracto):**

```
E   AssertionError: assert 'no autenticado' in 'no tiene permisos para descargar nóminas.'
WARNING  django.request:log.py:253 Forbidden: /payroll/1/download/
```

**Impacto:** Confusión entre falta de autenticación y falta de permisos; especificación REST no cumplida por parte de la API.

**Recomendación breve:** Ajustar la respuesta para clientes anónimos a 401 con mensaje claro (p.ej. "No autenticado"), o actualizar el test si la política del API es tratar ausencias de token como "sin permisos".

---

## Comandos útiles para reproducir

```powershell
# Ejecutar la suite completa UT-NOM-007
docker-compose exec web pytest /app/test/UT-NOM-007 -q

# Ejecutar test específico
docker-compose exec web pytest /app/test/UT-NOM-007/test_UT_NOM_007.py::TestPayrollDownload::test_ut_nom_007_03_unauthorized -q
```

---

**Generado:** 2025-11-26
**Autor:** Equipo de QA/Dev (automático)
