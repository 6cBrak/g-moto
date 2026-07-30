from rest_framework import serializers

from .models import Agence, Utilisateur


class AgenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Agence
        fields = [
            'id', 'nom', 'nom_commercial', 'logo', 'adresse', 'telephone', 'email',
            'site_web', 'rccm', 'nif', 'actif', 'date_creation',
        ]
        read_only_fields = ['id', 'date_creation']


class UtilisateurSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, min_length=8)
    agence_nom = serializers.CharField(source='agence.nom', read_only=True)

    class Meta:
        model = Utilisateur
        fields = [
            'id', 'username', 'first_name', 'last_name', 'email',
            'role', 'agence', 'agence_nom', 'is_active', 'password',
        ]
        read_only_fields = ['id']

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = Utilisateur(**validated_data)
        if password:
            user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance
