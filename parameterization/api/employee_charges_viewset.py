from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from parameterization.models import EmployeeCharge, EmployeeDepartment, Statues
from parameterization.serializers.employee_charges_serializers.employee_charges_create_serializer import EmployeeChargeCreateSerializer
from parameterization.serializers.employee_charges_serializers.employee_charges_list_serializer import EmployeeChargeListSerializer


class EmployeeChargeViewSet(viewsets.ViewSet):

    def create(self, request):
        serializer = EmployeeChargeCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Cargo creado exitosamente"},
                            status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        try:
            charge = EmployeeCharge.objects.get(pk=pk)
        except EmployeeCharge.DoesNotExist:
            return Response({"error": "Cargo no encontrado"}, status=status.HTTP_404_NOT_FOUND)

        serializer = EmployeeChargeCreateSerializer(charge, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Cargo actualizado exitosamente"},
                            status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path=r'list/(?P<department_id>\d+)')
    def listar_por_departamento(self, request, department_id=None):
        if not EmployeeDepartment.objects.filter(pk=department_id).exists():
            return Response({"detail": "Departamento no encontrado."},
                            status=status.HTTP_404_NOT_FOUND)

        charges = EmployeeCharge.objects.filter(id_employee_department_id=department_id)
        serializer = EmployeeChargeListSerializer(charges, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path=r'list/active/(?P<department_id>\d+)')
    def listar_activos_por_departamento(self, request, department_id=None):
        if not EmployeeDepartment.objects.filter(pk=department_id).exists():
            return Response({"detail": "Departamento no encontrado."},
                            status=status.HTTP_404_NOT_FOUND)

        charges = EmployeeCharge.objects.filter(
            id_employee_department_id=department_id,
            id_statues_id=1
        )
        serializer = EmployeeChargeListSerializer(charges, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['patch'], url_path='toggle-status')
    def toggle_status(self, request, pk=None):
        try:
            charge = EmployeeCharge.objects.get(pk=pk)
        except EmployeeCharge.DoesNotExist:
            return Response({"error": "Cargo no encontrado"}, status=status.HTTP_404_NOT_FOUND)

        if charge.id_statues_id == 1:
            try:
                charge.id_statues = Statues.objects.get(pk=2)
            except Statues.DoesNotExist:
                return Response({"error": "El estado con id=2 no existe"},
                                status=status.HTTP_400_BAD_REQUEST)
            message = "Cargo desactivado exitosamente"
        else:
            try:
                charge.id_statues = Statues.objects.get(pk=1)
            except Statues.DoesNotExist:
                return Response({"error": "El estado con id=1 no existe"},
                                status=status.HTTP_400_BAD_REQUEST)
            message = "Cargo activado exitosamente"

        charge.save(update_fields=['id_statues'])
        return Response({"message": message}, status=status.HTTP_200_OK)
