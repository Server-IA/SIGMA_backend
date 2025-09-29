# Tests del Sistema de Gestión de Maquinaria y Nómina

Este directorio contiene todos los tests del sistema, organizados por módulos y funcionalidades.

## Estructura de Tests

### Tests por Módulo
- **`test_machinery.py`**: Tests para el módulo de maquinaria
  - Tests de modelos (Machinery, MachineryTrackerSheet, MachineryUsageSheet)
  - Tests de API para endpoints de maquinaria
  - Tests de relaciones entre modelos

- **`test_maintenance.py`**: Tests para el módulo de mantenimiento
  - Tests de modelos (Maintenance, MaintenanceRequest, MaintenanceScheduling)
  - Tests de API para endpoints de mantenimiento
  - Tests de flujos de trabajo de mantenimiento

- **`test_users.py`**: Tests para el módulo de usuarios
  - Tests de modelo de usuario
  - Tests de autenticación
  - Tests de API de usuarios

- **`test_parameterization.py`**: Tests para el módulo de parametrización
  - Tests de modelos de parametrización (Brands, Models, Departments, etc.)
  - Tests de API para endpoints de parametrización
  - Tests de relaciones entre entidades

### Tests de Integración
- **`test_integration.py`**: Tests de integración del sistema completo
  - Tests de flujos de trabajo completos
  - Tests de consistencia de datos entre módulos
  - Tests de transacciones de base de datos

### Tests de Utilidades
- **`test_utils.py`**: Tests para utilidades y funciones auxiliares
  - Tests del servicio de carga de archivos
  - Tests de configuración de Firebase
  - Tests de validación de modelos

### Configuración
- **`conftest.py`**: Configuración de pytest con fixtures
- **`README.md`**: Este archivo de documentación

## Cómo Ejecutar los Tests

### Ejecutar todos los tests
```bash
# Con Docker
docker-compose exec web python manage.py test

# Con pytest
docker-compose exec web pytest

# Tests específicos
docker-compose exec web python manage.py test tests.test_machinery
docker-compose exec web pytest tests/test_machinery.py
```

### Ejecutar tests específicos
```bash
# Test de un módulo específico
docker-compose exec web python manage.py test tests.test_machinery

# Test de una clase específica
docker-compose exec web python manage.py test tests.test_machinery.MachineryModelTests

# Test de un método específico
docker-compose exec web python manage.py test tests.test_machinery.MachineryModelTests.test_machinery_creation
```

### Ejecutar tests con cobertura
```bash
# Instalar coverage
docker-compose exec web pip install coverage

# Ejecutar tests con cobertura
docker-compose exec web coverage run --source='.' manage.py test
docker-compose exec web coverage report
docker-compose exec web coverage html
```

## Cobertura de Tests

Los tests cubren:

### Modelos
- ✅ Creación y validación de modelos
- ✅ Relaciones entre modelos
- ✅ Métodos y propiedades de modelos
- ✅ Validaciones de campos requeridos

### APIs
- ✅ Endpoints de listado
- ✅ Endpoints de creación
- ✅ Endpoints de actualización
- ✅ Endpoints de eliminación
- ✅ Autenticación y permisos

### Integración
- ✅ Flujos de trabajo completos
- ✅ Consistencia de datos
- ✅ Transacciones de base de datos

### Utilidades
- ✅ Servicios auxiliares
- ✅ Configuraciones
- ✅ Validaciones

## Fixtures Disponibles

El archivo `conftest.py` proporciona fixtures para:

- `test_user`: Usuario de prueba
- `test_superuser`: Superusuario de prueba
- `test_brand`: Marca de prueba
- `test_model`: Modelo de prueba
- `test_department`: Departamento de prueba
- `test_machinery`: Máquina de prueba
- `test_maintenance`: Mantenimiento de prueba
- `api_client`: Cliente de API
- `authenticated_api_client`: Cliente de API autenticado

## Convenciones de Testing

### Nomenclatura
- Clases de test: `ModuleNameTests` o `FeatureNameTests`
- Métodos de test: `test_action_expected_result`
- Fixtures: `test_entity_name`

### Estructura de Tests
1. **setUp()**: Configuración inicial
2. **Tests de modelos**: Creación, validación, relaciones
3. **Tests de API**: Endpoints, autenticación, permisos
4. **Tests de integración**: Flujos completos
5. **Tests de utilidades**: Servicios auxiliares

### Datos de Prueba
- Usar factories o fixtures para datos de prueba
- Limpiar datos después de cada test
- Usar datos realistas pero ficticios

## Mejores Prácticas

1. **Aislamiento**: Cada test debe ser independiente
2. **Limpieza**: Limpiar datos después de cada test
3. **Nombres descriptivos**: Los nombres deben explicar qué se está probando
4. **Una aserción por test**: Idealmente, un test debe verificar una cosa
5. **Datos de prueba**: Usar datos mínimos necesarios para el test
6. **Cobertura**: Probar casos exitosos y de error

## Troubleshooting

### Problemas Comunes

1. **Tests fallan por autenticación**: Verificar que los tests usen `APITestCase` y manejen autenticación
2. **Datos no se limpian**: Verificar que se use `TestCase` en lugar de `TransactionTestCase`
3. **Relaciones no funcionan**: Verificar que los modelos estén correctamente relacionados
4. **Firebase no configurado**: Los tests de carga de archivos fallarán si Firebase no está configurado

### Debugging
```bash
# Ejecutar tests con verbosidad
docker-compose exec web python manage.py test --verbosity=2

# Ejecutar tests con debug
docker-compose exec web python manage.py test --debug-mode

# Ejecutar un test específico con debug
docker-compose exec web python manage.py test tests.test_machinery.MachineryModelTests.test_machinery_creation --debug-mode
```
