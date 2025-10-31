from rest_framework import serializers
from adminapp.models import Category, Client


# -------- Client Registration --------
class ClientCreateSerializer(serializers.ModelSerializer):
    password1 = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())  # ✅ added

    class Meta:
        model = Client
        fields = [
            "username", "email", "password1", "password2",
            "business_name", "contact_number", "address",
            "payment_method", "category"
        ]

    def validate(self, data):
        if data.get("password1") != data.get("password2"):
            raise serializers.ValidationError("Passwords do not match.")
        return data

    def create(self, validated_data):
        password = validated_data.pop("password1")
        validated_data.pop("password2", None)
        client = Client(**validated_data)
        client.set_password(password)
        client.save()
        return client



# -------- Login Serializer --------
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()


# -------- Category Serializer --------
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"
        read_only_fields = ["id"]


# -------- Client Serializer (for view/update) --------
class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = "__all__"
        read_only_fields = ["id", "is_active", "subscription_start", "subscription_end"]
