
````markdown
---
# BUG-UT-NOM-007-AUTH: Respuesta incorrecta para clientes no autenticados

**Resumen**
El endpoint `GET /payroll/{id_payroll}/download/` no cumple la especificación respecto al manejo de autenticación para clientes anónimos.

- Cuando se realiza una petición sin token, la API responde HTTP 403 con el mensaje "No tiene permisos para descargar nóminas." en vez de indicar explícitamente falta de autenticación (401 o mensaje "no autenticado").
- Esto puede confundir a clientes e integraciones que esperan distinguir entre "no autenticado" y "sin permisos".

**Qué debería pasar (según la documentación)**
- Peticiones sin credenciales válidas deben devolver HTTP 401 Unauthorized, o al menos un mensaje que indique claramente que el usuario no está autenticado ("no autenticado").
- La distinción entre falta de autenticación y falta de permisos debe ser clara en la respuesta.

**Qué pasó en realidad (evidencia)**
- Petición anónima (sin token):
	- HTTP 403
	- Body: `{"message":"No tiene permisos para descargar nóminas."}`
- Test unitario falló:
	- `AssertionError: assert 'no autenticado' in 'no tiene permisos para descargar nóminas.'`
- Ejecución manual:
	- `curl -i -X GET http://127.0.0.1:8000/payroll/1/download/` → HTTP 403, mensaje de permisos
- Petición con token inválido:
	- HTTP 401
	- Body: `{"detail":"Token inválido."}`

**Pasos para reproducir**
1. Ejecutar el test:
	 ```powershell
	 docker-compose exec web pytest /app/test/UT-NOM-007/test_UT_NOM_007.py::TestPayrollDownload::test_ut_nom_007_03_unauthorized -q
	 ```
2. Llamar manualmente sin Authorization header:
	 ```bash
	 curl -i -X GET http://127.0.0.1:8000/payroll/1/download/
	 ```

**Severidad propuesta**
- BAJA/MEDIA — No bloquea el flujo principal pero puede causar confusión y dificulta la integración con clientes que esperan respuestas RESTful estándar.

**Archivos/ubicaciones relevantes**
- `payroll/api/payroll_viewset.py` (ViewSet y configuración de permisos)
- `users/permissions.py` (permiso personalizado)
- `test/UT-NOM-007/test_UT_NOM_007.py` (test afectado)

---
Generado por: sistema de pruebas automatizado
````
