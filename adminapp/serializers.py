from rest_framework import serializers

from adminapp.models import Category

from django.contrib.auth.models import User





class UserCreateSerializer(serializers.ModelSerializer):

    password1 = serializers.CharField(write_only=True)

    password2 = serializers.CharField(write_only=True)

    password = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = ["username", "email", "password", "password1", "password2"]

    def validate(self, data):
        if data.get("password1") != data.get("password2"):
            raise serializers.ValidationError("Passwords do not match.")
        return data

    def create(self, validated_data):
        password1 = validated_data.pop("password1")
        password2 = validated_data.pop("password2")
        return User.objects.create_user(**validated_data, password=password1)



class LoginSerializer(serializers.Serializer):

    username=serializers.CharField()

    password=serializers.CharField()


class CategorySerializers(serializers.ModelSerializer):

    class Meta:

        model=Category

        fields="__all__"

        read_only_fields=["owner"]






