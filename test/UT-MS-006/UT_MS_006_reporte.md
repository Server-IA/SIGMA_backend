# UT-MS-006 - Consultar Datos Históricos de Solicitud

## Descripción
Como jefe de maquinaria, quiero consultar datos históricos de una solicitud finalizada mediante el endpoint GET `/data/{service_request_code}/by_request/` (permiso 172: monitoring.list_data_by_request), para analizar el comportamiento operativo, rendimiento logístico y consumo de la maquinaria mediante gráficas y comparaciones visuales.

## Precondiciones
- Usuario autenticado con rol "Jefe de maquinaria" o equivalente.
- Usuario tiene asignado el permiso con ID 172 (monitoring.list_data_by_request).
- Existe al menos una solicitud de servicio en el sistema.
- Existen registros de telemetría (Data) asociados a la solicitud.

## Datos de Entrada
```json
{
  "BASE_URL": "http://localhost:8000",
  "ENDPOINT": "/data/{service_request_code}/by_request/",
  "METHOD": "GET",
  "PERMISSION_ID": 172,
  "USER_ROLE": "Jefe de maquinaria",
  "SERVICE_REQUEST_EXAMPLE": {
    "id_request": "SOL-2025-0072",
    "customer": "Cliente ABC",
    "scheduled_start_date": "2025-11-06T23:10:10",
    "scheduled_end_date": "2025-11-06T23:13:11"
  },
  "QUERY_FILTERS": {
    "start_date": "2025-11-06T23:10:10 (ISO 8601, opcional)",
    "end_date": "2025-11-06T23:13:11 (ISO 8601, opcional)",
    "machinery_id": "1 (entero, opcional)",
    "operator_id": "1 (entero, opcional)"
  }
}
```

## Pasos (AAA)

### Arrange
- Crear usuario autenticado con rol "Jefe de maquinaria" y permiso 172 en el JWT payload.
- Crear o usar una solicitud de servicio (service_request) existente con código ejemplo: SOL-2025-0072.
- Preparar registros de telemetría (Data) asociados a la solicitud con diversos parámetros (velocidad, RPM, temperatura, etc.).
- Mockear la función `get_machinery_data` para simular los datos históricos retornados por la base de datos.

### Act
- Realizar petición GET a `/data/{service_request_code}/by_request/` con los parámetros de filtro (start_date, end_date, machinery_id, operator_id).
- Validar la autenticación JWT y verificación del permiso 172.
- Procesar los filtros e invocar `get_machinery_data` con los parámetros correspondientes.
- Serializar los datos con DataSerializer y retornar la respuesta.

### Assert
- Caso exitoso sin filtros: status 200, respuesta contiene lista de maquinarias con datos de telemetría (operating_time_hours, total_distance_km, effective_working_hours, parameters).
- Caso exitoso con filtros de fecha: status 200, `get_machinery_data` invocado con start_date y end_date correctos.
- Caso exitoso con filtro machinery_id: status 200, `get_machinery_data` invocado con machinery_id como entero.
- Caso exitoso con filtro operator_id: status 200, `get_machinery_data` invocado con operator_id como entero.
- Caso exitoso con todos los filtros: status 200, todos los parámetros (dates, machinery_id, operator_id) pasan correctamente.
- Sin permiso (172): status 403, mensaje "No tiene permiso para acceder al historial de los datos de la solicitud".
- Solicitud no encontrada: status 404, mensaje "Solicitud no encontrada".
- machinery_id inválido (no entero): status 400, mensaje "El parámetro machinery_id debe ser un número entero".
- operator_id inválido (no entero): status 400, mensaje "El parámetro operator_id debe ser un número entero".
- Formato de fecha inválido: status 400, mensaje "Formato de fecha inválido. Use el formato ISO 8601".
- end_date anterior a start_date: status 400, mensaje "La fecha de fin no puede ser anterior a la fecha de inicio".
- Resultado vacío (filtros sin coincidencias): status 200, lista vacía.
- Permiso en múltiples roles: status 200 si el permiso existe en cualquiera de los roles del usuario.

## Resultado Esperado
1) Endpoint GET `/data/{service_request_code}/by_request/` accesible y funcional.
2) Validación de permiso 172 correcta (rechaza acceso sin permisos, permite con permiso).
3) Filtros de fecha (start_date, end_date) procesados y validados (formato ISO 8601, end_date >= start_date).
4) Filtros de machinery_id y operator_id validados como enteros.
5) Respuesta exitosa contiene estructura JSON con:
   - Lista de maquinarias (id_machinery, machinery_name, serial_number).
   - Usuario operario (id_user, user_name).
   - Dispositivo (id_device, IMEI).
   - Datos agregados (operating_time_hours, total_distance_km, effective_working_hours).
   - Parámetros históricos con data_points y statistics (max, min, average).
6) Errores retornan status HTTP apropiado (400, 403, 404, 500) con mensaje descriptivo.

## Resultado Obtenido
- Exitosa por pruebas unitarias. Verificado:
  - Endpoint responde 200 OK para solicitud válida con permiso 172 y sin filtros.
  - Filtros de fecha (start_date, end_date) aceptados en formato ISO 8601 y validados correctamente.
  - Filtro machinery_id convertido a entero y pasado a `get_machinery_data`.
  - Filtro operator_id convertido a entero y pasado a `get_machinery_data`.
  - Validación rechaza valores no enteros para machinery_id y operator_id (status 400).
  - Validación rechaza fechas en formato inválido (status 400).
  - Validación rechaza end_date < start_date (status 400).
  - Acceso denegado sin permiso 172 (status 403).
  - Acceso denegado si solicitud no existe (status 404).
  - Respuesta exitosa con todos los filtros combinados.
  - Respuesta exitosa retorna lista vacía si no hay resultados.
  - Permiso funcionalmente verificado en múltiples roles del usuario.
  - DataSerializer invocado correctamente con contexto (request, start_date, end_date, machinery_id, operator_id).

## Estado / Fecha / Ejecutor
- Estado: Aprobado
- Fecha: 2025-11-08
- Ejecutor: Alejandro S
