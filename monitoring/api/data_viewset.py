from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from service_requests.models.service_request import ServiceRequest
from monitoring.serializers.data_serializer import DataSerializer, get_machinery_data
from utils.permissions import HasPermission

class DataViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated, HasPermission(172)]
    
    @action(detail=True, methods=['get'])
    def by_request(self, request, pk=None):
        try:
            # Verify request exists
            request_obj = ServiceRequest.objects.get(id_request=pk)
        except ServiceRequest.DoesNotExist:
            return Response(
                {"detail": "Request not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get the machinery data
        machinery_data = get_machinery_data(pk)
        
        # Serialize and return the data
        serializer = DataSerializer(machinery_data, many=True)
        return Response(serializer.data)
    
    # Add list and other standard actions if needed
    def list(self, request):
        return Response(
            {"detail": "Please provide a request ID using the 'by_request' action"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
