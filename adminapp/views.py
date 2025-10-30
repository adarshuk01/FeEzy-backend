from django.shortcuts import render

from adminapp.serializers import CategorySerializers

from rest_framework import generics

from adminapp.models import Category,User

from rest_framework import authentication,permissions



class CategoryCreateApiView(generics.ListCreateAPIView):

    serializer_class=CategorySerializers

    queryset=Category.objects.all()

    permission_classes=[permissions.IsAdminUser]

    authentication_classes=[authentication.BasicAuthentication]

    def perform_create(self, serializer):
        return serializer.save(owner=self.request.user)
    
    def get_queryset(self):
        return Category.objects.filter(owner=self.request.user)
    

