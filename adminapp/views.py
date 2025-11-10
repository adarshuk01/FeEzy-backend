from django.shortcuts import render

from adminapp.serializers import CategorySerializer,LoginSerializer,ClientCreateSerializer,PasswordUpdateSerializer,ForgotPasswordSerializer

from rest_framework import generics

from adminapp.models import Category,Client

from rest_framework import authentication,permissions,status

from rest_framework.authtoken.models import Token

from django.shortcuts import get_object_or_404

from django.contrib.auth import authenticate

from rest_framework.response import Response

from rest_framework.views import APIView

from rest_framework import status

from datetime import date, timedelta






class GetTokenApiView(APIView):
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            username = serializer.validated_data.get("username")
            password = serializer.validated_data.get("password")

            # Authenticate user (checks hashed password)
            user = authenticate(request, username=username, password=password)

            if user is not None:
                # Create or get token
                token, created = Token.objects.get_or_create(user=user)
                return Response(
                    {
                        "token": token.key,
                        "username": user.username,
                        "message": "Login successful",
                    },
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {"message": "Invalid username or password"},
                    status=status.HTTP_401_UNAUTHORIZED
                )

        # If serializer invalid
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class CategoryCreateApiView(generics.ListCreateAPIView):

    serializer_class=CategorySerializer

    queryset=Category.objects.all()

    permission_classes=[permissions.IsAdminUser]

    authentication_classes=[authentication.BasicAuthentication]

 
    




class ClientRegisterApiView(generics.ListCreateAPIView):
    serializer_class = ClientCreateSerializer
    queryset = Client.objects.all()
    permission_classes = [permissions.IsAdminUser]  
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)  

        client = serializer.save()

        return Response(
            {
                "message": "Client registered successfully",
                "client": serializer.data,
                "subscription_details": {
                    "amount": f"{client.subscription_amount}",
                    "valid_till": client.subscription_end,
                    "status": "Active" if client.is_active else "Inactive",
                }
            },
            status=status.HTTP_201_CREATED
        )






class PasswordUpdateApiView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = PasswordUpdateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Password updated successfully"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class ClientUpdateRetrieveDeleteView(generics.RetrieveUpdateDestroyAPIView):

    queryset=Client.objects.all()

    serializer_class=ClientCreateSerializer

    authentication_classes=[authentication.BasicAuthentication]

    permission_classes=[permissions.IsAdminUser]







class ClientRenewApiView(APIView):
    
    permission_classes = [permissions.IsAdminUser]  

    def post(self, request, pk, *args, **kwargs):
        client = get_object_or_404(Client, pk=pk)

        # Ensure subscription_end exists
        if not client.subscription_end:
            return Response(
                {"error": "Client does not have an active subscription."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if current date is within 5 days before the subscription_end
        today = date.today()
        days_left = (client.subscription_end - today).days

        if days_left > 5:
            return Response(
                {"error": f"Subscription can only be renewed within the last 5 days. ({days_left} days left)"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Calculate previous subscription duration
        old_duration = (
            (client.subscription_end - client.subscription_start).days
            if client.subscription_start and client.subscription_end
            else 365
        )

        # Renew with same details
        client.renew_subscription(
            duration_days=old_duration,
            amount=client.subscription_amount,
            currency=client.subscription_currency
        )

        return Response({
            "message": f"{client.business_name or client.username}'s subscription renewed successfully!",
            "subscription_start": client.subscription_start,
            "subscription_end": client.subscription_end,
            "subscription_amount": client.subscription_amount,
            "subscription_currency": client.subscription_currency,
        }, status=status.HTTP_200_OK)



class ForgotPasswordApiView(APIView):
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "New password sent to your email."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)