# Reporte de Pruebas Unitarias - UT-MAQ-001 a UT-MAQ-011
## HU-MAQ-001: Creación de Maquinaria General

**Fecha de Ejecución:** September 20, 2025  
**Ejecutado por:** Juan Nicolás Urrutia  

---

### ID: UT-MAQ-001

**Título:** Verificar creación exitosa de maquinaria con todos los campos válidos  

**Descripción:**  
Esta prueba verifica que se pueda crear una maquinaria exitosamente cuando se proporcionan todos los campos requeridos con valores válidos.  

**Precondiciones:**  
- Usuario autenticado creado (id_user=1)  
- Categorías de estatus, tipos primarios/secundarios, marcas y modelos creados en la base de datos  
- Dispositivo de telemetría disponible  
- Base de datos limpia para evitar conflictos de unicidad  

**Datos de Entrada:**  
- machinery_name: 'Tractor Test 001'  
- serial_number: 'ST-001-2024'  
- machinery_type: ID del tipo primario (Tractor)  
- id_model: ID del modelo creado  
- id_city: '1'  
- machinery_secondary_type: ID del tipo secundario  
- manufacturing_year: '2020'  
- tariff_subheading: '8701.10.00.00'  
- id_device: ID del dispositivo creado  
- responsible_user: ID del usuario (1)  
- image: Archivo de imagen válido (JPEG)  

**Pasos (AAA):**  
**Arrange:** Configurar usuario autenticado, crear todas las entidades relacionadas (categorías, tipos, marcas, modelos, dispositivo) en setup_method.  
**Act:** Enviar solicitud POST al endpoint '/machinery/create-general-sheet/' con los datos válidos en formato multipart.  
**Assert:** Verificar que el código de estado sea 201, que 'success' sea True, y que el mensaje contenga 'creada exitosamente'.  

**Resultado Esperado:**  
Código de estado 201, respuesta con success=True y mensaje de creación exitosa.  

**Resultado Obtenido:**  
Código de estado: 201  
Respuesta: {'success': True, 'message': 'Maquinaria y ficha general creada exitosamente'}  

**Estado:** PASÓ  

---

### ID: UT-MAQ-002

**Título:** Verificar validación de campos obligatorios faltantes  

**Descripción:**  
Esta prueba verifica que la API valide correctamente cuando faltan campos obligatorios en la solicitud.  

**Precondiciones:**  
- Usuario autenticado creado  
- Endpoint disponible  

**Datos de Entrada:**  
- Diccionario vacío {} (sin campos)  

**Pasos (AAA):**  
**Arrange:** Configurar cliente autenticado.  
**Act:** Enviar solicitud POST con datos vacíos.  
**Assert:** Verificar código 400, success=False, mensaje 'Error de validación', y que todos los campos obligatorios estén en 'details'.  

**Resultado Esperado:**  
Código 400 con lista de campos requeridos faltantes.  

**Resultado Obtenido:**  
Código de estado: 400  
Respuesta: {'success': False, 'message': 'Error de validación', 'details': {'machinery_name': [...], 'serial_number': [...], ...}}  

**Estado:** PASÓ  

---

### ID: UT-MAQ-003

**Título:** Verificar validación de nombre de maquinaria duplicado  

**Descripción:**  
Esta prueba verifica que no se permita crear maquinaria con un nombre que ya existe.  

**Precondiciones:**  
- Usuario autenticado  
- Maquinaria existente con nombre 'Tractor Duplicado'  

**Datos de Entrada:**  
- machinery_name: 'Tractor Duplicado' (duplicado)  
- serial_number: 'ST-NEW-001'  
- Otros campos válidos  

**Pasos (AAA):**  
**Arrange:** Crear maquinaria existente con el mismo nombre.  
**Act:** Intentar crear nueva maquinaria con nombre duplicado.  
**Assert:** Código 400, 'machinery_name' en details.  

**Resultado Esperado:**  
Error 400 indicando nombre duplicado.  

**Resultado Obtenido:**  
Código de estado: 400  
Respuesta: {'success': False, 'message': 'Error de validación', 'details': {'machinery_name': ['Ya existe una máquina con este nombre.'], ...}}  

**Estado:** PASÓ  

---

### ID: UT-MAQ-004

**Título:** Verificar validación de número de serie duplicado  

**Descripción:**  
Esta prueba verifica que no se permita crear maquinaria con un número de serie que ya existe.  

**Precondiciones:**  
- Usuario autenticado  
- Maquinaria existente con serial 'SR-DUPLICATE-001'  

**Datos de Entrada:**  
- machinery_name: 'Tractor Nuevo'  
- serial_number: 'SR-DUPLICATE-001' (duplicado)  
- Otros campos válidos  

**Pasos (AAA):**  
**Arrange:** Crear maquinaria existente con el mismo serial.  
**Act:** Intentar crear nueva con serial duplicado.  
**Assert:** Código 400, 'serial_number' en details.  

**Resultado Esperado:**  
Error 400 indicando serial duplicado.  

**Resultado Obtenido:**  
Código de estado: 400  
Respuesta: {'success': False, 'message': 'Error de validación', 'details': {'serial_number': ['Ya existe una máquina con este número de serie.'], ...}}  

**Estado:** PASÓ  

---

### ID: UT-MAQ-005

**Título:** Verificar validación de tipo de maquinaria inválido  

**Descripción:**  
Esta prueba verifica que se valide correctamente cuando se proporciona un ID de tipo de maquinaria que no existe.  

**Precondiciones:**  
- Usuario autenticado  
- Tipos válidos creados  

**Datos de Entrada:**  
- machinery_type: '999' (inválido)  
- Otros campos válidos  

**Pasos (AAA):**  
**Arrange:** Configurar datos con tipo inválido.  
**Act:** Enviar POST con tipo inexistente.  
**Assert:** Código 400, 'machinery_type' en details.  

**Resultado Esperado:**  
Error 400 indicando tipo inválido.  

**Resultado Obtenido:**  
Código de estado: 400  
Respuesta: {'success': False, 'message': 'Error de validación', 'details': {'machinery_type': ['Invalid pk "999" - object does not exist.']}}  

**Estado:** PASÓ  

---

### ID: UT-MAQ-006

**Título:** Verificar validación de año de fabricación inválido  

**Descripción:**  
Esta prueba verifica que se valide el año de fabricación dentro de rangos válidos (posterior a 1900 y no mayor al año actual).  

**Precondiciones:**  
- Usuario autenticado  

**Datos de Entrada:**  
- manufacturing_year: '1899' y '2026' (fuera de rango)  
- Otros campos válidos  

**Pasos (AAA):**  
**Arrange:** Configurar datos con años inválidos.  
**Act:** Enviar POST para cada año inválido.  
**Assert:** Código 400, 'manufacturing_year' en details.  

**Resultado Esperado:**  
Error 400 para años fuera de rango.  

**Resultado Obtenido:**  
Para 1899: Código 400, {'manufacturing_year': ['El año de fabricación debe ser posterior a 1900.']}  
Para 2026: Código 400, {'manufacturing_year': ['El año de fabricación no puede ser mayor al año actual.']}  

**Estado:** PASÓ  

---

### ID: UT-MAQ-007

**Título:** Verificar validación de formato de imagen inválido  

**Descripción:**  
Esta prueba verifica que se valide el formato del archivo de imagen.  

**Precondiciones:**  
- Usuario autenticado  

**Datos de Entrada:**  
- image: Archivo de texto falso (no imagen)  
- Otros campos válidos  

**Pasos (AAA):**  
**Arrange:** Crear archivo falso con extensión .txt.  
**Act:** Enviar POST con imagen inválida.  
**Assert:** Código 400, 'image' en details.  

**Resultado Esperado:**  
Error 400 indicando formato de imagen inválido.  

**Resultado Obtenido:**  
Código de estado: 400  
Respuesta: {'success': False, 'message': 'Error de validación', 'details': {'image': {'image': 'El archivo debe ser una imagen (JPEG, PNG, etc.)'}}}  

**Estado:** PASÓ  

---

### ID: UT-MAQ-008

**Título:** Verificar validación de dispositivo de telemetría en uso  

**Descripción:**  
Esta prueba verifica que no se permita asignar un dispositivo que ya está en uso por otra maquinaria.  

**Precondiciones:**  
- Usuario autenticado  
- Dispositivo asignado a maquinaria existente  

**Datos de Entrada:**  
- id_device: ID de dispositivo ya en uso  
- Otros campos válidos  

**Pasos (AAA):**  
**Arrange:** Crear maquinaria con dispositivo específico.  
**Act:** Intentar crear nueva maquinaria con el mismo dispositivo.  
**Assert:** Código 400, 'id_device' en details.  

**Resultado Esperado:**  
Error 400 indicando dispositivo en uso.  

**Resultado Obtenido:**  
Código de estado: 400  
Respuesta: {'success': False, 'message': 'Error de validación', 'details': {'id_device': ['Este dispositivo de telemetría ya está siendo utilizado por otra máquina.']}}  

**Estado:** PASÓ  

---

### ID: UT-MAQ-009

**Título:** Verificar validación de longitud máxima de campos  

**Descripción:**  
Esta prueba verifica que se valide la longitud máxima de campos de texto.  

**Precondiciones:**  
- Usuario autenticado  

**Datos de Entrada:**  
- machinery_name: Cadena de 256 caracteres 'A'*256  
- serial_number: 'B'*51  
- tariff_subheading: 'C'*51  
- Otros campos válidos  

**Pasos (AAA):**  
**Arrange:** Configurar datos con longitudes excesivas.  
**Act:** Enviar POST con datos largos.  
**Assert:** Código 400, campos con longitud excesiva en details.  

**Resultado Esperado:**  
Error 400 indicando campos demasiado largos.  

**Resultado Obtenido:**  
Código de estado: 400  
Respuesta: {'success': False, 'message': 'Error de validación', 'details': {'machinery_name': ['Ensure this field has no more than 255 characters.'], 'serial_number': [...], 'tariff_subheading': [...]}}  

**Estado:** PASÓ  

---

### ID: UT-MAQ-010

**Título:** Verificar validación de autorización de usuario  

**Descripción:**  
Esta prueba verifica el comportamiento cuando se usa un usuario diferente (simulación de permisos).  

**Precondiciones:**  
- Usuario alternativo creado (id_user=2)  

**Datos de Entrada:**  
- responsible_user: ID del usuario alternativo  
- Otros campos válidos  

**Pasos (AAA):**  
**Arrange:** Cambiar autenticación a usuario 2.  
**Act:** Enviar POST con usuario alternativo.  
**Assert:** Código 201, 403 o 400 según permisos.  

**Resultado Esperado:**  
Código 201 si tiene permisos, o error si no.  

**Resultado Obtenido:**  
Código de estado: 201  
Respuesta: {'success': True, 'message': 'Maquinaria y ficha general creada exitosamente'}  

**Estado:** PASÓ  

---

### ID: UT-MAQ-011

**Título:** Verificar estado inicial 'En Registro' de maquinaria creada  

**Descripción:**  
Esta prueba verifica que la maquinaria creada tenga el estado inicial correcto.  

**Precondiciones:**  
- Usuario autenticado  
- Estado 'En registro' configurado (id_statues=3)  

**Datos de Entrada:**  
- Campos válidos para crear maquinaria  

**Pasos (AAA):**  
**Arrange:** Configurar datos válidos.  
**Act:** Crear maquinaria y obtener el objeto de la BD.  
**Assert:** Verificar que machinery_operational_status.id_statues == 3.  

**Resultado Esperado:**  
Maquinaria creada con estado 'En registro'.  

**Resultado Obtenido:**  
Código de estado: 201  
Objeto creado con machinery_operational_status.id_statues = 3  

**Estado:** PASÓ  

---

**Resumen General:**  
Todas las pruebas unitarias (11/11) pasaron exitosamente, validando completamente el endpoint de creación de maquinaria general con sus validaciones correspondientes.