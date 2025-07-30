# users/serializers/person_serializers/person_create_serializer.py

from rest_framework import serializers
from users.models.person import Person
from users.models.user import User
from parameterization.models import Types, City, Statues
from django.utils import timezone


class PersonCreateSerializer(serializers.ModelSerializer):
    responsible_user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), write_only=True
    )
    document_type = serializers.PrimaryKeyRelatedField(queryset=Types.objects.all())
    gender_type = serializers.PrimaryKeyRelatedField(queryset=Types.objects.all())
    id_city = serializers.PrimaryKeyRelatedField(queryset=City.objects.all())
    person_status = serializers.PrimaryKeyRelatedField(queryset=Statues.objects.all())

    class Meta:
        model = Person
        fields = [
            'identification',
            'document_type',
            'first_name',
            'middle_name',
            'first_last_name',
            'second_last_name',
            'date_of_birth',
            'email',
            'address',
            'phone_number',
            'gender_type',
            'id_city',
            'person_status',
            'responsible_user',
        ]

    def create(self, validated_data):
        responsible_user = validated_data.pop('responsible_user')
        validated_data['id_responsible_user'] = responsible_user
        validated_data['creation_date'] = timezone.now().date()
        validated_data['modification_date'] = timezone.now().date()
        return Person.objects.create(**validated_data)
