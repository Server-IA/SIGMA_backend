# Reporte de Pruebas - Reentrenamiento Automático (HU-MS-008)

**Proyecto:** Sistema de Gestión de Maquinaria y Nómina
**Módulo:** Reentrenamiento / Predicción de Consumo de Combustible
**Historia de Usuario:** HU-MS-008 (Recolección automática y reentrenamiento diario)
**Fecha de Ejecución:** 17 de Noviembre de 2025
**Ejecutado por:** QA Automation (script)
**Ambiente:** Docker `web` container (pytest dentro del contenedor)

---

## Resumen Ejecutivo

| Métrica | Valor |
|--------:|:-----:|
| Total de archivos de prueba ejecutados | 2 |
| Pruebas unitarias/rápidas | 1 file (`WS-SM-008.py`) |
| Pruebas de integración controlada | 1 file (`WS-SM-008-integration.py`) |
| Total de tests | 4 |
| Aprobadas | 4 |
| Fallidas | 0 |
| Omited/Skip | 0 |
| Advertencias significativas | 1 (deprecación Django) + logs informativos del servicio |

---

## Archivos y Casos Ejecutados

- `test/WS-MS-008/WS-SM-008.py` (unit / filesystem behavior)
  - Objetivo: validar que la acumulación de filas en el CSV de entrenamiento y el contador funcionan correctamente; comprobar trigger lógico de reentrenamiento vía monkeypatch.
  - Resultado: APROBADO (todos los tests pasaron).

- `test/WS-MS-008/WS-SM-008-integration.py` (integración controlada)
  - Objetivo: ejecutar `prediction_service.predict_and_save_training_data` en un entorno controlado sin tocar producción:
    - `DummyModel` sustituye el modelo real (sin entrenamiento ni descarga).
    - Monkeypatch de getters internos (`_get_machinery_data`, `_get_request_data`, `_get_telemetry_data`, `_get_ambient_temperature`, `_get_consumption_real`) para devolver datos deterministas.
    - Redirect de `TRAINING_DATA_CSV` y `TRAINING_COUNTER_FILE` a `tmp_path`.
    - Monkeypatch de `_retrain_model` para simular reentrenamientos y verificar limpieza de CSV/contador.
  - Resultado: APROBADO (2 tests dentro del archivo pasaron).

---

## Resultados Detallados y Observaciones

- Total tests ejecutados: 4 — 4 PASSED, 0 FAILED.
- Mensajes y advertencias observadas:
  - `RemovedInDjango60Warning` en `machinery/models/periodic_maintenance.py` (CheckConstraint.deprecado). No afecta resultados actuales, es advertencia de compatibilidad futura.
  - `prediction_service` emitió logs informativos: "No se encontraron columnas esperadas, usando columnas básicas" cuando no existían `feature_columns.json` guardadas — esperado en entorno controlado.

---

## Mapeo contra los Criterios de Aceptación de HU-MS-008

La prueba intermedia valida la mayor parte de la lógica de preparación de datos y acumulación histórica requerida por la HU. A continuación el mapeo rápido:

- Recolección automática de variables (RPM, velocidad, temperatura, nivel de combustible, potencia nominal, implemento, textura, humedad, etc.): Parcialmente validado — la integración controlada ejecuta la preparación de features desde getters simulados que replican estos valores. Para validar 100% se requiere crear fixtures DB con `Data` reales y ejecutar sin monkeypatchs.
- Almacenamiento en repositorio histórico (CSV acumulado): Validado — la prueba verifica que se agregan filas al CSV y que el contador incrementa.
- Trigger de reentrenamiento y reseteo del contador: Validado en flujo (se simuló `_retrain_model` y se comprobó limpieza y reseteo según umbral configurado).
- Validación de integridad previa al reentrenamiento: Parcialmente — la prueba usa datos válidos; añadir casos con datos nulos o fuera de rango permitirá verificar las validaciones (sugerido como siguiente paso).
- Registro de meta-datos del reentrenamiento (fecha/hora, volumen, métricas, versión): NO cubierto por estas pruebas (requiere ejecutar `_retrain_model` real o instrumentar el método fake para simular estas escrituras en BD/logs).
- Promoción del modelo en producción y rollback en error: NO cubierto (implica integración con mecanismo de gestión de modelos y BD de versiones).

---

## Comandos Ejecutados

Los comandos usados dentro del contenedor `web` para ejecutar las pruebas fueron:

```powershell
docker-compose exec web pytest -q test/WS-MS-008/WS-SM-008.py
docker-compose exec web pytest -q test/WS-MS-008/WS-SM-008-integration.py
```

Notas: los archivos de prueba fueron añadidos al contenedor de forma local (sin modificar código fuera de `test/`). Todas las operaciones de I/O sobre CSV y counter se redirigieron a `tmp_path` dentro de cada test.

---

## Recomendaciones y Pasos Siguientes

1. (Prioridad alta) Añadir un test E2E que cree fixtures reales en la base de datos de prueba (`Parameters`, `Machinery`, `SpecificTechnicalSheet`, `ServiceRequest`, `RequestMachineryUser`, `Data`) y ejecute `predict_and_save_training_data` con `_load_model` monkeypatcheado (dummy). Esto validará la creación de features desde tablas reales.
2. (Prioridad media) Implementar casos negativos: datos nulos/fuera de rango para validar las comprobaciones previas al reentrenamiento.
3. (Prioridad media) Registrar en BD/logs la metadata del reentrenamiento (fecha/hora, volumen, métricas) en el flujo de `_retrain_model` o en un wrapper que lo invoque — las pruebas pueden verificar esos registros.
4. (Priorizable) Crear un job de CI que ejecute la prueba controlada (`WS-SM-008-integration.py`) como un job de integración ligera.

---

## Conclusión

Las pruebas añadidas confirman que la lógica de acumulación de datos y el trigger lógico de reentrenamiento funcionan correctamente en un entorno controlado y seguro. Para alcanzar la validación completa de la HU-MS-008 (incluyendo scheduler, entrenamiento real, métricas y promoción de modelo)

**Firma:** QA Automation
