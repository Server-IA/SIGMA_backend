# UT-NOM-005 - Listado de Nóminas Generadas

## Descripción
Como usuario del área de Recursos Humanos, quiero visualizar un listado de todas las nóminas generadas con su información principal, filtros avanzados y opciones de visualización y descarga, para consultar su estado, verificar detalles y acceder rápidamente a la generación de nuevas nóminas masivas de forma eficiente y centralizada.

## Precondiciones
- Usuario autenticado con rol apropiado.
- Usuario tiene asignado el permiso con ID 193 (payroll.retrieve).
- Existen nóminas generadas en el sistema.

## SQL Permiso (para pruebas/manuales)
```sql
INSERT INTO permission (id, name, description, category) 
VALUES (193, 'payroll.retrieve', 'listar nominas generadas', 'Nomina');
```

## Endpoint
- URL: `GET /payroll/list-generated/`
- Respuesta esperada (ejemplo):
```json
{
  "success": true,
  "data": [
    {
      "id_payroll": 131,
      "document_number": null,
      "employee_full_name": "",
      "responsible_user_full_name": "Juan Andres Veru Sarmiento",
      "creation_date": "2025-11-26T03:07:14.922671Z",
      "start_date": "2025-11-01",
      "end_date": "2025-11-30",
      "currency_type_name": "Dollar"
    }
  ]
}
```

## Pasos (AAA)

### Arrange
- Crear usuario autenticado con permiso 193 en JWT.
- Crear empleados, contratos y varias nóminas en la BD (al menos 5 para pruebas de paginación/listado).
- Crear la unidad monetaria usada (ej. `Dollar`) y asociarla a los contratos.

### Act
- Ejecutar `GET /payroll/list-generated/` como usuario con permiso 193.
- (Opcional) Probar sin token y con permisos insuficientes para validar 401/403.

### Assert
- Respuesta HTTP 200 y `success: true` cuando el usuario tiene permiso 193.
- `data` es una lista de objetos con las claves: `id_payroll`, `document_number`, `employee_full_name`, `responsible_user_full_name`, `creation_date`, `start_date`, `end_date`, `currency_type_name`.
- Si no hay resultados, `data` es lista vacía y `success` puede ser true o false según especificación; validar mensaje si aplica.

## Resultado Esperado
- Listado de nóminas correctamente devuelto para usuarios con permiso 193.
- Soporte básico para filtros y paginación (si el endpoint lo soporta).

## Resultado Obtenido
- Verifica respuesta 200 y estructura esperada para un usuario con permiso `193`.
- Verifica que se devuelve `401` cuando no se proporciona token.
- Verifica que se devuelve `403` cuando el usuario no tiene el permiso requerido.
- Valida la presencia y el valor de `currency_type_name` y la estructura de campos en cada elemento de `data`.
- Se copiaron archivos faltantes dentro del contenedor a `/app/payroll/serializers/...` y `/app/payroll/utils/` (`payroll_list_serializer.py`, `payroll_history_report_serializer.py`, `payroll_document_generator.py`, `contract_document_generator.py`, `contract_history_report_generator.py`, `audit_helpers.py`), y se reinició el contenedor antes de ejecutar `pytest`.
- Las llamadas externas a `AUTH_SERVICE_URL` se mockean con `@patch('payroll.serializers.payroll_serializers.payroll_list_serializer.requests.post')` para evitar dependencias de red; se reporta un warning deprecación (`CheckConstraint.check`) en otro módulo, no relacionado con la lógica bajo prueba.

## Estado / Fecha / Ejecutor
- Estado: Aprobado
- Fecha: 2025-11-27
- Ejecutor: Alejandro S
