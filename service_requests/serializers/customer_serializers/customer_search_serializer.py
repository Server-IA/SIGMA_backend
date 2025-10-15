from rest_framework import serializers
from service_requests.models.customer import Customer
from service_requests.serializers.customer_serializers.customer_detail_serializer import CustomerDetailSerializer

class CustomerSearchSerializer(serializers.Serializer):
    """
    Serializer for searching customers by document number.
    Returns the same fields as CustomerDetailSerializer.
    """
    document_number = serializers.IntegerField(required=True)

    def validate_document_number(self, value):
        """Check if document number is valid."""
        if not value or value < 0:
            raise serializers.ValidationError("Document number must be a positive number")
        return value

    def to_representation(self, instance):
        """Convert the customer instance to the same format as CustomerDetailSerializer."""
        return CustomerDetailSerializer(instance, context=self.context).data
