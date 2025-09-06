from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status

from parameterization.models import (
    BrandsCategory, Brands, Statues, StatuesCategory
)
from users.models.user import User


class BrandsApiTests(APITestCase):
    def setUp(self):
        # Usuario responsable
        self.user = User.objects.create(id_user=1)

        # Estados (1=Activo, 2=Inactivo)
        sc = StatuesCategory.objects.create(
            name="Estados generales",
            description="...",
            creation_date=timezone.now(),
            modification_date=timezone.now(),
            id_responsible_user=self.user
        )
        Statues.objects.create(
            id_statues=1,
            name="Activo",
            description="",
            id_statues_categories=sc,
            creation_date=timezone.now(),
            modification_date=timezone.now(),
            id_responsible_user=self.user
        )
        Statues.objects.create(
            id_statues=2,
            name="Inactivo",
            description="",
            id_statues_categories=sc,
            creation_date=timezone.now(),
            modification_date=timezone.now(),
            id_responsible_user=self.user
        )

        # Categorías
        self.cat1 = BrandsCategory.objects.create(
            name="Maquinaria",
            description="Cat marcas",
            creation_date=timezone.now(),
            modification_date=timezone.now(),
            id_responsible_user=self.user
        )
        self.cat_vacia = BrandsCategory.objects.create(
            name="Sin marcas",
            description="",
            creation_date=timezone.now(),
            modification_date=timezone.now(),
            id_responsible_user=self.user
        )

        # Marcas en cat1
        self.brand1 = Brands.objects.create(
            name="Marca Uno",
            description="A",
            id_brands_categories=self.cat1,
            id_statues_id=1,
            creation_date=timezone.now(),
            modification_date=timezone.now(),
            id_responsible_user=self.user
        )
        self.brand2 = Brands.objects.create(
            name="Otra Marca",
            description="B",
            id_brands_categories=self.cat1,
            id_statues_id=2,
            creation_date=timezone.now(),
            modification_date=timezone.now(),
            id_responsible_user=self.user
        )

    def test_list_brands_categories(self):
        resp = self.client.get("/brands_categories/list/")
        assert resp.status_code == status.HTTP_200_OK
        assert isinstance(resp.json(), list)
        assert {"id_brands_categories", "name", "description"} <= set(resp.json()[0].keys())

    def test_create_brand(self):
        payload = {
            "name": "Nueva Marca",
            "description": "X",
            "brands_category": self.cat1.pk,
            "statues": 1,
            "responsible_user": self.user.pk
        }
        resp = self.client.post("/brands/", payload, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        assert Brands.objects.filter(name="Nueva Marca").exists()

    def test_list_by_category_with_pagination_and_filter(self):
        # q debe filtrar por nombre
        resp = self.client.get(f"/brands/list/{self.cat1.pk}/?q=Marca&page=1&page_size=1")
        data = resp.json()
        assert resp.status_code == status.HTTP_200_OK
        assert data["count"] == 2
        assert data["page"] == 1 and data["page_size"] == 1
        assert len(data["data"]) == 1
        # Cada item incluye estado y nombre de categoría
        assert {"id_brands", "name", "description", "estado", "brands_category_name"} <= set(data["data"][0].keys())

    def test_list_active_by_category(self):
        resp = self.client.get(f"/brands/list/active/{self.cat1.pk}/")
        assert resp.status_code == status.HTTP_200_OK
        names = [b["name"] for b in resp.json()["data"]]
        assert names == ["Marca Uno"]

    def test_retrieve_brand(self):
        resp = self.client.get(f"/brands/{self.brand1.pk}/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["data"]["name"] == "Marca Uno"

    def test_destroy_brand(self):
        resp = self.client.delete(f"/brands/{self.brand2.pk}/")
        assert resp.status_code == status.HTTP_200_OK
        assert not Brands.objects.filter(pk=self.brand2.pk).exists()

    def test_toggle_status(self):
        assert Brands.objects.get(pk=self.brand1.pk).id_statues_id == 1
        resp = self.client.patch(f"/brands/{self.brand1.pk}/toggle-status/")
        assert resp.status_code == status.HTTP_200_OK
        assert Brands.objects.get(pk=self.brand1.pk).id_statues_id == 2

    def test_empty_category_message(self):
        resp = self.client.get(f"/brands/list/{self.cat_vacia.pk}/")
        data = resp.json()
        assert resp.status_code == status.HTTP_200_OK
        assert data["count"] == 0 and data["data"] == []
        assert "No existen marcas registradas para esta categoría" in data["message"]

    def test_invalid_category_returns_404(self):
        resp = self.client.get("/brands/list/999999/")
        assert resp.status_code == status.HTTP_404_NOT_FOUND


