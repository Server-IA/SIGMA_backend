from rest_framework import serializers
from django.utils import timezone
from payroll.models import Employee, EmployeeNews
from users.models.user import User
from parameterization.models import EmployeeCharge

class EmployeeUpdateSerializer(serializers.ModelSerializer):
    observation = serializers.CharField(write_only=True, required=True, allow_blank=False)
    email = serializers.EmailField(required=False, allow_blank=True, allow_null=True)
    id_employee_charge = serializers.PrimaryKeyRelatedField(
        queryset=EmployeeCharge.objects.all(),
        required=False
    )

    class Meta:
        model = Employee
        fields = [
            'email',
            'id_employee_charge',
            'observation'
        ]

    def validate_email(self, value):
        # Only validate if email is being updated and is not empty
        if value and Employee.objects.filter(email=value).exists():
            if self.instance and self.instance.email == value:
                return value  # Same email as current, no problem
            raise serializers.ValidationError("Ya existe un empleado con este correo electrónico.")
        return value

    def update(self, instance, validated_data):
        observation = validated_data.pop('observation', None)
        request = self.context.get('request')
        
        # Get the current user from the request
        responsible_user = None
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            from users.models.user import User
            user = request.user
            # Handle both JWTUser and regular User objects
            if hasattr(user, 'id'):
                try:
                    responsible_user = User.objects.get(pk=user.id)
                except User.DoesNotExist:
                    pass
        
        # Update employee fields
        if 'email' in validated_data:
            instance.email = validated_data['email']
        if 'id_employee_charge' in validated_data:
            instance.id_employee_charge = validated_data['id_employee_charge']
        
        # Update modification date
        instance.modification_date = timezone.now()
        
        # Save the instance
        instance.save()

        # Create EmployeeNews entry if we have a responsible user and observation
        if responsible_user and observation:
            EmployeeNews.objects.create(
                id_employee=instance,
                observation=observation,
                news_type='ACTUALIZACION_EMPLEADO',
                id_responsible_user=responsible_user
            )
        
        return instance
