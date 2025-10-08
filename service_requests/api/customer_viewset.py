from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from service_requests.models.customer import Customer
from service_requests.serializers.customer_serializers.customer_create_serializer import CustomerCreateSerializer
from rest_framework.permissions import IsAuthenticated
import logging

logger = logging.getLogger(__name__)

class CustomerViewSet(viewsets.ViewSet):
    """
    ViewSet para manejar las operaciones de clientes.
    """
    permission_classes = [IsAuthenticated]

    def check_permission(self, request, required_permission_id: int):
        """
        Verifica si el usuario tiene el permiso (por ID).
        """
        # Obtener el payload del JWT desde request.auth
        payload = getattr(request, "auth", None) or {}

        # Obtener roles del payload (soporta "rol" y "roles")
        user_roles = payload.get("rol") or payload.get("roles") or []

        # Extraer todos los IDs de permisos de todos los roles
        permisos_usuario = []
        for rol in user_roles:
            # Obtener permisos del rol (soporta "permisos" y "permissions")
            perms = rol.get("permisos") or rol.get("permissions") or []
            for perm in perms:
                if isinstance(perm, dict) and "id" in perm:
                    permisos_usuario.append(perm.get("id"))

        return required_permission_id in permisos_usuario

    @action(detail=False, methods=['post'])
    def create_customer(self, request):
        """
        Crea un nuevo cliente.
        """
        # Verificar que el usuario esté autenticado
        if not request.user.is_authenticated:
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        permission_id = 133
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para crear clientes"},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            serializer = CustomerCreateSerializer(
                data=request.data,
                context={'request': request}
            )
            
            if serializer.is_valid():
                customer = serializer.save()
                return Response({
                    'success': True,
                    'message': 'Cliente creado exitosamente',
                    'id_customer': customer.id_customer
                }, status=status.HTTP_201_CREATED)
            
            return Response({
                'success': False,
                'message': 'Error de validación',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Error al crear cliente: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error al procesar la solicitud',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def list_customers(self, request):
        """
        Lista todos los clientes.
        """
        # Verificar que el usuario esté autenticado
        if not request.user.is_authenticated:
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Verificar permiso (debes definir el ID de permiso correcto)
        permission_id = 0  # Reemplaza con el ID de permiso correcto para listar clientes
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para listar clientes"},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            customers = Customer.objects.all()
            # Aquí puedes agregar lógica de filtrado si es necesario
            
            # Crear una lista de diccionarios con los datos de los clientes
            customers_data = []
            for customer in customers:
                customer_data = {
                    'id_customer': customer.id_customer,
                    'id_user': customer.id_user_id,
                    'document_number': customer.document_number,
                    'name': customer.name,
                    'first_last_name': customer.first_last_name,
                    'second_last_name': customer.second_last_name,
                    'email': customer.email,
                    'phone': customer.phone,
                    'address': customer.address,
                    'customer_statues': customer.customer_statues_id,
                    'creation_date': customer.creation_date,
                    'modification_date': customer.modification_date
                }
                customers_data.append(customer_data)
            
            return Response({
                'success': True,
                'data': customers_data
            })
            
        except Exception as e:
            logger.error(f"Error al listar clientes: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error al procesar la solicitud',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
