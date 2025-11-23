Historia de Usuario 
Como usuario del área de Recursos Humanos, quiero visualizar un listado completo y ordenado de todas las novedades registradas en el sistema, incluyendo su fecha, autor y descripción, y acceder al cargue masivo de novedades mediante un archivo Excel, para consultar el historial de eventos y gestionar eficientemente los ajustes adicionales asociados a los empleados.

Criterios de Aceptación:
Desde el módulo Novedades, el sistema debe mostrar una tabla principal con todas las novedades registradas, incluyendo las columnas:
Fecha de la novedad
Autor
Tipo de novedad (ej.: Nuevo empleado, Cambio de contrato, Modificación del empleado, Finalización de contrato, Cargue masivo de novedades)
Descripción
Empleado asociado (Documento – Nombre completo)
Origen (Automática / Carga masiva)
En la parte superior, debe existir un botón “Filtros”, que despliegue un modal con los siguientes campos:
Documento del empleado
Tipo de novedad (lista desplegable con los eventos definidos)
Fecha Desde
Fecha Hasta
Botones: Aplicar filtros / Limpiar filtros
Si no se encuentran resultados, debe mostrarse el mensaje: “No se encontraron novedades con los criterios seleccionados.”
El listado debe contar con:
Paginación configurable (10, 25, 50 o 100 registros por página).
Ordenamiento asc/desc por:
Fecha
Empleado
Tipo de novedad
Autor
En la parte superior de la vista debe existir un botón “Cargar novedades masivas”, visible solo para usuarios con permisos. Al presionarlo, se debe abrir un modal con:
Botón para seleccionar y subir un archivo Excel.
Campo Descripción (obligatorio, máximo 255 caracteres).
Botones: Subir / Cancelar
Solo usuarios con permisos de consulta pueden ver el listado.
Las novedades no pueden modificarse ni eliminarse.
El listado de novedades debe actualizarse automáticamente cuando el sistema registre una novedad automática (nuevo empleado, fin de contrato, etc.).