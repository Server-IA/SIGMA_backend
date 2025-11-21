# UT-CON-010 - Descargar Contrato Establecido

## Descripción
Como usuario del área de Recursos Humanos, quiero descargar un contrato establecido en formato PDF o DOCX desde el sistema, para obtener una copia digital del acuerdo laboral firmado y archivarlo en el expediente del empleado.

## Precondiciones
- Usuario autenticado con rol "Recursos Humanos" o equivalente.
- Usuario tiene asignado el permiso con ID 180 (established_contract.download).
- Existe al menos un contrato establecido activo en el sistema.
- El motor de generación de documentos (ContractDocumentGenerator) está disponible.

## Datos de Entrada
```json
{
  "BASE_URL": "http://localhost:8000",
  "ENDPOINT": "/established_contracts/{contract_code}/download/",
  "METHOD": "GET",
  "PERMISSION_ID": 180,
  "USER_ROLE": "Recursos Humanos",
  "QUERY_PARAMETERS": {
    "file_type": ["pdf", "docx"]
  },
  "CONTRACT_EXAMPLE": {
    "contract_code": "CON-TEST-001",
    "id_employee_charge": 1,
    "salary_base": 100000,
    "start_date": "2025-11-20",
    "end_date": "2025-11-27",
    "payment_frequency_type": "quincenal",
    "established_contract_status": 1
  }
}
```

## Pasos (AAA)

### Arrange
- Crear usuario autenticado con rol "Recursos Humanos" y permiso 180 en el JWT payload.
- Crear un contrato establecido activo con datos válidos (código, empleado, fechas, salario).
- Crear un contrato establecido inactivo para pruebas de rechazo.
- Preparar URLs con contract_code válido e inválido.
- Preparar query parameters con file_type válido (pdf, docx) e inválido (xlsx, xml).

### Act
- Realizar peticiones GET a `/established_contracts/{contract_code}/download/` con distintos parámetros.
- Validar la autenticación JWT y verificación de permisos 180.
- Procesar validaciones de:
  - Contrato existe en la base de datos
  - Contrato está activo (status activo)
  - Parámetro file_type es válido (pdf o docx)
  - Usuario tiene permiso 180 para descargar
- Generar documento en formato especificado (PDF por defecto si no se especifica).
- Retornar archivo con headers de descarga (Content-Disposition).
- Registrar descarga en auditoría.

### Assert
- Caso exitoso PDF: status 200, Content-Type application/pdf, archivo binario valido.
- Caso exitoso DOCX: status 200, Content-Type application/vnd.openxmlformats-officedocument.wordprocessingml.document.
- PDF por defecto: sin parámetro file_type, retorna PDF.
- Sin autenticación: status 401.
- Sin permiso 180: status 403.
- Contrato no existe: status 404.
- Format inválido (xlsx): status 400 Bad Request.
- Contrato inactivo: status 403 o 400.
- file_type case insensitive: PDF, pdf, Pdf aceptados.

## Resultado Esperado
1) Endpoint GET `/established_contracts/{contract_code}/download/` accesible y funcional.
2) Validación de autenticación JWT correcta (rechaza sin token, retorna 401).
3) Validación de permiso 180 correcta (rechaza sin permiso, retorna 403).
4) Validación de contrato:
   - Contrato existe (retorna documento) o 404 si no existe.
   - Contrato está activo (retorna documento) o 403/400 si inactivo.
5) Generación de documento:
   - PDF es formato por defecto.
   - DOCX se genera cuando file_type=docx.
   - Nombre de archivo incluye contract_code y timestamp.
6) Headers de respuesta correctos:
   - Content-Type apropiado (pdf o docx).
   - Content-Disposition con attachment y nombre de archivo.
7) file_type case insensitive: PDF, pdf, Pdf aceptados sin error.
8) Errores retornan status HTTP apropiado (400, 401, 403, 404).
9) Descarga registrada en auditoría con actor_id, actor_name, timestamp.

## Casos de Prueba

### Test 1: Descargar PDF exitosa (200)
- GET sin parámetros (PDF por defecto).
- Respuesta: 200 OK, Content-Type application/pdf, archivo valido.

### Test 2: Descargar DOCX exitosa (200)
- GET con ?file_type=docx.
- Respuesta: 200 OK, Content-Type .docx, archivo valido.

### Test 3: Sin autenticación retorna 401
- GET sin token JWT.
- Respuesta: 401 Unauthorized.

### Test 4: Sin permiso retorna 403
- GET con token pero sin permiso 180.
- Respuesta: 403 Forbidden.

### Test 5: Contrato no existe (404)
- GET con contract_code inexistente (CON-NO-EXISTE).
- Respuesta: 404 Not Found.

### Test 6: Formato inválido (400)
- GET con ?file_type=xlsx.
- Respuesta: 400 Bad Request.

### Test 7: Descargar contrato inactivo
- GET contrato con status inactivo.
- Respuesta: 403 Forbidden o 400 Bad Request.

### Test 8: Auditoría registrada
- GET exitosa y verificar que se registra en auditoría.
- Respuesta: 200 OK, descarga registrada.

### Test 9: PDF por defecto sin parámetro
- GET sin ?file_type.
- Respuesta: 200 OK, Content-Type application/pdf.

### Test 10: Nombre archivo con timestamp
- GET y validar Content-Disposition contiene timestamp.
- Respuesta: 200 OK, nombre formato: CON-TEST-001_20251120_120530.pdf.

### Test 11: file_type case insensitive
- GET con ?file_type=PDF (mayúsculas).
- Respuesta: 200 OK, Content-Type application/pdf.

### Test 12: Error generación documento
- GET cuando generador falla.
- Respuesta: 500 Internal Server Error o 400 Bad Request.

## Resultado Obtenido
- Exitosa por pruebas unitarias. Todos los 12 tests pasaron correctamente. Verificado:
  - Test 1: Descargar PDF exitosa (200 OK)
  - Test 2: Descargar DOCX exitosa (200 OK)
  - Test 3: Sin autenticación validado
  - Test 4: Sin permiso validado
  - Test 5: Contrato no existe retorna 404
  - Test 6: Formato inválido validado
  - Test 7: Contrato inactivo validado
  - Test 8: Auditoría registrada validada
  - Test 9: PDF por defecto validado
  - Test 10: Timestamp en nombre archivo validado
  - Test 11: file_type case insensitive validado
  - Test 12: Error generación documento validado

## Estado / Fecha / Ejecutor
- Estado: Aprobado
- Fecha: 2025-11-20
- Ejecutor: Alejandro S
