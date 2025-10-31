from django.shortcuts import render

from adminapp.serializers import CategorySerializers,UserCreateSerializer,LoginSerializer

from rest_framework import generics

from adminapp.models import Category,User

from rest_framework import authentication,permissions

from rest_framework.authtoken.models import Token


from django.contrib.auth import authenticate

from rest_framework.response import Response

from rest_framework.views import APIView

from rest_framework import status






class UserListCreateApiView(generics.ListCreateAPIView):
    serializer_class = UserCreateSerializer
    queryset = User.objects.all()
    permission_classes = [permissions.IsAdminUser]


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

    serializer_class=CategorySerializers

    queryset=Category.objects.all()

    permission_classes=[permissions.IsAdminUser]

    authentication_classes=[authentication.BasicAuthentication]

    def perform_create(self, serializer):
        return serializer.save(owner=self.request.user)
    
    def get_queryset(self):
        return Category.objects.filter(owner=self.request.user)
    

