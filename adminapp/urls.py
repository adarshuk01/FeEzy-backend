from django.urls import path

from adminapp import views

urlpatterns = [

    path('category/',views.CategoryCreateApiView.as_view()),

    path('user/',views.UserListCreateApiView.as_view()),

    path('token/',views.GetTokenApiView.as_view())


]