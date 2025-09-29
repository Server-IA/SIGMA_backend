**UT-MAQ-003 — HU-MAQ-003 Informe de Pruebas**
- **Archivo:** `test/UT-MAQ-003/test_UT_MAQ_003_HU_MAQ_003.py`
- **Fecha:** 2025-09-23
- **Ejecutor:** Django `manage.py test` dentro de Docker (servicio `web`) con verbosity=2

**Resumen**
- Total de pruebas: 9
- Aprobadas: 9
- Fallidas: 0
- Omitidas: 0

**Detalles de Pruebas**

### UT-MAQ-003.1
**Título**  
Creación exitosa de ficha técnica específica

**Descripción**  
Verificar que el endpoint crea la ficha técnica específica cuando se proporcionan datos válidos.

**Precondiciones**  
- Mock del método `get_serializer` del viewset configurado para devolver un serializador válido (is_valid=True, save y data presentes).
- Base de datos de prueba inicializada.

**Datos de Entrada**  
JSON con todos los campos requeridos: machinery_id, power, category, etc. (ver código de prueba para datos completos).

**Pasos (AAA)**  
- Arrange: Configurar mock del serializador para simular validación exitosa.
- Act: Enviar POST a /machinery-specific-sheet/ con datos válidos.
- Assert: Verificar status 201 y que la respuesta contenga success: true.

**Resultado Esperado**  
HTTP 201 Created, respuesta con success: true.

**Resultado Obtenido**  
Aprobado

**Estado**  
Aprobado

**Fecha Ejecución**  
2025-09-23

**Ejecutado por**  
Sistema

### UT-MAQ-003.2
**Título**  
Error por falta de machinery_id

**Descripción**  
Verificar que el endpoint retorna error cuando falta el campo machinery_id.

**Precondiciones**  
- Mock del método `get_serializer` configurado para lanzar ValidationError en is_valid.
- Base de datos de prueba inicializada.

**Datos de Entrada**  
JSON sin machinery_id, con otros campos válidos.

**Pasos (AAA)**  
- Arrange: Configurar mock para lanzar ValidationError con mensaje sobre machinery_id.
- Act: Enviar POST a /machinery-specific-sheet/ sin machinery_id.
- Assert: Verificar status 400 y error en machinery_id.

**Resultado Esperado**  
HTTP 400 Bad Request, error en machinery_id.

**Resultado Obtenido**  
Aprobado

**Estado**  
Aprobado

**Fecha Ejecución**  
2025-09-23

**Ejecutado por**  
Sistema

### UT-MAQ-003.3
**Título**  
Error por power inválido

**Descripción**  
Verificar que el endpoint retorna error cuando power es <= 0.

**Precondiciones**  
- Mock del método `get_serializer` configurado para lanzar ValidationError en is_valid.
- Base de datos de prueba inicializada.

**Datos de Entrada**  
JSON con power=0, otros campos válidos.

**Pasos (AAA)**  
- Arrange: Configurar mock para lanzar ValidationError con mensaje sobre power.
- Act: Enviar POST con power=0.
- Assert: Verificar status 400 y error en power.

**Resultado Esperado**  
HTTP 400 Bad Request, error en power.

**Resultado Obtenido**  
Aprobado

**Estado**  
Aprobado

**Fecha Ejecución**  
2025-09-23

**Ejecutado por**  
Sistema

### UT-MAQ-003.4
**Título**  
Error por categoría inválida

**Descripción**  
Verificar que el endpoint retorna error cuando category es inválida.

**Precondiciones**  
- Mock del método `get_serializer` configurado para lanzar ValidationError en is_valid.
- Base de datos de prueba inicializada.

**Datos de Entrada**  
JSON con category='InvalidCategory', otros campos válidos.

**Pasos (AAA)**  
- Arrange: Configurar mock para lanzar ValidationError con mensaje sobre category.
- Act: Enviar POST con category inválida.
- Assert: Verificar status 400 y error en category.

**Resultado Esperado**  
HTTP 400 Bad Request, error en category.

**Resultado Obtenido**  
Aprobado

**Estado**  
Aprobado

**Fecha Ejecución**  
2025-09-23

**Ejecutado por**  
Sistema

### UT-MAQ-003.5
**Título**  
Error por subcategoría inválida

**Descripción**  
Verificar que el endpoint retorna error cuando subcategory es inválida.

**Precondiciones**  
- Mock del método `get_serializer` configurado para lanzar ValidationError en is_valid.
- Base de datos de prueba inicializada.

**Datos de Entrada**  
JSON con subcategory='InvalidSubcategory', otros campos válidos.

**Pasos (AAA)**  
- Arrange: Configurar mock para lanzar ValidationError con mensaje sobre subcategory.
- Act: Enviar POST con subcategory inválida.
- Assert: Verificar status 400 y error en subcategory.

**Resultado Esperado**  
HTTP 400 Bad Request, error en subcategory.

**Resultado Obtenido**  
Aprobado

**Estado**  
Aprobado

**Fecha Ejecución**  
2025-09-23

**Ejecutado por**  
Sistema

### UT-MAQ-003.6
**Título**  
Error por falta de brand

**Descripción**  
Verificar que el endpoint retorna error cuando falta el campo brand.

**Precondiciones**  
- Mock del método `get_serializer` configurado para lanzar ValidationError en is_valid.
- Base de datos de prueba inicializada.

**Datos de Entrada**  
JSON sin brand, otros campos válidos.

**Pasos (AAA)**  
- Arrange: Configurar mock para lanzar ValidationError con mensaje sobre brand.
- Act: Enviar POST sin brand.
- Assert: Verificar status 400 y error en brand.

**Resultado Esperado**  
HTTP 400 Bad Request, error en brand.

**Resultado Obtenido**  
Aprobado

**Estado**  
Aprobado

**Fecha Ejecución**  
2025-09-23

**Ejecutado por**  
Sistema

### UT-MAQ-003.7
**Título**  
Error por year inválido

**Descripción**  
Verificar que el endpoint retorna error cuando year está fuera de rango.

**Precondiciones**  
- Mock del método `get_serializer` configurado para lanzar ValidationError en is_valid.
- Base de datos de prueba inicializada.

**Datos de Entrada**  
JSON con year=1800, otros campos válidos.

**Pasos (AAA)**  
- Arrange: Configurar mock para lanzar ValidationError con mensaje sobre year.
- Act: Enviar POST con year inválido.
- Assert: Verificar status 400 y error en year.

**Resultado Esperado**  
HTTP 400 Bad Request, error en year.

**Resultado Obtenido**  
Aprobado

**Estado**  
Aprobado

**Fecha Ejecución**  
2025-09-23

**Ejecutado por**  
Sistema

### UT-MAQ-003.8
**Título**  
Error por working_hours inválido

**Descripción**  
Verificar que el endpoint retorna error cuando working_hours es negativo.

**Precondiciones**  
- Mock del método `get_serializer` configurado para lanzar ValidationError en is_valid.
- Base de datos de prueba inicializada.

**Datos de Entrada**  
JSON con working_hours=-1, otros campos válidos.

**Pasos (AAA)**  
- Arrange: Configurar mock para lanzar ValidationError con mensaje sobre working_hours.
- Act: Enviar POST con working_hours negativo.
- Assert: Verificar status 400 y error en working_hours.

**Resultado Esperado**  
HTTP 400 Bad Request, error en working_hours.

**Resultado Obtenido**  
Aprobado

**Estado**  
Aprobado

**Fecha Ejecución**  
2025-09-23

**Ejecutado por**  
Sistema

### UT-MAQ-003.9
**Título**  
Error por fuel_capacity inválido

**Descripción**  
Verificar que el endpoint retorna error cuando fuel_capacity es <= 0.

**Precondiciones**  
- Mock del método `get_serializer` configurado para lanzar ValidationError en is_valid.
- Base de datos de prueba inicializada.

**Datos de Entrada**  
JSON con fuel_capacity=0, otros campos válidos.

**Pasos (AAA)**  
- Arrange: Configurar mock para lanzar ValidationError con mensaje sobre fuel_capacity.
- Act: Enviar POST con fuel_capacity=0.
- Assert: Verificar status 400 y error en fuel_capacity.

**Resultado Esperado**  
HTTP 400 Bad Request, error en fuel_capacity.

**Resultado Obtenido**  
Aprobado

**Estado**  
Aprobado

**Fecha Ejecución**  
2025-09-23

**Ejecutado por**  
Sistema

**Recomendaciones / Próximos pasos**
- Hacer commit de las pruebas a la rama `tests` y abrir PR.
- Considerar agregar pruebas para casos extremos en serializadores anidados y manejo de subida de archivos (imágenes/documentos).
- Opcionalmente agregar fixtures de fábrica para evitar repetir `valid_data` en múltiples pruebas.
