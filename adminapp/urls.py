from django.urls import path

from adminapp import views

urlpatterns = [

    path('category/',views.CategoryCreateApiView.as_view()),

    path('user/',views.ClientRegisterApiView.as_view()),

    path('token/',views.GetTokenApiView.as_view()),

    path('update-password/',views.PasswordUpdateApiView.as_view())


]