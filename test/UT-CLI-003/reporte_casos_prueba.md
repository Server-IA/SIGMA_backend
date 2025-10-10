# Reporte de Casos de Prueba - HU-CLI-003

## UT-CLI-003

**ID**  
UT-CLI-003  

**Título**  
200 OK – Detalle obtenido exitosamente (camino feliz, cliente con id_user)

**Descripción**  
Verificar que el endpoint retorna correctamente los datos completos del cliente cuando existe y el usuario tiene permisos válidos.

**Precondiciones**  
- Cliente con id_customer=49 existe
- Usuario autenticado con permiso 134 (customer.view_detail)
- Mock de CustomerDetailSerializer configurado correctamente

**Datos de Entrada**  
GET /api/customers/49/detail/

**Pasos (AAA)**  
Arrange: Usuario con permiso 134, cliente válido con datos completos.  
Act: Invocar endpoint con id_customer=49.  
Assert: Retorna HTTP 200 con "success": true, mensaje esperado y data con todos los campos del cliente.

**Resultado Esperado**  
200 OK y cuerpo:
```json
{ "success": true, "message": "Detalle del cliente obtenido exitosamente", "data": {...} }
```

**Resultado Obtenido**  
200 OK con estructura correcta de respuesta y datos del cliente completos.

**Estado**  
✅ PASÓ

**Fecha Ejecución**  
10/10/2025

**Ejecutado por**  
Juan Camilo

---

## UT-CLI-003.1

**ID**  
UT-CLI-003.1  

**Título**  
200 OK – Detalle obtenido exitosamente (cliente sin id_user)

**Descripción**  
Validar que el endpoint retorna correctamente el detalle del cliente aunque el campo id_user sea null.

**Precondiciones**  
- Cliente id_customer=50 existe y id_user=null
- Usuario autenticado con permiso 134

**Datos de Entrada**  
GET /api/customers/50/detail/

**Pasos (AAA)**  
Arrange: Mock cliente sin id_user.  
Act: GET /customers/50/detail/.  
Assert: HTTP 200 y el campo "id_user": null en el body.

**Resultado Esperado**  
200 con "success": true y "id_user": null en data.

**Resultado Obtenido**  
200 OK con "id_user": null correctamente manejado en la respuesta.

**Estado**  
✅ PASÓ

**Fecha Ejecución**  
10/10/2025

**Ejecutado por**  
Juan Camilo

---

## UT-CLI-003.2

**ID**  
UT-CLI-003.2  

**Título**  
404 Not Found – Cliente inexistente

**Descripción**  
Validar que el endpoint retorna un 404 cuando el cliente consultado no existe en la BD.

**Precondiciones**  
- No existe cliente con id_customer=9999

**Datos de Entrada**  
GET /api/customers/9999/detail/

**Pasos (AAA)**  
Arrange: Mock BD sin cliente 9999.  
Act: Invocar endpoint.  
Assert: Retorna HTTP 404 y mensaje "Cliente no encontrado".

**Resultado Esperado**  
```json
{ "success": false, "message": "Cliente no encontrado" }
```

**Resultado Obtenido**  
404 Not Found con mensaje "Cliente no encontrado" correcto.

**Estado**  
✅ PASÓ

**Fecha Ejecución**  
10/10/2025

**Ejecutado por**  
Juan Camilo

---

## UT-CLI-003.3

**ID**  
UT-CLI-003.3  

**Título**  
403 Forbidden – Usuario sin permiso 134

**Descripción**  
Verificar que el endpoint niega acceso si el usuario no cuenta con el permiso requerido (customer.view_detail).

**Precondiciones**  
- Usuario autenticado sin permiso 134

**Datos de Entrada**  
GET /api/customers/49/detail/

**Pasos (AAA)**  
Arrange: Usuario sin permiso.  
Act: Ejecutar GET.  
Assert: HTTP 403 con mensaje de error.

**Resultado Esperado**  
```json
{ "success": false, "message": "No tiene permisos para ver el detalle del cliente." }
```

**Resultado Obtenido**  
403 Forbidden con mensaje de permisos correcto.

**Estado**  
✅ PASÓ

**Fecha Ejecución**  
10/10/2025

**Ejecutado por**  
Juan Camilo

---

## UT-CLI-003.4

**ID**  
UT-CLI-003.4  

**Título**  
500 Internal Server Error – Excepción no controlada

**Descripción**  
Validar que si ocurre un error inesperado en la consulta o serialización, el endpoint retorna 500 con mensaje descriptivo.

**Precondiciones**  
- Simular excepción en Customer.objects.select_related().get()

**Datos de Entrada**  
GET /api/customers/49/detail/

**Pasos (AAA)**  
Arrange: Mock que lanza excepción.  
Act: Ejecutar GET.  
Assert: HTTP 500 con "success": false y "message": "Error al procesar la solicitud".

**Resultado Esperado**  
```json
{ "success": false, "message": "Error al procesar la solicitud" }
```

**Resultado Obtenido**  
500 Internal Server Error con mensaje de error genérico correcto.

**Estado**  
✅ PASÓ

**Fecha Ejecución**  
10/10/2025

**Ejecutado por**  
Juan Camilo

---

## UT-CLI-003.5

**ID**  
UT-CLI-003.5  

**Título**  
Validación de campos obligatorios en data serializada

**Descripción**  
Comprobar que el objeto retornado contiene todas las claves esperadas (identificación, contacto, dirección, estado, etc.).

**Precondiciones**  
- Cliente con datos completos y serializer configurado correctamente

**Datos de Entrada**  
GET /api/customers/49/detail/

**Pasos (AAA)**  
Arrange: Cliente válido con datos completos.  
Act: GET.  
Assert: data contiene: type_document_id, document_number, check_digit, person_type_name, name, first_last_name, email, phone, address, customer_statues_name.

**Resultado Esperado**  
Todos los campos presentes y con valores válidos no nulos.

**Resultado Obtenido**  
Todos los campos obligatorios presentes en la respuesta con valores válidos.

**Estado**  
✅ PASÓ

**Fecha Ejecución**  
10/10/2025

**Ejecutado por**  
Juan Camilo

---

## UT-CLI-003.6

**ID**  
UT-CLI-003.6  

**Título**  
Validación del serializer – Tipos de datos correctos

**Descripción**  
Verificar que el serializer retorna los tipos de datos correctos según el modelo (int, string, null).

**Precondiciones**  
- Mock serializer configurado con valores válidos

**Datos de Entrada**  
GET /api/customers/49/detail/

**Pasos (AAA)**  
Arrange: Cliente con datos válidos.  
Act: Ejecutar GET.  
Assert: Validar tipos (id_customer: int, document_number: int, name: str, email: str, etc.).

**Resultado Esperado**  
Todos los campos cumplen con el tipo de dato esperado.

**Resultado Obtenido**  
Todos los tipos de datos validados correctamente según el modelo.

**Estado**  
✅ PASÓ

**Fecha Ejecución**  
10/10/2025

**Ejecutado por**  
Juan Camilo

---

## UT-CLI-003.7

**ID**  
UT-CLI-003.7  

**Título**  
Validar mensaje y estructura de respuesta exitosa

**Descripción**  
Confirmar que el endpoint retorna siempre la estructura estándar de respuesta: success, message, data.

**Precondiciones**  
- Usuario con permiso 134

**Datos de Entrada**  
GET /api/customers/49/detail/

**Pasos (AAA)**  
Arrange: Mock response exitosa.  
Act: Invocar endpoint.  
Assert: Body tiene llaves success, message, data y message="Detalle del cliente obtenido exitosamente".

**Resultado Esperado**  
Estructura y texto de mensaje correctos.

**Resultado Obtenido**  
Estructura estándar de respuesta validada correctamente con mensaje esperado.

**Estado**  
✅ PASÓ

**Fecha Ejecución**  
10/10/2025

**Ejecutado por**  
Juan Camilo

---

## Resumen de Ejecución

| Caso de Prueba | Estado | Observaciones |
|----------------|--------|---------------|
| UT-CLI-003 | ✅ PASÓ | Detalle exitoso con id_user |
| UT-CLI-003.1 | ✅ PASÓ | Detalle exitoso sin id_user |
| UT-CLI-003.2 | ✅ PASÓ | Cliente inexistente (404) |
| UT-CLI-003.3 | ✅ PASÓ | Usuario sin permiso (403) |
| UT-CLI-003.4 | ✅ PASÓ | Error interno servidor (500) |
| UT-CLI-003.5 | ✅ PASÓ | Validación campos obligatorios |
| UT-CLI-003.6 | ✅ PASÓ | Validación tipos de datos |
| UT-CLI-003.7 | ✅ PASÓ | Estructura respuesta exitosa |

**Total de Pruebas:** 8  
**Pruebas Exitosas:** 8  
**Pruebas Fallidas:** 0  
**Porcentaje de Éxito:** 100%

**Fecha de Ejecución:** 10/10/2025  
**Ejecutado por:** Juan Camilo  
**Entorno:** Docker con PostgreSQL  
**Tiempo de Ejecución:** 5.77 segundos
