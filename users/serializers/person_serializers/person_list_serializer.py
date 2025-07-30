from rest_framework import serializers
from users.models.person import Person

class PersonListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Person
        fields = [
            'identification',
            'document_type',
            'first_name',
            'middle_name',
            'first_last_name',
            'second_last_name',
            'person_status'
        ]
