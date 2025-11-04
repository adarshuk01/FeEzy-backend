import random
import string
from rest_framework import serializers
from adminapp.models import Category, Client


import random
import string
from django.core.mail import send_mail
from rest_framework import serializers
from adminapp.models import Client
from django.conf import settings


class ClientCreateSerializer(serializers.ModelSerializer):
    email = serializers.EmailField()
    password = serializers.CharField(read_only=True)

    class Meta:
        model = Client
        fields = [
            'username',
            'email',
            'password',
            'business_name',
            'contact_number',
            'address',
            'payment_method',
        ]

    def create(self, validated_data):
        # Generate random 10-character password
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))

        # Create client and hash password
        client = Client(**validated_data)
        client.set_password(password)
        client.save()

        # Attach generated password temporarily (for response)
        client.generated_password = password

        # -------- Send email to the client --------
        subject = "Your Account Credentials"
        message = (
            f"Hello {client.username},\n\n"
            f"Your account has been created successfully.\n"
            f"Here are your login details:\n\n"
            f"Username: {client.username}\n"
            f"Password: {password}\n\n"
            f"Please change your password after your first login.\n\n"
            f"Regards,\nAdmin Team"
        )
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [client.email]

        send_mail(subject, message, from_email, recipient_list, fail_silently=False)

        return client

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if hasattr(instance, 'generated_password'):
            data['generated_password'] = instance.generated_password
        return data





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
