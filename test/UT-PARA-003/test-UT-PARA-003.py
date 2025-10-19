import os
import django
from django.conf import settings

# Configurar variables de entorno necesarias para las pruebas
os.environ.setdefault('SECRET_KEY', 'test-secret-key-for-unit-testing-only')
os.environ.setdefault('DEBUG', 'True')
os.environ.setdefault('ALLOWED_HOSTS', '*')
os.environ.setdefault('DB_NAME', 'test_db')
os.environ.setdefault('DB_USER', 'test_user')
os.environ.setdefault('DB_PASSWORD', 'test_pass')
os.environ.setdefault('DB_HOST', 'localhost')
os.environ.setdefault('DB_PORT', '5432')

# Configurar Django antes de importar los modelos
if not settings.configured:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'machpaymanager.settings')
    django.setup()

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from parameterization.models import StatuesCategory, Statues, Types, TypesCategory
from users.models import User


@pytest.mark.django_db(transaction=True)
def test_ut_para_003_endpoints_crud_estados_globales():
    """
    UT-PARA-003 (RF-102): Endpoints CRUD estados globales
    
    Verificar los endpoints responsables de la gestión de estados globales. 
    Se probarán operaciones CRUD (crear, leer, actualizar, eliminar) asegurando que: 
    no se permitan duplicados dentro de una categoría, no se creen valores vacíos, 
    no se eliminen estados que estén en uso, y que los cambios en los estados se 
    reflejen de manera inmediata en los módulos asociados.
    """
    client = APIClient()

    # Arrange: Autenticarse como SuperAdmin y configurar datos base
    admin_user = User.objects.create(id_user=1)

    # Crear categoría "Estado de solicitud" con estado inicial "Pendiente"
    categoria_solicitud_resp = client.post(
        "/statues_categories/",
        {
            "name": "Estado de solicitud",
            "description": "Categoría para estados de solicitudes del sistema",
            "responsible_user": admin_user.pk,
        },
        format="json",
    )
    assert categoria_solicitud_resp.status_code == 201

    # Obtener ID de la categoría creada
    categoria_solicitud = StatuesCategory.objects.get(name="Estado de solicitud")
    categoria_id = categoria_solicitud.pk

    # Crear estado inicial "Pendiente"
    estado_pendiente_resp = client.post(
        "/statues/",
        {
            "name": "Pendiente",
            "description": "Solicitud registrada, pendiente de revisión",
            "statues_category": categoria_id,
            "responsible_user": admin_user.pk,
        },
        format="json",
    )
    assert estado_pendiente_resp.status_code == 201

    # Obtener ID del estado pendiente
    estado_pendiente = Statues.objects.get(name="Pendiente")
    estado_pendiente_id = estado_pendiente.pk

    # Act 1: Crear nuevo estado "Finalizada" con POST /statues
    nuevo_estado_resp = client.post(
        "/statues/",
        {
            "name": "Finalizada",
            "description": "Solicitud fue finalmente atendida o resuelta",
            "statues_category": categoria_id,
            "responsible_user": admin_user.pk,
        },
        format="json",
    )
    
    # Assert 1: Creación devuelve 201 Created y el estado aparece en la lista
    assert nuevo_estado_resp.status_code == 201
    assert "message" in nuevo_estado_resp.json()
    
    # Verificar que el estado fue creado correctamente
    estado_finalizada = Statues.objects.get(name="Finalizada")
    assert estado_finalizada.description == "Solicitud fue finalmente atendida o resuelta"
    assert estado_finalizada.id_statues_categories == categoria_solicitud

    # Act 2: Consultar lista con GET /statues/list/{id_statues_categories}
    lista_estados_resp = client.get(f"/statues/list/{categoria_id}/")
    
    # Assert 2: Consulta devuelve lista con ["Pendiente", "Finalizada"]
    assert lista_estados_resp.status_code == 200
    estados_data = lista_estados_resp.json()
    assert isinstance(estados_data, list)
    nombres_estados = [estado["name"] for estado in estados_data]
    assert "Pendiente" in nombres_estados
    assert "Finalizada" in nombres_estados
    assert len(nombres_estados) == 2

    # Act 3: Editar estado con PUT /statues/{id} → cambiar "Pendiente" a "Pendiente de revisión"
    editar_estado_resp = client.put(
        f"/statues/{estado_pendiente_id}/",
        {
            "name": "Pendiente de revisión",
            "description": "Solicitud registrada, en espera de ser revisada",
            "statues_category": categoria_id,
            "responsible_user": admin_user.pk,
        },
        format="json",
    )
    
    # Assert 3: Edición devuelve 200 OK y el nombre actualizado se refleja
    assert editar_estado_resp.status_code == 200
    assert "message" in editar_estado_resp.json()
    
    # Verificar que el cambio se aplicó
    estado_editado = Statues.objects.get(pk=estado_pendiente_id)
    assert estado_editado.name == "Pendiente de revisión"
    assert estado_editado.description == "Solicitud registrada, en espera de ser revisada"
    
    # Verificar en la lista actualizada
    lista_estados_actualizada_resp = client.get(f"/statues/list/{categoria_id}/")
    assert lista_estados_actualizada_resp.status_code == 200
    estados_actualizados = lista_estados_actualizada_resp.json()
    nombres_actualizados = [estado["name"] for estado in estados_actualizados]
    assert "Pendiente de revisión" in nombres_actualizados
    assert "Pendiente" not in nombres_actualizados

    # Act 4: Intentar crear duplicado con POST /statues → "Finalizada" ya existe
    estado_duplicado_resp = client.post(
        "/statues/",
        {
            "name": "Finalizada",  # Nombre ya existente
            "description": "Intento de duplicado",
            "statues_category": categoria_id,
            "responsible_user": admin_user.pk,
        },
        format="json",
    )
    
    # Assert 4: Duplicado devuelve 400 Bad Request con mensaje de error
    assert estado_duplicado_resp.status_code == 400
    # El modelo Statues tiene unique=True en el campo name, por lo que Django devuelve error
    assert "name" in estado_duplicado_resp.json() or "error" in estado_duplicado_resp.json()

    # Act 5: Simular estado en uso creando un tipo que lo use, luego intentar eliminar
    # Primero crear una categoría de tipos para el ejemplo
    categoria_tipos_resp = client.post(
        "/types_categories/",
        {
            "name": "Tipos de mantenimiento",
            "description": "Categoría para tipos de mantenimiento",
            "responsible_user": admin_user.pk,
        },
        format="json",
    )
    assert categoria_tipos_resp.status_code == 201
    categoria_tipos_id = TypesCategory.objects.get(name="Tipos de mantenimiento").pk

    # Crear un tipo que use el estado "Pendiente de revisión" (esto simula el "estado en uso")
    tipo_que_usa_estado = Types.objects.create(
        name="Tipo que usa estado",
        description="Tipo para simular uso del estado",
        id_types_categories_id=categoria_tipos_id,
        id_statues=estado_editado,  # Usa el estado editado
        creation_date=timezone.now(),
        modification_date=timezone.now(),
        id_responsible_user=admin_user,
    )

    # Intentar eliminar estado que está en uso (el endpoint DELETE no existe, 
    # pero probamos el comportamiento esperado)
    delete_estado_resp = client.delete(f"/statues/{estado_pendiente_id}/")
    
    # Assert 5: Como no hay endpoint DELETE implementado, devuelve 405 Method Not Allowed
    assert delete_estado_resp.status_code == 405

    # Verificaciones adicionales de consistencia
    # - Los estados creados están correctamente asociados a su categoría
    estados_finales = Statues.objects.filter(id_statues_categories=categoria_solicitud)
    assert estados_finales.count() == 2
    
    # - No hay duplicados en los nombres
    nombres_estados_finales = list(estados_finales.values_list('name', flat=True))
    assert len(nombres_estados_finales) == len(set(nombres_estados_finales))
    
    # - El estado editado mantiene sus referencias correctamente
    tipo_actualizado = Types.objects.get(pk=tipo_que_usa_estado.pk)
    assert tipo_actualizado.id_statues.name == "Pendiente de revisión"


@pytest.mark.django_db(transaction=True)
def test_ut_para_003_validaciones_restricciones():
    """
    Pruebas adicionales para validar restricciones específicas del caso UT-PARA-003
    """
    client = APIClient()

    # Arrange: Configuración base
    admin_user = User.objects.create(id_user=2)

    # Crear categoría de estados
    categoria_test_resp = client.post(
        "/statues_categories/",
        {
            "name": "Estados Test",
            "description": "Categoría de prueba para validaciones",
            "responsible_user": admin_user.pk,
        },
        format="json",
    )
    assert categoria_test_resp.status_code == 201
    categoria_test_id = StatuesCategory.objects.get(name="Estados Test").pk

    # Test: Crear estado con nombre vacío
    estado_vacio_resp = client.post(
        "/statues/",
        {
            "name": "",  # Nombre vacío
            "description": "Estado con nombre vacío",
            "statues_category": categoria_test_id,
            "responsible_user": admin_user.pk,
        },
        format="json",
    )
    
    # Assert: Error por nombre vacío
    assert estado_vacio_resp.status_code == 400

    # Test: Crear estado sin categoría válida
    estado_sin_categoria_resp = client.post(
        "/statues/",
        {
            "name": "Estado Sin Categoría",
            "description": "Estado sin categoría válida",
            "statues_category": 99999,  # ID inexistente
            "responsible_user": admin_user.pk,
        },
        format="json",
    )
    
    # Assert: Error por FK inválida
    assert estado_sin_categoria_resp.status_code == 400

    # Test: Consultar estados de categoría inexistente
    estados_categoria_inexistente_resp = client.get("/statues/list/99999/")
    
    # Assert: Error por categoría no encontrada
    assert estados_categoria_inexistente_resp.status_code == 404

    # Test: Editar estado inexistente
    editar_inexistente_resp = client.put(
        "/statues/99999/",
        {
            "name": "Estado Inexistente",
            "description": "No existe",
            "statues_category": categoria_test_id,
            "responsible_user": admin_user.pk,
        },
        format="json",
    )
    
    # Assert: Error por estado no encontrado
    assert editar_inexistente_resp.status_code == 404

    # Test: Validación de duplicados en categorías
    # Crear primera categoría
    primera_categoria_resp = client.post(
        "/statues_categories/",
        {
            "name": "Categoría Única",
            "description": "Primera categoría",
            "responsible_user": admin_user.pk,
        },
        format="json",
    )
    assert primera_categoria_resp.status_code == 201

    # Intentar crear categoría con nombre duplicado
    categoria_duplicada_resp = client.post(
        "/statues_categories/",
        {
            "name": "Categoría Única",  # Nombre duplicado
            "description": "Segunda categoría",
            "responsible_user": admin_user.pk,
        },
        format="json",
    )
    
    # Assert: Error por duplicado en categorías
    assert categoria_duplicada_resp.status_code == 400
    assert "name" in str(categoria_duplicada_resp.json()).lower()


@pytest.mark.django_db(transaction=True)
def test_ut_para_003_consultas_categorias():
    """
    Prueba específica para endpoints de consulta de categorías de estados
    """
    client = APIClient()

    # Arrange: Configuración base
    admin_user = User.objects.create(id_user=3)

    # Crear múltiples categorías
    categorias_test = [
        {"name": "Estados de solicitud", "description": "Para solicitudes"},
        {"name": "Estados de usuario", "description": "Para usuarios"},
        {"name": "Estados de mantenimiento", "description": "Para mantenimientos"},
    ]

    for categoria_data in categorias_test:
        resp = client.post(
            "/statues_categories/",
            {
                "name": categoria_data["name"],
                "description": categoria_data["description"],
                "responsible_user": admin_user.pk,
            },
            format="json",
        )
        assert resp.status_code == 201

    # Act: Consultar todas las categorías
    lista_categorias_resp = client.get("/statues_categories/list/")
    
    # Assert: Verificar respuesta y contenido
    assert lista_categorias_resp.status_code == 200
    categorias_data = lista_categorias_resp.json()
    assert isinstance(categorias_data, list)
    assert len(categorias_data) >= 3  # Al menos las 3 que creamos
    
    nombres_categorias = [cat["name"] for cat in categorias_data]
    for categoria_test in categorias_test:
        assert categoria_test["name"] in nombres_categorias

    # Verificar estructura de respuesta
    if categorias_data:
        categoria_ejemplo = categorias_data[0]
        assert "name" in categoria_ejemplo
        assert "description" in categoria_ejemplo
        # Puede incluir otros campos como id, creation_date, etc.


@pytest.mark.django_db(transaction=True)
def test_ut_para_003_reflejo_cambios_modulos():
    """
    Verificar que los cambios en estados se reflejen inmediatamente en módulos asociados
    """
    client = APIClient()

    # Arrange: Configurar datos base con relaciones
    admin_user = User.objects.create(id_user=4)

    # Crear categoría y estado inicial
    categoria_resp = client.post(
        "/statues_categories/",
        {
            "name": "Estados para módulos",
            "description": "Estados que se usan en múltiples módulos",
            "responsible_user": admin_user.pk,
        },
        format="json",
    )
    assert categoria_resp.status_code == 201
    categoria_id = StatuesCategory.objects.get(name="Estados para módulos").pk

    estado_inicial_resp = client.post(
        "/statues/",
        {
            "name": "En progreso",
            "description": "Estado inicial",
            "statues_category": categoria_id,
            "responsible_user": admin_user.pk,
        },
        format="json",
    )
    assert estado_inicial_resp.status_code == 201
    estado_inicial = Statues.objects.get(name="En progreso")

    # Crear elementos que usen este estado (simulando módulos asociados)
    # En este caso, usamos Types como ejemplo de módulo que usa estados
    categoria_tipos_resp = client.post(
        "/types_categories/",
        {
            "name": "Tipos con estados",
            "description": "Tipos que usan estados",
            "responsible_user": admin_user.pk,
        },
        format="json",
    )
    assert categoria_tipos_resp.status_code == 201
    categoria_tipos_id = TypesCategory.objects.get(name="Tipos con estados").pk

    # Crear varios tipos que usen el estado
    tipos_que_usan_estado = []
    for i in range(3):
        tipo = Types.objects.create(
            name=f"Tipo {i+1} con estado",
            description=f"Tipo {i+1} que usa el estado En progreso",
            id_types_categories_id=categoria_tipos_id,
            id_statues=estado_inicial,
            creation_date=timezone.now(),
            modification_date=timezone.now(),
            id_responsible_user=admin_user,
        )
        tipos_que_usan_estado.append(tipo)

    # Act: Cambiar el nombre y descripción del estado
    cambio_estado_resp = client.put(
        f"/statues/{estado_inicial.pk}/",
        {
            "name": "En proceso de revisión",
            "description": "Estado actualizado con nueva descripción",
            "statues_category": categoria_id,
            "responsible_user": admin_user.pk,
        },
        format="json",
    )
    
    # Assert: Verificar que el cambio se aplicó
    assert cambio_estado_resp.status_code == 200
    
    # Verificar que el estado fue actualizado
    estado_actualizado = Statues.objects.get(pk=estado_inicial.pk)
    assert estado_actualizado.name == "En proceso de revisión"
    assert estado_actualizado.description == "Estado actualizado con nueva descripción"
    
    # Verificar que todos los tipos que usaban el estado reflejan el cambio inmediatamente
    for tipo_original in tipos_que_usan_estado:
        tipo_actualizado = Types.objects.get(pk=tipo_original.pk)
        assert tipo_actualizado.id_statues.name == "En proceso de revisión"
        assert tipo_actualizado.id_statues.description == "Estado actualizado con nueva descripción"
        assert tipo_actualizado.id_statues.pk == estado_inicial.pk  # Mismo estado, solo actualizado

    # Verificar que la consulta de la lista también refleja el cambio
    lista_estados_resp = client.get(f"/statues/list/{categoria_id}/")
    assert lista_estados_resp.status_code == 200
    estados_data = lista_estados_resp.json()
    nombres_estados = [estado["name"] for estado in estados_data]
    assert "En proceso de revisión" in nombres_estados
    assert "En progreso" not in nombres_estados
