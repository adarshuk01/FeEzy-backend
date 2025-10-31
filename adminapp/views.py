from django.shortcuts import render

from adminapp.serializers import CategorySerializer,LoginSerializer,ClientCreateSerializer

from rest_framework import generics

from adminapp.models import Category,Client

from rest_framework import authentication,permissions

from rest_framework.authtoken.models import Token


from django.contrib.auth import authenticate

from rest_framework.response import Response

from rest_framework.views import APIView

from rest_framework import status








class GetTokenApiView(APIView):
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data.get("username")
            password = serializer.validated_data.get("password")

            user = authenticate(request, username=username, password=password)
            if user:
                token, created = Token.objects.get_or_create(user=user)
                return Response(
                    {"token": token.key, "username": user.username},
                    status=status.HTTP_200_OK
                )
            return Response(
                {"message": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




class CategoryCreateApiView(generics.ListCreateAPIView):

    serializer_class=CategorySerializer

    queryset=Category.objects.all()

    permission_classes=[permissions.IsAdminUser]

    authentication_classes=[authentication.BasicAuthentication]

 
    



class ClientRegisterApiView(generics.CreateAPIView):
    serializer_class = ClientCreateSerializer
    queryset = Client.objects.all()
    permission_classes = [permissions.IsAdminUser]  

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            client = serializer.save()
            return Response(
                {
                    "message": "Client registered successfully",
                    "client": serializer.data
                },
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
