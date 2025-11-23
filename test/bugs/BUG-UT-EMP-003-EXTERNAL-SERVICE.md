# BUG: Endpoint /employees/{id}/detail/ — fallo por manejo de servicio externo

**ID:** BUG-UT-EMP-003-EXTERNAL-SERVICE

**Resumen**
El endpoint `GET /employees/{id}/detail/` no cumple la especificación respecto a la integración con el microservicio de usuarios (`AUTH_SERVICE`).

- No prioriza los campos devueltos por el servicio externo (p. ej. `email`) cuando están disponibles; devuelve en su lugar el `email` local del modelo `Employee`.
- Cuando la consulta al servicio externo falla (excepción, timeout o respuesta inesperada), la implementación actual registra el error en logs pero lo suprime; la vista responde HTTP 200 en vez de devolver HTTP 500 tal como documentado.

**Qué debería pasar (según la documentación)**
- `personal_info.email` debe mostrar el email devuelto por el microservicio de usuarios cuando éste exista.
- Si hay un fallo de procesamiento relacionado con la consulta al servicio externo (p. ej. excepción de red, respuesta inválida), el endpoint debe retornar HTTP 500 con el siguiente formato JSON:

```json
{
  "success": false,
  "message": "Ocurrió un error al procesar la solicitud.",
  "error": "Descripción técnica del error..."
}
```

**Qué pasó en realidad (evidencia)**
- UT-EMP-003-01 (detalle completo): El test creó un `Employee` con `email='full@test.com'` y además configuró datos mock del servicio externo con `email='user123@test.com'`. La respuesta devolvió `"email": "full@test.com"` (email local) y el test falló:

```
E   AssertionError: assert 'full@test.com' == 'user123@test.com'
```

- UT-EMP-003-07 (simulación de fallo del servicio externo): El test forzó una excepción en el helper de usuarios. La vista registró el error en los logs pero respondió `200 OK` en vez de `500`. Fracciones relevantes del log/captura de pytest:

```
Error inesperado consultando servicio externo de usuarios: External Service Error
ERROR    service_requests.utils.external_user_helper:external_user_helper.py:84 Error inesperado consultando servicio externo de usuarios: External Service Error
ERROR    payroll.serializers.employee_contracts_serializers.employee_detail_serializer:employee_detail_serializer.py:197 Error consultando servicio externo de usuarios: External Service Error

FAILED test/UT-EMP-003/test_UT_EMP_003.py::TestEmployeeDetail::test_ut_emp_003_07_internal_error - assert 200 == 500
```

**Pasos para reproducir**
1. Levantar los servicios con `docker-compose up --build` (o usar el entorno local de desarrollo). Asegurarse de que `web` está accesible en `http://127.0.0.1:8000`.
2. Ejecutar la suite de tests relevante o invocar manualmente:

- Ejecutar tests (desde host):
```powershell
docker-compose exec web pytest -q test/UT-EMP-003 -q
```

- Ejecutar el test unitario específico (verbose):
```powershell
docker-compose exec web pytest -q test/UT-EMP-003::TestEmployeeDetail::test_ut_emp_003_01_full_detail -vv
docker-compose exec web pytest -q test/UT-EMP-003::TestEmployeeDetail::test_ut_emp_003_07_internal_error -vv
```

- Llamada manual con curl/Postman (requiere token válido):
```powershell
# desde host, ejecutado dentro del contenedor web para que la llamada use la misma red y env vars
docker-compose exec web /bin/sh -c "curl -sS -H 'Authorization: Bearer <TOKEN>' http://127.0.0.1:8000/employees/123/detail/ -D -"
```

**Notas sobre pruebas manuales (Postman / curl)**
- Sí: puedes probar el endpoint con Postman o `curl` siempre que tu `web` esté en ejecución y tengas un token válido (Authorization: Bearer <TOKEN>). La llamada hará una petición al microservicio definido por `AUTH_SERVICE_URL` desde dentro del contenedor `web`.
- Si `AUTH_SERVICE_URL` apunta a un servicio real disponible, la respuesta incluirá los datos externos (si están) y podrás comprobar `personal_info.email` con Postman.
- Si quieres simular un fallo del servicio externo (respuesta 500 o desconexión), tienes dos opciones:
  1. Levantar un mock HTTP local que responda 500 en las rutas que el código consulta (`/users/users/basic-user-list/by-ids` y `/users/users/by-document/{doc}`), y volver a desplegar `web` con `AUTH_SERVICE_URL` apuntando al mock (requiere reiniciar el contenedor o cambiar la configuración de entorno). Ejemplo de mock (Python/Flask) más abajo.
  2. Cambiar `AUTH_SERVICE_URL` a una dirección no enrutada (p. ej. `http://10.255.255.1:8081`) y reiniciar `web` — esto provocará una excepción de conexión en la llamada.

**Mock simple (para pruebas locales)**
Guarda este script como `mock_auth_service.py` y ejecútalo en el host (requiere Python + Flask):

```python
from flask import Flask, request, jsonify
app = Flask(__name__)

@app.route('/users/users/basic-user-list/by-ids', methods=['POST'])
def basic_list():
    # Para simular éxito, devolver JSON con data. Para simular fallo, usar status=500.
    payload = request.get_json() or {}
    ids = payload.get('ids', [])
    # Simular éxito para id 123
    data = []
    for i in ids:
        if int(i) == 123:
            data.append({
                'id': 123,
                'name': 'Juan',
                'first_last_name': 'Veru',
                'second_last_name': 'Sarmiento',
                'document_number': '1079172265',
                'email': 'user123@test.com'
            })
    return jsonify({'data': data}), 200

@app.route('/users/users/by-document/<doc>', methods=['GET'])
def by_document(doc):
    # Simular fallo: uncomment next line to return 500
    # return 'Error', 500
    if doc == '1079172265':
        return jsonify({'id': 123, 'document_number': doc, 'email': 'user123@test.com'}), 200
    return jsonify({}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8081)
```

Si ejecutas el mock en el host en el puerto `8081`, reasigna `AUTH_SERVICE_URL` en el contenedor `web` apuntando a `http://host.docker.internal:8081` (Windows/Mac) o al host IP (Linux), luego reinicia `web`.

**Severidad propuesta**
- MEDIA — Funcionalidad degradada. La UX y las integraciones dependen de datos externos; el servicer error supressed puede esconder fallos serios.

**Propuesta de corrección (cambio mínimo recomendado)**
1. En `payroll/serializers/.../employee_detail_serializer.py`, preferir el email del servicio externo cuando esté presente, por ejemplo:
```py
email = user_data.get('email') if user_data and user_data.get('email') else getattr(obj, 'email', None)
```
2. En `service_requests/utils/external_user_helper.py`, no silenciar excepciones inesperadas: registrar y relanzar (raise) para que la vista pueda manejarlo y devolver 500 según la especificación.

Estos cambios hacen que:
- El endpoint muestre el email externo cuando exista.
- Errores al consultar el servicio externo provoquen una respuesta 500, como la documentación indica.

**Archivos/ubicaciones relevantes**
- `payroll/serializers/employee_contracts_serializers/employee_detail_serializer.py`
- `service_requests/utils/external_user_helper.py`
- Test afectado: `test/UT-EMP-003/test_UT_EMP_003.py`

---

Si quieres, puedo (según tus indicaciones):
- crear un PR con los cambios de corrección mínimos propuestos (modificaría producción), o
- preparar instrucciones paso a paso para reproducir el fallo desde Postman incluyendo cómo ejecutar el mock y reiniciar `web` con `AUTH_SERVICE_URL` apuntando al mock (sin tocar código), o
- ahora mismo guardar este bug report en el repo (ya lo hice) y luego preparar un ticket más formal para JIRA/GitHub con patches propuestos.

Dime cómo prefieres proceder: crear PR (fix), o sólo dejar el bug report y preparar pasos para reproducir localmente (mock + restart).